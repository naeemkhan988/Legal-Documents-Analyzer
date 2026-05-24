"""
API Endpoint - Search
======================
Semantic search and RAG-powered Q&A across documents.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.models import SearchHistory
from backend.database.session import get_db
from backend.schemas.analysis import (
    RAGAnswerRequest,
    RAGAnswerResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from backend.services.rag_pipeline import full_rag_answer
from backend.services.vector_search import search as vector_search
from backend.utils.constants import DEFAULT_USER_ID

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(body: SearchRequest, db: Session = Depends(get_db)):
    """Search across all documents."""
    results = vector_search(body.query, document_id=body.document_id, top_k=body.top_k)
    items = [
        SearchResultItem(text=text, score=round(score, 4), document_id=doc_id)
        for text, score, doc_id in results
    ]

    # Log search
    db.add(SearchHistory(
        user_id=DEFAULT_USER_ID, query=body.query,
        document_id=body.document_id, results_count=len(items),
    ))
    db.commit()

    return SearchResponse(query=body.query, results=items, total=len(items))


@router.post("/{document_id}", response_model=SearchResponse)
async def search_within_document(
    document_id: str, body: SearchRequest, db: Session = Depends(get_db),
):
    """Search within a specific document."""
    results = vector_search(body.query, document_id=document_id, top_k=body.top_k)
    items = [
        SearchResultItem(text=text, score=round(score, 4), document_id=doc_id)
        for text, score, doc_id in results
    ]
    return SearchResponse(query=body.query, results=items, total=len(items))


@router.get("/history")
async def get_search_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get search history."""
    total = db.query(SearchHistory).count()
    rows = (
        db.query(SearchHistory)
        .order_by(SearchHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {"id": r.id, "query": r.query, "results_count": r.results_count,
             "created_at": str(r.created_at)}
            for r in rows
        ],
        "total": total,
    }


@router.post("/rag-answer", response_model=RAGAnswerResponse)
async def rag_answer(body: RAGAnswerRequest, db: Session = Depends(get_db)):
    """RAG pipeline: retrieve context + generate answer."""
    try:
        result = full_rag_answer(body.query, document_id=body.document_id)
    except Exception as exc:
        raise HTTPException(503, f"RAG pipeline error: {exc}")

    sources = [
        SearchResultItem(text=s["text"], score=s["score"], document_id=s.get("document_id"))
        for s in result.get("sources", [])
    ]
    return RAGAnswerResponse(
        query=body.query, answer=result["answer"], sources=sources,
    )
