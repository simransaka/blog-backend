from pathlib import Path
import logging

import chromadb
import ollama

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import EMBEDDING_MODEL, CHROMA_DIR

logger = logging.getLogger(__name__)

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name="markdown_documents"
)

# forming chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n## ", "\n### ", "\n\n", "\n", " "]
)

def generate_embeddings(text: str) -> list[float]:
    response = ollama.embeddings(
        model = EMBEDDING_MODEL,
        prompt = text
    )

    return response["embedding"]

def index_markdown_file(
    file_id: str,
    title: str,
    file_path: str,
    version: int = 1
):
    file_id = str(file_id)
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {file_path}"
        )

    existing = collection.get(
        where={
            "$and": [
                {"file_id": file_id},
                {"version": version}
            ]
        },
        include=["metadatas"]
    )

    existing_chunks = existing.get("ids") or []

    if existing_chunks:
        logger.info(
            f"Embeddings already exist for file {file_id} with version {version}"
        )

        return len(existing_chunks)

    markdown_content = path.read_text(encoding="utf-8")

    chunks = text_splitter.split_text(markdown_content)

    if not chunks:
        raise ValueError("Markdown file contains no content.")

    embeddings = [
        generate_embeddings(chunk)
        for chunk in chunks
    ]

    chunk_ids = [
        f"{file_id}_{version}_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "file_id": file_id,
            "title": title,
            "chunk_index": i,
            "version": version
        }
        for i in range(len(chunks))
    ]

    # Remove older versions after new embeddings are ready
    collection.delete(
        where={"file_id": file_id}
    )

    # storing in chromadb
    collection.add(
        ids=chunk_ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(
        f"Successfully indexed {len(chunks)} chunks for file {file_id}"
    )

    return len(chunks)