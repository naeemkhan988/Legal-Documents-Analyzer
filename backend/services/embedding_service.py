"""
Service - Embedding Service
=============================
Generates dense vector embeddings using Sentence-Transformers and
persists them alongside the text chunks in the database.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

import numpy as np

from backend.utils.decorators import log_execution
from backend.utils.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# ── Module-level model cache ──────────────────────────────────────────
_model = None
_model_name: str | None = None


def load_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load (or return cached) Sentence-Transformer model.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier.

    Returns
    -------
    SentenceTransformer
        The loaded model instance.
    """
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s …", model_name)
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        logger.info("Embedding model loaded successfully.")
        return _model
    except Exception as exc:
        raise EmbeddingError(
            message=f"Failed to load embedding model '{model_name}'.",
            detail=str(exc),
        )


@log_execution
def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Generate a single embedding vector for *text*.

    Returns
    -------
    np.ndarray
        1-D float32 embedding vector.
    """
    model = load_model(model_name)
    try:
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.astype(np.float32)
    except Exception as exc:
        raise EmbeddingError(message="Embedding generation failed.", detail=str(exc))


@log_execution
def embed_batch(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> List[np.ndarray]:
    """Generate embeddings for a list of texts.

    Parameters
    ----------
    texts : List[str]
        Input texts to embed.
    batch_size : int
        Encoding batch size (tune to GPU memory).

    Returns
    -------
    List[np.ndarray]
        One embedding per input text.
    """
    if not texts:
        return []

    model = load_model(model_name)
    try:
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=batch_size,
        )
        return [e.astype(np.float32) for e in embeddings]
    except Exception as exc:
        raise EmbeddingError(message="Batch embedding generation failed.", detail=str(exc))


def save_embeddings_to_db(
    db,
    document_id: str,
    chunks: List[str],
    embeddings: List[np.ndarray],
) -> int:
    """Persist text chunks and their embeddings to the ``document_embeddings`` table.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    document_id : str
        Parent document ID.
    chunks : List[str]
        Text chunks.
    embeddings : List[np.ndarray]
        Corresponding embedding vectors.

    Returns
    -------
    int
        Number of rows inserted.
    """
    from backend.database.models import DocumentEmbedding

    rows: list = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        row = DocumentEmbedding(
            document_id=document_id,
            chunk_index=idx,
            text_chunk=chunk,
            embedding=json.dumps(emb.tolist()),
        )
        rows.append(row)

    db.add_all(rows)
    db.commit()
    logger.info("Saved %d embeddings for document %s", len(rows), document_id)
    return len(rows)


def get_embeddings_from_db(
    db,
    document_id: str,
) -> List[tuple[str, np.ndarray]]:
    """Load stored embeddings for a document.

    Returns
    -------
    List[tuple[str, np.ndarray]]
        List of (text_chunk, embedding_vector) tuples ordered by chunk_index.
    """
    from backend.database.models import DocumentEmbedding

    rows = (
        db.query(DocumentEmbedding)
        .filter(DocumentEmbedding.document_id == document_id)
        .order_by(DocumentEmbedding.chunk_index)
        .all()
    )
    results: list[tuple[str, np.ndarray]] = []
    for row in rows:
        vec = np.array(json.loads(row.embedding), dtype=np.float32) if row.embedding else np.array([])
        results.append((row.text_chunk, vec))
    return results
