"""
Schemas - Common
=================
Shared Pydantic response / request models used across multiple endpoints.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Error / Success envelopes ─────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standardised error payload."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int = 400


class SuccessResponse(BaseModel):
    """Standardised success payload."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


# ── Pagination ────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated results."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Health ────────────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    """Health-check response."""
    status: str = "ok"
    database: str = "unknown"
    llm: str = "unknown"
    embeddings: str = "unknown"
    version: str = "1.0.0"
