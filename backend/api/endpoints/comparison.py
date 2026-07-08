"""
API Endpoint - Comparison
===========================
Compare multiple legal documents side-by-side.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
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
from backend.utils.exceptions import LegalRAGError

logger = logging.getLogger(__name__)
blueprint = Blueprint("comparison", __name__)


@blueprint.route("", methods=["POST"])
def compare():
    """Compare two or more documents."""
    body_data = request.get_json() or {}
    try:
        body = ComparisonRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))

    db = get_db()
    # Load documents
    texts = {}
    for did in body.document_ids:
        doc = db.query(Document).filter(Document.id == did).first()
        if not doc or not doc.cleaned_text:
            raise LegalRAGError(f"Document {did} not found or has no text.")
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

    resp = ComparisonResponse(
        id=comp.id,
        document_ids=body.document_ids,
        comparison_result={**result, "summary": summary},
        differences=result.get("differences"),
        created_at=comp.created_at,
    )
    return jsonify(resp.model_dump()), 201


@blueprint.route("/<comparison_id>", methods=["GET"])
def get_comparison(comparison_id: str):
    """Get a saved comparison."""
    db = get_db()
    comp = db.query(Comparison).filter(Comparison.id == comparison_id).first()
    if not comp:
        raise LegalRAGError("Comparison not found.")
        
    resp = ComparisonResponse.model_validate(comp)
    return jsonify(resp.model_dump())


@blueprint.route("/by-clause", methods=["POST"])
def compare_by_clause():
    """Compare a specific clause type across documents."""
    body_data = request.get_json() or {}
    try:
        body = ClauseComparisonRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))

    db = get_db()
    texts = {}
    for did in body.document_ids:
        doc = db.query(Document).filter(Document.id == did).first()
        if not doc or not doc.cleaned_text:
            raise LegalRAGError(f"Document {did} not found.")
        texts[did] = doc.cleaned_text

    result = compare_by_clause_type(texts, body.clause_type)
    return jsonify(result)
