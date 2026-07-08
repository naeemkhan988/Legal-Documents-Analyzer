"""
API Endpoint - Documents
=========================
Upload, list, view, and delete legal documents.
"""

from __future__ import annotations

import logging
import math
import os

from flask import Blueprint, jsonify, request

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
from backend.utils.exceptions import LegalRAGError
from backend.utils.helpers import get_file_extension

logger = logging.getLogger(__name__)
blueprint = Blueprint("documents", __name__)


@blueprint.route("/upload", methods=["POST"])
def upload_document():
    """Upload a legal document (PDF / DOCX / TXT), extract text, and index."""
    if "file" not in request.files:
        raise LegalRAGError(Messages.INVALID_FILE_TYPE, detail="No file part in the request")
        
    file = request.files["file"]
    if file.filename == "":
        raise LegalRAGError(Messages.INVALID_FILE_TYPE, detail="No selected file")

    db = get_db()

    # Validate file type
    ext = get_file_extension(file.filename or "unknown.txt")
    if ext not in SUPPORTED_FILE_TYPES:
        raise LegalRAGError(Messages.INVALID_FILE_TYPE, detail=f"Supported types: {SUPPORTED_FILE_TYPES}")

    # Read content to check size, then reset pointer
    content = file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise LegalRAGError(Messages.FILE_TOO_LARGE, detail=f"Max size is {settings.MAX_FILE_SIZE} bytes")
    file.seek(0)

    # Save to disk
    file_path = save_upload_file(file, file.filename)

    # Extract text
    try:
        raw_text = extract_text(file_path, ext)
    except Exception as exc:
        raise LegalRAGError("Text extraction failed", detail=str(exc))

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
    
    # Return 201 Created with JSON
    response_data = DocumentDetailResponse.model_validate(doc).model_dump()
    return jsonify(response_data), 201


@blueprint.route("", methods=["GET"])
def list_documents():
    """List all uploaded documents with pagination."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    
    if page < 1: page = 1
    if page_size < 1: page_size = 1
    if page_size > 100: page_size = 100

    db = get_db()
    total = db.query(Document).count()
    offset = (page - 1) * page_size
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    
    resp = DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 1,
    )
    return jsonify(resp.model_dump())


@blueprint.route("/<document_id>", methods=["GET"])
def get_document(document_id: str):
    """Get full document details."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise LegalRAGError(Messages.DOCUMENT_NOT_FOUND)
        
    return jsonify(DocumentDetailResponse.model_validate(doc).model_dump())


@blueprint.route("/<document_id>/text", methods=["GET"])
def get_document_text(document_id: str):
    """Get raw and cleaned text for a document."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise LegalRAGError(Messages.DOCUMENT_NOT_FOUND)
        
    resp = DocumentTextResponse(
        id=doc.id,
        filename=doc.filename,
        raw_text=doc.raw_text,
        cleaned_text=doc.cleaned_text,
    )
    return jsonify(resp.model_dump())


@blueprint.route("/<document_id>", methods=["DELETE"])
def delete_document(document_id: str):
    """Delete a document and its associated data."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise LegalRAGError(Messages.DOCUMENT_NOT_FOUND)

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
    
    return jsonify(SuccessResponse(message=Messages.DOCUMENT_DELETED).model_dump())
