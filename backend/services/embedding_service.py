"""
Service - Embedding Service
=============================
Generates dense vector embeddings using Sentence-Transformers and
persists them. Adds Redis caching for embeddings.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

import numpy as np
import redis

from backend.config import settings
from backend.utils.decorators import log_execution
from backend.utils.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

_model = None
_model_name: str | None = None

# Redis cache setup for embeddings
try:
    redis_client = redis.from_url(settings.CELERY_BROKER_URL)
except Exception:
    redis_client = None


def load_model(model_name: str = "all-MiniLM-L6-v2"):
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s …", model_name)
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        return _model
    except Exception as exc:
        raise EmbeddingError(f"Failed to load embedding model '{model_name}'.", detail=str(exc))


@log_execution
def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Generate a single embedding vector with caching."""
    cache_key = f"emb:{model_name}:{hash(text)}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return np.array(json.loads(cached), dtype=np.float32)

    model = load_model(model_name)
    try:
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        if redis_client:
            redis_client.setex(cache_key, 86400, json.dumps(embedding.tolist()))
        return embedding
    except Exception as exc:
        raise EmbeddingError(message="Embedding generation failed.", detail=str(exc))


@log_execution
def embed_batch(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> List[np.ndarray]:
    if not texts:
        return []
    
    # Simple caching for batch
    embeddings = []
    texts_to_embed = []
    indices_to_embed = []

    for i, text in enumerate(texts):
        cache_key = f"emb:{model_name}:{hash(text)}"
        if redis_client and (cached := redis_client.get(cache_key)):
            embeddings.append(np.array(json.loads(cached), dtype=np.float32))
        else:
            embeddings.append(None)
            texts_to_embed.append(text)
            indices_to_embed.append(i)

    if texts_to_embed:
        model = load_model(model_name)
        try:
            new_embs = model.encode(texts_to_embed, convert_to_numpy=True, show_progress_bar=False, batch_size=batch_size)
            for i, emb in zip(indices_to_embed, new_embs):
                emb_f32 = emb.astype(np.float32)
                embeddings[i] = emb_f32
                if redis_client:
                    redis_client.setex(f"emb:{model_name}:{hash(texts[i])}", 86400, json.dumps(emb_f32.tolist()))
        except Exception as exc:
            raise EmbeddingError(message="Batch embedding generation failed.", detail=str(exc))

    return embeddings


def save_embeddings_to_db(db, document_id: str, chunks: List[str], embeddings: List[np.ndarray]) -> int:
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
    return len(rows)


def get_embeddings_from_db(db, document_id: str) -> List[tuple[str, np.ndarray]]:
    from backend.database.models import DocumentEmbedding
    rows = db.query(DocumentEmbedding).filter(DocumentEmbedding.document_id == document_id).order_by(DocumentEmbedding.chunk_index).all()
    results: list[tuple[str, np.ndarray]] = []
    for row in rows:
        vec = np.array(json.loads(row.embedding), dtype=np.float32) if row.embedding else np.array([])
        results.append((row.text_chunk, vec))
    return results
