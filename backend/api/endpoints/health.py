"""
API Endpoint - Health Checks
==============================
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import settings
from backend.dependencies import get_db
from backend.schemas.common import HealthStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=HealthStatus)
def overall_health():
    return HealthStatus(status="ok", version=settings.APP_VERSION)


@router.get("/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": str(exc)}


@router.get("/llm")
def llm_health():
    try:
        from backend.services.llm_service import check_llm_health
        ok = check_llm_health()
        return {"status": "ok" if ok else "degraded", "llm": settings.LLM_SERVICE.value}
    except Exception:
        return {"status": "unavailable", "llm": settings.LLM_SERVICE.value}


@router.get("/embeddings")
def embeddings_health():
    try:
        from backend.services.embedding_service import load_model
        load_model()
        return {"status": "ok", "model": settings.EMBEDDING_MODEL}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
