"""
API Endpoint - Comparison
===========================
Compare multiple legal documents side-by-side.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.models import Comparison, Document
from backend.database.session import get_db
from backend.schemas.analysis import (
    ClauseComparisonRequest,
    ComparisonRequest,
    ComparisonResponse,
)
from backend.services.contract_comparator import (
    compare_by_clause_type,
    compare_documents,
    generate_comparison_summary,
    highlight_changes,
)
from backend.utils.constants import DEFAULT_USER_ID

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compare", tags=["Comparison"])


@router.post("", response_model=ComparisonResponse, status_code=201)
async def compare(body: ComparisonRequest, db: Session = Depends(get_db)):
    """Compare two or more documents."""
    # Load documents
    texts = {}
    for did in body.document_ids:
        doc = db.query(Document).filter(Document.id == did).first()
        if not doc or not doc.cleaned_text:
            raise HTTPException(404, f"Document {did} not found or has no text.")
        texts[did] = doc.cleaned_text

    result = compare_documents(texts)
    result = highlight_changes(result)
    summary = generate_comparison_summary(result)

    comp = Comparison(
        user_id=DEFAULT_USER_ID,
        document_ids=body.document_ids,
        comparison_result=result,
        differences=result.get("differences"),
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)

    return ComparisonResponse(
        id=comp.id,
        document_ids=body.document_ids,
        comparison_result={**result, "summary": summary},
        differences=result.get("differences"),
        created_at=comp.created_at,
    )


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """Get a saved comparison."""
    comp = db.query(Comparison).filter(Comparison.id == comparison_id).first()
    if not comp:
        raise HTTPException(404, "Comparison not found.")
    return comp


@router.post("/by-clause")
async def compare_by_clause(body: ClauseComparisonRequest, db: Session = Depends(get_db)):
    """Compare a specific clause type across documents."""
    texts = {}
    for did in body.document_ids:
        doc = db.query(Document).filter(Document.id == did).first()
        if not doc or not doc.cleaned_text:
            raise HTTPException(404, f"Document {did} not found.")
        texts[did] = doc.cleaned_text

    result = compare_by_clause_type(texts, body.clause_type)
    return result
