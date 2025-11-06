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
    """
    __tablename__ = "opportunities"
    
    opportunity_id = Column(String(50), primary_key=True)
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
    
    # Relationships
    documents = relationship("ManualDocument", back_populates="opportunity", cascade="all, delete-orphan")
    analyses = relationship("AIAnalysisResult", back_populates="opportunity", cascade="all, delete-orphan")
    
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
    Tüm ajan çıktıları bu tabloya, fırsat ID'si ile bağlanarak JSONB olarak kaydedilecektir.
    """
    __tablename__ = "ai_analysis_results"
    
    analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(String(50), ForeignKey("opportunities.opportunity_id"), nullable=False)
    analysis_status = Column(String(50), nullable=False, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    analysis_version = Column(String(20), default="1.0")
    consolidated_output = Column(JSONB)  # Tüm ajan çıktıları burada birleştirilir
    start_time = Column(TIMESTAMP(timezone=True), server_default=func.now())
    end_time = Column(TIMESTAMP(timezone=True))
    analysis_duration_seconds = Column(Numeric)
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="analyses")
    
    def __repr__(self):
        return f"<AIAnalysisResult(analysis_id='{self.analysis_id}', opportunity_id='{self.opportunity_id}', status='{self.analysis_status}')>"


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

