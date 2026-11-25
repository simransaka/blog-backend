from typing import Optional
import logging
from pathlib import Path

from src.chatbot.services import (
    update_embedding_status,
    collection,
    generate_embeddings,
    index_markdown_file
)
logger = logging.getLogger(__name__)


def check_embeddings(
    file_id: str,
    version: int
) -> bool:
    result = collection.get(
        where={
            "$and": [
                {"file_id": str(file_id)},
                {"version": version}
            ]
        },
        limit=1
    )

    return len(result.get("ids", [])) > 0


def generate_missing_embeddings(document,db):
    file_id = str(document.id)
    version = document.version
    file_path = Path(document.file_path)

    if check_embeddings(file_id, version):
        logger.info(f"Embeddings already exist for file ID {file_id}")
        return

    try:
        update_embedding_status(
            db=db,
            file_id=file_id,
            status="processing"
        )

        chunk_count = index_markdown_file(
            file_id=file_id,
            title=document.title,
            file_path=str(file_path),
            version=version
        )

        update_embedding_status(
            db=db,
            file_id=file_id,
            status="completed"
        )

        logger.info(
            "Generated %s embeddings for file ID: %s",
            chunk_count,
            file_id
        )

    except Exception:
        db.rollback()

        update_embedding_status(
            db=db,
            file_id=file_id,
            status="failed"
        )

        logger.exception(
            "Embedding generation failed for file ID: %s",
            file_id
        )

        raise


def retrieve_relevant_chunks(
    question: str,
    file_id: Optional[str] = None,
    version: Optional[int] = None,
    top_k: int = 4,
):
    """
     Retrieve relevant Markdown chunks from ChromaDB.

    Args:
        question: User's question.
        file_id: Optional ID of a specific Markdown file.
        version: Optional document version.
        top_k: Maximum number of chunks to retrieve.
        
    Returns:
        List of relevant chunks with their metadata.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be greater than zero")

    # does chromadb contains embeddings
    total_chunks = collection.count()

    if total_chunks == 0:
        logger.warning("No embeddings found in ChromaDB.")
        return []

    # convert user's question into an embedding
    question_embedding = generate_embeddings(question)

    # build metadata filters
    filters = []

    if file_id is not None:
        filters.append({"file_id": str(file_id)})

    if version is not None:
        filters.append({"version": version})

    where = None

    if len(filters) == 1:
        where = filters[0]
    elif len(filters) > 1:
        where = {"$and": filters}

    # search for similar chunks
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(top_k, total_chunks),
        where=where,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    # format results
    relevant_chunks = []

    for i in range(len(results["ids"][0])):
        relevant_chunks.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return relevant_chunks