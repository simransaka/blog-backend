from sqlalchemy import func

from sqlalchemy.orm import Session

from src.database import ChatConversation, ChatJob



def get_or_create_conversation(
    db: Session,
    user_id: int,
    file_id: str,
    version: int,
) -> ChatConversation:

    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.user_id == user_id,
            ChatConversation.file_id == file_id,
            ChatConversation.version == version,
        )
        .first()
    )

    if conversation:
        return conversation

    conversation = ChatConversation(
        user_id=user_id,
        file_id=file_id,
        version=version
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def create_chat_job(
    db: Session,
    conversation_id: str,
    question: str,
) -> ChatJob:

    job = ChatJob(
        conversation_id=conversation_id,
        question=question,
        status="queued",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def update_chat_job(
    db: Session,
    job_id: str,
    status: str,
    answer: str = None,
    sources: list = None,
    error: str = None,
) -> ChatJob:

    job = (
        db.query(ChatJob)
        .filter(ChatJob.id == job_id)
        .first()
    )

    if job is None:
        return None

    job.status = status
    job.answer = answer
    job.sources = sources
    job.error = error
    job.updated_at = func.now()

    db.commit()
    db.refresh(job)

    return job


def get_conversation_history(
    db: Session,
    conversation_id: str,
) -> list:

    jobs = (
        db.query(ChatJob)
        .filter(
            ChatJob.conversation_id == conversation_id
        )
        .order_by(
            ChatJob.created_at.asc(),
            ChatJob.id.asc()
        )
        .all()
    )

    return [
        {
            "id": str(job.id),
            "question": job.question,
            "answer": job.answer,
            "sources": job.sources or [],
            "status": job.status,
            "error": job.error,
            "created_at": job.created_at,
        }
        for job in jobs
    ]