"""
mergenlite_models.py — Compatibility Shim
==========================================
DEPRECATED: Use `mergen.api.app.models.db_models` directly.
This file re-exports all models so legacy root-level scripts keep working.
"""

import warnings
import sys
import os

warnings.warn(
    "mergenlite_models is deprecated. "
    "Import from mergen.api.app.models.db_models instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Ensure the mergen API app is importable
_project_root = os.path.dirname(os.path.abspath(__file__))
_api_path = os.path.join(_project_root, "mergen", "api")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from app.db import Base  # noqa: E402, F401
from app.models.db_models import (  # noqa: E402, F401
    Opportunity,
    OpportunityAttachment,
    OpportunityHistory,
    AIAnalysisResult,
    AnalysisLog,
    AgentRun,
    AgentMessage,
    Document,
    Hotel,
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
