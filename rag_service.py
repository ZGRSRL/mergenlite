#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Servisi
Vector embeddings ve semantic search için
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("sentence-transformers not available, using simple text matching")

class RAGService:
    """RAG servisi - Vector embeddings ve semantic search"""
    
    def __init__(self):
        self.model = None
        if RAG_AVAILABLE:
            try:
                # Hafif model kullan (daha hızlı)
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("RAG model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load RAG model: {e}")
                self.model = None
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Metinler için embeddings oluştur"""
        
        if not RAG_AVAILABLE or self.model is None:
            # Basit fallback - metin uzunluğu bazlı
            return np.array([[len(text)] for text in texts])
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return np.array([[len(text)] for text in texts])
    
    def retrieve_relevant_context(self, query_text: str, documents: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """İlgili bağlamı getir"""
        
        if documents is None:
            # Eğer doküman listesi verilmemişse, query'den direkt çıkarım yap
            return [{
                'text': query_text[:500],
                'relevance_score': 1.0,
                'source': 'query'
            }]
        
        try:
            # Query ve dokümanlar için embeddings oluştur
            query_embedding = self.create_embeddings([query_text])[0]
            doc_embeddings = self.create_embeddings(documents)
            
            # Cosine similarity hesapla
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append({
                    'text': documents[i][:500],  # İlk 500 karakter
                    'relevance_score': float(similarity),
                    'source': f'document_{i}'
                })
            
            # En yüksek benzerlik skoruna göre sırala
            similarities.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Top 5 sonucu döndür
            return similarities[:5]
        
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return [{
                'text': query_text[:500],
                'relevance_score': 1.0,
                'source': 'fallback'
            }]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Metni chunk'lara böl"""
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            
            start = end - overlap
        
        return chunks
    
    def search_similar(self, query: str, corpus: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Benzer metinleri ara"""
        
        return self.retrieve_relevant_context(query, corpus)[:top_k]

