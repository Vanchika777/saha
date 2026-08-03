"""
RAG service: LangChain + Groq LLM for book question-answering.
Supports single-book, multi-book retrieval, and general literary conversation.
"""
from typing import List, Generator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import Config
from app.utils.embedder import query_collection, query_multiple_collections

# ── System prompt ────────────────────────────────────────────
SYSTEM_PROMPT = """You are Saha, a warm, enthusiastic, and knowledgeable AI book companion.

Your role:
- Respond warmly to greetings, casual chatter, and general questions about literature, reading habits, authors, or genres.
- When book context is provided, ground your detailed analysis in the retrieved passages and cite the book titles.
- When NO book context is available (or the user is just saying hello), be conversational, friendly, and invite them to discuss their favorite books, ask for recommendations, or upload a book to analyze!

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
        return "No specific book content attached. Engage in friendly conversation, answer general literary queries, or welcome the user."

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

    recent = messages[-max_turns * 2:]
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
    """Non-streaming RAG or general answer."""
    chunks = []
    if book_ids and isinstance(book_ids, list) and len(book_ids) > 0:
        try:
            if len(book_ids) == 1:
                chunks = query_collection(user_id, book_ids[0], question, n_results)
            else:
                chunks = query_multiple_collections(user_id, book_ids, question, n_results_per_book=3)
        except Exception:
            chunks = []

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

    answer = getattr(response, "content", str(response))

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
    """Streaming response generator."""
    chunks = []
    
    if book_ids and isinstance(book_ids, list) and len(book_ids) > 0:
        try:
            if len(book_ids) == 1:
                chunks = query_collection(user_id, book_ids[0], question, n_results)
            else:
                chunks = query_multiple_collections(user_id, book_ids, question, n_results_per_book=3)
        except Exception:
            chunks = []

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
            yield str(chunk.content)
        elif isinstance(chunk, str) and chunk:
            yield chunk