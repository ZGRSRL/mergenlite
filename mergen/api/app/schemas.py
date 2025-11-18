"""
Pydantic Schemas for API Request/Response Models.
"""
from datetime import datetime
from typing import Optional, Any, List, Dict

from pydantic import BaseModel


# ============================================================================
# Health Check Schema
# ============================================================================


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


# ============================================================================
# Opportunity & Attachment Schemas
# ============================================================================


class OpportunityBase(BaseModel):
    notice_id: str
    title: str
    posted_date: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    agency: Optional[str] = None
    office: Optional[str] = None
    naics_code: Optional[str] = None
    psc_code: Optional[str] = None
    status: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    raw_data: Optional[Any] = None
    cached_data: Optional[Any] = None


class OpportunityRead(OpportunityBase):
    id: int
    raw_data: Optional[Any] = None
    cached_data: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityAttachmentBase(BaseModel):
    opportunity_id: int
    name: str
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class OpportunityAttachmentCreate(OpportunityAttachmentBase):
    attachment_type: Optional[str] = "document"
    extra_metadata: Optional[Any] = None


class OpportunityAttachmentRead(OpportunityAttachmentBase):
    id: int
    attachment_type: Optional[str] = None
    downloaded: Optional[bool] = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityWithAttachments(OpportunityRead):
    attachments: List[OpportunityAttachmentRead] = []


# ============================================================================
# Sync / Download Job Schemas
# ============================================================================


class SamSyncRequest(BaseModel):
    naics_code: Optional[str] = None
    keyword: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    days_back: Optional[int] = 30
    limit: Optional[int] = 1000


class SyncResponse(BaseModel):
    success: bool
    job_id: str
    count_new: int = 0
    count_updated: int = 0
    total_processed: int = 0
    count_attachments: int = 0
    message: Optional[str] = None


class SyncJobRead(BaseModel):
    id: int
    job_id: str
    status: str
    sync_type: str
    params: Optional[Any] = None
    count_new: int = 0
    count_updated: int = 0
    count_attachments: int = 0
    total_processed: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncLogRead(BaseModel):
    id: int
    job_id: str
    level: str
    message: str
    step: Optional[str] = None
    extra_metadata: Optional[Any] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class DownloadJobRead(BaseModel):
    id: int
    job_id: str
    opportunity_id: int
    status: str
    total_attachments: int = 0
    downloaded_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DownloadLogRead(BaseModel):
    id: int
    job_id: str
    level: str
    message: str
    step: Optional[str] = None
    attachment_name: Optional[str] = None
    extra_metadata: Optional[Any] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class DownloadResponse(BaseModel):
    success: bool
    job_id: str
    message: str


# ============================================================================
# Pipeline / Analysis Schemas
# ============================================================================


class PipelineRunRequest(BaseModel):
    opportunity_id: int
    attachment_ids: Optional[List[int]] = None
    pipeline_version: Optional[str] = "v1"
    analysis_type: Optional[str] = "sow_draft"
    agent_name: Optional[str] = "autogen"
    options: Optional[Dict[str, Any]] = None


class PipelineRunResponse(BaseModel):
    analysis_result_id: int
    status: str
    message: Optional[str] = None


class AnalysisResultRead(BaseModel):
    id: int
    opportunity_id: int
    analysis_type: str
    status: str
    pipeline_version: Optional[str] = None
    agent_name: Optional[str] = None
    result_json: Optional[Any] = None
    confidence: Optional[float] = None
    pdf_path: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisLogRead(BaseModel):
    id: int
    analysis_result_id: int
    step: Optional[str] = None
    level: str
    message: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# History / Agent Run / Training / Decision Schemas
# ============================================================================


class OpportunityHistoryRead(BaseModel):
    id: int
    opportunity_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    change_source: Optional[str] = None
    meta: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRunRead(BaseModel):
    id: int
    opportunity_id: Optional[int] = None
    run_type: str
    correlation_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingExampleRead(BaseModel):
    id: int
    opportunity_id: Optional[int] = None
    example_type: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    outcome: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionCacheRead(BaseModel):
    key_hash: str
    pattern_desc: Optional[str] = None
    recommended_hotels: Optional[Any] = None
    created_at: datetime
    extra_metadata: Optional[Any] = None

    class Config:
        from_attributes = True


class DecisionCacheContext(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    notice_id: Optional[str] = None
    naics_code: Optional[str] = None
    location_type: Optional[str] = None
    participants: Optional[int] = None
    nights: Optional[int] = None
    date_range: Optional[str] = None
    budget_total: Optional[float] = None
    estimated_value: Optional[str] = None
    event_requirements: Optional[Dict[str, Any]] = None


class DecisionCacheLookupResponse(BaseModel):
    key_hash: str
    signature: Dict[str, str]
    matched: bool
    pattern: Optional[DecisionCacheRead] = None


class DecisionCacheSaveRequest(DecisionCacheContext):
    pattern_desc: Optional[str] = None
    recommended_hotels: Optional[Any] = None


class HotelMatchRead(BaseModel):
    id: int
    generated_at: Optional[datetime] = None
    hotels: List[Any] = []
    reasoning: Optional[str] = None
    decision_metadata: Optional[Dict[str, Any]] = None

# ============================================================================
# Email Log Schemas
# ============================================================================


class EmailLogCreate(BaseModel):
    direction: str
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    raw_body: Optional[str] = None
    parsed_summary: Optional[str] = None
    related_agent_run_id: Optional[int] = None
    related_llm_call_id: Optional[int] = None


class EmailLogRead(BaseModel):
    id: int
    opportunity_id: Optional[int] = None
    direction: str
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    parsed_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Document Schemas
# ============================================================================


class Document(BaseModel):
    id: int
    kind: str
    title: str
    path: str
    meta_json: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Requirement / Evidence / Facility Schemas
# ============================================================================


class Requirement(BaseModel):
    id: int
    rfq_id: int
    code: Optional[str] = None
    text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Evidence(BaseModel):
    id: int
    requirement_id: int
    source_doc_id: Optional[int] = None
    snippet: Optional[str] = None
    score: Optional[float] = None
    evidence_type: Optional[str] = None
    extra_metadata: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FacilityFeature(BaseModel):
    id: int
    name: str
    value: str
    category: Optional[str] = None
    source_doc_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PricingItem(BaseModel):
    id: int
    rfq_id: int
    name: str
    description: Optional[str] = None
    qty: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PastPerformance(BaseModel):
    id: int
    title: str
    client: Optional[str] = None
    scope: Optional[str] = None
    period: Optional[str] = None
    value: Optional[float] = None
    ref_info: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Clause(BaseModel):
    id: int
    document_id: int
    text: str
    tags: Optional[Any] = None
    clause_ref: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VectorChunk(BaseModel):
    id: int
    document_id: int
    chunk: str
    embedding: Optional[Any] = None
    chunk_type: Optional[str] = None
    page_number: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Compliance Schemas
# ============================================================================


class ComplianceMatrixItem(BaseModel):
    requirement: Requirement
    evidence: List[Evidence] = []
    risk_level: str
    gap_analysis: str
    mitigation: str


class ComplianceMatrix(BaseModel):
    rfq_id: int
    items: List[ComplianceMatrixItem]
    overall_risk: str
    total_requirements: int
    met_requirements: int
    gap_requirements: int


# ============================================================================
# Proposal Schemas
# ============================================================================


class ProposalDraft(BaseModel):
    rfq_id: int
    executive_summary: str
    technical_approach: str
    past_performance: str
    pricing_summary: str
    compliance_matrix: Optional[Any] = None
    created_at: datetime
