"""
Legal Document Analyzer (LegalRAG) - FastAPI Application Entry Point
=====================================================================
Production-ready FastAPI application with CORS, database init,
route registration, global error handling, and structured logging.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.config import configure_logging, settings
from backend.database.session import init_db
from backend.utils.exceptions import LegalRAGError

# ── Logging ───────────────────────────────────────────────────────────
configure_logging()
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise DB on startup."""
    logger.info("🚀 Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    init_db()
    logger.info("✅ Database initialised")
    yield
    logger.info("🛑 Shutting down %s", settings.APP_NAME)


# ── App Factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered legal document analysis platform with RAG, clause extraction, and risk scoring.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Timing Middleware ─────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    if elapsed > 2.0:
        logger.warning("Slow request: %s %s took %.2fs", request.method, request.url.path, elapsed)
    return response


# ── Global Exception Handler ─────────────────────────────────────────
@app.exception_handler(LegalRAGError)
async def legalrag_error_handler(request: Request, exc: LegalRAGError):
    logger.error("LegalRAGError: %s | detail=%s", exc.message, exc.detail)
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error.", "detail": str(exc) if settings.DEBUG else None},
    )


# ── Register Routes ──────────────────────────────────────────────────
app.include_router(api_router)


# ── Root Endpoint ─────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
