"""
API Endpoint - Reports
========================
Generate and download analysis reports in PDF / HTML / JSON / Excel.
"""

from __future__ import annotations

import logging
import math
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Analysis, Report
from backend.database.session import get_db
from backend.schemas.analysis import ReportRequest, ReportResponse
from backend.services.report_generator import (
    export_to_excel,
    generate_html_report,
    generate_json_report,
    generate_pdf_report,
)
from backend.utils.constants import DEFAULT_USER_ID, Messages
from backend.utils.exceptions import LegalRAGError

logger = logging.getLogger(__name__)
blueprint = Blueprint("reports", __name__)


@blueprint.route("/<analysis_id>", methods=["POST"])
def create_report(analysis_id: str):
    """Generate a report for an analysis."""
    body_data = request.get_json() or {}
    try:
        body = ReportRequest.model_validate(body_data)
    except Exception as exc:
        raise LegalRAGError("Invalid request data", detail=str(exc))

    db = get_db()
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise LegalRAGError(Messages.ANALYSIS_NOT_FOUND)

    analysis_data = {
        "document_id": analysis.document_id,
        "risk_score": analysis.risk_score,
        "risk_level": analysis.risk_level,
        "risk_summary": analysis.risk_summary,
        "summary": analysis.summary,
        "clauses": analysis.clauses_json or [],
        "entities": analysis.entities_json,
        "recommendations": analysis.recommendations_json or [],
    }

    # Generate report content
    reports_dir = Path(settings.UPLOAD_DIR) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]

    if body.report_type == "pdf":
        content = generate_pdf_report(analysis_data)
        file_path = reports_dir / f"report_{file_id}.pdf"
        file_path.write_bytes(content)
    elif body.report_type == "html":
        content = generate_html_report(analysis_data)
        file_path = reports_dir / f"report_{file_id}.html"
        file_path.write_text(content, encoding="utf-8")
    elif body.report_type == "json":
        import json
        content = generate_json_report(analysis_data)
        file_path = reports_dir / f"report_{file_id}.json"
        file_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    elif body.report_type == "excel":
        content = export_to_excel([analysis_data])
        file_path = reports_dir / f"report_{file_id}.xlsx"
        file_path.write_bytes(content)
    else:
        raise LegalRAGError("Unsupported report type.")

    report = Report(
        user_id=DEFAULT_USER_ID,
        analysis_id=analysis_id,
        report_type=body.report_type,
        file_path=str(file_path),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    resp = ReportResponse.model_validate(report)
    return jsonify(resp.model_dump()), 201


@blueprint.route("/<report_id>/download", methods=["GET"])
def download_report(report_id: str):
    """Download a generated report file."""
    db = get_db()
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise LegalRAGError(Messages.REPORT_NOT_FOUND)

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise LegalRAGError("Report file not found on disk.", detail=str(file_path))

    media_types = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    mimetype = media_types.get(report.report_type, "application/octet-stream")
    
    return send_file(
        file_path.absolute(),
        mimetype=mimetype,
        as_attachment=True,
        download_name=file_path.name,
    )


@blueprint.route("", methods=["GET"])
def list_reports():
    """List all generated reports."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    
    if page < 1: page = 1
    if page_size < 1: page_size = 1
    if page_size > 100: page_size = 100

    db = get_db()
    total = db.query(Report).count()
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return jsonify({
        "items": [ReportResponse.model_validate(r).model_dump() for r in reports],
        "total": total,
        "page": page,
        "total_pages": math.ceil(total / page_size) if total else 1,
    })
