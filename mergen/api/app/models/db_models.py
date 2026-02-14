"""
MergenLite — Unified Database Models  (Single Source of Truth)
================================================================
All table definitions live here.  Other files (models_unified.py,
mergenlite_models.py) are DEPRECATED and will be removed.

Tables:
  Core      : opportunities, opportunity_attachments
  Analysis  : ai_analysis_results, analysis_logs
  Jobs      : sync_jobs, sync_logs, download_jobs, download_logs
  Hotel     : hotels, email_log
  Agents    : agent_runs, agent_messages, llm_calls
  Documents : documents, requirements, evidence,
              facility_features, pricing_items, past_performance, clauses
  RAG       : vector_chunks (pgvector)
  Meta      : opportunity_history, decision_cache, training_examples
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# pgvector — graceful fallback if extension not available
try:
    from pgvector.sqlalchemy import Vector as PgVector

    VECTOR_TYPE = PgVector(1536)  # OpenAI embedding dimension
except ImportError:
    PgVector = None
    VECTOR_TYPE = JSON  # fallback: store as plain JSON array

from app.db import Base


class Opportunity(Base):
    """Unified Opportunity model shared by React + FastAPI."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String(255), nullable=False, index=True)
    notice_id = Column(String(100), nullable=True, index=True)
    solicitation_number = Column(String(100), nullable=True, index=True)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    posted_date = Column(DateTime(timezone=True), nullable=True, index=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)

    agency = Column(String(255), nullable=True)
    office = Column(String(255), nullable=True)
    organization_type = Column(String(100), nullable=True)
    point_of_contact = Column(Text, nullable=True)

    naics_code = Column(String(100), nullable=True, index=True)
    psc_code = Column(String(100), nullable=True)
    classification_code = Column(String(100), nullable=True)
    set_aside = Column(String(100), nullable=True)
    contract_type = Column(String(100), nullable=True)
    notice_type = Column(String(100), nullable=True)

    place_of_performance = Column(Text, nullable=True)
    estimated_value = Column(Float, nullable=True)

    status = Column(String(50), nullable=False, default="active")
    sam_gov_link = Column(String(512), nullable=True)

    raw_data = Column(JSON, nullable=True)
    cached_data = Column(JSON, nullable=True)
    cache_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    attachments = relationship(
        "OpportunityAttachment",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    analysis_results = relationship(
        "AIAnalysisResult",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    hotels = relationship(
        "Hotel",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    @property
    def raw_json(self):
        return self.raw_data

    @property
    def analyzed(self):
        if self.cached_data and isinstance(self.cached_data, dict):
            return bool(self.cached_data.get("analysis") or self.cached_data.get("analyzed"))
        return bool(self.analysis_results)

    @property
    def source(self):
        if self.raw_data and isinstance(self.raw_data, dict):
            return self.raw_data.get("source", "unknown")
        return "unknown"

    @property
    def organization(self):
        if self.raw_data and isinstance(self.raw_data, dict):
            return self.raw_data.get("fullParentPathName") or self.raw_data.get("organization")
        return None


class OpportunityAttachment(Base):
    """Stored resource links / attachments for an opportunity."""

    __tablename__ = "opportunity_attachments"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(512), nullable=False)
    source_url = Column(String(1024), nullable=True)
    attachment_type = Column(String(50), default="document")
    mime_type = Column(String(255), nullable=True)
    size_bytes = Column(Integer, nullable=True)

    local_path = Column(String(1024), nullable=True)
    downloaded = Column(Boolean, default=False, nullable=False)
    storage_path = Column(String(1024), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", back_populates="attachments")


class AIAnalysisResult(Base):
    """Outputs generated by AutoGen / analysis pipelines."""

    __tablename__ = "ai_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)

    analysis_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)

    result_json = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)

    pdf_path = Column(String(1024), nullable=True)
    json_path = Column(String(1024), nullable=True)
    markdown_path = Column(String(1024), nullable=True)

    agent_name = Column(String(100), nullable=True)
    pipeline_version = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", back_populates="analysis_results")
    logs = relationship("AnalysisLog", back_populates="analysis_result", cascade="all, delete-orphan")


class AnalysisLog(Base):
    """Log entries for a given analysis run."""

    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_result_id = Column(Integer, ForeignKey("ai_analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)

    step = Column(String(100), nullable=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=True, index=True)

    analysis_result = relationship("AIAnalysisResult", back_populates="logs")


class SyncJob(Base):
    """Track SAM sync jobs."""

    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")
    sync_type = Column(String(50), nullable=False, default="sam")

    params = Column(JSON, nullable=True)
    count_new = Column(Integer, default=0)
    count_updated = Column(Integer, default=0)
    count_attachments = Column(Integer, default=0)
    total_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    logs = relationship("SyncLog", back_populates="job", cascade="all, delete-orphan")


class SyncLog(Base):
    """Per-job log entries for sync operations."""

    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("sync_jobs.job_id"), nullable=False, index=True)

    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    step = Column(String(100), nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=True, index=True)

    job = relationship("SyncJob", back_populates="logs")


class DownloadJob(Base):
    """Track background attachment downloads."""

    __tablename__ = "download_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")

    total_attachments = Column(Integer, default=0)
    downloaded_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    logs = relationship("DownloadLog", back_populates="job", cascade="all, delete-orphan")


class DownloadLog(Base):
    """Log entries for download jobs."""

    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("download_jobs.job_id"), nullable=False, index=True)

    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    attachment_name = Column(String(512), nullable=True)
    step = Column(String(100), nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=True, index=True)

    job = relationship("DownloadJob", back_populates="logs")


