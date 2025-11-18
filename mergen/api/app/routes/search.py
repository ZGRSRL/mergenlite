from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import VectorChunk
from ..services.llm.rag import search_documents

router = APIRouter()


@router.get("/")
async def search(
    query: str,
    document_type: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search documents using RAG"""
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Search using RAG
    results = search_documents(db, query, document_type, limit)
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@router.get("/similar/{chunk_id}")
async def find_similar(
    chunk_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Find similar chunks to a specific chunk"""
    
    chunk = db.query(VectorChunk).filter(VectorChunk.id == chunk_id).first()
    
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    # TODO: Implement similarity search using vector embeddings
    # This would use FAISS or similar vector database
    
    return {
        "chunk_id": chunk_id,
        "similar_chunks": []
    }



