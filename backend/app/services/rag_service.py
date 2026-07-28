"""
RAG service: LangChain + Groq LLM for book question-answering.
Supports single-book and multi-book retrieval.
"""
from typing import List, Optional, Generator
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from app.config import Config
from app.utils.embedder import query_collection, query_multiple_collections

# ── System prompt ────────────────────────────────────────────
SYSTEM_PROMPT = """You are Saha, an expert AI book companion. You help users explore, understand, and discuss books with deep insight and enthusiasm.

You have access to the actual content of the user's books through retrieved passages. When answering:
- Ground your answers in the retrieved passages when relevant
- Cite the book title when referencing specific content
- Be conversational, insightful, and intellectually engaging
- If a question isn't covered by the retrieved passages, you may use your general knowledge but be transparent about it
- For questions about themes, characters, or plot — be thoughtful and literary in your analysis

Context from books:
{context}

Chat history:
{chat_history}"""

HUMAN_TEMPLATE = "{question}"


def _build_llm(streaming: bool = False) -> ChatGroq:
    return ChatGroq(
        api_key=Config.GROQ_API_KEY,
        model=Config.GROQ_MODEL,
        temperature=0.7,
        streaming=streaming,
        max_tokens=2048,
    )


def _format_context(chunks: List[dict]) -> str:
    """Format retrieved chunks into a readable context block."""
    if not chunks:
        return "No specific book content retrieved for this query."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("book_title", "Unknown Book")
        text = chunk.get("text", "")
        parts.append(f"[{i}] From '{title}':\n{text}")

    return "\n\n---\n\n".join(parts)


def _format_history(messages: List[dict], max_turns: int = 6) -> str:
    """Format recent chat history for context window."""
    if not messages:
        return "No previous conversation."

    recent = messages[-max_turns * 2:]  # last N turns (user + assistant each)
    parts = []
    for m in recent:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Saha: {content}")

    return "\n".join(parts)


def answer_question(
    user_id: str,
    book_ids: List[str],
    question: str,
    chat_history: List[dict],
    n_results: int = 5,
) -> dict:
    """
    Non-streaming RAG answer.

    Returns:
        {answer: str, sources: [{book_title, chunk_index, text_snippet}]}
    """
    # Retrieve relevant chunks
    if len(book_ids) == 1:
        chunks = query_collection(user_id, book_ids[0], question, n_results)
    else:
        chunks = query_multiple_collections(user_id, book_ids, question, n_results_per_book=3)

    context = _format_context(chunks)
    history = _format_history(chat_history)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_TEMPLATE),
    ])

    llm = _build_llm(streaming=False)
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "chat_history": history,
        "question": question,
    })

    answer = response.content

    # Build sources for citation display
    sources = [
        {
            "book_title": c.get("book_title"),
            "book_id": c.get("book_id"),
            "chunk_index": c.get("chunk_index"),
            "text_snippet": c.get("text", "")[:200],
        }
        for c in chunks[:3]
    ]

    return {"answer": answer, "sources": sources}


def stream_answer(
    user_id: str,
    book_ids: List[str],
    question: str,
    chat_history: List[dict],
    n_results: int = 5,
) -> Generator[str, None, None]:
    """
    Streaming RAG answer — yields token strings one by one.
    Use with Flask SSE or SocketIO.
    """
    if len(book_ids) == 1:
        chunks = query_collection(user_id, book_ids[0], question, n_results)
    else:
        chunks = query_multiple_collections(user_id, book_ids, question, n_results_per_book=3)

    context = _format_context(chunks)
    history = _format_history(chat_history)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_TEMPLATE),
    ])

    llm = _build_llm(streaming=True)
    chain = prompt | llm

    for chunk in chain.stream({
        "context": context,
        "chat_history": history,
        "question": question,
    }):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content
