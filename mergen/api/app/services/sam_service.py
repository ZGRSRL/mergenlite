"""
SAM.gov API Service Layer
Backend için merkezi SAM entegrasyon servisi
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Import existing SAMIntegration if available
try:
    import sys
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from sam_integration import SAMIntegration
    SAM_INTEGRATION_AVAILABLE = True
except ImportError:
    SAM_INTEGRATION_AVAILABLE = False
    logger.warning("SAMIntegration not available")
    SAMIntegration = None


async def fetch_opportunities_from_sam(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    SAM API'den fırsat listesi çeker.
    
    Args:
        params: Query filtreleri (naics, keyword, date_from, date_to, days_back, limit)
    
    Returns:
        Raw SAM JSON kayıtları listesi
    """
    if not SAM_INTEGRATION_AVAILABLE:
        logger.error("SAMIntegration not available")
        return []
    
    try:
        sam = SAMIntegration()
        
        if not sam.api_key:
            logger.error("SAM_API_KEY not found")
            return []
        
        # Map params to SAMIntegration format
        naics_codes = [params.get('naics')] if params.get('naics') else None
        keywords = params.get('keyword')
        days_back = params.get('days_back', 30)
        limit = params.get('limit', 1000)
        
        # Fetch opportunities
        opportunities = sam.fetch_opportunities(
            naics_codes=naics_codes,
            keywords=keywords,
            days_back=days_back,
            limit=limit
        )
        
        logger.info(f"Fetched {len(opportunities)} opportunities from SAM")
        return opportunities
        
    except Exception as e:
        logger.error(f"Error fetching opportunities from SAM: {e}", exc_info=True)
        return []


def get_sam_api_key() -> Optional[str]:
    """Get SAM API key from environment"""
    return os.getenv('SAM_API_KEY', '').strip() or None

