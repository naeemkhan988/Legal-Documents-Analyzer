"""
API Endpoint - Pages (Server-Rendered HTML)
=============================================
Jinja2-based HTML pages replacing the React frontend.
Each route queries the DB via SQLAlchemy and renders a template.
"""

from __future__ import annotations

import logging
from flask import Blueprint, render_template

from backend.config import settings
from backend.database.models import Analysis, Document, Report
from backend.database.session import get_db

logger = logging.getLogger(__name__)
blueprint = Blueprint("pages", __name__)


# ── Dashboard ─────────────────────────────────────────────────────────
@blueprint.route("/", methods=["GET"])
def dashboard():
    """Dashboard: upload form + recent document list."""
    db = get_db()
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
    return render_template(
        "dashboard.html",
        documents=docs,
        total_docs=total_docs,
        total_analyzed=total_analyzed,
        high_risk=high_risk,
    )


# ── Document Detail ──────────────────────────────────────────────────
@blueprint.route("/document/<document_id>", methods=["GET"])
def document_detail(document_id: str):
    """Document overview with tabs: Overview / Full Text / Analysis."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return render_template(
            "dashboard.html",
            documents=[], total_docs=0,
            total_analyzed=0, high_risk=0,
            error="Document not found.",
        )
    # Try to load latest analysis
    analysis = (
        db.query(Analysis)
        .filter(Analysis.document_id == document_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    return render_template(
        "document.html",
        doc=doc,
        analysis=analysis,
    )


# ── Search ────────────────────────────────────────────────────────────
@blueprint.route("/search", methods=["GET"])
def search_page():
    """Semantic search + RAG Q&A page."""
    return render_template("search.html")


# ── Compare ───────────────────────────────────────────────────────────
@blueprint.route("/compare", methods=["GET"])
def compare_page():
    """Document comparison page with document picker."""
    db = get_db()
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )
    return render_template(
        "compare.html",
        documents=docs,
    )


# ── Reports ───────────────────────────────────────────────────────────
@blueprint.route("/reports", methods=["GET"])
def reports_page():
    """List generated reports with download links."""
    db = get_db()
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "reports.html",
        reports=reports,
    )


# ── Settings ──────────────────────────────────────────────────────────
@blueprint.route("/settings", methods=["GET"])
def settings_page():
    """LLM configuration display + system info."""
    return render_template(
        "settings.html",
        settings=settings,
    )
