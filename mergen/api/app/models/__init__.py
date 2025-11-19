"""
Models package for database models and SOW data structures.
"""
# Import database models from db_models.py
from .db_models import (
    Opportunity,
    OpportunityAttachment,
    OpportunityHistory,
    AIAnalysisResult,
    AnalysisLog,
    AgentRun,
    AgentMessage,
    Document,
    LLMCall,
    EmailLog,
    DecisionCache,
    TrainingExample,
    SyncJob,
    SyncLog,
    DownloadJob,
    DownloadLog,
    Requirement,
    Evidence,
    FacilityFeature,
    PricingItem,
    PastPerformance,
    Clause,
    VectorChunk,
)

# Import SOW data models
from .sow_data_model import SOWDataModel, CalendarDay, SeatingLayout

__all__ = [
    # Database models
    "Opportunity",
    "OpportunityAttachment", 
    "OpportunityHistory",
    "AIAnalysisResult",
    "AnalysisLog",
    "AgentRun",
    "AgentMessage",
    "Document",
    "LLMCall",
    "EmailLog",
    "DecisionCache",
    "TrainingExample",
    "SyncJob",
    "SyncLog",
    "DownloadJob",
    "DownloadLog",
    "Requirement",
    "Evidence",
    "FacilityFeature",
    "PricingItem",
    "PastPerformance",
    "Clause",
    "VectorChunk",
    # SOW data models
    "SOWDataModel",
    "CalendarDay",
    "SeatingLayout"
]

