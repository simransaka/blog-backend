import logging

from langgraph.types import Command

from src.database import SessionLocal, BlogThread, BlogJobEvent
from src.graph.graph import blog

from src.chatbot.services import index_document_in_background

logger = logging.getLogger(__name__)

NODE_STAGES = {
    "router": "Router",
    "submit_evidence": "Research",
    "planner": "Blog structure",
    "reducer": "Preparing draft",
    "critique": "Reviewing blog quality",
    "revision": "Improving blog",
}


########################
### HELPER FUNCTIONS ###
########################

def extract_interrupt_data(update):
    interrupts = update.get("__interrupt__")

    if not interrupts:
        return None

    interrupt = interrupts[0]

    # LangGraph Interrupt object
    if hasattr(interrupt, "value"):
        return interrupt.value

    # Dictionary fallback
    if isinstance(interrupt, dict):
        return interrupt.get("value", interrupt)

    return None


def save_job_event(
        thread_id: str,
        event_type: str,
        event_data: dict | None = None,
):
    db = SessionLocal()

    try:
        event = BlogJobEvent(
            thread_id=thread_id,
            event_type=event_type,
            event_data=event_data,
        )

        db.add(event)
        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            f"Failed to save evnt {event_type} for thread {thread_id}"
        )
        raise

    finally:
        db.close()


def get_graph_state(config: dict):
    """
    Retrieve the latest state from the LangGraph checkpoint.
    """
    snapshot = blog.get_state(config)

    if not snapshot or not snapshot.values:
        return {}

    return snapshot.values


def get_task_ids(plan):
    if isinstance(plan, dict):
        tasks = plan.get("tasks", [])
    else:
        tasks = getattr(plan, "tasks", []) or []

    task_ids = set()
    for task in tasks:
        task_id = (
            task.get("id")
            if isinstance(task, dict)
            else getattr(task, "id", None)
        )
        if task_id is not None:
            task_ids.add(str(task_id))

    return task_ids


def section_batch_complete(expected_task_ids, completed_task_ids):
    return bool(expected_task_ids) and expected_task_ids.issubset(
        completed_task_ids
    )


def record_worker_update(
    thread_id,
    worker_update,
    expected_task_ids,
    completed_task_ids,
    sections_started_sent,
    sections_prepared_sent,
):
    if not expected_task_ids:
        raise ValueError("Worker update received without planned task IDs.")

    if not sections_started_sent:
        update_job(
            thread_id,
            current_stage="Writing blog sections",
        )
        save_job_event(
            thread_id,
            "stage",
            {
                "stage": "Writing blog sections",
                "message": "Writing blog sections in progress",
            },
        )
        save_job_event(
            thread_id,
            "sections_started",
            {"task_ids": sorted(expected_task_ids)},
        )
        sections_started_sent = True

    for section_data in worker_update.get("sections", []):
        if (
            not isinstance(section_data, (list, tuple))
            or len(section_data) < 2
        ):
            continue

        task_id = str(section_data[0])
        if task_id not in expected_task_ids:
            raise ValueError(
                f"Worker returned unexpected task ID: {task_id}"
            )

        if task_id not in completed_task_ids:
            completed_task_ids.add(task_id)
            save_section_event(thread_id, section_data)

    if (
        not sections_prepared_sent
        and section_batch_complete(expected_task_ids, completed_task_ids)
    ):
        save_job_event(thread_id, "sections_prepared", {})
        sections_prepared_sent = True

    return sections_started_sent, sections_prepared_sent


def save_section_event(thread_id: str, section_data: tuple):
    """
    Save one completed worker section as a job event.
    """

    task_id, section_content = section_data

    save_job_event(
        thread_id,
        "section_completed",
        {
            "task_id": task_id,
            "content": section_content,
        },
    )


######################
### MAIN FUNCTIONS ###
######################

def update_job(
    thread_id: str,
    status: str = None,
    current_stage: str = None,
    error: str = None
):
    db = SessionLocal()

    try:
        thread = (
            db.query(BlogThread)
            .filter(BlogThread.thread_id == thread_id)
            .first()
        )

        if thread:
            if status is not None:
                thread.status = status

            if current_stage is not None:
                thread.current_stage = current_stage

            if error is not None:
                thread.error = error

            db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed to update job: %s", thread_id)

    finally:
        db.close()




