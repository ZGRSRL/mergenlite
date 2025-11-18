"""
Smoke Tests for Opportunities CRUD
Basic tests: sync → list → detail
"""
import pytest
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Opportunity, OpportunityAttachment
from app.crud.opportunities import (
    upsert_opportunity,
    get_opportunity,
    list_opportunities,
    get_attachments_for_opportunity
)
from app.services.opportunity_sync_service import sync_from_sam


@pytest.fixture
def db_session():
    """Get database session"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def test_opportunity_upsert(db_session: Session):
    """Test creating/updating an opportunity"""
    test_data = {
        "opportunity_id": "test_opp_001",
        "notice_id": "test_notice_001",
        "title": "Test Opportunity",
        "posted_date": None,
        "naics_code": "721110",
        "raw_data": {"test": "data"},
        "status": "active"
    }
    
    opp = upsert_opportunity(db_session, test_data)
    
    assert opp.id is not None
    assert opp.notice_id == "test_notice_001"
    assert opp.title == "Test Opportunity"
    assert opp.naics_code == "721110"
    
    # Test update
    test_data["title"] = "Updated Title"
    updated_opp = upsert_opportunity(db_session, test_data)
    
    assert updated_opp.id == opp.id
    assert updated_opp.title == "Updated Title"


def test_get_opportunity(db_session: Session):
    """Test getting an opportunity by ID"""
    # Create test opportunity
    test_data = {
        "opportunity_id": "test_opp_002",
        "notice_id": "test_notice_002",
        "title": "Test Opportunity 2",
        "naics_code": "721110",
        "status": "active"
    }
    opp = upsert_opportunity(db_session, test_data)
    
    # Get by ID
    retrieved = get_opportunity(db_session, opp.id)
    
    assert retrieved is not None
    assert retrieved.id == opp.id
    assert retrieved.title == "Test Opportunity 2"


def test_list_opportunities(db_session: Session):
    """Test listing opportunities with filters"""
    # Create test opportunities
    for i in range(5):
        test_data = {
            "opportunity_id": f"test_opp_{i}",
            "notice_id": f"test_notice_{i}",
            "title": f"Test Opportunity {i}",
            "naics_code": "721110" if i % 2 == 0 else "541511",
            "status": "active"
        }
        upsert_opportunity(db_session, test_data)
    
    # List all
    all_opps = list_opportunities(db_session, skip=0, limit=10)
    assert len(all_opps) >= 5
    
    # Filter by NAICS
    naics_opps = list_opportunities(db_session, skip=0, limit=10, naics_code="721110")
    assert all(opp.naics_code == "721110" for opp in naics_opps)
    
    # Filter by keyword
    keyword_opps = list_opportunities(db_session, skip=0, limit=10, keyword="Test Opportunity 0")
    assert len(keyword_opps) >= 1
    assert "Test Opportunity 0" in keyword_opps[0].title


def test_sync_from_sam_integration(db_session: Session):
    """Test sync from SAM (requires SAM_API_KEY)"""
    import os
    if not os.getenv("SAM_API_KEY"):
        pytest.skip("SAM_API_KEY not set, skipping integration test")
    
    import asyncio
    result = asyncio.run(sync_from_sam(db_session, {
        "naics": "721110",
        "days_back": 7,
        "limit": 10
    }))
    
    assert "count_new" in result
    assert "count_updated" in result
    assert "total_processed" in result
    assert result["total_processed"] >= 0


def test_opportunity_with_attachments(db_session: Session):
    """Test opportunity with attachments relationship"""
    # Create opportunity
    test_data = {
        "opportunity_id": "test_opp_003",
        "notice_id": "test_notice_003",
        "title": "Test Opportunity with Attachments",
        "naics_code": "721110",
        "status": "active"
    }
    opp = upsert_opportunity(db_session, test_data)
    
    # Create attachment
    from app.crud.opportunities import create_attachment
    attachment_data = {
        "opportunity_id": opp.id,
        "name": "test_file.pdf",
        "source_url": "https://example.com/test_file.pdf",
        "attachment_type": "document"
    }
    attachment = create_attachment(db_session, attachment_data)
    
    assert attachment.id is not None
    assert attachment.opportunity_id == opp.id
    
    # Get attachments for opportunity
    attachments = get_attachments_for_opportunity(db_session, opp.id)
    assert len(attachments) >= 1
    assert attachments[0].name == "test_file.pdf"