# ============================================================================
# Opportunity history / agent logging / LLM logging / learning tables
# ============================================================================

class OpportunityHistory(Base):
    """Track status transitions for opportunities."""

    __tablename__ = "opportunity_history"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(100), nullable=True)
    new_status = Column(String(100), nullable=False)
    changed_by = Column(String(255), nullable=False)
    change_source = Column(String(100), nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])


class AgentRun(Base):
    """Represents a single AutoGen/pipeline run for an opportunity."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=True, index=True)
    run_type = Column(String(100), nullable=False)
    correlation_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="started")
    error_message = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    messages = relationship("AgentMessage", back_populates="agent_run", cascade="all, delete-orphan")
    llm_calls = relationship("LLMCall", back_populates="agent_run", cascade="all, delete-orphan")


class AgentMessage(Base):
    """Message-level log entries for each agent run."""

    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    agent_run = relationship("AgentRun", back_populates="messages")


class LLMCall(Base):
    """LLM call log entries for auditing and analytics."""

    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_name = Column(String(100), nullable=True)
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agent_run = relationship("AgentRun", back_populates="llm_calls")


class EmailLog(Base):
    """Extended email log with linkage to agent runs/LLM calls."""

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
    related_agent_run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    related_llm_call_id = Column(Integer, ForeignKey("llm_calls.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])
    hotel = relationship("Hotel", back_populates="email_logs")
    agent_run = relationship("AgentRun", foreign_keys=[related_agent_run_id])
    llm_call = relationship("LLMCall", foreign_keys=[related_llm_call_id])


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


class DecisionCache(Base):
    """Stores reusable decision patterns (e.g., hotel selections)."""

    __tablename__ = "decision_cache"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    pattern_desc = Column(Text, nullable=True)
    recommended_hotels = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    extra_metadata = Column(JSON, nullable=True)


class TrainingExample(Base):
    """Stores structured examples for future fine-tuning/RAG usage."""

    __tablename__ = "training_examples"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    example_type = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    outcome = Column(String(50), nullable=True)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    opportunity = relationship("Opportunity", foreign_keys=[opportunity_id])


class Document(Base):
    """Stores uploaded/processed documents (RFQ, SOW, facility specs, etc.)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(100), nullable=False, index=True)  # rfq, sow, facility, past_performance, pricing
    title = Column(String(512), nullable=False)
    path = Column(String(1024), nullable=False)
    meta_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    requirements = relationship("Requirement", back_populates="rfq", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="source_document", cascade="all, delete-orphan")
    facility_features = relationship("FacilityFeature", back_populates="source_document", cascade="all, delete-orphan")
    pricing_items = relationship("PricingItem", back_populates="rfq", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    vector_chunks = relationship("VectorChunk", back_populates="document", cascade="all, delete-orphan")


class Requirement(Base):
    """Individual requirement extracted from an RFQ document."""

    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=True)
    text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True, default="pending")
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rfq = relationship("Document", back_populates="requirements")
    evidence = relationship("Evidence", back_populates="requirement", cascade="all, delete-orphan")


class Evidence(Base):
    """Evidence items that support requirements (facility features, past performance, etc.)."""

    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    source_doc_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    snippet = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    evidence_type = Column(String(50), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    requirement = relationship("Requirement", back_populates="evidence")
    source_document = relationship("Document", back_populates="evidence", foreign_keys=[source_doc_id])


class FacilityFeature(Base):
    """Structured facility data extracted from hotel/facility specs."""

    __tablename__ = "facility_features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    source_doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source_document = relationship("Document", back_populates="facility_features")


class PricingItem(Base):
    """Structured pricing entry for RFQ responses."""

    __tablename__ = "pricing_items"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    qty = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rfq = relationship("Document", back_populates="pricing_items")


class PastPerformance(Base):
    """Stored past performance examples for proposals."""

    __tablename__ = "past_performance"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    client = Column(String(255), nullable=True)
    scope = Column(Text, nullable=True)
    period = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    ref_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Clause(Base):
    """FAR/contract clauses extracted from RFQ documents."""

    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    clause_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="clauses")


class VectorChunk(Base):
    """Vectorized chunks used for semantic search / RAG via pgvector."""

    __tablename__ = "vector_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk = Column(Text, nullable=False)
    embedding = Column(VECTOR_TYPE, nullable=True)  # pgvector native or JSON fallback
    chunk_type = Column(String(50), nullable=True)   # 'summary', 'paragraph', 'table', etc.
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)      # for cost tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="vector_chunks")
