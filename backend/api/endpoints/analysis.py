"""
API Endpoint - Analysis
========================
Run full or partial analyses on uploaded documents.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.models import Analysis, Clause, Document
from backend.database.session import get_db
from backend.schemas.analysis import (
    AnalysisResponse,
    AnalysisSummaryResponse,
    ClauseResponse,
    EntityResponse,
    RiskAssessmentResponse,
)
from backend.services.clause_extractor import extract_all_clauses
from backend.services.llm_service import summarize_document, get_recommendations, extract_key_terms
from backend.services.ner_service import extract_entities
from backend.services.risk_scorer import explain_risk, get_risk_level, score_document
from backend.utils.constants import DEFAULT_USER_ID, Messages

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["Analysis"])


def _get_document(document_id: str, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, Messages.DOCUMENT_NOT_FOUND)
    if not doc.cleaned_text:
        raise HTTPException(422, "Document has no extracted text.")
    return doc


@router.post("/{document_id}", response_model=AnalysisResponse, status_code=201)
async def analyze_document(document_id: str, db: Session = Depends(get_db)):
    """Run a full analysis: clauses, entities, risk scoring, summary."""
    doc = _get_document(document_id, db)
    text = doc.cleaned_text

    # 1. Extract clauses
    extracted = extract_all_clauses(text)
    clause_dicts = [
        {"clause_type": c.clause_type, "text": c.text, "risk_level": c.risk_level,
         "confidence": c.confidence}
        for c in extracted
    ]

    # 2. Risk scoring
    risk_score = score_document(extracted)
    risk_level = get_risk_level(risk_score)
    risk_summary = explain_risk(extracted, risk_score)

    # 3. Entities
    entities = extract_entities(text)

    # 4. LLM summary (best-effort)
    try:
        summary = summarize_document(text)
    except Exception:
        summary = "Summary generation is unavailable. Please check LLM configuration."

    # 5. Recommendations (best-effort)
    try:
        clauses_text = "\n".join(f"[{c.clause_type}] {c.text[:200]}" for c in extracted[:10])
        recs = get_recommendations(clauses_text, risk_score)
    except Exception:
        recs = ["Configure an LLM backend for AI-powered recommendations."]

    # Persist analysis
    analysis = Analysis(
        document_id=document_id,
        user_id=DEFAULT_USER_ID,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_summary=risk_summary,
        clauses_json=clause_dicts,
        entities_json=entities,
        summary=summary,
        recommendations_json=recs,
    )
    db.add(analysis)

    # Persist individual clauses
    for c in extracted:
        db.add(Clause(
            analysis_id=analysis.id,
            clause_type=c.clause_type,
            text=c.text,
            risk_level=c.risk_level,
            confidence=c.confidence,
            suggested_change=c.suggested_change,
        ))

    db.commit()
    db.refresh(analysis)

    return AnalysisResponse(
        id=analysis.id,
        document_id=document_id,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_summary=risk_summary,
        summary=summary,
        clauses=[ClauseResponse(**c) for c in clause_dicts],
        entities=EntityResponse(**entities),
        recommendations=recs,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.get("/{document_id}", response_model=AnalysisResponse)
async def get_analysis(document_id: str, db: Session = Depends(get_db)):
    """Get the latest analysis for a document."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.document_id == document_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(404, Messages.ANALYSIS_NOT_FOUND)

    return AnalysisResponse(
        id=analysis.id,
        document_id=document_id,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        risk_summary=analysis.risk_summary,
        summary=analysis.summary,
        clauses=[ClauseResponse(**c) for c in (analysis.clauses_json or [])],
        entities=EntityResponse(**(analysis.entities_json or {})) if analysis.entities_json else None,
        recommendations=analysis.recommendations_json or [],
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.post("/{document_id}/clauses")
async def extract_clauses_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Extract clauses only."""
    doc = _get_document(document_id, db)
    clauses = extract_all_clauses(doc.cleaned_text)
    return {"document_id": document_id, "clauses": [
        {"clause_type": c.clause_type, "text": c.text, "confidence": c.confidence, "risk_level": c.risk_level}
        for c in clauses
    ]}


@router.post("/{document_id}/entities")
async def extract_entities_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Extract named entities only."""
    doc = _get_document(document_id, db)
    entities = extract_entities(doc.cleaned_text)
    return {"document_id": document_id, "entities": entities}


@router.post("/{document_id}/risk-score")
async def get_risk_score_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Calculate risk score only."""
    doc = _get_document(document_id, db)
    clauses = extract_all_clauses(doc.cleaned_text)
    score = score_document(clauses)
    level = get_risk_level(score)
    return {"document_id": document_id, "risk_score": score, "risk_level": level}


@router.post("/{document_id}/summary")
async def get_summary_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Generate AI summary only."""
    doc = _get_document(document_id, db)
    try:
        summary = summarize_document(doc.cleaned_text)
        key_terms = extract_key_terms(doc.cleaned_text)
    except Exception as exc:
        raise HTTPException(503, f"LLM service unavailable: {exc}")
    return AnalysisSummaryResponse(document_id=document_id, summary=summary, key_terms=key_terms)
