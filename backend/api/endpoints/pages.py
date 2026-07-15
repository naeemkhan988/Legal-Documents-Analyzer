"""
API Endpoint - Pages (Server-Rendered HTML)
=============================================
Jinja2-based HTML pages replacing the React frontend.
Each route queries the DB via SQLAlchemy and renders a template.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Analysis, Document, Report
from backend.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

templates = Jinja2Templates(directory="backend/templates")

# ── Dashboard ─────────────────────────────────────────────────────────
@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard: upload form + recent document list."""
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .limit(20)
        .all()
    )
    total_docs = db.query(Document).count()
    total_analyzed = db.query(Analysis).distinct(Analysis.document_id).count()
    # Count documents with a HIGH risk analysis
    high_risk = (
        db.query(Analysis)
        .filter(Analysis.risk_level == "RED")
        .count()
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "documents": docs,
            "total_docs": total_docs,
            "total_analyzed": total_analyzed,
            "high_risk": high_risk,
        }
    )


# ── Document Detail ──────────────────────────────────────────────────
@router.get("/document/{document_id}")
def document_detail(request: Request, document_id: str, db: Session = Depends(get_db)):
    """Document overview with tabs: Overview / Full Text / Analysis."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "documents": [], "total_docs": 0,
                "total_analyzed": 0, "high_risk": 0,
                "error": "Document not found.",
            }
        )
    # Try to load latest analysis
    analysis = (
        db.query(Analysis)
        .filter(Analysis.document_id == document_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    return templates.TemplateResponse(
        "document.html",
        {
            "request": request,
            "doc": doc,
            "analysis": analysis,
        }
    )


# ── Search ────────────────────────────────────────────────────────────
@router.get("/search")
def search_page(request: Request):
    """Semantic search + RAG Q&A page."""
    return templates.TemplateResponse("search.html", {"request": request})


# ── Compare ───────────────────────────────────────────────────────────
@router.get("/compare")
def compare_page(request: Request, db: Session = Depends(get_db)):
    """Document comparison page with document picker."""
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "documents": docs,
        }
    )


# ── Reports ───────────────────────────────────────────────────────────
@router.get("/reports")
def reports_page(request: Request, db: Session = Depends(get_db)):
    """List generated reports with download links."""
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .limit(50)
        .all()
    )
    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "reports": reports,
        }
    )


# ── Settings ──────────────────────────────────────────────────────────
@router.get("/settings")
def settings_page(request: Request):
    """LLM configuration display + system info."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "settings": settings,
        }
    )
