"""
Service - Vector Search (Chroma)
==================================
Manages the Chroma vector index for semantic similarity search
across document chunks. Implements hybrid search (Vector + BM25).
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict

from backend.config import settings
from backend.utils.decorators import log_execution
from backend.utils.exceptions import VectorDatabaseError

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

logger = logging.getLogger(__name__)

_client = None
_collection_cache: dict = {}


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        persist_dir = str(settings.vector_db_path)
        _client = chromadb.PersistentClient(path=persist_dir)
        return _client
    except Exception as exc:
        raise VectorDatabaseError("Failed to initialise Chroma vector database.", detail=str(exc))


def _get_collection(name: str = "legal_documents"):
    if name in _collection_cache:
        return _collection_cache[name]
    client = _get_client()
    try:
        collection = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        _collection_cache[name] = collection
        return collection
    except Exception as exc:
        raise VectorDatabaseError(f"Failed to get/create collection '{name}'.", detail=str(exc))


@log_execution
def build_vector_index(
    document_id: str,
    chunks: List[str],
    embeddings: List,
    collection_name: str = "legal_documents",
) -> int:
    if not chunks:
        return 0

    collection = _get_collection(collection_name)
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

    emb_lists = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]

    try:
        collection.upsert(ids=ids, documents=chunks, embeddings=emb_lists, metadatas=metadatas)
        return len(chunks)
    except Exception as exc:
        raise VectorDatabaseError("Failed to index document chunks.", detail=str(exc))


@log_execution
def search(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
    collection_name: str = "legal_documents",
    metadata_filter: Optional[Dict] = None,
) -> List[Tuple[str, float, Optional[str]]]:
    from backend.services.embedding_service import embed_text
    collection = _get_collection(collection_name)

    try:
        query_embedding = embed_text(query).tolist()
        
        where_filter = metadata_filter or {}
        if document_id:
            where_filter["document_id"] = document_id
            
        where_filter = where_filter if where_filter else None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2, # Fetch more for hybrid reranking
            where=where_filter,
            include=["documents", "distances", "metadatas"],
        )

        output: List[Tuple[str, float, Optional[str]]] = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0]

            for doc, dist, meta in zip(docs, distances, metadatas):
                similarity = max(0.0, 1.0 - dist)
                doc_id = meta.get("document_id") if meta else None
                output.append((doc, similarity, doc_id))

        # Hybrid Search with BM25 if available
        if BM25Okapi and output:
            tokenized_corpus = [doc[0].lower().split(" ") for doc in output]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split(" ")
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # Combine scores (normalize and average)
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
            hybrid_output = []
            for i, (doc, vector_score, doc_id) in enumerate(output):
                norm_bm25 = bm25_scores[i] / max_bm25
                hybrid_score = (vector_score * 0.7) + (norm_bm25 * 0.3)
                hybrid_output.append((doc, hybrid_score, doc_id))
            
            hybrid_output.sort(key=lambda x: x[1], reverse=True)
            output = hybrid_output[:top_k]
        else:
            output = output[:top_k]

        return output
    except Exception as exc:
        raise VectorDatabaseError("Semantic search failed.", detail=str(exc))


def delete_index(document_id: str, collection_name: str = "legal_documents") -> None:
    collection = _get_collection(collection_name)
    try:
        existing = collection.get(where={"document_id": document_id}, include=[])
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception as exc:
        logger.error("Failed to delete vectors for %s: %s", document_id, exc)
