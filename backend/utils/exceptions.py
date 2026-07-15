"""
Utils - Custom Exceptions
===========================
Typed exception hierarchy so that API endpoints can map errors to
appropriate HTTP status codes and log messages.
"""

from __future__ import annotations


class LegalRAGError(Exception):
    """Base exception for the LegalRAG application."""

    def __init__(self, message: str = "An unexpected error occurred.", detail: str | None = None, status_code: int = 400):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.message)


class DocumentProcessingError(LegalRAGError):
    """Raised when document parsing / text extraction fails."""

    def __init__(self, message: str = "Failed to process the document.", detail: str | None = None):
        super().__init__(message, detail)


class EmbeddingError(LegalRAGError):
    """Raised when embedding generation or retrieval fails."""

    def __init__(self, message: str = "Embedding operation failed.", detail: str | None = None):
        super().__init__(message, detail)


class AnalysisError(LegalRAGError):
    """Raised when a document analysis step fails."""

    def __init__(self, message: str = "Analysis operation failed.", detail: str | None = None):
        super().__init__(message, detail)


class LLMServiceError(LegalRAGError):
    """Raised when the LLM backend is unreachable or returns an error."""

    def __init__(self, message: str = "LLM service is unavailable.", detail: str | None = None):
        super().__init__(message, detail, status_code=502)


class VectorDatabaseError(LegalRAGError):
    """Raised when vector store operations (Chroma) fail."""

    def __init__(self, message: str = "Vector database operation failed.", detail: str | None = None):
        super().__init__(message, detail, status_code=500)


class FileValidationError(LegalRAGError):
    """Raised when an uploaded file fails validation checks."""

    def __init__(self, message: str = "File validation failed.", detail: str | None = None):
        super().__init__(message, detail)