def run_blog_job(
    thread_id: str,
    graph_input,
    config: dict,
    user_id: int,
):
    """
    Run LangGraph independently of the frontend connection.
    """

    try:
        # Mark the job as running.
        update_job(
            thread_id,
            status="running",
            current_stage="Starting",
            error=None,
        )

        sections_prepared_sent = False
        sections_started_sent = False
        expected_task_ids = set()
        completed_task_ids = set()

        # Execute the graph.
        for update in blog.stream(
            graph_input,
            config=config,
            stream_mode="updates",
        ):

            for node_name in update.keys():

                if node_name in ("planner", "edit_plan"):
                    node_output = update.get(node_name, {})
                    expected_task_ids = get_task_ids(
                        node_output.get("plan")
                    )

                # Handle human-review interrupt.
                if node_name == "__interrupt__":

                    interrupt_data = extract_interrupt_data(update)

                    if interrupt_data is None:
                        raise ValueError(
                            f"Interrupt data missing for thread {thread_id}"
                        )

                    update_job(
                        thread_id,
                        status="waiting_for_review",
                        current_stage="Waiting for plan approval",
                    )

                    db = SessionLocal()

                    try:
                        thread = (
                            db.query(BlogThread)
                            .filter(
                                BlogThread.thread_id == thread_id
                            )
                            .first()
                        )

                        if thread:
                            thread.review_data = interrupt_data
                            db.commit()

                    except Exception:
                        db.rollback()

                        logger.exception(
                            "Failed to save review data for thread %s",
                            thread_id,
                        )
                        raise

                    finally:
                        db.close()

                    save_job_event(
                        thread_id,
                        "interrupt",
                        {
                            "message": "Please review the blog plan.",
                            "review_data": interrupt_data,
                        },
                    )

                    logger.info(
                        "Thread %s is waiting for human review",
                        thread_id,
                    )

                    return

                # Handle worker section progress.
                if node_name == "worker":
                    worker_update = update.get("worker", {})
                    (
                        sections_started_sent,
                        sections_prepared_sent,
                    ) = record_worker_update(
                        thread_id,
                        worker_update,
                        expected_task_ids,
                        completed_task_ids,
                        sections_started_sent,
                        sections_prepared_sent,
                    )

                # Handle workflow stages.
                stage = NODE_STAGES.get(node_name)

                if stage:
                    update_job(
                        thread_id,
                        current_stage=stage,
                    )

                    save_job_event(
                        thread_id,
                        "stage",
                        {
                            "stage": stage,
                            "message": f"{stage} completed",
                        },
                    )

                    logger.info(
                        "Thread %s: %s",
                        thread_id,
                        stage,
                    )

        # Retrieve the final graph state.
        final_state = get_graph_state(config)

        final_blog = final_state.get("final", "")
        document_title = final_state.get("document_title", "")
        document_path = final_state.get("document_path", "")

        if not final_blog:
            raise ValueError(
                "Graph completed without producing a final blog."
            )

        # Register the Markdown document and generate embeddings.
        if document_title and document_path:
            index_document_in_background(
                title=document_title,
                file_path=document_path,
                user_id=user_id,
            )

        # Save the completed blog event.
        save_job_event(
            thread_id,
            "complete",
            {
                "blog": final_blog,
                "document_title": document_title,
                "document_path": document_path,
            },
        )

        # Mark the job as completed.
        update_job(
            thread_id,
            status="completed",
            current_stage="Completed",
        )

        logger.info(
            "Blog generation completed for thread %s",
            thread_id,
        )

    except Exception as exc:
        logger.exception(
            "Blog generation failed: %s",
            thread_id,
        )

        update_job(
            thread_id,
            status="failed",
            error=str(exc),
        )

        try:
            save_job_event(
                thread_id,
                "error",
                {
                    "message": str(exc),
                },
            )

        except Exception:
            logger.exception(
                "Failed to save error event for thread %s",
                thread_id,
            )


