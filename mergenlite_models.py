"""
MergenLite Sadeleştirilmiş Veritabanı Modelleri
4 temel tablo için SQLAlchemy modelleri
"""

from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Opportunity(Base):
    """
    opportunities tablosu: SAM.gov Fırsatları
    GSA API'ye göre: Opportunity ID (unique) ve Notice ID (solicitation number) farklı şeyler
    """
    __tablename__ = "opportunities"
    
    opportunity_id = Column(String(50), primary_key=True)  # GSA Opportunity ID (32 hex chars)
    notice_id = Column(String(100), nullable=True, index=True)  # Notice ID / Solicitation Number
    solicitation_number = Column(String(100), nullable=True, index=True)  # Solicitation Number (alternatif)
    title = Column(String(512), nullable=False)
    notice_type = Column(String(100))
    naics_code = Column(String(10))
    response_deadline = Column(DateTime)
    estimated_value = Column(Numeric(15, 2))
    place_of_performance = Column(String(255))
    sam_gov_link = Column(String(512))
    raw_data = Column(JSONB)  # SAM.gov API'den gelen ham verinin tamamı
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - lazy loading ile (tablo yapısı uyumsuz olabilir)
    documents = relationship("ManualDocument", back_populates="opportunity", cascade="all, delete-orphan", lazy='select')
    # analyses relationship kaldırıldı - ai_analysis_results tablosunda FK yok, manuel join yapılıyor
    
    def __repr__(self):
        return f"<Opportunity(opportunity_id='{self.opportunity_id}', title='{self.title[:50]}...')>"


class ManualDocument(Base):
    """
    manual_documents tablosu: Manuel Yüklenen Dokümanlar
    """
    __tablename__ = "manual_documents"
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(String(50), ForeignKey("opportunities.opportunity_id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_mime_type = Column(String(100))
    storage_path = Column(String(512), nullable=False)
    document_metadata = Column(JSONB)  # Kullanıcı tarafından girilen başlık, etiketler vb.
    upload_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="documents")
    
    def __repr__(self):
        return f"<ManualDocument(document_id='{self.document_id}', file_name='{self.file_name}')>"


class AIAnalysisResult(Base):
    """
    ai_analysis_results tablosu: Konsolide AI Analiz Sonuçları
    ZGR_AI veritabanı şemasına uygun (id SERIAL, farklı kolon yapısı)
    """
    __tablename__ = "ai_analysis_results"
    
    # Veritabanındaki gerçek şema
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(255), nullable=False)  # Foreign key olarak tanımlanmamış (veritabanında FK yok)
    analysis_type = Column(String(100), nullable=False)
    result = Column(JSONB, nullable=False)  # consolidated_output yerine result
    confidence = Column(Numeric)  # DOUBLE PRECISION -> Numeric
    timestamp = Column(TIMESTAMP, nullable=False)
    agent_name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships - opportunity_id FK değil, manuel join yapılacak
    # opportunity = relationship("Opportunity", back_populates="analyses", foreign_keys=[opportunity_id])
    
    def __repr__(self):
        return f"<AIAnalysisResult(id={self.id}, opportunity_id='{self.opportunity_id}', analysis_type='{self.analysis_type}')>"


class SystemSession(Base):
    """
    system_sessions tablosu: Hafif Kullanıcı ve Sistem İzleme
    MergenAI'daki 'user_sessions' ve 'system_metrics' tablolarının basitleştirilmiş birleşimi
    """
    __tablename__ = "system_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_start = Column(TIMESTAMP(timezone=True), server_default=func.now())
    user_identifier = Column(String(100))
    analysis_count = Column(Integer, default=0)
    metric_data = Column(JSONB)  # Hafif sistem metrikleri (CPU/Bellek kullanımı, hız vb.)
    
    def __repr__(self):
        return f"<SystemSession(session_id='{self.session_id}', user='{self.user_identifier}', analyses={self.analysis_count})>"

