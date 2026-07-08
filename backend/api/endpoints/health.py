"""
API Endpoint - Health Checks
==============================
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify
from sqlalchemy import text

from backend.config import settings
from backend.database.session import get_db
from backend.schemas.common import HealthStatus

logger = logging.getLogger(__name__)
blueprint = Blueprint("health", __name__)


@blueprint.route("", methods=["GET"])
def overall_health():
    status = HealthStatus(status="ok", version=settings.APP_VERSION)
    return jsonify(status.model_dump())


@blueprint.route("/db", methods=["GET"])
def database_health():
    db = get_db()
    try:
        db.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as exc:
        return jsonify({"status": "error", "database": str(exc)})


@blueprint.route("/llm", methods=["GET"])
def llm_health():
    try:
        from backend.services.llm_service import check_llm_health
        ok = check_llm_health()
        return jsonify({"status": "ok" if ok else "degraded", "llm": settings.LLM_SERVICE.value})
    except Exception:
        return jsonify({"status": "unavailable", "llm": settings.LLM_SERVICE.value})


@blueprint.route("/embeddings", methods=["GET"])
def embeddings_health():
    try:
        from backend.services.embedding_service import load_model
        load_model()
        return jsonify({"status": "ok", "model": settings.EMBEDDING_MODEL})
    except Exception as exc:
        return jsonify({"status": "error", "detail": str(exc)})
