import logging

from src.database import SessionLocal
from src.database import ChatJob, ChatConversation

from .chat_service import chat_with_markdowns

from .chat_persistence_service import update_chat_job


logger = logging.getLogger(__name__)


def process_chat_job_in_background(
    job_id: str,
    top_k: int=4,
):
    db = SessionLocal()

    try:
        # fetch chat job
        job = (
            db.query(ChatJob)
            .filter(ChatJob.id == job_id)
            .first()
        )

        if job is None:
            logger.error(f"Chat job not found {job_id}")
            return

        # fetch job's conversation
        conversation = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.id == job.conversation_id
            )
            .first()
        )

        if conversation is None:
            raise ValueError("Chat conversation not found")

        # mark job as processing
        update_chat_job(
            db=db,
            job_id=job_id,
            status="processing",
        )

        # generate the answer
        response = chat_with_markdowns(
            question=job.question,
            file_id=str(conversation.file_id),
            version=conversation.version,
            top_k=top_k,
        )

        # save the answer
        update_chat_job(
            db=db,
            job_id=job_id,
            status="completed",
            answer=response.get("answer"),
            sources=response.get("sources", [])
        )

        logger.info(
            f"Chat job completed successfully: {job_id}"
        )

    except Exception as exc:
        db.rollback()

        logger.exception(
            f"Background chat job failed: {job_id}"
        )

        try:
            update_chat_job(
                db=db,
                job_id=job_id,
                status="failed",
                error=str(exc)
            )
        except Exception:
            db.rollback()
            logger.exception(
                f"Could not update failed job: {job_id}"
            )

    finally:
        db.close()