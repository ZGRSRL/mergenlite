import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DistilSAM")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv('mergen/.env')

try:
    from sam_integration import SAMIntegration
    from detailed_opportunity_analysis import DetailedOpportunityAnalyzer
    from backend_utils import get_db_session
    from mergenlite_models import Opportunity
    from mail_package import build_mail_package, send_email_via_smtp
    from pdf_report_builder import build_pdf_report
    from sow_pdf_generator import generate_gpt_style_sow_pdf # Added import  # Added import
except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}")
    logger.error("Make sure you are running this script from the project root (d:\\Mergenlite).")
    sys.exit(1)

def main():
    print("="*80)
    print("SAM.GOV END-TO-END TEST")
    print("Fetch -> DB Save -> Analyze -> Email")
    print("="*80)
    
    # 1. Initialize SAM Integration
    print("\n[1] Initializing SAM.gov Integration...")
    sam = SAMIntegration()
    
    # Check if API key is loaded
    if not sam.api_key:
        print("ERROR: SAM_API_KEY not found in environment or .env file.")
        sys.exit(1)
        
    print(f"API Key loaded. Version: {sam.api_version}")

    # 2. Fetch Opportunities (Rate Limited)
    print("\n[2] Fetching opportunities (Limit: 5)...")
    opportunities = []
    try:
        # Try to fetch real data
        opportunities = sam.fetch_opportunities(
            naics_codes=['721110'], 
            days_back=30, 
            limit=5
        )
    except Exception as e:
        print(f"Error fetching opportunities: {e}")
        print("    [NOTE] API call failed (likely Rate Limit 429). Switching to MOCK data.")
        opportunities = []

    # Mock Data Fallback if API blocked
    if not opportunities:
        print(">> No opportunities found or API blocked.")
        print(">> GENERATING MOCK DATA to continue test pipeline...")
        opportunities = [{
            'opportunityId': 'MOCK-123456789',
            'noticeId': 'MOCK-NOTICE-001',
            'title': 'Mock Hotel Services for Testing',
            'solicitationNumber': 'SOL-TEST-001',
            'postedDate': datetime.now().isoformat(),
            'responseDeadLine': datetime.now().isoformat(),
            'description': 'This is a mock opportunity description for end-to-end testing purposes.',
            'raw_data': {'mock': True}
        }]

    print(f"Processing {len(opportunities)} opportunities.")
    
    # 3. Save to Database
    print("\n[3] Saving to Database...")
    db = get_db_session()
    if db:
        try:
            for i, opp in enumerate(opportunities, 1):
                opp_id = opp.get('opportunityId')
                notice_id = opp.get('noticeId')
                title = opp.get('title')
                print(f"  {i}. [{notice_id}] {title[:60]}...")
                
                # Check exist
                existing = db.query(Opportunity).filter(Opportunity.opportunity_id == opp_id).first()
                if not existing:
                    new_opp = Opportunity(
                        opportunity_id=opp_id,
                        notice_id=notice_id,
                        title=title,
                        raw_data=opp.get('raw_data', {})
                    )
                    db.add(new_opp)
                    print(f"     -> INSERTED into DB")
                else:
                    print(f"     -> ALREADY EXISTS in DB")
            db.commit()
            print("  [OK] Database sync complete.")
        except Exception as e:
            print(f"  [ERROR] Database error: {e}")
            db.rollback()
        finally:
            db.close()
    else:
        print("  [WARN] Database connection failed.")

    # 4. Run End-to-End Analysis
    selected_opp = opportunities[0]
    target_id = selected_opp.get('opportunityId') or selected_opp.get('noticeId')
    
    print(f"\n[4] Starting Detailed Analysis for: {target_id}")
    
    analyzer = DetailedOpportunityAnalyzer(target_id)
    analysis_success = False
    
    try:
        # A. Fetch Data
        print("    -> Fetching full details...")
        # If mock, skip fetch
        if 'MOCK-' in target_id:
             analyzer.opportunity_data = selected_opp
        else:
            analyzer.fetch_opportunity_data()
        
        # B. Download Docs
        print("    -> Downloading documents...")
        if 'MOCK-' in target_id:
            # Create a dummy file for email attachment test
            dummy_pdf = analyzer.output_dir / "analysis_report.pdf"
            dummy_pdf.parent.mkdir(parents=True, exist_ok=True)
            with open(dummy_pdf, 'w') as f:
                f.write("Dummy PDF Content")
            print("       (Mock PDF created)")
        else:
             analyzer.download_documents()
        
        # C. Run Analysis Agents
        print("    -> Running agents...")
        if 'MOCK-' in target_id:
            # Mock results with RICH DATA for PDF testing
            results = {
                'agents': {
                    'requirements_extractor': {
                        'total_requirements': 12,
                        'requirements': [
                            {'text': 'Vendor must provide 50 single occupancy rooms for 5 nights (Sep 10-15).', 'priority': 'high', 'category': 'lodging', 'source': 'SOW.pdf'},
                            {'text': 'Hotel must be within 2 miles of the Convention Center.', 'priority': 'high', 'category': 'location', 'source': 'SOW.pdf'},
                            {'text': 'Breakfast must be included in the room rate (Federal Per Diem compliant).', 'priority': 'medium', 'category': 'food_beverage', 'source': 'SOW.pdf'},
                            {'text': 'Conference room "Alpha" must seat 100 people in classroom style.', 'priority': 'high', 'category': 'conference', 'source': 'RFQ_Details.docx'},
                            {'text': 'Main conference room requires 2 projectors, 2 screens, and 4 wireless microphones.', 'priority': 'medium', 'category': 'av_technical', 'source': 'RFQ_Details.docx'},
                            {'text': 'Vendor must accept government purchase card (GPC) for payments under $10,000.', 'priority': 'low', 'category': 'invoicing', 'source': 'SOW.pdf'},
                            {'text': 'Cancellation policy must allow full refund up to 72 hours prior to arrival.', 'priority': 'high', 'category': 'contractual', 'source': 'Terms.pdf'},
                            {'text': 'High-speed wireless internet access required in all meeting spaces and guest rooms.', 'priority': 'medium', 'category': 'technical', 'source': 'SOW.pdf'},
                        ]
                    },
                    'compliance_analyst': {'results': {
                        'gap_count': 0,
                        'met_count': 8, 
                        'overall_risk': 'Low'
                    }},
                    'proposal_writer': {'results': {'executive_summary': 'This is a mock executive summary for the email test.'}},
                    'quality_assurance': {'results': {'quality_score': 0.95, 'completeness': 1.0}}
                }
            }
            # Create dummy report.json for mail_package - WITH REQUIREMENTS
            report_data = {
                'opportunity_info': {'solicitation_number': selected_opp.get('noticeId'), 'title': selected_opp.get('title')},
                'requirements': results['agents']['requirements_extractor']['requirements'], # Pass full reqs
                'fit_assessment': {
                    'overall_score': 95,
                    'summary': 'Excellent fit based on mock analysis. All requirements appear to be met.',
                    'strengths': ['Perfect Location', 'Capacity Met', 'Compliant Terms'],
                    'risks': ['None detected']
                }
            }
            with open(analyzer.output_dir / "report.json", "w") as f:
                json.dump(report_data, f)
            
            # GENERATE PDF REPORT FOR TESTING
            print("    [MOCK] Generating PDF Report...")
            pdf_path = analyzer.output_dir / "detailed_analysis_report.pdf"
            build_pdf_report(
                report_json=report_data,
                output_path=str(pdf_path),
                opportunity_code=target_id
            )
            
            # GENERATE SOW PDF (Blue Band Style)
            print("    [MOCK] Generating SOW PDF...")
            sow_pdf_path = analyzer.output_dir / f"sow_hotel_{target_id}.pdf"
            generate_gpt_style_sow_pdf(
                output_path=str(sow_pdf_path),
                opportunity_code=target_id,
                sow_data={
                    "solicitation_number": "MOCK-SOL-123",
                    "agency": "Mock Agency",
                    "event_title": "Mock Hotel Services",
                    "meeting_name": "Mock Conference",
                    "meeting_dates": "September 10-15, 2025"
                }
            )
            
            analysis_success = True
        else:
            results = analyzer.run_detailed_analysis()
            analysis_success = True
            
        print("  [OK] Analysis complete.")

    except Exception as e:
        print(f"  [ERROR] Analysis failed: {e}")
        # Continue to email if we have partial results or mock needed? 
        # For now, let's assume we need success to email.
    
    # 5. Email Results
    if analysis_success:
        print("\n[5] Sending Email...")
        print("    From: mergen.system@gmail.com (Configured System Email)")
        print("    To:   ozgursarli@hotmail.com")
        
        # SMTP Config
        smtp_config = {
             'host': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
             'port': int(os.getenv('SMTP_PORT', 587)),
             'username': os.getenv('SMTP_USERNAME', 'arl.zgr@gmail.com'),
             'password': os.getenv('SMTP_PASSWORD', ''),
             'use_tls': True
        }
        
        if not smtp_config['password']:
             print("    [WARN] SMTP_PASSWORD not set in environment. Checking .env...")
             # Try to force load if not set
             pass

        package = build_mail_package(
            opportunity_code=target_id,
            folder_path=str(analyzer.output_dir),
            to_email="ozgursarli@hotmail.com",
            from_email="arl.zgr@gmail.com"
        )
        
        success = send_email_via_smtp(package, smtp_config)
        if success:
            print("    [OK] Email sent successfully.")
        else:
            print("    [ERROR] Failed to send email. Check logs.")

if __name__ == "__main__":
    main()
