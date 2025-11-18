import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ...models import VectorChunk, Document
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Global model instance
_model = None


def get_embedding_model():
    """Get or create the embedding model"""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def create_embeddings(texts: List[str]) -> np.ndarray:
    """Create embeddings for a list of texts"""
    model = get_embedding_model()
    return model.encode(texts)


def search_documents(
    db: Session,
    query: str,
    document_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search documents using RAG"""
    logger.info(f"Searching documents with query: {query}")
    
    # Create query embedding
    query_embedding = create_embeddings([query])[0]
    
    # Build query
    query_builder = db.query(VectorChunk)
    
    if document_type:
        query_builder = query_builder.join(Document).filter(
            Document.kind == document_type
        )
    
    # Get all chunks
    chunks = query_builder.all()
    
    if not chunks:
        return []
    
    # Calculate similarities
    similarities = []
    for chunk in chunks:
        if chunk.embedding:
            # Convert embedding to numpy array if it's stored as list
            if isinstance(chunk.embedding, list):
                chunk_embedding = np.array(chunk.embedding)
            else:
                chunk_embedding = chunk.embedding
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            similarities.append((chunk, similarity))
    
    # Sort by similarity and return top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for chunk, similarity in similarities[:limit]:
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.chunk,
            "similarity": float(similarity),
            "chunk_type": chunk.chunk_type,
            "page_number": chunk.page_number
        })
    
    return results


def retrieve_context(
    db: Session,
    query: str,
    document_types: Optional[List[str]] = None,
    limit: int = 5
) -> str:
    """Retrieve context for a query using RAG"""
    results = search_documents(db, query, None, limit)
    
    if not results:
        return "No relevant context found."
    
    # Combine results into context
    context_parts = []
    for result in results:
        context_parts.append(f"Document {result['document_id']}: {result['text']}")
    
    return "\n\n".join(context_parts)


def find_similar_chunks(
    db: Session,
    chunk_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Find similar chunks to a specific chunk"""
    # Get the source chunk
    source_chunk = db.query(VectorChunk).filter(VectorChunk.id == chunk_id).first()
    
    if not source_chunk or not source_chunk.embedding:
        return []
    
    # Convert embedding to numpy array
    if isinstance(source_chunk.embedding, list):
        source_embedding = np.array(source_chunk.embedding)
    else:
        source_embedding = source_chunk.embedding
    
    # Get all other chunks
    other_chunks = db.query(VectorChunk).filter(
        VectorChunk.id != chunk_id,
        VectorChunk.embedding.isnot(None)
    ).all()
    
    # Calculate similarities
    similarities = []
    for chunk in other_chunks:
        if isinstance(chunk.embedding, list):
            chunk_embedding = np.array(chunk.embedding)
        else:
            chunk_embedding = chunk.embedding
        
        similarity = np.dot(source_embedding, chunk_embedding) / (
            np.linalg.norm(source_embedding) * np.linalg.norm(chunk_embedding)
        )
        similarities.append((chunk, similarity))
    
    # Sort by similarity and return top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for chunk, similarity in similarities[:limit]:
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.chunk,
            "similarity": float(similarity),
            "chunk_type": chunk.chunk_type,
            "page_number": chunk.page_number
        })
    
    return results


def build_context_for_requirement(
    db: Session,
    requirement_text: str,
    rfq_id: int
) -> str:
    """Build context for a specific requirement"""
    # Search for relevant evidence
    evidence_results = search_documents(
        db, requirement_text, None, limit=5
    )
    
    # Search for facility features
    facility_results = search_documents(
        db, "facility features shuttle wifi parking", "facility", limit=3
    )
    
    # Search for past performance
    past_perf_results = search_documents(
        db, "past performance similar project", "past_performance", limit=3
    )
    
    # Combine results
    context_parts = []
    
    if evidence_results:
        context_parts.append("Evidence:")
        for result in evidence_results:
            context_parts.append(f"- {result['text']}")
    
    if facility_results:
        context_parts.append("\nFacility Features:")
        for result in facility_results:
            context_parts.append(f"- {result['text']}")
    
    if past_perf_results:
        context_parts.append("\nPast Performance:")
        for result in past_perf_results:
            context_parts.append(f"- {result['text']}")
    
    return "\n".join(context_parts) if context_parts else "No relevant context found."
