"""
API Endpoint - Documents
=========================
Upload, list, view, and delete legal documents.
"""

from __future__ import annotations

import logging
import math
import os

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import Document
from backend.database.session import get_db
from backend.schemas.common import SuccessResponse
from backend.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentTextResponse,
)
from backend.services.document_parser import extract_text, save_upload_file
from backend.services.text_cleaner import clean_for_analysis, split_into_chunks
from backend.services.embedding_service import embed_batch, save_embeddings_to_db
from backend.services.vector_search import build_vector_index
from backend.utils.constants import DEFAULT_USER_ID, SUPPORTED_FILE_TYPES, Messages
from backend.utils.helpers import get_file_extension

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentDetailResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a legal document (PDF / DOCX / TXT), extract text, and index."""
    # Validate file type
    ext = get_file_extension(file.filename or "unknown.txt")
    if ext not in SUPPORTED_FILE_TYPES:
        raise HTTPException(400, Messages.INVALID_FILE_TYPE)

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(413, Messages.FILE_TOO_LARGE)
    await file.seek(0)

    # Save to disk
    file_path = save_upload_file(file, file.filename)

    # Extract text
    try:
        raw_text = extract_text(file_path, ext)
    except Exception as exc:
        raise HTTPException(422, f"Text extraction failed: {exc}")

    cleaned = clean_for_analysis(raw_text)

    # Persist document record
    doc = Document(
        user_id=DEFAULT_USER_ID,
        filename=file.filename or "document",
        file_type=ext,
        file_path=file_path,
        file_size=len(content),
        raw_text=raw_text,
        cleaned_text=cleaned,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Generate embeddings & build vector index (background-safe)
    try:
        chunks = split_into_chunks(cleaned)
        if chunks:
            embeddings = embed_batch(chunks)
            save_embeddings_to_db(db, doc.id, chunks, embeddings)
            build_vector_index(doc.id, chunks, embeddings)
    except Exception as exc:
        logger.warning("Embedding/indexing failed for %s: %s", doc.id, exc)

    logger.info("Document uploaded: %s (id=%s)", doc.filename, doc.id)
    return doc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all uploaded documents with pagination."""
    total = db.query(Document).count()
    offset = (page - 1) * page_size
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 1,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get full document details."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, Messages.DOCUMENT_NOT_FOUND)
    return doc


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
async def get_document_text(document_id: str, db: Session = Depends(get_db)):
    """Get raw and cleaned text for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, Messages.DOCUMENT_NOT_FOUND)
    return DocumentTextResponse(
        id=doc.id,
        filename=doc.filename,
        raw_text=doc.raw_text,
        cleaned_text=doc.cleaned_text,
    )


@router.delete("/{document_id}", response_model=SuccessResponse)
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its associated data."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, Messages.DOCUMENT_NOT_FOUND)

    # Remove file from disk
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except OSError:
        pass

    # Remove from vector index
    try:
        from backend.services.vector_search import delete_index
        delete_index(document_id)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return SuccessResponse(message=Messages.DOCUMENT_DELETED)
