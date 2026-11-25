
import logging

from src.database.connection import SessionLocal
from src.chatbot.services import (
    register_markdown_file,
    update_embedding_status,
    index_markdown_file
)

logger = logging.getLogger(__name__)


def index_document_in_background(
    title: str,
    file_path: str,
    user_id: int
):
    db = SessionLocal()
    document = None

    try:
        # Register Markdown file in MySQL
        document = register_markdown_file(
            db=db,
            title=title,
            file_path=file_path,
            user_id=user_id
        )

        logger.info(
            "Markdown registered in MySQL. ID: %s, USER ID: %s",
            document.id,
            user_id
        )

        # Generate and store embeddings in ChromaDB
        chunk_count = index_markdown_file(
            file_id=document.id,
            title=document.title,
            file_path=document.file_path,
            version=document.version
        )

        # Update status in MySQL
        update_embedding_status(
            db=db,
            file_id=document.id,
            status="completed"
        )

        logger.info(
            "Background indexing completed. Chunks: %s",
            chunk_count
        )

    except Exception:
        logger.exception("Background document indexing failed.")

        if document is not None:
            try:
                db.rollback()
                update_embedding_status(
                    db=db,
                    file_id=document.id,
                    status="failed"
                )
            except Exception:
                db.rollback()
                logger.exception("Could not update embedding status.")

    finally:
        db.close()