"""
SAM Record to Opportunity Mapper
SAM.gov raw kayıtlarını Opportunity model formatına çevirir
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats"""
    if not value:
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        try:
            # ISO format: "2024-01-15T10:30:00Z" or "2024-01-15T10:30:00+00:00"
            value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except Exception:
            try:
                # Try other formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
    
    return None


def map_sam_record_to_opportunity(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    SAM raw kaydı -> OpportunityCreate dict
    
    Args:
        record: SAM.gov API'den gelen raw kayıt
    
    Returns:
        Opportunity model için uygun dict
    """
    # Primary identifiers
    notice_id = record.get("noticeId") or record.get("id") or record.get("solicitationNumber")
    opportunity_id = record.get("opportunityId") or notice_id
    
    # Title
    title = record.get("title") or record.get("subject") or "Başlık Yok"
    
    # Dates
    posted_date = parse_datetime(record.get("postedDate") or record.get("posted_date"))
    response_deadline = parse_datetime(record.get("responseDeadLine") or record.get("responseDeadline") or record.get("response_deadline"))
    
    # Organization
    agency = record.get("agency") or record.get("fullParentPathName") or record.get("organization")
    office = record.get("office") or record.get("department")
    
    # Classification
    naics_code = record.get("naicsCode") or record.get("naics_code")
    psc_code = record.get("pscCode") or record.get("psc_code")
    
    # Links
    sam_gov_link = record.get("uiLink") or record.get("samGovLink") or record.get("link")
    if not sam_gov_link and notice_id:
        sam_gov_link = f"https://sam.gov/opp/{notice_id}/view"
    
    # Build cached_data for frequently used fields
    cached_data = {
        "typeOfNotice": record.get("typeOfNotice") or record.get("noticeType"),
        "setAside": record.get("setAside"),
        "contractType": record.get("contractType") or record.get("contract_type"),
        "classificationCode": record.get("classificationCode") or record.get("classification_code"),
        "estimatedValue": record.get("estimatedValue") or record.get("estimated_value"),
        "placeOfPerformance": record.get("placeOfPerformance") or record.get("place_of_performance"),
        "organizationType": record.get("organizationType") or record.get("organization_type"),
    }
    
    # Remove None values from cached_data
    cached_data = {k: v for k, v in cached_data.items() if v is not None}
    
    return {
        "opportunity_id": opportunity_id or notice_id,  # Fallback to notice_id
        "notice_id": notice_id,
        "solicitation_number": record.get("solicitationNumber") or record.get("solicitation_number"),
        "title": title,
        "description": record.get("description") or record.get("descriptionText"),
        "posted_date": posted_date,
        "response_deadline": response_deadline,
        "agency": agency,
        "office": office,
        "naics_code": naics_code,
        "psc_code": psc_code,
        "classification_code": record.get("classificationCode") or record.get("classification_code"),
        "set_aside": record.get("setAside") or record.get("set_aside"),
        "contract_type": record.get("contractType") or record.get("contract_type"),
        "place_of_performance": record.get("placeOfPerformance") or record.get("place_of_performance"),
        "organization_type": record.get("organizationType") or record.get("organization_type"),
        "point_of_contact": record.get("pointOfContact") or record.get("point_of_contact"),
        "notice_type": record.get("noticeType") or record.get("typeOfNotice"),
        "estimated_value": record.get("estimatedValue") or record.get("estimated_value"),
        "sam_gov_link": sam_gov_link,
        "status": "active",
        "raw_data": record,  # Store full SAM response
        "cached_data": cached_data if cached_data else None,
    }


def extract_attachments_from_sam_record(record: Dict[str, Any], opportunity_id: int) -> List[Dict[str, Any]]:
    """
    SAM kaydından attachment/resource link bilgilerini çıkarır
    Birden fazla alan ve formatı destekler: resourceLinks, attachments, documents, raw_data
    
    Args:
        record: SAM.gov API'den gelen raw kayıt
        opportunity_id: Opportunity database ID (not SAM opportunity_id)
    
    Returns:
        OpportunityAttachmentCreate formatında dict listesi
    """
    attachments = []
    seen_urls = set()  # Duplicate URL'leri önlemek için
    
    def add_attachment(url: str, name: str, att_type: str = "resourceLink", mime_type: str = None, size_bytes: int = None, metadata: Dict = None):
        """Helper function to add attachment if URL is valid and not duplicate"""
        if not url or not isinstance(url, str) or url in seen_urls:
            return
        seen_urls.add(url)
        
        # Extract filename from URL if name is not provided
        if not name or name == "":
            name = url.split("/")[-1] or url.split("?")[0].split("/")[-1] or f"document_{len(attachments) + 1}"
        
        attachments.append({
            "opportunity_id": opportunity_id,
            "name": name,
            "source_url": url,
            "attachment_type": att_type,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "extra_metadata": metadata or {}
        })
    
    # 1. Resource links (top level)
    resource_links = record.get("resourceLinks") or record.get("resource_links") or []
    if isinstance(resource_links, str):
        resource_links = [resource_links]
    
    for idx, link in enumerate(resource_links):
        if isinstance(link, str):
            add_attachment(link, link.split("/")[-1] or f"resource_{idx + 1}", "resourceLink", 
                          metadata={"source": "sam_resource_link", "index": idx})
        elif isinstance(link, dict):
            url = link.get("url") or link.get("link") or link.get("downloadUrl") or link.get("href")
            name = link.get("title") or link.get("name") or link.get("description") or f"resource_{idx + 1}"
            mime_type = link.get("type") or link.get("mimeType") or link.get("fileType")
            size_bytes = link.get("size") or link.get("fileSize")
            if url:
                add_attachment(url, name, "resourceLink", mime_type, size_bytes,
                              metadata={"source": "sam_resource_link", "index": idx, "raw": link})
    
    # 2. Attachments (top level)
    sam_attachments = record.get("attachments") or record.get("attachmentLinks") or []
    if isinstance(sam_attachments, str):
        sam_attachments = [sam_attachments]
    
    for idx, att in enumerate(sam_attachments):
        if isinstance(att, str):
            add_attachment(att, att.split("/")[-1] or f"attachment_{idx + 1}", "attachment",
                          metadata={"source": "sam_attachment", "index": idx})
        elif isinstance(att, dict):
            url = att.get("url") or att.get("link") or att.get("sourceUrl") or att.get("downloadUrl")
            name = att.get("name") or att.get("fileName") or att.get("title") or att.get("description") or f"attachment_{idx + 1}"
            mime_type = att.get("mimeType") or att.get("type") or att.get("fileType")
            size_bytes = att.get("size") or att.get("fileSize")
            if url:
                add_attachment(url, name, "attachment", mime_type, size_bytes,
                              metadata={"source": "sam_attachment", "index": idx, "raw": att})
    
    # 3. Documents (top level)
    documents = record.get("documents") or []
    if isinstance(documents, str):
        documents = [documents]
    
    for idx, doc in enumerate(documents):
        if isinstance(doc, str):
            add_attachment(doc, doc.split("/")[-1] or f"document_{idx + 1}", "document",
                          metadata={"source": "sam_document", "index": idx})
        elif isinstance(doc, dict):
            url = doc.get("url") or doc.get("link") or doc.get("downloadUrl")
            name = doc.get("title") or doc.get("name") or doc.get("description") or f"document_{idx + 1}"
            mime_type = doc.get("mimeType") or doc.get("type") or doc.get("fileType")
            size_bytes = doc.get("size") or doc.get("fileSize")
            if url:
                add_attachment(url, name, "document", mime_type, size_bytes,
                              metadata={"source": "sam_document", "index": idx, "raw": doc})
    
    # 4. Check raw_data if it's a dict (nested structure)
    raw_data = record.get("raw_data")
    if isinstance(raw_data, dict):
        # Recursively check raw_data for attachments
        raw_resource_links = raw_data.get("resourceLinks") or raw_data.get("resource_links") or []
        if isinstance(raw_resource_links, str):
            raw_resource_links = [raw_resource_links]
        
        for idx, link in enumerate(raw_resource_links):
            if isinstance(link, str):
                add_attachment(link, link.split("/")[-1] or f"raw_resource_{idx + 1}", "resourceLink",
                              metadata={"source": "raw_data_resource_link", "index": idx})
            elif isinstance(link, dict):
                url = link.get("url") or link.get("link") or link.get("downloadUrl") or link.get("href")
                name = link.get("title") or link.get("name") or link.get("description") or f"raw_resource_{idx + 1}"
                if url:
                    add_attachment(url, name, "resourceLink",
                                  metadata={"source": "raw_data_resource_link", "index": idx})
        
        raw_attachments = raw_data.get("attachments") or []
        if isinstance(raw_attachments, str):
            raw_attachments = [raw_attachments]
        
        for idx, att in enumerate(raw_attachments):
            if isinstance(att, str):
                add_attachment(att, att.split("/")[-1] or f"raw_attachment_{idx + 1}", "attachment",
                              metadata={"source": "raw_data_attachment", "index": idx})
            elif isinstance(att, dict):
                url = att.get("url") or att.get("link") or att.get("downloadUrl")
                name = att.get("title") or att.get("name") or att.get("description") or f"raw_attachment_{idx + 1}"
                if url:
                    add_attachment(url, name, "attachment",
                                  metadata={"source": "raw_data_attachment", "index": idx})
    
    return attachments
