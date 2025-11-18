"""
AutoGen Document Management System
Manuel döküman ekleme ve analiz sistemi
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import shutil

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AutoGen imports (optional)
try:
    from autogen import ConversableAgent, GroupChat, GroupChatManager
    from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, using fallback analysis only")

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor

@dataclass
class DocumentMetadata:
    """Döküman metadata"""
    id: str
    title: str
    description: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: datetime
    source: str  # "manual", "sam_api", "bulk_upload"
    tags: List[str]
    notice_id: Optional[str] = None
    opportunity_title: Optional[str] = None
    analysis_status: str = "pending"  # "pending", "analyzing", "completed", "failed"
    analysis_results: Optional[Dict] = None

@dataclass
class AnalysisResult:
    """Analiz sonucu"""
    document_id: str
    analysis_type: str  # "content", "keywords", "sentiment", "summary"
    result: Dict[str, Any]
    confidence: float
    timestamp: datetime
    agent_name: str

class DocumentStorageManager:
    """Döküman depolama yöneticisi"""
    
    def __init__(self):
        self.storage_dir = Path("./documents/manual_uploads")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Alt klasörler
        self.pdf_dir = self.storage_dir / "pdfs"
        self.doc_dir = self.storage_dir / "docs"
        self.txt_dir = self.storage_dir / "texts"
        self.other_dir = self.storage_dir / "others"
        
        for dir_path in [self.pdf_dir, self.doc_dir, self.txt_dir, self.other_dir]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info(f"Document storage initialized: {self.storage_dir}")
    
    def save_document(self, file_content: bytes, filename: str, metadata: DocumentMetadata) -> bool:
        """Dökümanı kaydet"""
        try:
            # Dosya tipine göre klasör seç
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                target_dir = self.pdf_dir
            elif file_ext in ['.doc', '.docx']:
                target_dir = self.doc_dir
            elif file_ext == '.txt':
                target_dir = self.txt_dir
            else:
                target_dir = self.other_dir
            
            # Dosya adını güvenli hale getir
            safe_filename = self._create_safe_filename(filename)
            file_path = target_dir / safe_filename
            
            # Dosyayı kaydet
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Metadata'yı güncelle
            metadata.file_path = str(file_path)
            metadata.file_size = len(file_content)
            
            logger.info(f"Document saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Document save error: {e}")
            return False
    
    def _create_safe_filename(self, filename: str) -> str:
        """Güvenli dosya adı oluştur"""
        # Güvenli karakterler
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        
        # Dosya adını temizle
        safe_name = "".join(c for c in filename if c in safe_chars)
        
        # UUID ekle (benzersizlik için)
        name_parts = Path(safe_name).stem, Path(safe_name).suffix
        unique_name = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}{name_parts[1]}"
        
        return unique_name
    
    def get_document_path(self, document_id: str) -> Optional[Path]:
        """Döküman yolunu al"""
        # Veritabanından document_id ile file_path'i al
        # Bu fonksiyon database manager ile entegre edilecek
        pass

class DocumentAnalysisAgent:
    """Döküman analiz agenti"""
    
    def __init__(self, name: str = "DocumentAnalyzer"):
        self.name = name
        self.agent = None
        
        # OpenAI API key kontrolü
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and AUTOGEN_AVAILABLE:
            try:
                self.agent = ConversableAgent(
                    name=name,
                    system_message=f"""Sen bir döküman analiz uzmanısın. Görevin:
                    
                    1. **İçerik Analizi:** Dökümanın ana konularını ve temalarını belirle
                    2. **Anahtar Kelime Çıkarımı:** Önemli terimleri ve kavramları çıkar
                    3. **Özet Oluşturma:** Dökümanın önemli noktalarını özetle
                    4. **Kategori Belirleme:** Dökümanı uygun kategoriye yerleştir
                    5. **İlgili Fırsatlar:** SAM.gov fırsatlarıyla ilişkilendir
                    
                    Analiz sonuçlarını JSON formatında döndür:
                    {{
                        "summary": "Döküman özeti",
                        "keywords": ["anahtar1", "anahtar2"],
                        "categories": ["kategori1", "kategori2"],
                        "themes": ["tema1", "tema2"],
                        "confidence": 0.85,
                        "related_opportunities": ["fırsat1", "fırsat2"]
                    }}
                    """,
                    llm_config={
                        "model": "gpt-4",
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                )
                logger.info("AutoGen agent initialized with OpenAI")
            except Exception as e:
                logger.warning(f"AutoGen agent initialization failed: {e}")
                self.agent = None
        else:
            logger.warning("OpenAI API key not found, using fallback analysis")
    
    def analyze_document(self, document_content: str, metadata: DocumentMetadata) -> AnalysisResult:
        """Dökümanı analiz et"""
        try:
            if self.agent:
                # AutoGen agent ile analiz
                prompt = f"""
                Aşağıdaki dökümanı analiz et:
                
                **Döküman Bilgileri:**
                - Başlık: {metadata.title}
                - Açıklama: {metadata.description}
                - Kaynak: {metadata.source}
                - Etiketler: {', '.join(metadata.tags)}
                
                **Döküman İçeriği:**
                {document_content[:5000]}  # İlk 5000 karakter
                
                Lütfen detaylı analiz yap ve JSON formatında sonuç döndür.
                """
                
                # Agent ile analiz
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # JSON parse et
                try:
                    result_data = json.loads(response)
                except json.JSONDecodeError:
                    # JSON parse edilemezse basit analiz yap
                    result_data = {
                        "summary": response[:500],
                        "keywords": metadata.tags,
                        "categories": ["General"],
                        "themes": ["Document Analysis"],
                        "confidence": 0.7,
                        "related_opportunities": []
                    }
            else:
                # Fallback analiz (AutoGen olmadan)
                result_data = self._fallback_analysis(document_content, metadata)
            
            # Analiz sonucu oluştur
            analysis_result = AnalysisResult(
                document_id=metadata.id,
                analysis_type="comprehensive",
                result=result_data,
                confidence=result_data.get("confidence", 0.7),
                timestamp=datetime.now(),
                agent_name=self.name
            )
            
            logger.info(f"Document analysis completed: {metadata.id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return AnalysisResult(
                document_id=metadata.id,
                analysis_type="comprehensive",
                result={"error": str(e)},
                confidence=0.0,
                timestamp=datetime.now(),
                agent_name=self.name
            )
    
    def _fallback_analysis(self, document_content: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Fallback analiz (AutoGen olmadan)"""
        try:
            # Basit analiz yap
            content_lower = document_content.lower()
            
            # Anahtar kelime çıkarımı (basit)
            words = content_lower.split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # 3 karakterden uzun kelimeler
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # En sık kullanılan kelimeler
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [word for word, freq in top_keywords]
            
            # Kategori belirleme (basit)
            categories = []
            if any(word in content_lower for word in ['hotel', 'lodging', 'accommodation']):
                categories.append('Hospitality')
            if any(word in content_lower for word in ['contract', 'agreement', 'service']):
                categories.append('Contract Services')
            if any(word in content_lower for word in ['technical', 'software', 'system']):
                categories.append('Technology')
            if not categories:
                categories = ['General']
            
            # Özet oluşturma (basit)
            sentences = document_content.split('.')
            summary = '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else document_content[:200] + '...'
            
            return {
                "summary": summary,
                "keywords": keywords,
                "categories": categories,
                "themes": metadata.tags if metadata.tags else ["Document Analysis"],
                "confidence": 0.6,  # Fallback için düşük güven
                "related_opportunities": [],
                "analysis_method": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis error: {e}")
            return {
                "summary": f"Document: {metadata.title}",
                "keywords": metadata.tags if metadata.tags else [],
                "categories": ["General"],
                "themes": ["Document Analysis"],
                "confidence": 0.5,
                "related_opportunities": [],
                "analysis_method": "fallback_error"
            }

class DocumentDatabaseManager:
    """Döküman veritabanı yöneticisi"""
    
    def __init__(self):
        self.db_conn = None
        self._connect_db()
        self._create_tables()
    
    def _connect_db(self):
        """Veritabanına bağlan"""
        try:
            self.db_conn = psycopg2.connect(
                host='localhost',
                database='sam',
                user='postgres',
                password='postgres'
            )
            logger.info("Document database connected")
        except Exception as e:
            logger.error(f"Document database connection failed: {e}")
            self.db_conn = None
    
    def _create_tables(self):
        """Döküman tablolarını oluştur"""
        if not self.db_conn:
            return
        
        try:
            with self.db_conn.cursor() as cur:
                # Manuel dökümanlar tablosu
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS manual_documents (
                        id VARCHAR(255) PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        description TEXT,
                        file_path VARCHAR(1000) NOT NULL,
                        file_type VARCHAR(50) NOT NULL,
                        file_size BIGINT NOT NULL,
                        upload_date TIMESTAMP NOT NULL,
                        source VARCHAR(50) NOT NULL,
                        tags TEXT[],
                        notice_id VARCHAR(255),
                        opportunity_title VARCHAR(500),
                        analysis_status VARCHAR(50) DEFAULT 'pending',
                        analysis_results JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Analiz sonuçları tablosu
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_analysis_results (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(255) NOT NULL,
                        analysis_type VARCHAR(100) NOT NULL,
                        result JSONB NOT NULL,
                        confidence FLOAT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        agent_name VARCHAR(100) NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES manual_documents(id)
                    )
                """)
                
                # Döküman-fırsat ilişkileri tablosu
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_opportunity_relations (
                        id SERIAL PRIMARY KEY,
                        document_id VARCHAR(255) NOT NULL,
                        opportunity_id VARCHAR(255) NOT NULL,
                        relation_type VARCHAR(100) NOT NULL,
                        confidence FLOAT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES manual_documents(id),
                        FOREIGN KEY (opportunity_id) REFERENCES opportunities(opportunity_id)
                    )
                """)
                
                self.db_conn.commit()
                logger.info("Document tables created successfully")
                
        except Exception as e:
            logger.error(f"Table creation error: {e}")
            if self.db_conn:
                self.db_conn.rollback()
    
    def save_document_metadata(self, metadata: DocumentMetadata) -> bool:
        """Döküman metadata'sını kaydet"""
        if not self.db_conn:
            return False
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO manual_documents (
                        id, title, description, file_path, file_type, file_size,
                        upload_date, source, tags, notice_id, opportunity_title,
                        analysis_status, analysis_results
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        file_path = EXCLUDED.file_path,
                        file_type = EXCLUDED.file_type,
                        file_size = EXCLUDED.file_size,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    metadata.id, metadata.title, metadata.description,
                    metadata.file_path, metadata.file_type, metadata.file_size,
                    metadata.upload_date, metadata.source, metadata.tags,
                    metadata.notice_id, metadata.opportunity_title,
                    metadata.analysis_status, json.dumps(metadata.analysis_results) if metadata.analysis_results else None
                ))
                
                self.db_conn.commit()
                logger.info(f"Document metadata saved: {metadata.id}")
                return True
                
        except Exception as e:
            logger.error(f"Document metadata save error: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False
    
    def save_analysis_result(self, analysis_result: AnalysisResult) -> bool:
        """Analiz sonucunu kaydet"""
        if not self.db_conn:
            return False
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO document_analysis_results (
                        document_id, analysis_type, result, confidence, timestamp, agent_name
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    analysis_result.document_id,
                    analysis_result.analysis_type,
                    json.dumps(analysis_result.result),
                    analysis_result.confidence,
                    analysis_result.timestamp,
                    analysis_result.agent_name
                ))
                
                # Dökümanın analiz durumunu güncelle
                cur.execute("""
                    UPDATE manual_documents 
                    SET analysis_status = 'completed', 
                        analysis_results = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    json.dumps(analysis_result.result),
                    analysis_result.document_id
                ))
                
                self.db_conn.commit()
                logger.info(f"Analysis result saved: {analysis_result.document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Analysis result save error: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False
    
    def get_documents(self, limit: int = 100, status: str = None) -> List[Dict]:
        """Dökümanları al"""
        if not self.db_conn:
            return []
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM manual_documents"
                params = []
                
                if status:
                    query += " WHERE analysis_status = %s"
                    params.append(status)
                
                query += " ORDER BY upload_date DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Get documents error: {e}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict]:
        """ID ile döküman al"""
        if not self.db_conn:
            return None
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM manual_documents WHERE id = %s",
                    (document_id,)
                )
                result = cur.fetchone()
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Get document by ID error: {e}")
            return None
    
    def close(self):
        """Bağlantıyı kapat"""
        if self.db_conn:
            self.db_conn.close()

class AutoGenDocumentManager:
    """AutoGen döküman yönetim sistemi"""
    
    def __init__(self):
        self.storage_manager = DocumentStorageManager()
        self.database_manager = DocumentDatabaseManager()
        self.analysis_agent = DocumentAnalysisAgent()
        
        logger.info("AutoGen Document Manager initialized")
    
    def upload_document(self, file_content: bytes, filename: str, 
                       title: str, description: str = "", 
                       tags: List[str] = None, notice_id: str = None) -> Dict[str, Any]:
        """Döküman yükle"""
        
        try:
            # Metadata oluştur
            document_id = str(uuid.uuid4())
            file_type = Path(filename).suffix.lower()
            
            metadata = DocumentMetadata(
                id=document_id,
                title=title,
                description=description,
                file_path="",  # Storage manager tarafından doldurulacak
                file_type=file_type,
                file_size=0,  # Storage manager tarafından doldurulacak
                upload_date=datetime.now(),
                source="manual",
                tags=tags or [],
                notice_id=notice_id
            )
            
            # Dökümanı kaydet
            if self.storage_manager.save_document(file_content, filename, metadata):
                # Metadata'yı veritabanına kaydet
                if self.database_manager.save_document_metadata(metadata):
                    logger.info(f"Document uploaded successfully: {document_id}")
                    
                    return {
                        'success': True,
                        'document_id': document_id,
                        'message': 'Döküman başarıyla yüklendi'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Metadata kaydetme hatası'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Dosya kaydetme hatası'
                }
                
        except Exception as e:
            logger.error(f"Document upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_document(self, document_id: str) -> Dict[str, Any]:
        """Dökümanı analiz et"""
        
        try:
            # Döküman metadata'sını al
            metadata_dict = self.database_manager.get_document_by_id(document_id)
            if not metadata_dict:
                return {
                    'success': False,
                    'error': 'Döküman bulunamadı'
                }
            
            # Metadata objesi oluştur (gereksiz alanları çıkar)
            metadata_dict_clean = {k: v for k, v in metadata_dict.items() 
                                 if k in ['id', 'title', 'description', 'file_path', 'file_type', 
                                         'file_size', 'upload_date', 'source', 'tags', 'notice_id', 
                                         'opportunity_title', 'analysis_status', 'analysis_results']}
            metadata = DocumentMetadata(**metadata_dict_clean)
            
            # Analiz durumunu güncelle
            metadata.analysis_status = "analyzing"
            self.database_manager.save_document_metadata(metadata)
            
            # Döküman içeriğini oku
            file_path = Path(metadata.file_path)
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'Dosya bulunamadı'
                }
            
            # Dosya tipine göre içerik oku
            if metadata.file_type == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif metadata.file_type == '.pdf':
                # PDF okuma için PyPDF2 veya benzeri kütüphane gerekli
                content = f"[PDF Content - {metadata.title}]"
            else:
                content = f"[File Content - {metadata.title}]"
            
            # Analiz yap
            analysis_result = self.analysis_agent.analyze_document(content, metadata)
            
            # Analiz sonucunu kaydet
            if self.database_manager.save_analysis_result(analysis_result):
                return {
                    'success': True,
                    'analysis_result': analysis_result.result,
                    'confidence': analysis_result.confidence,
                    'message': 'Analiz tamamlandı'
                }
            else:
                return {
                    'success': False,
                    'error': 'Analiz sonucu kaydetme hatası'
                }
                
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_documents_list(self, limit: int = 100, status: str = None) -> List[Dict]:
        """Döküman listesini al"""
        return self.database_manager.get_documents(limit, status)
    
    def get_document_analysis(self, document_id: str) -> Optional[Dict]:
        """Döküman analizini al"""
        document = self.database_manager.get_document_by_id(document_id)
        if document and document.get('analysis_results'):
            return document['analysis_results']
        return None
    
    def close(self):
        """Sistemleri kapat"""
        self.database_manager.close()

# Global instance
autogen_doc_manager = AutoGenDocumentManager()

def upload_manual_document(file_content: bytes, filename: str, 
                          title: str, description: str = "", 
                          tags: List[str] = None, notice_id: str = None) -> Dict[str, Any]:
    """Manuel döküman yükle"""
    return autogen_doc_manager.upload_document(
        file_content, filename, title, description, tags, notice_id
    )

def analyze_manual_document(document_id: str) -> Dict[str, Any]:
    """Manuel dökümanı analiz et"""
    return autogen_doc_manager.analyze_document(document_id)

def get_manual_documents(limit: int = 100, status: str = None) -> List[Dict]:
    """Manuel dökümanları al"""
    return autogen_doc_manager.get_documents_list(limit, status)

def get_document_analysis_results(document_id: str) -> Optional[Dict]:
    """Döküman analiz sonuçlarını al"""
    return autogen_doc_manager.get_document_analysis(document_id)

if __name__ == "__main__":
    # Test
    print("AutoGen Document Management System Test")
    
    # Test dökümanı oluştur
    test_content = b"This is a test document content for analysis."
    test_filename = "test_document.txt"
    
    # Döküman yükle
    result = upload_manual_document(
        file_content=test_content,
        filename=test_filename,
        title="Test Document",
        description="Test document for AutoGen analysis",
        tags=["test", "analysis", "sam"]
    )
    
    print(f"Upload result: {result}")
    
    if result['success']:
        # Analiz yap
        analysis_result = analyze_manual_document(result['document_id'])
        print(f"Analysis result: {analysis_result}")
    
    # Dökümanları listele
    documents = get_manual_documents()
    print(f"Documents count: {len(documents)}")
    
    autogen_doc_manager.close()
