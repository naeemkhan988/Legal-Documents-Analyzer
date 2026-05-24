"""
Database - ORM Models
======================
Complete SQLAlchemy models for the 8 core tables:

1. User
2. Document
3. DocumentEmbedding
4. Analysis
5. Clause
6. Comparison
7. SearchHistory
8. Report
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin


def _uuid() -> str:
    """Generate a URL-safe UUID4 string."""
    return uuid.uuid4().hex


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. User
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class User(Base, TimestampMixin):
    """Registered platform user."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", lazy="selectin"
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    comparisons: Mapped[list["Comparison"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    search_history: Mapped[list["SearchHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Document
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Document(Base, TimestampMixin):
    """An uploaded legal document (PDF / DOCX / TXT)."""

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, txt
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="documents")
    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename!r}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. DocumentEmbedding
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DocumentEmbedding(Base, TimestampMixin):
    """Vector embedding for a text chunk belonging to a document."""

    __tablename__ = "document_embeddings"
    __table_args__ = (
        Index("ix_embeddings_doc_chunk", "document_id", "chunk_index"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialised vector

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<DocumentEmbedding doc={self.document_id} chunk={self.chunk_index}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Analysis(Base, TimestampMixin):
    """Full analysis output for a document."""

    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_doc_user", "document_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)  # RED/YELLOW/GREEN
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    clauses_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    entities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="analyses")
    user: Mapped["User"] = relationship(back_populates="analyses")
    clauses: Mapped[list["Clause"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Analysis doc={self.document_id} risk={self.risk_level}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Clause
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Clause(Base, TimestampMixin):
    """Individual clause extracted from an analysis."""

    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_type: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suggested_change: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="clauses")

    def __repr__(self) -> str:
        return f"<Clause {self.clause_type!r} risk={self.risk_level}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Comparison(Base, TimestampMixin):
    """Side-by-side comparison of two or more documents."""

    __tablename__ = "comparisons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    comparison_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    differences: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="comparisons")

    def __repr__(self) -> str:
        return f"<Comparison docs={self.document_ids}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. SearchHistory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SearchHistory(Base, TimestampMixin):
    """Audit log of user search queries."""

    __tablename__ = "search_history"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory q={self.query[:30]!r}>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Report(Base, TimestampMixin):
    """Generated report artefact (PDF / HTML / JSON / Excel)."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, html, json, excel
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="reports")
    analysis: Mapped["Analysis"] = relationship(back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report {self.report_type} analysis={self.analysis_id}>"
