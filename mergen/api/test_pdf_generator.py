#!/usr/bin/env python
"""
Generate a sample PDF using the analysis PDF generator to verify styling/content.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json

# Ensure imports resolve
import sys

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from app.services.pdf_generator import generate_analysis_pdf, REPORTLAB_AVAILABLE  # type: ignore


def build_sample_payload():
    today = datetime.utcnow().date()
    sow_analysis = {
        "event_details": {
            "event_name": "Judicial Training Summit",
            "solicitation_number": "RFQ-12345",
            "agency": "Department of Justice",
            "start_date": (today + timedelta(days=30)).isoformat(),
            "end_date": (today + timedelta(days=33)).isoformat(),
            "location": "Washington, DC",
            "submission_due_date": (today + timedelta(days=10)).isoformat(),
        },
        "room_requirements": {
            "total_room_nights": 120,
            "special_requirements": "Suites near elevators, late checkout for instructors.",
            "daily_breakdown": [
                {"day": "Day 1", "date": (today + timedelta(days=30)).isoformat(), "rooms_per_night": 40},
                {"day": "Day 2", "date": (today + timedelta(days=31)).isoformat(), "rooms_per_night": 40},
                {"day": "Day 3", "date": (today + timedelta(days=32)).isoformat(), "rooms_per_night": 40},
            ],
        },
        "function_space_requirements": {
            "daily_breakdown": [
                {
                    "day": "Day 1",
                    "date": (today + timedelta(days=30)).isoformat(),
                    "rooms": [
                        {
                            "room_name": "Grand Ballroom",
                            "setup": "Classroom",
                            "capacity": 150,
                            "av_needs": "Dual projectors, confidence monitors",
                            "special_notes": "Government podium branding",
                        }
                    ],
                }
            ]
        },
        "av_requirements": {
            "hybrid_meeting_requirements": {
                "owls_required": "2 per breakout room",
                "zoom_management": "Vendor provides live operator",
                "other_requirements": "HD recording delivery in MP4 within 48 hours.",
            },
            "court_reporter_audio_feed": {"required": "Yes", "details": "XLR line out at FOH console."},
            "breakout_room_power_setup": {"power_strips": "4 per room", "setup_requirements": "Reset nightly."},
        },
        "food_beverage_requirements": {
            "daily_breakdown": [
                {
                    "day": "Day 1",
                    "date": (today + timedelta(days=30)).isoformat(),
                    "items": [
                        {"time": "07:30", "headcount": 120, "menu": "Hot breakfast buffet"},
                        {"time": "12:00", "headcount": 120, "menu": "Plated lunch"},
                    ],
                }
            ]
        },
        "commercial_terms": {
            "naics_code": "721110",
            "psc_code": "X111",
            "set_aside_type": "Small Business",
            "size_standard": "35M",
            "ada_compliance": "Required",
            "wifi_internet": "Dedicated 100Mbps line included",
            "parking_requirements": "Self parking included for 20 vehicles",
            "cancellation_terms": "Full refund up to 30 days prior",
            "av_discount_required": "10%",
            "fb_discount_required": "15%",
        },
        "cost_proposal": {
            "quote_due_date": (today + timedelta(days=12)).isoformat(),
            "submission_method": "Email",
            "submission_email": "contracts@example.gov",
            "required_attachments": "Itemized cost breakdown, banquet event orders",
        },
        "evaluation_criteria": {
            "payment_terms": "Net 30",
            "tax_exemption_status": "Yes - certificate provided",
            "billing_method": "Milestone",
            "cancellation_policy": "Government standard clause",
        },
        "compliance_requirements": {
            "far_clauses": [{"number": "52.212-4", "title": "Contract Terms"}],
            "edar_clauses": [{"number": "3452.216-71", "title": "Contracting Officer Authority"}],
        },
        "appendices": {
            "additional_documents": "Floor plans, sample seating charts",
            "other_requirements": "Security clearance list 2 weeks prior",
        },
    }
    opportunity = {
        "notice_id": "RFQ-12345",
        "title": "Judicial Training Summit Support",
        "agency": "Department of Justice",
        "naics_code": "721110",
    }
    analysis_result = {
        "sow_analysis": sow_analysis,
        "opportunity": opportunity,
        "document_analysis": {
            "documents_analyzed": 3,
            "total_word_count": 18452,
            "total_text_length": "18 pages",
            "total_tables": 12,
        },
        "notes": "This sample PDF confirms the styling, sections, and data rendering pipeline.",
    }
    return analysis_result, opportunity


def main() -> int:
    print("=" * 60)
    print("PDF GENERATOR TEST")
    print("=" * 60)
    
    if not REPORTLAB_AVAILABLE:
        print("[ERROR] reportlab is not installed. Run `pip install reportlab`.")
        return 1
    
    analysis_result, opportunity = build_sample_payload()
    
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"sample_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    success = generate_analysis_pdf(output_file, analysis_result, opportunity)
    if success and output_file.exists():
        print(f"[OK] Sample PDF generated: {output_file}")
        return 0
    print("[ERROR] Failed to generate PDF. Check logs for details.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
