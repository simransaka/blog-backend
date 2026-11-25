import json
import uuid
import logging

from typing import Literal
from pathlib import Path

from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.types import Command

from src.graph.graph import blog
from src.chatbot.services import (
    index_document_in_background
)
from src.database import MarkdownFile
from src.auth import get_current_user
from src.database import (
    User,
    BlogThread,
    SessionLocal,
    get_db,
    BlogJobEvent
)
from src.services.blog_job import run_blog_job, resume_blog_job
from api.schemas import BlogRequest, ReviewRequest


router = APIRouter()

logger = logging.getLogger(__name__)


# ==================================================
# LANGGRAPH NODE -> FRONTEND STAGE
# ==================================================

NODE_STAGES = {
    "router": "Router",
    "submit_evidence": "Research",
    "planner": "Blog structure",
    "worker": "Writing blog sections",
    "reducer": "Preparing draft",
    "critique": "Reviewing blog quality",
    "revision": "Improving blog",
}


# ==================================================
# SSE HELPER
# ==================================================

def send_event(event: dict) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


# ==================================================
# INTERRUPT EXTRACTION
# ==================================================

def get_interrupt_data(update: dict):

    interrupts = update.get("__interrupt__")

    if not interrupts:
        return None

    interrupt = interrupts[0]

    return getattr(interrupt, "value", interrupt)


# ==================================================
# PLAN HELPERS
# ==================================================

def get_plan_tasks(plan):
    """
    Extract tasks from either a dictionary or a Pydantic model.
    """

    if plan is None:
        return []

    if isinstance(plan, dict):
        return plan.get("tasks", [])

    return getattr(plan, "tasks", [])


def get_task_count(plan):
    return len(get_plan_tasks(plan))


def get_task_titles(plan):
    """
    Return a dictionary containing task IDs and their titles.

    Example:
    {
        "1": "Introduction",
        "2": "How It Works"
    }
    """

    task_titles = {}

    tasks = get_plan_tasks(plan)

    for index, task in enumerate(tasks):

        if isinstance(task, dict):
            task_id = task.get("id", index + 1)
            title = task.get("title", f"Section {task_id}")

        else:
            task_id = getattr(task, "id", index + 1)
            title = getattr(task, "title", f"Section {task_id}")

        task_titles[str(task_id)] = title

    return task_titles


# ==================================================
# GET CRITIQUE SCORE
# ==================================================

def get_critique_score(critique):

    if critique is None:
        return None

    if isinstance(critique, dict):
        return critique.get("score")

    return getattr(critique, "score", None)


# ==================================================
# GET DRAFT CONTENT
# ==================================================

def get_draft_content(node_output):

    if not isinstance(node_output, dict):
        return None

    draft = node_output.get("draft")

    if draft:
        return draft

    return node_output.get("final")


# ==================================================
# ROUTER RESPONSE
# ==================================================

def get_needs_research(node_output):
    """
    Extract the router's needs_research boolean.
    """

    if not isinstance(node_output, dict):

        if hasattr(node_output, "model_dump"):
            node_output = node_output.model_dump()

        else:
            return None

    value = node_output.get("needs_research")

    if value is None:

        router_data = node_output.get("router")

        if isinstance(router_data, dict):
            value = router_data.get("needs_research")

    return value if isinstance(value, bool) else None


# ==================================================
# RESEARCHED PAGE URLS
# ==================================================

def _as_dict(value):
    """Convert supported model objects into dictionaries."""

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "__dict__"):
        return vars(value)

    return None


def extract_researched_urls(value):
    """
    Extract page URLs from evidence, source, page, or URL collections.
    """

    urls = []
    seen = set()

    url_keys = {
        "url",
        "source_url",
        "page_url",
        "canonical_url",
    }

    collection_keys = {
        "researched_urls",
        "urls",
        "evidence",
        "sources",
        "pages",
        "fetched_pages",
    }

    def add_url(candidate):

        if not isinstance(candidate, str):
            return

        candidate = candidate.strip()

        if (
            candidate.startswith(("http://", "https://"))
            and candidate not in seen
        ):
            seen.add(candidate)
            urls.append(candidate)

    def visit(item, parent_key=None):

        if isinstance(item, (list, tuple)):

            for child in item:
                visit(child, parent_key)

            return

        if isinstance(item, str):

            if parent_key in url_keys:
                add_url(item)

            return

        item_dict = _as_dict(item)

        if not isinstance(item_dict, dict):
            return

        for key, child in item_dict.items():

            normalized_key = str(key).lower()

            if normalized_key in url_keys:

                add_url(child)

            elif normalized_key in collection_keys:

                visit(child, normalized_key)

            elif isinstance(child, (dict, list, tuple)):

                visit(child, normalized_key)

    visit(value)

    return urls


