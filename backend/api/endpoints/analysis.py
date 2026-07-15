"""
API Endpoint - Analysis
========================
Run full or partial analyses on uploaded documents.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.models import Analysis, Clause, Document
from backend.dependencies import get_db
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
from backend.utils.exceptions import LegalRAGError

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_document(document_id: str, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=Messages.DOCUMENT_NOT_FOUND)
    if not doc.cleaned_text:
        raise HTTPException(status_code=422, detail="Document has no extracted text.")
    return doc


@router.post("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
def analyze_document(document_id: str, db: Session = Depends(get_db)):
    """Run a full analysis asynchronously."""
    doc = _get_document(document_id, db)
    
    from backend.services.celery_worker import run_document_analysis_task
    from backend.database.models import Task
    
    task_res = run_document_analysis_task.delay(document_id)
    
    task_record = Task(
        task_id=task_res.id,
        task_type="analysis",
        status="PENDING"
    )
    db.add(task_record)
    db.commit()
    
    return {"message": "Analysis started.", "task_id": task_res.id}


@router.get("/{document_id}", response_model=AnalysisResponse)
def get_analysis(document_id: str, db: Session = Depends(get_db)):
    """Get the latest analysis for a document."""
    analysis = (
        db.query(Analysis)
        .filter(Analysis.document_id == document_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail=Messages.ANALYSIS_NOT_FOUND)

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
def extract_clauses_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Extract clauses only."""
    doc = _get_document(document_id, db)
    clauses = extract_all_clauses(doc.cleaned_text)
    return {"document_id": document_id, "clauses": [
        {"clause_type": c.clause_type, "text": c.text, "confidence": c.confidence, "risk_level": c.risk_level}
        for c in clauses
    ]}


@router.post("/{document_id}/entities")
def extract_entities_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Extract named entities only."""
    doc = _get_document(document_id, db)
    entities = extract_entities(doc.cleaned_text)
    return {"document_id": document_id, "entities": entities}


@router.post("/{document_id}/risk-score")
def get_risk_score_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Calculate risk score only."""
    doc = _get_document(document_id, db)
    clauses = extract_all_clauses(doc.cleaned_text)
    score = score_document(clauses)
    level = get_risk_level(score)
    return {"document_id": document_id, "risk_score": score, "risk_level": level}


@router.post("/{document_id}/summary", response_model=AnalysisSummaryResponse)
def get_summary_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Generate AI summary only."""
    doc = _get_document(document_id, db)
    try:
        summary = summarize_document(doc.cleaned_text)
        key_terms = extract_key_terms(doc.cleaned_text)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {exc}")
        
    return AnalysisSummaryResponse(document_id=document_id, summary=summary, key_terms=key_terms)
