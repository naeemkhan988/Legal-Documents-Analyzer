"""
Service - RAG Pipeline
========================
Retrieval-Augmented Generation pipeline with Query Expansion and Reranking.
"""

from __future__ import annotations

import logging
from typing import Dict, Generator, List, Optional

from backend.services.llm_service import generate_text, stream_response
from backend.services.vector_search import search
from backend.utils.decorators import log_execution
from backend.utils.helpers import truncate_text
from backend.utils.prompts import RAG_ANSWER_PROMPT

logger = logging.getLogger(__name__)


def rewrite_query(query: str) -> str:
    """Use LLM to rewrite/expand the query for better retrieval."""
    prompt = f"Rewrite the following legal query to improve search retrieval by adding synonyms and relevant legal terms. Only return the rewritten query.\n\nQuery: {query}"
    try:
        expanded = generate_text(prompt, max_tokens=100)
        return expanded.strip()
    except Exception:
        return query


@log_execution
def retrieve_context(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """Retrieve the most relevant text chunks using hybrid search."""
    expanded_query = rewrite_query(query)
    logger.info(f"Original Query: {query} | Expanded: {expanded_query}")
    
    results = search(expanded_query, document_id=document_id, top_k=top_k)

    if not results:
        return ""

    # Simple LLM reranking prompt could go here, but hybrid search covers basic reranking.
    context_parts: List[str] = []
    for idx, (text, score, doc_id) in enumerate(results, 1):
        context_parts.append(f"[Source {idx} | Score: {score:.2f}]\n{text}")

    return "\n\n---\n\n".join(context_parts)


@log_execution
def generate_answer(query: str, context: str) -> str:
    if not context:
        return "I couldn't find relevant information in the uploaded documents."

    prompt = RAG_ANSWER_PROMPT.format(
        context=truncate_text(context, 5000),
        question=query,
    )
    return generate_text(prompt, max_tokens=600)


@log_execution
def full_rag_answer(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
) -> Dict:
    expanded_query = rewrite_query(query)
    results = search(expanded_query, document_id=document_id, top_k=top_k)

    sources = [
        {"text": text, "score": round(score, 4), "document_id": doc_id}
        for text, score, doc_id in results
    ]

    context = "\n\n---\n\n".join(f"[Source {i}]\n{text}" for i, (text, _, _) in enumerate(results, 1))
    answer = generate_answer(query, context)

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
    }


def stream_rag_response(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
) -> Generator[str, None, None]:
    context = retrieve_context(query, document_id=document_id, top_k=top_k)
    if not context:
        yield "I couldn't find relevant information."
        return

    prompt = RAG_ANSWER_PROMPT.format(context=truncate_text(context, 5000), question=query)
    for token in stream_response(prompt):
        yield token