# ==================================================
# GRAPH STREAM
# ==================================================

def stream_graph(
    graph_input,
    config,
    thread_id,
    background_tasks: BackgroundTasks,
    user_id: int
):

    final_blog = ""

    expected_workers = 0

    # Track completed section IDs.
    completed_task_ids = set()

    # Track whether progress events have already been sent.
    sections_started_sent = False
    sections_event_sent = False
    draft_event_sent = False

    # Store section ID -> section title.
    task_titles = {}

    # Keep URLs from every research iteration.
    researched_urls = []

    # --------------------------------------------------
    # LOAD EXISTING PLAN FROM CHECKPOINT
    # --------------------------------------------------

    # Important for /review because the planner may not run
    # again when the graph resumes after human review.

    try:

        snapshot = blog.get_state(config)

        state_values = snapshot.values or {}

        existing_plan = state_values.get("plan")

        expected_workers = get_task_count(existing_plan)

        task_titles = get_task_titles(existing_plan)

    except Exception:

        logger.info(
            "No existing checkpoint plan found. "
            "The plan will be loaded from the planner node."
        )

    try:

        for update in blog.stream(
            graph_input,
            config=config,
            stream_mode="updates",
        ):
            logger.info("LANGGRAPH STREAM UPDATE: %s", update)

            # --------------------------------------
            # HUMAN REVIEW INTERRUPT
            # --------------------------------------

            interrupt_data = get_interrupt_data(update)

            if interrupt_data is not None:

                yield send_event({
                    "type": "interrupt",
                    "thread_id": thread_id,
                    "data": interrupt_data,
                })

                return

            # --------------------------------------
            # NODE UPDATES
            # --------------------------------------

            for node_name, node_output in update.items():

                if not isinstance(node_output, dict):
                    node_output = {}

                # ----------------------------------
                # PLANNER COMPLETED
                # ----------------------------------

                if node_name == "planner":

                    plan = node_output.get("plan")

                    expected_workers = get_task_count(plan)

                    task_titles = get_task_titles(plan)

                    logger.info(
                        "Planner completed. Expected sections: %s",
                        expected_workers
                    )

                # ----------------------------------
                # WORKER COMPLETED
                # ----------------------------------

                if node_name == "worker":

                    worker_sections = node_output.get(
                        "sections",
                        []
                    )

                    # Notify frontend that section writing
                    # has started.

                    if not sections_started_sent:

                        sections_started_sent = True

                        yield send_event({
                            "type": "sections_started",
                            "total_sections": expected_workers,
                        })

                        yield send_event({
                            "type": "stage",
                            "message": "Writing blog sections in progress",
                        })

                    # Process completed sections.

                    for section in worker_sections:

                        if (
                            not isinstance(section, (list, tuple))
                            or len(section) < 2
                        ):
                            continue

                        task_id = str(section[0])

                        # Avoid duplicate completion events.

                        if task_id in completed_task_ids:
                            continue

                        completed_task_ids.add(task_id)

                        section_title = task_titles.get(
                            task_id,
                            f"Section {task_id}"
                        )

                        logger.info(
                            "Section completed: Task ID=%s, Title=%s",
                            task_id,
                            section_title
                        )

                        # Send the completed section details
                        # to the Streamlit frontend.

                        yield send_event({
                            "type": "section_completed",
                            "task_id": task_id,
                            "title": section_title,
                        })

                    # Check whether every planned section
                    # has completed.

                    if (
                        expected_workers > 0
                        and len(completed_task_ids) >= expected_workers
                        and not sections_event_sent
                    ):

                        sections_event_sent = True

                        yield send_event({
                            "type": "sections_prepared",
                        })

                        yield send_event({
                            "type": "draft_preparing",
                        })

                # ----------------------------------
                # OTHER STAGE EVENTS
                # ----------------------------------

                logger.info(
                    "NODE UPDATE RECEIVED: %s | STAGE: %s | OUTPUT: %s",
                    node_name,
                    NODE_STAGES.get(node_name),
                    node_output
                )

                stage = NODE_STAGES.get(node_name)

                if stage:

                    if node_name != "worker":

                        stage_event = {
                            "type": "stage",
                            "message": f"{stage} completed",
                        }

                        # Include router decision.

                        if node_name == "router":

                            stage_event["needs_research"] = (
                                get_needs_research(node_output)
                            )

                        # Include researched URLs.

                        elif node_name == "submit_evidence":

                            new_urls = extract_researched_urls(
                                node_output
                            )

                            for url in new_urls:

                                if url not in researched_urls:
                                    researched_urls.append(url)

                            stage_event["researched_urls"] = list(
                                researched_urls
                            )

                        yield send_event(stage_event)

                # ----------------------------------
                # REDUCER: INITIAL DRAFT
                # ----------------------------------

                if node_name == "reducer":

                    # Fallback in case the expected worker count
                    # was unavailable.

                    if not sections_event_sent:

                        sections_event_sent = True

                        yield send_event({
                            "type": "sections_prepared",
                        })

                        yield send_event({
                            "type": "draft_preparing",
                        })

                    draft = get_draft_content(node_output)

                    if draft and not draft_event_sent:

                        draft_event_sent = True

                        yield send_event({
                            "type": "draft",
                            "draft": draft,
                        })

                        yield send_event({
                            "type": "stage",
                            "message": "Preparing draft completed",
                        })

                        yield send_event({
                            "type": "critique_started",
                        })

                # ----------------------------------
                # CRITIQUE COMPLETED
                # ----------------------------------

                if node_name == "critique":

                    critique = node_output.get("critique")

                    score = get_critique_score(critique)

                    if score is None:
                        score = node_output.get("score")

                    if score is not None:

                        yield send_event({
                            "type": "critique_completed",
                            "score": score,
                        })

                # ----------------------------------
                # REVISION
                # ----------------------------------

                if node_name == "revision":

                    yield send_event({
                        "type": "stage",
                        "message": "Improving blog in progress",
                    })

                # ----------------------------------
                # TRACK FINAL CONTENT
                # ----------------------------------

                if node_output.get("final"):

                    final_blog = node_output["final"]

        # ------------------------------------------
        # GET FINAL GRAPH STATE
        # ------------------------------------------

        snapshot = blog.get_state(config)

        state_values = snapshot.values or {}

        final_blog = state_values.get("final", final_blog)

        # Get document details saved by reducer.

        document_title = state_values.get("document_title")

        document_path = state_values.get("document_path")

        # ------------------------------------------
        # COLLECT RESEARCHED URLS
        # ------------------------------------------

        final_urls = extract_researched_urls({
            "evidence": state_values.get("evidence", []),
            "researched_urls": state_values.get(
                "researched_urls", []
            ),
            "sources": state_values.get("sources", []),
            "pages": state_values.get("pages", []),
        })

        for url in final_urls:

            if url not in researched_urls:
                researched_urls.append(url)

        # ------------------------------------------
        # FINAL CRITIQUE SCORE
        # ------------------------------------------

        critique = state_values.get("critique")

        score = get_critique_score(critique)

        if score is not None:

            yield send_event({
                "type": "critique_completed",
                "score": score,
            })

        # ------------------------------------------
        # FINAL RESEARCH EVENT
        # ------------------------------------------

        if researched_urls:

            yield send_event({
                "type": "stage",
                "message": "Research completed",
                "researched_urls": list(researched_urls),
            })

        # ------------------------------------------
        # SCHEDULE BACKGROUND INDEXING
        # ------------------------------------------

        if document_title and document_path:

            background_tasks.add_task(
                index_document_in_background,
                title=document_title,
                file_path=document_path,
                user_id=user_id
            )

            logger.info(
                "Document indexing scheduled in background."
            )

        else:

            logger.warning(
                "Document indexing skipped: title or path missing."
            )

        # ------------------------------------------
        # WORKFLOW COMPLETED
        # ------------------------------------------

        yield send_event({
            "type": "complete",
            "blog": final_blog,
        })

    except Exception as exc:

        logger.exception("Blog workflow failed")

        yield send_event({
            "type": "error",
            "message": str(exc),
        })


