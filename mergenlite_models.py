"""
MergenLite Sadeleştirilmiş Veritabanı Modelleri
4 temel tablo için SQLAlchemy modelleri
"""

from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, Text, Float
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
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String(255), nullable=False, index=True)  # Artık PK değil
    notice_id = Column(String(100), nullable=True, index=True)
    solicitation_number = Column(String(100), nullable=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True) # Added
    
    notice_type = Column(String(100))
    naics_code = Column(String(100)) # Increased length
    response_deadline = Column(DateTime(timezone=True))
    estimated_value = Column(Numeric(15, 2))
    place_of_performance = Column(Text)
    
    agency = Column(String(255), nullable=True) # Added
    office = Column(String(255), nullable=True) # Added
    
    sam_gov_link = Column(String(512))
    status = Column(String(50), nullable=False, default="active")  # active, archived, etc.
    raw_data = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - lazy loading ile (tablo yapısı uyumsuz olabilir)
    documents = relationship("ManualDocument", back_populates="opportunity", cascade="all, delete-orphan", lazy='select')
    hotels = relationship("Hotel", back_populates="opportunity", cascade="all, delete-orphan")
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
    # Veritabanındaki gerçek şema (inspect results)
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(Integer, nullable=False)  # FK to opportunities.id (Integer)
    analysis_type = Column(String(100), nullable=False)
    
    # Mapped columns
    result = Column(JSONB, name='consolidated_output', nullable=True)  # Map 'result' attr to 'consolidated_output' column
    confidence = Column(Float)  # DOUBLE PRECISION
    
    # Timestamp mappings
    timestamp = Column(TIMESTAMP, name='completed_at', nullable=True) # Map 'timestamp' to 'completed_at'
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    agent_name = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<AIAnalysisResult(id={self.id}, opportunity_id={self.opportunity_id}, type='{self.analysis_type}')>"


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


class Hotel(Base):
    """Target entity (Hotel) for an opportunity outreach."""
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    manager_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    status = Column(String(50), default="queued", index=True)  # queued, sent, replied, negotiating, rejected, booked
    rating = Column(Float, nullable=True)
    price_quote = Column(String(100), nullable=True)

    unread_count = Column(Integer, default=0)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    opportunity = relationship("Opportunity", back_populates="hotels")
    email_logs = relationship("EmailLog", back_populates="hotel", cascade="all, delete-orphan")


class EmailLog(Base):
    """Extended email log."""
    __tablename__ = "email_log"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="SET NULL"), nullable=True)
    direction = Column(String(20), nullable=False)
    subject = Column(String(512), nullable=True)
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    message_id = Column(String(255), nullable=True)
    in_reply_to = Column(String(255), nullable=True)
    raw_body = Column(Text, nullable=True)
    parsed_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    hotel = relationship("Hotel", back_populates="email_logs")

