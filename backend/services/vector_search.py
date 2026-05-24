"""
Service - Vector Search (Chroma)
==================================
Manages the Chroma vector index for semantic similarity search
across document chunks.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from backend.config import settings
from backend.utils.decorators import log_execution
from backend.utils.exceptions import VectorDatabaseError

logger = logging.getLogger(__name__)

# ── Module-level Chroma client ────────────────────────────────────────
_client = None
_collection_cache: dict = {}


def _get_client():
    """Lazy-initialise the Chroma persistent client."""
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        persist_dir = str(settings.vector_db_path)
        _client = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False,
            )
        )
        logger.info("Chroma client initialised at %s", persist_dir)
        return _client
    except Exception:
        # Newer chromadb versions
        try:
            import chromadb

            persist_dir = str(settings.vector_db_path)
            _client = chromadb.PersistentClient(path=persist_dir)
            logger.info("Chroma PersistentClient initialised at %s", persist_dir)
            return _client
        except Exception as exc:
            raise VectorDatabaseError(
                message="Failed to initialise Chroma vector database.",
                detail=str(exc),
            )


def _get_collection(name: str = "legal_documents"):
    """Get or create a Chroma collection."""
    if name in _collection_cache:
        return _collection_cache[name]
    client = _get_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        _collection_cache[name] = collection
        return collection
    except Exception as exc:
        raise VectorDatabaseError(
            message=f"Failed to get/create collection '{name}'.",
            detail=str(exc),
        )


@log_execution
def build_vector_index(
    document_id: str,
    chunks: List[str],
    embeddings: List,
    collection_name: str = "legal_documents",
) -> int:
    """Index document chunks into Chroma.

    Parameters
    ----------
    document_id : str
        Source document identifier.
    chunks : List[str]
        Text chunks to index.
    embeddings : List
        Corresponding embedding vectors (lists or np.ndarray).
    collection_name : str
        Chroma collection name.

    Returns
    -------
    int
        Number of vectors indexed.
    """
    if not chunks:
        return 0

    collection = _get_collection(collection_name)

    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

    # Convert numpy arrays to lists if needed
    emb_lists = []
    for e in embeddings:
        emb_lists.append(e.tolist() if hasattr(e, "tolist") else list(e))

    try:
        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=emb_lists,
            metadatas=metadatas,
        )
        logger.info("Indexed %d chunks for document %s", len(chunks), document_id)
        return len(chunks)
    except Exception as exc:
        raise VectorDatabaseError(
            message="Failed to index document chunks.",
            detail=str(exc),
        )


@log_execution
def search(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
    collection_name: str = "legal_documents",
) -> List[Tuple[str, float, Optional[str]]]:
    """Perform semantic search.

    Parameters
    ----------
    query : str
        Natural language query.
    document_id : str, optional
        Restrict search to a specific document.
    top_k : int
        Number of results to return.

    Returns
    -------
    List[Tuple[str, float, Optional[str]]]
        List of (text, similarity_score, document_id) tuples.
    """
    from backend.services.embedding_service import embed_text

    collection = _get_collection(collection_name)

    try:
        query_embedding = embed_text(query).tolist()

        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "distances", "metadatas"],
        )

        output: List[Tuple[str, float, Optional[str]]] = []
        if results and results["documents"]:
            docs = results["documents"][0]
            distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)

            for doc, dist, meta in zip(docs, distances, metadatas):
                # Chroma cosine distance → similarity score
                similarity = max(0.0, 1.0 - dist)
                doc_id = meta.get("document_id") if meta else None
                output.append((doc, similarity, doc_id))

        logger.info("Search returned %d results for query: %.60s…", len(output), query)
        return output
    except Exception as exc:
        raise VectorDatabaseError(
            message="Semantic search failed.",
            detail=str(exc),
        )


def semantic_search_with_score(
    query: str,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """Convenience wrapper returning (chunk, score) pairs."""
    results = search(query, top_k=top_k)
    return [(text, score) for text, score, _ in results]


@log_execution
def delete_index(
    document_id: str,
    collection_name: str = "legal_documents",
) -> None:
    """Remove all vectors belonging to *document_id* from the index."""
    collection = _get_collection(collection_name)
    try:
        # Get existing IDs for this document
        existing = collection.get(
            where={"document_id": document_id},
            include=[],
        )
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info("Deleted %d vectors for document %s", len(existing["ids"]), document_id)
    except Exception as exc:
        logger.error("Failed to delete vectors for %s: %s", document_id, exc)
