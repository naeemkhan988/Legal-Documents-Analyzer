"""
Schemas - Analysis
===================
Pydantic models for analysis results, clauses, entities, risk scoring,
and document comparison.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Clause ────────────────────────────────────────────────────────────

class ClauseResponse(BaseModel):
    """Single extracted clause."""
    id: Optional[str] = None
    clause_type: str
    text: str
    risk_level: Optional[str] = None
    confidence: float = 0.0
    suggested_change: Optional[str] = None

    class Config:
        from_attributes = True


# ── Entity ────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    """Named-entity extraction result."""
    parties: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    amounts: List[Dict[str, Any]] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    organisations: List[str] = Field(default_factory=list)


# ── Risk ──────────────────────────────────────────────────────────────

class RiskAssessmentResponse(BaseModel):
    """Overall risk assessment for a document."""
    risk_score: float = Field(ge=0, le=100)
    risk_level: str  # RED / YELLOW / GREEN
    risk_summary: str
    clause_risks: List[ClauseResponse] = Field(default_factory=list)


# ── Full Analysis ─────────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    """Complete analysis output."""
    id: str
    document_id: str
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_summary: Optional[str] = None
    summary: Optional[str] = None
    clauses: List[ClauseResponse] = Field(default_factory=list)
    entities: Optional[EntityResponse] = None
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisSummaryResponse(BaseModel):
    """AI-generated document summary."""
    document_id: str
    summary: str
    key_terms: List[str] = Field(default_factory=list)


# ── Comparison ────────────────────────────────────────────────────────

class ComparisonRequest(BaseModel):
    """Request body for comparing multiple documents."""
    document_ids: List[str] = Field(min_length=2, max_length=5)


class ClauseComparisonRequest(BaseModel):
    """Request body for clause-specific comparison."""
    document_ids: List[str] = Field(min_length=2, max_length=5)
    clause_type: str


class ComparisonResponse(BaseModel):
    """Side-by-side comparison result."""
    id: str
    document_ids: List[str]
    comparison_result: Optional[Dict[str, Any]] = None
    differences: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Search ────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(min_length=1, max_length=1000)
    document_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    """Individual search hit."""
    text: str
    score: float
    document_id: Optional[str] = None
    chunk_index: Optional[int] = None


class SearchResponse(BaseModel):
    """Search results list."""
    query: str
    results: List[SearchResultItem]
    total: int


class RAGAnswerRequest(BaseModel):
    """RAG pipeline question."""
    query: str = Field(min_length=1, max_length=1000)
    document_id: Optional[str] = None


class RAGAnswerResponse(BaseModel):
    """RAG pipeline answer with sources."""
    query: str
    answer: str
    sources: List[SearchResultItem] = Field(default_factory=list)


# ── Report ────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    """Report generation request."""
    report_type: str = Field(default="pdf", pattern="^(pdf|html|json|excel)$")


class ReportResponse(BaseModel):
    """Report metadata."""
    id: str
    analysis_id: str
    report_type: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
