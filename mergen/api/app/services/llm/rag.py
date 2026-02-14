"""
MergenLite — RAG Service (pgvector-backed)
============================================
Retrieval-Augmented Generation service that:
  1. Splits documents into chunks
  2. Generates embeddings via OpenAI (text-embedding-3-small)
  3. Stores embeddings in PostgreSQL using pgvector
  4. Performs semantic search with cosine distance

Falls back to in-process sentence-transformers when OpenAI key is absent.
"""

import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...models import Document, VectorChunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding backends
# ---------------------------------------------------------------------------
_OPENAI_DIMENSION = 1536
_LOCAL_DIMENSION = 384  # all-MiniLM-L6-v2
_local_model = None


def _openai_embed(texts: List[str]) -> List[List[float]]:
    """Call OpenAI embeddings API."""
    import openai

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small",
    )
    return [d.embedding for d in resp.data]


def _local_embed(texts: List[str]) -> List[List[float]]:
    """Fallback: sentence-transformers (CPU-only, no API key needed)."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
    vecs = _local_model.encode(texts)
    return [v.tolist() for v in vecs]


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Create embeddings — OpenAI when available, else local model."""
    if os.getenv("OPENAI_API_KEY"):
        try:
            return _openai_embed(texts)
        except Exception as exc:
            logger.warning("OpenAI embedding failed, falling back to local: %s", exc)
    return _local_embed(texts)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_text(
    text_content: str,
    max_tokens: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split *text_content* into overlapping chunks of roughly *max_tokens* words.
    Returns a list of dicts: {"text": ..., "token_count": ...}
    """
    words = text_content.split()
    chunks: List[Dict[str, Any]] = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)
        if chunk_str.strip():
            chunks.append({
                "text": chunk_str,
                "token_count": len(chunk_words),
            })
        start += max_tokens - overlap
    return chunks


# ---------------------------------------------------------------------------
# Ingest: chunk → embed → store
# ---------------------------------------------------------------------------
def ingest_document(
    db: Session,
    document_id: int,
    raw_text: str,
    chunk_type: str = "paragraph",
    page_number: Optional[int] = None,
) -> int:
    """
    Split *raw_text* into chunks, embed them, and INSERT into vector_chunks.
    Returns the number of chunks created.
    """
    chunks = chunk_text(raw_text)
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = create_embeddings(texts)

    count = 0
    for chunk_info, emb in zip(chunks, embeddings):
        vc = VectorChunk(
            document_id=document_id,
            chunk=chunk_info["text"],
            embedding=emb,
            chunk_type=chunk_type,
            page_number=page_number,
            token_count=chunk_info["token_count"],
        )
        db.add(vc)
        count += 1

    db.commit()
    logger.info("Ingested %d chunks for document_id=%d", count, document_id)
    return count


# ---------------------------------------------------------------------------
# Search (pgvector cosine distance)
# ---------------------------------------------------------------------------
def search_documents(
    db: Session,
    query: str,
    document_type: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Semantic search using pgvector's `<=>` (cosine distance) operator.
    Falls back to in-memory numpy cosine similarity when pgvector is not available.
    """
    query_emb = create_embeddings([query])[0]

    # Try native pgvector query first
    try:
        return _pgvector_search(db, query_emb, document_type, limit)
    except Exception:
        logger.debug("pgvector native query unavailable, falling back to numpy")
        return _numpy_search(db, query_emb, document_type, limit)


def _pgvector_search(
    db: Session,
    query_emb: List[float],
    document_type: Optional[str],
    limit: int,
) -> List[Dict[str, Any]]:
    """Use pgvector `<=>` operator for fast cosine-distance search."""
    emb_str = "[" + ",".join(str(v) for v in query_emb) + "]"

    sql = """
        SELECT vc.id, vc.document_id, vc.chunk, vc.chunk_type, vc.page_number,
               1 - (vc.embedding <=> :emb::vector) AS similarity
        FROM vector_chunks vc
    """
    if document_type:
        sql += " JOIN documents d ON d.id = vc.document_id WHERE d.kind = :kind"
    sql += " ORDER BY vc.embedding <=> :emb::vector LIMIT :lim"

    params: dict = {"emb": emb_str, "lim": limit}
    if document_type:
        params["kind"] = document_type

    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "chunk_id": r[0],
            "document_id": r[1],
            "text": r[2],
            "chunk_type": r[3],
            "page_number": r[4],
            "similarity": float(r[5]),
        }
        for r in rows
    ]


def _numpy_search(
    db: Session,
    query_emb: List[float],
    document_type: Optional[str],
    limit: int,
) -> List[Dict[str, Any]]:
    """Fallback: fetch all chunks and compute cosine similarity in Python."""
    q = db.query(VectorChunk)
    if document_type:
        q = q.join(Document).filter(Document.kind == document_type)
    chunks = q.all()

    if not chunks:
        return []

    query_vec = np.array(query_emb)
    scored = []
    for chunk in chunks:
        if chunk.embedding is None:
            continue
        emb_arr = np.array(chunk.embedding) if isinstance(chunk.embedding, list) else chunk.embedding
        sim = float(np.dot(query_vec, emb_arr) / (np.linalg.norm(query_vec) * np.linalg.norm(emb_arr) + 1e-9))
        scored.append((chunk, sim))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "text": c.chunk,
            "chunk_type": c.chunk_type,
            "page_number": c.page_number,
            "similarity": sim,
        }
        for c, sim in scored[:limit]
    ]


# ---------------------------------------------------------------------------
# Higher-level helpers
# ---------------------------------------------------------------------------
def retrieve_context(
    db: Session,
    query: str,
    document_types: Optional[List[str]] = None,
    limit: int = 5,
) -> str:
    """Retrieve and concatenate the top-k relevant chunks as context string."""
    results = search_documents(db, query, None, limit)
    if not results:
        return "No relevant context found."
    return "\n\n".join(
        f"[Doc {r['document_id']}] {r['text']}" for r in results
    )


def find_similar_chunks(
    db: Session,
    chunk_id: int,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Find chunks similar to a given chunk."""
    source = db.query(VectorChunk).filter(VectorChunk.id == chunk_id).first()
    if not source or source.embedding is None:
        return []

    emb = source.embedding if isinstance(source.embedding, list) else list(source.embedding)
    try:
        return _pgvector_search(db, emb, None, limit + 1)
    except Exception:
        return _numpy_search(db, emb, None, limit + 1)


def build_context_for_requirement(
    db: Session,
    requirement_text: str,
    rfq_id: int,
) -> str:
    """Build a structured context block for a specific RFQ requirement."""
    evidence = search_documents(db, requirement_text, None, limit=5)
    facility = search_documents(db, "facility features shuttle wifi parking", "facility", limit=3)
    past_perf = search_documents(db, "past performance similar project", "past_performance", limit=3)

    parts: List[str] = []
    if evidence:
        parts.append("Evidence:")
        parts.extend(f"- {r['text']}" for r in evidence)
    if facility:
        parts.append("\nFacility Features:")
        parts.extend(f"- {r['text']}" for r in facility)
    if past_perf:
        parts.append("\nPast Performance:")
        parts.extend(f"- {r['text']}" for r in past_perf)

    return "\n".join(parts) if parts else "No relevant context found."