# ==================================================
# GENERATE BLOG
# ==================================================

@router.post("/generate")
def generate_blog(
    request: BlogRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logger.info(
        f"Blog generation requested by user_id {current_user.id}"
    )

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    graph_input = {
            "topic": request.topic,
            "sections": [],
            "draft": "",
            "final": "",
            "web_search_count": 0,
            "research_steps": 0,
            "fetch_count": 0,
            "evidence": [],
    }

    try:
        blog_thread = BlogThread(
            thread_id=thread_id,
            user_id=current_user.id,
            status="queued",
        )

        db.add(blog_thread)
        db.commit()

    except Exception:
        db.rollback()
        raise

    background_tasks.add_task(
        run_blog_job,
        thread_id,
        graph_input,
        config,
        current_user.id,
    )

    return {
        "thread_id": thread_id,
        "status": "queued",
        "message": "Blog generation started."
    }


# ==================================================
# HUMAN REVIEW
# ==================================================

@router.post("/review", status_code=202)
def submit_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # check if thread belongs to logged-in user
    blog_thread = (
        db.query(BlogThread)
        .filter(
            BlogThread.thread_id == request.thread_id,
            BlogThread.user_id == current_user.id,
        )
        .first()
    )

    if not blog_thread:
        raise HTTPException(
            status_code=404,
            detail="Blog generation job not found.",
        )

    # ensure graph is waiting for human review
    if blog_thread.status != "waiting_for_review":
        raise HTTPException(
            status_code=400,
            detail="This blog is not waiting for review."
        )

    resume_data = {
        "review": request.review
    }

    if request.edited_plan is not None:
        resume_data["edited_plan"] = request.edited_plan

    # use same langgraph thread id
    config = {
        "configurable":{
            "thread_id": request.thread_id
        }
    }

    blog_thread.status = "running"
    db.commit()

    # resume graph in background
    background_tasks.add_task(
        resume_blog_job,
        request.thread_id,
        resume_data,
        config,
        current_user.id
    )

    return {
        "thread_id": request.thread_id,
        "status": "running",
        "message": "Blog generation resumed",
    }



@router.get("/my-blogs")
def get_my_blogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the logged-in user's saved blogs.
    """

    blogs = (
        db.query(MarkdownFile)
        .filter(MarkdownFile.user_id == current_user.id)
        .order_by(MarkdownFile.id.desc())
        .all()
    )

    return [
        {
            "id": blog.id,
            "title": blog.title
        }
        for blog in blogs
    ]


@router.get("/my-blogs/{blog_id}")
def get_my_blog(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return the full Markdown content of one blog.
    Only its owner can access it.
    """

    blog = (
        db.query(MarkdownFile)
        .filter(
            MarkdownFile.id == blog_id,
            MarkdownFile.user_id == current_user.id
        )
        .first()
    )

    if not blog:
        raise HTTPException(
            status_code=404,
            detail="Blog not found.",
        )

    file_path = Path(blog.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Blog content file not found."
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Unable to read blog content."
        )

    return {
        "id": blog.id,
        "title": blog.title,
        "content": content
    }


@router.get("/status/{thread_id}")
def get_blog_status(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blog_thread = (
        db.query(BlogThread)
        .filter(
            BlogThread.thread_id == thread_id,
            BlogThread.user_id == current_user.id,
        )
        .first()
    )

    if not blog_thread:
        raise HTTPException(
            status_code=404,
            detail="Blog generation job not found.",
        )

    return {
        "thread_id": blog_thread.thread_id,
        "status": blog_thread.status,
        "current_stage": blog_thread.current_stage,
        "error": blog_thread.error,
        "review_data": blog_thread.review_data,
    }



@router.get("/events/{thread_id}")
def get_blog_events(
    thread_id: str,
    after_id: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify thread ownership.
    blog_thread = (
        db.query(BlogThread)
        .filter(
            BlogThread.thread_id == thread_id,
            BlogThread.user_id == current_user.id,
        )
        .first()
    )

    if not blog_thread:
        raise HTTPException(
            status_code=404,
            detail="Blog generation job not found.",
        )

    # Fetch events in chronological order.
    events = (
        db.query(BlogJobEvent)
        .filter(
            BlogJobEvent.thread_id == thread_id,
            BlogJobEvent.id > after_id,
        )
        .order_by(BlogJobEvent.id.asc())
        .all()
    )

    return {
        "thread_id": thread_id,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "event_data": event.event_data,
                "created_at": event.created_at.isoformat()
                if event.created_at else None,
            }
            for event in events
        ],
    }