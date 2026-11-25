from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.chatbot.services import chat_with_markdowns
from src.auth import get_current_user
from src.database import (
    MarkdownFile,
    User,
    ChatJob,
    ChatConversation,
)
from src.chatbot.services.chat_persistence_service import (
    get_or_create_conversation,
    create_chat_job,
    get_conversation_history,
)
from src.chatbot.services.background_chat import (
    process_chat_job_in_background
)


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    file_id: str
    question: str
    top_k: int = 4

class ConversationRequest(BaseModel):
    file_id: str


@router.post("")
def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(MarkdownFile)
        .filter(
            MarkdownFile.id == request.file_id,
            MarkdownFile.user_id == current_user.id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Markdown file not found"
        )

    # find or create conversation
    conversation = get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        file_id=str(document.id),
        version=document.version,
    )

    # create independent chat job
    job = create_chat_job(
        db=db,
        conversation_id=str(conversation.id),
        question=request.question,
    )

    background_tasks.add_task(
        process_chat_job_in_background,
        str(job.id),
        request.top_k,
    )

    return {
        "job_id": str(job.id),
        "conversation_id": str(conversation.id),
        "status": job.status,
        "message": "Chat job created successfully."
    }


@router.get("/documents")
def get_chat_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(MarkdownFile)
        .filter(MarkdownFile.user_id == current_user.id)
        .order_by(MarkdownFile.id.desc())
        .all()
    )

    return [
        {
            "id": str(document.id),
            "title": document.title,
            "version": document.version
        }
        for document in documents
    ]



@router.get("/jobs/{job_id}")
def get_chat_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = (
        db.query(ChatJob)
        .join(
            ChatConversation,
            ChatJob.conversation_id == ChatConversation.id,
        )
        .filter(
            ChatJob.id == job_id,
            ChatConversation.user_id == current_user.id,
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Chat job not found",
        )

    return {
        "job_id": str(job.id),
        "question": job.question,
        "answer": job.answer,
        "sources": job.sources or [],
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at,
    }



@router.get("/conversations/{conversation_id}/history")
def get_chat_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Chat conversation not found",
        )

    history = get_conversation_history(
        db=db,
        conversation_id=str(conversation.id),
    )

    return {
        "conversation_id": str(conversation.id),
        "file_id": str(conversation.file_id),
        "version": conversation.version,
        "messages": history,
    }


@router.post("/conversations")
def get_or_create_chat_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify document ownership
    document = (
        db.query(MarkdownFile)
        .filter(
            MarkdownFile.id == request.file_id,
            MarkdownFile.user_id == current_user.id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Markdown file not found",
        )

    conversation = get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        file_id=str(document.id),
        version=document.version,
    )

    return {
        "conversation_id": str(conversation.id),
        "file_id": str(document.id),
        "version": document.version,
    }
