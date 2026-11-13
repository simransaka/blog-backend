import uuid

from sqlalchemy import Column, String, Integer, TIMESTAMP, text
from sqlalchemy.dialects.mysql import CHAR

from src.database.connection import Base

class MarkdownFile(Base):
    __tablename__ = "markdown_files"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
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