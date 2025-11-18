#!/usr/bin/env python3
"""
Demo data seeding script for ZgrBid
"""
import os
import sys
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, engine
from app.models import Document, Requirement, Evidence, FacilityFeature, PricingItem, PastPerformance, VectorChunk
from app.db import Base

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def seed_demo_data():
    """Seed demo data"""
    db = SessionLocal()
    
    try:
        # Create sample documents
        rfq_doc = Document(
            kind="rfq",
            title="AQD Seminar RFQ - 140D0424Q0292",
            path="samples/rfq.pdf",
            meta_json={
                "rfq_number": "140D0424Q0292",
                "agency": "Department of Defense",
                "location": "Orlando, FL",
                "event_dates": "2024-04-14 to 2024-04-18"
            }
        )
        db.add(rfq_doc)
        db.flush()
        
        facility_doc = Document(
            kind="facility",
            title="DoubleTree Technical Specifications",
            path="samples/facility.pdf",
            meta_json={
                "hotel_name": "DoubleTree by Hilton",
                "location": "Orlando, FL",
                "capacity": 100
            }
        )
        db.add(facility_doc)
        db.flush()
        
        past_perf_doc = Document(
            kind="past_performance",
            title="Past Performance Portfolio",
            path="samples/past_performance.pdf",
            meta_json={
                "company": "ZgrBid Solutions",
                "years_experience": 10
            }
        )
        db.add(past_perf_doc)
        db.flush()
        
        pricing_doc = Document(
            kind="pricing",
            title="Pricing Spreadsheet",
            path="samples/pricing.xlsx",
            meta_json={
                "currency": "USD",
                "tax_rate": 0.0
            }
        )
        db.add(pricing_doc)
        db.flush()
        
        # Create sample requirements
        requirements = [
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-001",
                text="Accommodate 100 participants for general session",
                category="capacity",
                priority="high"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-002",
                text="Provide 2 breakout rooms for 15 participants each",
                category="capacity",
                priority="high"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-003",
                text="Event dates: April 14-18, 2024",
                category="date",
                priority="critical"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-004",
                text="Provide airport shuttle service",
                category="transport",
                priority="medium"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-005",
                text="Provide complimentary Wi-Fi internet access",
                category="av",
                priority="medium"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-006",
                text="Comply with FAR 52.204-24 representation requirements",
                category="clauses",
                priority="critical"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-007",
                text="Submit invoices through IPP system",
                category="invoice",
                priority="high"
            ),
            Requirement(
                rfq_id=rfq_doc.id,
                code="R-008",
                text="Provide AV equipment for main room and breakout rooms",
                category="av",
                priority="high"
            )
        ]
        
        for req in requirements:
            db.add(req)
        db.flush()
        
        # Create sample facility features
        facility_features = [
            FacilityFeature(
                name="shuttle",
                value="Free airport shuttle service available every 30 minutes",
                source_doc_id=facility_doc.id
            ),
            FacilityFeature(
                name="wifi",
                value="Complimentary high-speed Wi-Fi throughout the property",
                source_doc_id=facility_doc.id
            ),
            FacilityFeature(
                name="parking",
                value="Complimentary self-parking for all guests",
                source_doc_id=facility_doc.id
            ),
            FacilityFeature(
                name="breakout_rooms",
                value="2 breakout rooms available, each accommodating 15 participants",
                source_doc_id=facility_doc.id
            ),
            FacilityFeature(
                name="boardroom",
                value="Executive boardroom available for 20 participants",
                source_doc_id=facility_doc.id
            ),
            FacilityFeature(
                name="av_equipment",
                value="Full AV equipment including projectors, microphones, and screens",
                source_doc_id=facility_doc.id
            )
        ]
        
        for feature in facility_features:
            db.add(feature)
        db.flush()
        
        # Create sample pricing items
        pricing_items = [
            PricingItem(
                rfq_id=rfq_doc.id,
                name="Room Block - 4 nights",
                description="Accommodation for 100 participants, 4 nights",
                qty=100.0,
                unit="room_night",
                unit_price=135.00,
                total_price=54000.00,
                category="lodging"
            ),
            PricingItem(
                rfq_id=rfq_doc.id,
                name="Main Room AV Setup",
                description="Audio-visual equipment for main conference room",
                qty=1.0,
                unit="setup",
                unit_price=2500.00,
                total_price=2500.00,
                category="av"
            ),
            PricingItem(
                rfq_id=rfq_doc.id,
                name="Breakout Room AV",
                description="Audio-visual equipment for 2 breakout rooms",
                qty=2.0,
                unit="room",
                unit_price=500.00,
                total_price=1000.00,
                category="av"
            ),
            PricingItem(
                rfq_id=rfq_doc.id,
                name="Airport Shuttle Service",
                description="Shuttle service for airport transfers",
                qty=1.0,
                unit="service",
                unit_price=1500.00,
                total_price=1500.00,
                category="transportation"
            ),
            PricingItem(
                rfq_id=rfq_doc.id,
                name="Project Management",
                description="Full project management and coordination",
                qty=1.0,
                unit="project",
                unit_price=5000.00,
                total_price=5000.00,
                category="management"
            )
        ]
        
        for item in pricing_items:
            db.add(item)
        db.flush()
        
        # Create sample past performance
        past_performances = [
            PastPerformance(
                title="KYNG Statewide BPA Conference Management",
                client="Kentucky National Guard",
                scope="Full conference management for 75 participants including facility coordination, AV services, and logistics",
                period="2022-2023",
                value=45000.0,
                ref_info={
                    "poc": "John Smith",
                    "title": "Contracting Officer",
                    "phone": "+1-502-555-0123",
                    "email": "john.smith@ky.ng.mil"
                }
            ),
            PastPerformance(
                title="Aviano Air Base Training Seminar",
                client="US Air Force",
                scope="Training seminar management for 50 participants with AV support and facility coordination",
                period="2023",
                value=32000.0,
                ref_info={
                    "poc": "Sarah Johnson",
                    "title": "Training Coordinator",
                    "phone": "+39-0434-30-1234",
                    "email": "sarah.johnson@us.af.mil"
                }
            ),
            PastPerformance(
                title="Department of Energy Workshop Series",
                client="US Department of Energy",
                scope="Multi-day workshop series for 120 participants with comprehensive event management",
                period="2023-2024",
                value=85000.0,
                ref_info={
                    "poc": "Michael Brown",
                    "title": "Program Manager",
                    "phone": "+1-202-555-0456",
                    "email": "michael.brown@energy.gov"
                }
            )
        ]
        
        for perf in past_performances:
            db.add(perf)
        db.flush()
        
        # Create sample evidence
        evidence_items = [
            Evidence(
                requirement_id=requirements[0].id,  # R-001
                source_doc_id=facility_doc.id,
                snippet="Main conference room accommodates up to 100 participants with theater-style seating",
                score=0.95,
                evidence_type="facility"
            ),
            Evidence(
                requirement_id=requirements[1].id,  # R-002
                source_doc_id=facility_doc.id,
                snippet="2 breakout rooms available, each accommodating 15 participants",
                score=0.90,
                evidence_type="facility"
            ),
            Evidence(
                requirement_id=requirements[3].id,  # R-004
                source_doc_id=facility_doc.id,
                snippet="Free airport shuttle service available every 30 minutes",
                score=0.85,
                evidence_type="facility"
            ),
            Evidence(
                requirement_id=requirements[4].id,  # R-005
                source_doc_id=facility_doc.id,
                snippet="Complimentary high-speed Wi-Fi throughout the property",
                score=0.90,
                evidence_type="facility"
            )
        ]
        
        for evidence in evidence_items:
            db.add(evidence)
        db.flush()
        
        # Create sample vector chunks
        sample_chunks = [
            "Main conference room accommodates up to 100 participants with theater-style seating",
            "2 breakout rooms available, each accommodating 15 participants",
            "Free airport shuttle service available every 30 minutes",
            "Complimentary high-speed Wi-Fi throughout the property",
            "Complimentary self-parking for all guests",
            "Executive boardroom available for 20 participants",
            "Full AV equipment including projectors, microphones, and screens"
        ]
        
        for i, chunk_text in enumerate(sample_chunks):
            chunk = VectorChunk(
                document_id=facility_doc.id,
                chunk=chunk_text,
                embedding=[0.1] * 384,  # Placeholder embedding
                chunk_type="paragraph",
                page_number=1
            )
            db.add(chunk)
        
        db.commit()
        
        print(f"Demo data seeded successfully!")
        print(f"RFQ ID: {rfq_doc.id}")
        print(f"Facility Doc ID: {facility_doc.id}")
        print(f"Past Performance Doc ID: {past_perf_doc.id}")
        print(f"Pricing Doc ID: {pricing_doc.id}")
        print(f"Total Requirements: {len(requirements)}")
        print(f"Total Facility Features: {len(facility_features)}")
        print(f"Total Pricing Items: {len(pricing_items)}")
        print(f"Total Past Performance: {len(past_performances)}")
        
    except Exception as e:
        print(f"Error seeding demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating tables...")
    create_tables()
    
    print("Seeding demo data...")
    seed_demo_data()
    
    print("Demo data seeding completed!")



