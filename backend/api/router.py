"""
API - Main Router
==================
Aggregates all endpoint routers into a single API router.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.endpoints.analysis import router as analysis_router
from backend.api.endpoints.comparison import router as comparison_router
from backend.api.endpoints.documents import router as documents_router
from backend.api.endpoints.health import router as health_router
from backend.api.endpoints.reports import router as reports_router
from backend.api.endpoints.search import router as search_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)
api_router.include_router(search_router)
api_router.include_router(comparison_router)
api_router.include_router(reports_router)
