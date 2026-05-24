"""
Schemas - Document
===================
Pydantic models for document upload, listing, and detail views.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────

class DocumentUploadRequest(BaseModel):
    """Metadata sent alongside the file upload (all optional)."""
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# ── Response schemas ──────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Lightweight document representation for list views."""
    id: str
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    """Full document representation including extracted text."""
    id: str
    user_id: str
    filename: str
    file_type: str
    file_path: str
    file_size: int
    raw_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentTextResponse(BaseModel):
    """Raw / cleaned text for a single document."""
    id: str
    filename: str
    raw_text: Optional[str] = None
    cleaned_text: Optional[str] = None
