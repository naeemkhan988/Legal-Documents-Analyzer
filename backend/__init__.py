"""
Legal Document Analyzer (LegalRAG) - Flask Application Factory
==============================================================
Production-ready Flask application with CORS, database init,
route registration, global error handling, and structured logging.
"""

from __future__ import annotations

import logging
import time

from flask import Flask, g, jsonify, request
from flask_cors import CORS

from backend.config import configure_logging, settings
from backend.database.session import SessionLocal, init_db
from backend.utils.exceptions import LegalRAGError

# Import blueprints
from backend.api.endpoints.analysis import blueprint as analysis_bp
from backend.api.endpoints.comparison import blueprint as comparison_bp
from backend.api.endpoints.documents import blueprint as documents_bp
from backend.api.endpoints.health import blueprint as health_bp
from backend.api.endpoints.pages import blueprint as pages_bp
from backend.api.endpoints.reports import blueprint as reports_bp
from backend.api.endpoints.search import blueprint as search_bp

# ── Logging ───────────────────────────────────────────────────────────
configure_logging()
logger = logging.getLogger(__name__)

def create_app() -> Flask:
    """Create and configure the Flask application."""
    logger.info("🚀 Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)
    
    app = Flask(
        __name__, 
        template_folder="templates", 
        static_folder="static",
        static_url_path="/static"
    )
    
    # Init DB
    init_db()
    logger.info("✅ Database initialised")
    
    # CORS setup
    # CORS_ORIGINS is typically a list in config, e.g. ["http://localhost:3000"]
    # Flask-CORS accepts a list for origins.
    CORS(app, resources={r"/*": {"origins": settings.CORS_ORIGINS}})

    # ── Request / App Context Hooks ───────────────────────────────────
    @app.before_request
    def before_request_hook():
        # Timing start
        g.start_time = time.perf_counter()
        # DB Session setup
        g.db = SessionLocal()

    @app.after_request
    def after_request_hook(response):
        if hasattr(g, "start_time"):
            elapsed = time.perf_counter() - g.start_time
            response.headers["X-Process-Time"] = f"{elapsed:.4f}"
            if elapsed > 2.0:
                logger.warning("Slow request: %s %s took %.2fs", request.method, request.path, elapsed)
        return response

    @app.teardown_appcontext
    def teardown_appcontext_hook(exception=None):
        db = getattr(g, "db", None)
        if db is not None:
            db.close()

    # ── Error Handlers ───────────────────────────────────────────────
    @app.errorhandler(LegalRAGError)
    def handle_legalrag_error(exc):
        logger.error("LegalRAGError: %s | detail=%s", exc.message, exc.detail)
        response = jsonify({
            "success": False,
            "error": exc.message,
            "detail": exc.detail
        })
        response.status_code = 422
        return response

    @app.errorhandler(Exception)
    def handle_general_exception(exc):
        # Werkzeug HTTP exceptions have a code attribute, but general exceptions don't.
        status_code = getattr(exc, "code", 500)
        
        # Don't log 404s as errors
        if status_code != 404:
            logger.exception("Unhandled exception on %s %s", request.method, request.path)
            
        detail = str(exc) if settings.DEBUG else None
        error_msg = getattr(exc, "name", "Internal server error.")
        
        response = jsonify({
            "success": False,
            "error": error_msg,
            "detail": detail
        })
        response.status_code = status_code
        return response

    # ── Register Blueprints ──────────────────────────────────────────
    app.register_blueprint(pages_bp)
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(analysis_bp, url_prefix="/api/analyze")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(comparison_bp, url_prefix="/api/compare")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    return app
