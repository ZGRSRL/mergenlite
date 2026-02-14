"""
Models package — re-exports from db_models.py (Single Source of Truth).
"""

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
    Hotel,
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

# SOW data models (Pydantic, not SQLAlchemy)
from .sow_data_model import SOWDataModel, CalendarDay, SeatingLayout

__all__ = [
    # Core
    "Opportunity",
    "OpportunityAttachment",
    "OpportunityHistory",
    # Analysis
    "AIAnalysisResult",
    "AnalysisLog",
    # Agents
    "AgentRun",
    "AgentMessage",
    "LLMCall",
    # Documents & RAG
    "Document",
    "Requirement",
    "Evidence",
    "FacilityFeature",
    "PricingItem",
    "PastPerformance",
    "Clause",
    "VectorChunk",
    # Hotel & Email
    "Hotel",
    "EmailLog",
    # Jobs
    "SyncJob",
    "SyncLog",
    "DownloadJob",
    "DownloadLog",
    # Learning
    "DecisionCache",
    "TrainingExample",
    # SOW
    "SOWDataModel",
    "CalendarDay",
    "SeatingLayout",
]
