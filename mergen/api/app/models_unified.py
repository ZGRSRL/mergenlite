"""
Unified Opportunity Model
React ve FastAPI için tek bir şema tanımı
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


class Opportunity(Base):
    """
    Unified Opportunity Model
    React ve FastAPI için tek bir şema
    """
    __tablename__ = "opportunities"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # SAM.gov Identifiers
    opportunity_id = Column(String(255), nullable=False, index=True)  # SAM Opportunity ID (32 hex chars)
    notice_id = Column(String(100), nullable=True, index=True)  # Notice ID / Solicitation Number
    solicitation_number = Column(String(100), nullable=True, index=True)  # Alternative solicitation number
    
    # Basic Info
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # Dates
    posted_date = Column(DateTime(timezone=True), nullable=True, index=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Classification
    naics_code = Column(String(100), nullable=True, index=True)
    psc_code = Column(String(100), nullable=True)  # Product/Service Code
    classification_code = Column(String(100), nullable=True)
    set_aside = Column(String(100), nullable=True)
    contract_type = Column(String(100), nullable=True)
    notice_type = Column(String(100), nullable=True)
    
    # Organization
    agency = Column(String(255), nullable=True)  # Agency name
    office = Column(String(255), nullable=True)  # Office/division
    organization_type = Column(String(100), nullable=True)
    point_of_contact = Column(Text, nullable=True)
    
    # Location & Value
    place_of_performance = Column(Text, nullable=True)
    estimated_value = Column(Float, nullable=True)
    
    # Links
    sam_gov_link = Column(String(512), nullable=True)
    
    # Data Storage
    raw_data = Column(JSON, nullable=True)  # Raw SAM.gov API response
    cached_data = Column(JSON, nullable=True)  # Cached analysis results
    cache_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    attachments = relationship("OpportunityAttachment", back_populates="opportunity", cascade="all, delete-orphan")
    analysis_results = relationship("AIAnalysisResult", back_populates="opportunity", cascade="all, delete-orphan")
    
    # Computed properties for backward compatibility
    @property
    def raw_json(self):
        """Alias for raw_data"""
        return self.raw_data
    
    @property
    def analyzed(self):
        """Check if analysis exists"""
        if self.cached_data and isinstance(self.cached_data, dict):
            return bool(self.cached_data.get('analysis') or self.cached_data.get('analyzed'))
        # Also check ai_analysis_results
        return len(self.analysis_results) > 0 if hasattr(self, 'analysis_results') else False
    
    @property
    def source(self):
        """Extract source from raw_data"""
        if self.raw_data and isinstance(self.raw_data, dict):
            return self.raw_data.get('source', 'unknown')
        return 'unknown'


class OpportunityAttachment(Base):
    """
    Opportunity Attachments / Resource Links
    SAM.gov'dan gelen dokümanlar ve resource linkleri
    """
    __tablename__ = "opportunity_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String(255), ForeignKey("opportunities.opportunity_id"), nullable=False, index=True)
    
    # Attachment Info
    name = Column(String(512), nullable=False)
    source_url = Column(String(1024), nullable=False)  # SAM.gov URL
    attachment_type = Column(String(50), nullable=False)  # 'resourceLink', 'attachment', 'document'
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # Bytes
    
    # Storage
    local_path = Column(String(1024), nullable=True)  # Local file path if downloaded
    downloaded = Column(Boolean, default=False, nullable=False)
    storage_path = Column(String(1024), nullable=True)  # S3 or other storage path
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional metadata from SAM
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="attachments")


class AIAnalysisResult(Base):
    """
    AI Analysis Results
    AutoGen pipeline ve diğer analiz sonuçları
    """
    __tablename__ = "ai_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String(255), ForeignKey("opportunities.opportunity_id"), nullable=False, index=True)
    
    # Analysis Info
    analysis_type = Column(String(100), nullable=False, index=True)  # 'sow_draft', 'risk_analysis', 'compliance_matrix', 'requirements_extraction'
    status = Column(String(50), nullable=False, default='pending', index=True)  # 'pending', 'running', 'completed', 'failed'
    
    # Results
    result_json = Column(JSON, nullable=True)  # Structured analysis results
    confidence = Column(Float, nullable=True)  # Confidence score 0.0-1.0
    
    # Output Files
    pdf_path = Column(String(1024), nullable=True)  # Generated PDF path
    json_path = Column(String(1024), nullable=True)  # Generated JSON path
    markdown_path = Column(String(1024), nullable=True)  # Generated Markdown path
    
    # Metadata
    agent_name = Column(String(100), nullable=True)  # Which agent generated this
    pipeline_version = Column(String(50), nullable=True)  # Pipeline version used
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="analysis_results")
    logs = relationship("AnalysisLog", back_populates="analysis_result", cascade="all, delete-orphan")


class AnalysisLog(Base):
    """
    Analysis Logs
    Pipeline ve agent log kayıtları
    """
    __tablename__ = "analysis_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_result_id = Column(Integer, ForeignKey("ai_analysis_results.id"), nullable=False, index=True)
    
    # Log Info
    step = Column(String(100), nullable=True)  # Pipeline step name
    level = Column(String(20), nullable=False, index=True)  # 'INFO', 'WARNING', 'ERROR', 'DEBUG'
    message = Column(Text, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=True, index=True)
    
    # Relationships
    analysis_result = relationship("AIAnalysisResult", back_populates="logs")

