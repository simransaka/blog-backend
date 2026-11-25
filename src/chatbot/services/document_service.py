from pathlib import Path
from sqlalchemy.orm import Session

from src.database import MarkdownFile

def register_markdown_file(
    db: Session,
    title: str,
    file_path: str,
    user_id: int
):
    markdown_file = MarkdownFile(
        title=title,
        file_path=str(Path(file_path).resolve()),
        version=1,
        embedding_status="pending",
        user_id=user_id
    )

    db.add(markdown_file)
    db.commit()
    db.refresh(markdown_file)

    return markdown_file


def update_embedding_status(
    db: Session,
    file_id: str,
    status: str
):
    document = (
        db.query(MarkdownFile)
        .filter(MarkdownFile.id == file_id)
        .first()
    )

    if document is None:
        raise ValueError(
            f"Document not found:{file_id}"
        )

    document.embedding_status = status
    db.commit()

    return document