"""
Legal Document Analyzer (LegalRAG) - Configuration Module
==========================================================
Centralised configuration management. All tunables are loaded from
environment variables (or a `.env` file) and exposed as typed,
validated Pydantic settings objects.
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings

# ── Project root (one level above ``backend/``) ────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class LLMProvider(str, Enum):
    """Supported LLM backend providers."""
    OLLAMA = "ollama"
    GROQ = "groq"
    HUGGINGFACE = "huggingface"


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    # -- General --------------------------------------------------------
    APP_NAME: str = "LegalRAG"
    APP_VERSION: str = "1.0.0"
    FASTAPI_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"

    # -- Database -------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./legal_analyzer.db"

    # -- LLM ------------------------------------------------------------
    LLM_SERVICE: LLMProvider = LLMProvider.OLLAMA

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "mixtral-8x7b-32768"

    HF_API_TOKEN: str = ""
    HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # -- Embeddings -----------------------------------------------------
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # -- Vector DB ------------------------------------------------------
    VECTOR_DB_PATH: str = "./chroma_db"

    # -- File Uploads ---------------------------------------------------
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 52_428_800  # 50 MB

    # -- CORS -----------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # -- Logging --------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # -- Google Calendar (optional) -------------------------------------
    GOOGLE_CALENDAR_CREDENTIALS_FILE: str = ""
    GOOGLE_CALENDAR_TOKEN_FILE: str = ""

    # -- Validators -----------------------------------------------------
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: str | list) -> list:
        """Accept both a JSON string and a Python list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()

    # -- Derived helpers ------------------------------------------------
    @property
    def upload_path(self) -> Path:
        """Resolved upload directory, created if absent."""
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def vector_db_path(self) -> Path:
        """Resolved Chroma persistent directory."""
        p = Path(self.VECTOR_DB_PATH)
        p.mkdir(parents=True, exist_ok=True)
        return p

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ── Singleton instance -------------------------------------------------
settings = Settings()


def configure_logging() -> None:
    """Set up root logger according to ``settings.LOG_LEVEL``."""
    log_fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format=log_fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Silence overly chatty third-party loggers
    for noisy in ("httpx", "httpcore", "chromadb", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
