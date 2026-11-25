import ollama

from src.config import MODEL
from src.chatbot.services import retrieve_relevant_chunks


def chat_with_markdowns(
    question: str,
    file_id: str,
    version: int,
    top_k: int = 4
):
    """
    Answer a user's question using previously generated Markdown files
    """

    if not question or not question.strip():
        raise ValueError("question cannot be empty.")

    relevant_chunks = retrieve_relevant_chunks(
        question=question,
        file_id=file_id,
        version=version,
        top_k=top_k
    )

    if not relevant_chunks:
        return {
            "answer": "I couldn't find relevant information in your Markdown documents.",
            "sources": []
        }

    # context for LLM
    context_parts = []
    sources = []

    for index, chunk in enumerate(relevant_chunks, start=1):
        metadata = chunk["metadata"]

        title = metadata.get("title", "Unknown document")
        source_file_id = metadata.get("file_id")
        chunk_index = metadata.get("chunk_index")

        context_parts.append(
            f"""
            [Source: {index}]
            Title: {title}
            File ID: {source_file_id}
            Chunk Index: {chunk_index}

            Content:
            {chunk["content"]}
            """
        )

        sources.append({
            "file_id": source_file_id,
            "title": title,
            "chunk_index": chunk_index,
            "distance": chunk["distance"]
        })

    context = "\n\n".join(context_parts)

    system_prompt = """
    You are a helpful chatbot that answers questions
    using the provided Markdown document context.

    Follow these rules:

    1. Answer using only the provided context.
    2. Do not invent or assume information.
    3. If the context does not contain the answer,
       clearly say that the information is not available.
    4. Keep your answers simple and easy to understand.
    5. Mention source references such as [Source 1]
       when using information from the context.
    """

    user_prompt = f"""
    Context:
    {context}

    User Question:
    {question}

    Answer the question using the context above
    """

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    answer = response["message"]["content"]

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }