"""
SAM.gov Integration Service
Fetches RFQ/SOW documents from SAM.gov API
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ..parsing.pdf_utils import process_pdf
from ..parsing.excel_reader import process_excel
from ...models import Document
from ...db import get_db

logger = logging.getLogger(__name__)

class SAMGovIntegration:
    """SAM.gov API integration for fetching RFQ/SOW documents"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "your_sam_gov_api_key"
        self.base_url = "https://api.sam.gov"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_opportunities(
        self, 
        keywords: List[str] = None,
        naics_codes: List[str] = None,
        date_range_days: int = 30,
        opportunity_type: str = "rfq"
    ) -> List[Dict[str, Any]]:
        """Search for opportunities on SAM.gov"""
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=date_range_days)
            
            # Build search parameters
            params = {
                "q": " ".join(keywords) if keywords else "conference meeting seminar",
                "naics": ",".join(naics_codes) if naics_codes else "561110",  # Event planning
                "postedFrom": start_date.strftime("%Y-%m-%d"),
                "postedTo": end_date.strftime("%Y-%m-%d"),
                "typeOfSetAside": "NONE",
                "typeOfSetAsideDescription": "No Set-Aside Used",
                "opportunityType": opportunity_type.upper(),
                "limit": 100
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/opportunities",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                opportunities = data.get("opportunitiesData", [])
                
                logger.info(f"Found {len(opportunities)} opportunities on SAM.gov")
                return opportunities
                
        except Exception as e:
            logger.error(f"Error searching SAM.gov opportunities: {e}")
            return []
    
    async def get_opportunity_details(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific opportunity"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/opportunities/{notice_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching opportunity details for {notice_id}: {e}")
            return None
    
    async def download_attachments(
        self, 
        notice_id: str, 
        attachment_urls: List[str]
    ) -> List[Dict[str, Any]]:
        """Download attachments from SAM.gov opportunity"""
        
        downloaded_files = []
        
        for i, url in enumerate(attachment_urls):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    
                    # Determine file type and name
                    content_type = response.headers.get("content-type", "")
                    if "pdf" in content_type:
                        file_extension = "pdf"
                        file_type = "rfq" if "rfq" in url.lower() else "sow"
                    elif "excel" in content_type or "spreadsheet" in content_type:
                        file_extension = "xlsx"
                        file_type = "pricing"
                    else:
                        file_extension = "pdf"
                        file_type = "unknown"
                    
                    filename = f"sam_gov_{notice_id}_attachment_{i+1}.{file_extension}"
                    
                    # Save file
                    file_path = f"samples/{filename}"
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    downloaded_files.append({
                        "filename": filename,
                        "file_path": file_path,
                        "file_type": file_type,
                        "size": len(response.content),
                        "url": url
                    })
                    
                    logger.info(f"Downloaded attachment: {filename}")
                    
            except Exception as e:
                logger.error(f"Error downloading attachment {url}: {e}")
                continue
        
        return downloaded_files
    
    async def process_sam_opportunity(
        self, 
        opportunity: Dict[str, Any],
        db_session
    ) -> Dict[str, Any]:
        """Process a SAM.gov opportunity and create documents"""
        
        notice_id = opportunity.get("noticeId")
        title = opportunity.get("title", "Unknown Title")
        
        logger.info(f"Processing SAM.gov opportunity: {title}")
        
        # Get detailed opportunity information
        details = await self.get_opportunity_details(notice_id)
        if not details:
            return {"error": "Could not fetch opportunity details"}
        
        # Extract attachment URLs
        attachments = details.get("attachments", [])
        attachment_urls = [att.get("url") for att in attachments if att.get("url")]
        
        # Download attachments
        downloaded_files = await self.download_attachments(notice_id, attachment_urls)
        
        # Create document records
        created_documents = []
        
        for file_info in downloaded_files:
            # Create document record
            document = Document(
                kind=file_info["file_type"],
                title=f"{title} - {file_info['filename']}",
                path=file_info["file_path"],
                meta_json={
                    "sam_gov_notice_id": notice_id,
                    "sam_gov_title": title,
                    "download_date": datetime.now().isoformat(),
                    "file_size": file_info["size"],
                    "source": "sam_gov"
                }
            )
            
            db_session.add(document)
            db_session.commit()
            db_session.refresh(document)
            
            created_documents.append(document)
            
            # Process document based on type
            if file_info["file_type"] in ["rfq", "sow", "facility", "past_performance"]:
                # Process PDF in background
                asyncio.create_task(
                    process_pdf(document.id, file_info["file_path"], file_info["file_type"])
                )
            elif file_info["file_type"] == "pricing":
                # Process Excel in background
                asyncio.create_task(
                    process_excel(document.id, file_info["file_path"])
                )
        
        return {
            "notice_id": notice_id,
            "title": title,
            "downloaded_files": len(downloaded_files),
            "created_documents": [doc.id for doc in created_documents],
            "status": "success"
        }
    
    async def auto_fetch_opportunities(
        self,
        keywords: List[str] = None,
        naics_codes: List[str] = None,
        max_opportunities: int = 10
    ) -> List[Dict[str, Any]]:
        """Automatically fetch and process opportunities from SAM.gov"""
        
        # Search for opportunities
        opportunities = await self.search_opportunities(
            keywords=keywords,
            naics_codes=naics_codes
        )
        
        if not opportunities:
            logger.info("No opportunities found on SAM.gov")
            return []
        
        # Limit to max_opportunities
        opportunities = opportunities[:max_opportunities]
        
        # Process each opportunity
        results = []
        db_session = next(get_db())
        
        try:
            for opportunity in opportunities:
                result = await self.process_sam_opportunity(opportunity, db_session)
                results.append(result)
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(2)
                
        finally:
            db_session.close()
        
        return results

# SAM.gov specific search configurations
SAM_GOV_CONFIGS = {
    "conference_meetings": {
        "keywords": ["conference", "meeting", "seminar", "training", "workshop"],
        "naics_codes": ["561110", "561920"],  # Event planning and convention services
        "opportunity_types": ["rfq", "rfi", "sources_sought"]
    },
    "event_management": {
        "keywords": ["event management", "conference planning", "meeting services"],
        "naics_codes": ["561110"],
        "opportunity_types": ["rfq", "sources_sought"]
    },
    "av_services": {
        "keywords": ["audio visual", "av equipment", "conference technology"],
        "naics_codes": ["561110", "541512"],
        "opportunity_types": ["rfq", "sources_sought"]
    }
}

async def fetch_sam_gov_opportunities(
    config_name: str = "conference_meetings",
    max_opportunities: int = 10
) -> List[Dict[str, Any]]:
    """Convenience function to fetch opportunities using predefined configurations"""
    
    config = SAM_GOV_CONFIGS.get(config_name, SAM_GOV_CONFIGS["conference_meetings"])
    
    sam_integration = SAMGovIntegration()
    
    return await sam_integration.auto_fetch_opportunities(
        keywords=config["keywords"],
        naics_codes=config["naics_codes"],
        max_opportunities=max_opportunities
    )