def resume_blog_job(
    thread_id: str,
    resume_data: dict,
    config: dict,
    user_id: int,
):
    """
    Resume a paused LangGraph thread execution after human review,
    independently of the frontend connection.
    """

    try:
        # Mark the job as running.
        update_job(
            thread_id,
            status="running",
            current_stage="Resuming blog generation",
            error=None,
        )

        save_job_event(
            thread_id,
            "stage",
            {
                "stage": "Resuming blog generation",
                "message": "Blog generation resumed after human review",
            },
        )

        sections_prepared_sent = False
        sections_started_sent = False
        expected_task_ids = get_task_ids(
            get_graph_state(config).get("plan")
        )
        completed_task_ids = set()

        # Resume LangGraph execution.
        for update in blog.stream(
            Command(resume=resume_data),
            config=config,
            stream_mode="updates",
        ):

            for node_name in update.keys():

                node_output = update.get(node_name, {})

                if node_name in ("planner", "edit_plan"):
                    expected_task_ids = get_task_ids(
                        node_output.get("plan")
                    )
                    completed_task_ids.clear()
                    sections_started_sent = False
                    sections_prepared_sent = False

                elif node_name == "critique":
                    critique = node_output.get("critique")
                    feedback = (
                        critique.get("sections_to_revise", [])
                        if isinstance(critique, dict)
                        else getattr(
                            critique,
                            "sections_to_revise",
                            [],
                        )
                    )
                    if feedback:
                        expected_task_ids = {
                            str(
                                item.get("task_id")
                                if isinstance(item, dict)
                                else item.task_id
                            )
                            for item in feedback
                        }
                        completed_task_ids.clear()
                        sections_started_sent = False
                        sections_prepared_sent = False

                # Handle another human-review interrupt.
                if node_name == "__interrupt__":

                    interrupt_data = extract_interrupt_data(update)

                    if interrupt_data is None:
                        raise ValueError(
                            f"Interrupt data missing for thread {thread_id}"
                        )

                    db = SessionLocal()

                    try:
                        thread = (
                            db.query(BlogThread)
                            .filter(
                                BlogThread.thread_id == thread_id
                            )
                            .first()
                        )

                        if thread:
                            thread.status = "waiting_for_review"
                            thread.current_stage = (
                                "Waiting for plan approval"
                            )
                            thread.review_data = interrupt_data

                            db.commit()

                    except Exception:
                        db.rollback()

                        logger.exception(
                            "Failed to save review data for thread %s",
                            thread_id,
                        )
                        raise

                    finally:
                        db.close()

                    save_job_event(
                        thread_id,
                        "interrupt",
                        {
                            "message": "Please review the blog plan.",
                            "review_data": interrupt_data,
                        },
                    )

                    logger.info(
                        "Thread %s is waiting for human review",
                        thread_id,
                    )

                    return

                # Handle worker section progress.
                if node_name == "worker":
                    (
                        sections_started_sent,
                        sections_prepared_sent,
                    ) = record_worker_update(
                        thread_id,
                        node_output,
                        expected_task_ids,
                        completed_task_ids,
                        sections_started_sent,
                        sections_prepared_sent,
                    )

                # Handle workflow stages.
                stage = NODE_STAGES.get(node_name)

                if stage:
                    update_job(
                        thread_id,
                        current_stage=stage,
                    )

                    save_job_event(
                        thread_id,
                        "stage",
                        {
                            "stage": stage,
                            "message": f"{stage} completed",
                        },
                    )

                    logger.info(
                        "Thread %s: %s",
                        thread_id,
                        stage,
                    )

        # Retrieve the final graph state.
        final_state = get_graph_state(config)

        final_blog = final_state.get("final", "")
        document_title = final_state.get("document_title", "")
        document_path = final_state.get("document_path", "")

        if not final_blog:
            raise ValueError(
                "Graph completed without producing a final blog."
            )

        # Register the Markdown document and generate embeddings.
        if document_title and document_path:
            index_document_in_background(
                title=document_title,
                file_path=document_path,
                user_id=user_id,
            )

        # Save the completed blog event.
        save_job_event(
            thread_id,
            "complete",
            {
                "blog": final_blog,
                "document_title": document_title,
                "document_path": document_path,
            },
        )

        # Mark the job as completed.
        update_job(
            thread_id,
            status="completed",
            current_stage="Completed",
        )

        logger.info(
            "Blog generation completed for thread %s",
            thread_id,
        )

    except Exception as exc:
        logger.exception(
            "Blog resume failed: %s",
            thread_id,
        )

        update_job(
            thread_id,
            status="failed",
            error=str(exc),
        )

        try:
            save_job_event(
                thread_id,
                "error",
                {
                    "message": str(exc),
                },
            )

        except Exception:
            logger.exception(
                "Failed to save error event for thread %s",
                thread_id,
            )