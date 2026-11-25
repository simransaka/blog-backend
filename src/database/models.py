import uuid

from sqlalchemy import (
    Column,
    String,
    Integer, 
    TIMESTAMP,
    text,
    Boolean,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.dialects.mysql import CHAR

from src.database.connection import Base

class MarkdownFile(Base):
    __tablename__ = "markdown_files"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),nullable=True,
        index=True
    )

    title = Column(String(255), nullable=False)

    file_path = Column(String(500), nullable=False)

    version = Column(Integer, default=1)

    embedding_status = Column(
        String(20),
        default="pending"
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP")
    )


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )


class BlogThread(Base):
    __tablename__ = "blog_threads"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    thread_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="queued",
        server_default="queued"
    )

    current_stage = Column(
        String(100),
        nullable=True
    )

    error = Column(
        Text,
        nullable=True
    )

    review_data = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP  ")
    )


class BlogJobEvent(Base):
    __tablename__ = "blog_job_events"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    thread_id = Column(
        String(36),
        ForeignKey("blog_threads.thread_id"),
        nullable=False,
        index=True
    )

    event_type = Column(
        String(50),
        nullable=False,
    )

    event_data = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "file_id",
            "version",
            name="uq_chat_user_file_version"
        ),
    )

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    file_id = Column(
        CHAR(36),
        ForeignKey("markdown_files.id"),
        nullable=False,
        index=True
    )

    version = Column(
        Integer,
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP")
    )

class ChatJob(Base):
    __tablename__ = "chat_jobs"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    conversation_id = Column(
        CHAR(36),
        ForeignKey("chat_conversations.id"),
        nullable=False,
        index=True
    )

    question = Column(
        Text,
        nullable=False
    )

    answer = Column(
        Text,
        nullable=True
    )

    sources = Column(
        JSON,
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="queued",
        server_default="queued",
        index=True
    )

    error = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP")
    )