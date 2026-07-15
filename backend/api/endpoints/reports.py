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
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Analysis, Report
from backend.dependencies import get_db
from backend.schemas.analysis import ReportRequest, ReportResponse
from backend.services.report_generator import (
    export_to_excel,
    generate_html_report,
    generate_json_report,
    generate_pdf_report,
)
from backend.utils.constants import DEFAULT_USER_ID, Messages

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
def create_report(analysis_id: str, body: ReportRequest, db: Session = Depends(get_db)):
    """Generate a report asynchronously."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail=Messages.ANALYSIS_NOT_FOUND)

    from backend.services.celery_worker import generate_report_task
    from backend.database.models import Task
    
    task_res = generate_report_task.delay(analysis_id, body.report_type)
    
    task_record = Task(
        task_id=task_res.id,
        task_type=f"report_{body.report_type}",
        status="PENDING"
    )
    db.add(task_record)
    db.commit()
    
    return {"message": "Report generation started.", "task_id": task_res.id}


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    """Download a generated report file."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=Messages.REPORT_NOT_FOUND)

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    media_types = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    mimetype = media_types.get(report.report_type, "application/octet-stream")
    
    return FileResponse(
        path=file_path.absolute(),
        media_type=mimetype,
        filename=file_path.name
    )


@router.get("")
def list_reports(
    page: int = Query(1, ge=1), 
    page_size: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List all generated reports."""
    total = db.query(Report).count()
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return {
        "items": [ReportResponse.model_validate(r).model_dump() for r in reports],
        "total": total,
        "page": page,
        "total_pages": math.ceil(total / page_size) if total else 1,
    }
