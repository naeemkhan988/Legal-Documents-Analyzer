"""
Legal Document Analyzer - FastAPI Application
Production-ready with async support, automatic docs, and template rendering.
"""

from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import logging

from backend.config import settings, configure_logging
from backend.database.session import init_db, SessionLocal
from backend.utils.exceptions import LegalRAGError

# Import routers
from backend.api.endpoints.documents import router as documents_router
from backend.api.endpoints.analysis import router as analysis_router
from backend.api.endpoints.search import router as search_router
from backend.api.endpoints.comparison import router as comparison_router
from backend.api.endpoints.reports import router as reports_router
from backend.api.endpoints.health import router as health_router
from backend.api.endpoints.pages import router as pages_router  # Template routes
from backend.api.endpoints.tasks import router as tasks_router
from backend.api.endpoints.auth import router as auth_router

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

configure_logging()
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Legal Document Analyzer",
        description="AI-powered legal document analysis with RAG and LLM",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Mount static files and templates
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")
    templates = Jinja2Templates(directory="backend/templates")

    # Database init
    init_db()

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        if process_time > 2.0:
            logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
        return response

    # Error handlers
    @app.exception_handler(LegalRAGError)
    async def legalrag_exception_handler(request: Request, exc: LegalRAGError):
        logger.error(f"LegalRAGError: {exc.message}")
        status_code = getattr(exc, "status_code", 400)
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "error": exc.message, "detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return {"success": False, "error": "Internal server error"}

    # Register routers (API Versioning v1)
    api_v1_router = APIRouter(prefix="/api/v1")
    api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
    api_v1_router.include_router(health_router, prefix="/health", tags=["Health"])
    api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
    api_v1_router.include_router(analysis_router, prefix="/analyze", tags=["Analysis"])
    api_v1_router.include_router(search_router, prefix="/search", tags=["Search"])
    api_v1_router.include_router(comparison_router, prefix="/compare", tags=["Comparison"])
    api_v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
    api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
    
    app.include_router(api_v1_router)

    # Legacy routes (backward compatibility)
    legacy_router = APIRouter(prefix="/api", deprecated=True)
    legacy_router.include_router(auth_router, prefix="/auth")
    legacy_router.include_router(health_router, prefix="/health")
    legacy_router.include_router(documents_router, prefix="/documents")
    legacy_router.include_router(analysis_router, prefix="/analyze")
    legacy_router.include_router(search_router, prefix="/search")
    legacy_router.include_router(comparison_router, prefix="/compare")
    legacy_router.include_router(reports_router, prefix="/reports")
    legacy_router.include_router(tasks_router, prefix="/tasks")

    app.include_router(legacy_router)
    
    app.include_router(pages_router)  # Template pages at root

    logger.info("🚀 Legal Document Analyzer FastAPI started successfully")
    return app


app = create_app()