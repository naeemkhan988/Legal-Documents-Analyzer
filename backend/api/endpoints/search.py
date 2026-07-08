"""
API Endpoint - Search
======================
Semantic search and RAG-powered Q&A across documents.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import Blueprint, jsonify, request
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
from backend.utils.exceptions import LegalRAGError

logger = logging.getLogger(__name__)
blueprint = Blueprint("search", __name__)


@blueprint.route("", methods=["POST"])
def semantic_search():
    """Search across all documents."""
    body_data = request.get_json() or {}
    try:
        body = SearchRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))
        
    db = get_db()
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

    resp = SearchResponse(query=body.query, results=items, total=len(items))
    return jsonify(resp.model_dump())


@blueprint.route("/<document_id>", methods=["POST"])
def search_within_document(document_id: str):
    """Search within a specific document."""
    body_data = request.get_json() or {}
    try:
        body = SearchRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))

    results = vector_search(body.query, document_id=document_id, top_k=body.top_k)
    items = [
        SearchResultItem(text=text, score=round(score, 4), document_id=doc_id)
        for text, score, doc_id in results
    ]
    
    resp = SearchResponse(query=body.query, results=items, total=len(items))
    return jsonify(resp.model_dump())


@blueprint.route("/history", methods=["GET"])
def get_search_history():
    """Get search history."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    
    if page < 1: page = 1
    if page_size < 1: page_size = 1
    if page_size > 100: page_size = 100

    db = get_db()
    total = db.query(SearchHistory).count()
    rows = (
        db.query(SearchHistory)
        .order_by(SearchHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return jsonify({
        "items": [
            {"id": r.id, "query": r.query, "results_count": r.results_count,
             "created_at": str(r.created_at)}
            for r in rows
        ],
        "total": total,
    })


@blueprint.route("/rag-answer", methods=["POST"])
def rag_answer():
    """RAG pipeline: retrieve context + generate answer."""
    body_data = request.get_json() or {}
    try:
        body = RAGAnswerRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))
        
    try:
        result = full_rag_answer(body.query, document_id=body.document_id)
    except Exception as exc:
        raise LegalRAGError(f"RAG pipeline error: {exc}")

    sources = [
        SearchResultItem(text=s["text"], score=s["score"], document_id=s.get("document_id"))
        for s in result.get("sources", [])
    ]
    resp = RAGAnswerResponse(
        query=body.query, answer=result["answer"], sources=sources,
    )
    return jsonify(resp.model_dump())
