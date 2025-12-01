from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Analysis 251'yi tam kontrol et
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 251).first()

if result:
    print("=" * 70)
    print("📊 ANALİZ 251 - TAM İÇERİK KONTROLÜ")
    print("=" * 70)
    print()
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis:
            # Event Details
            event = sow_analysis.get('EventDetails', {})
            print("📅 Event Details:")
            print(f"   Event Name: {event.get('event_name', 'N/A')}")
            print(f"   Start Date: {event.get('start_date', 'N/A')}")
            print(f"   End Date: {event.get('end_date', 'N/A')}")
            print(f"   Submission Due: {event.get('submission_due', 'N/A')}")
            
            # Commercial Terms
            commercial = sow_analysis.get('CommercialTerms', {})
            print(f"\n💼 Commercial Terms:")
            print(f"   NAICS: {commercial.get('naics_code', 'N/A')}")
            print(f"   PSC: {commercial.get('psc_code', 'N/A')}")
            print(f"   Set-Aside: {commercial.get('set_aside_type', 'N/A')}")
            print(f"   Size Standard: {commercial.get('size_standard', 'N/A')}")
            
            # Submission Package
            submission = sow_analysis.get('SubmissionPackage', {})
            print(f"\n📦 Submission Package:")
            print(f"   Method: {submission.get('submission_method', 'N/A')}")
            print(f"   Due Date: {submission.get('due_datetime_local', 'N/A')}")
            emails = submission.get('submission_emails', [])
            print(f"   Emails: {len(emails)} - {emails}")
            sections = submission.get('required_sections', [])
            print(f"   Sections: {len(sections)}")
            for sec in sections[:3]:
                print(f"      - {sec.get('name', 'N/A')}: {sec.get('max_pages', 'N/A')} pages")
            
            # Evaluation Criteria
            eval_criteria = sow_analysis.get('EvaluationCriteria', {})
            print(f"\n⭐ Evaluation Criteria:")
            factors = eval_criteria.get('factors', [])
            print(f"   Factors: {len(factors)}")
            for factor in factors:
                print(f"      - {factor.get('name', 'N/A')}: {factor.get('weight', 'N/A')}")
            notes = eval_criteria.get('notes', [])
            if notes:
                print(f"   Notes: {notes[:2]}")
            
            # Cost Proposal
            cost = sow_analysis.get('CostProposal', {})
            print(f"\n💰 Cost Proposal:")
            print(f"   Quote Due: {cost.get('quote_due_datetime_local', 'N/A')}")
            print(f"   Submission Method: {cost.get('submission_method', 'N/A')}")
            print(f"   Submission Email: {cost.get('submission_email', 'N/A')}")
            
            # Compliance Requirements
            compliance = sow_analysis.get('ComplianceRequirements', {})
            far_clauses = compliance.get('far_clauses', [])
            print(f"\n📋 Compliance Requirements:")
            print(f"   FAR Clauses: {len(far_clauses)}")
            for clause in far_clauses[:3]:
                print(f"      - {clause}")
            
            # Check what's missing
            print(f"\n⚠️ Eksik Veriler Kontrolü:")
            missing = []
            if not commercial.get('psc_code'):
                missing.append("PSC Code")
            if not commercial.get('set_aside_type'):
                missing.append("Set-Aside Type")
            if not submission.get('submission_emails') or len(submission.get('submission_emails', [])) == 0:
                missing.append("Submission Emails")
            if not eval_criteria.get('factors') or len(eval_criteria.get('factors', [])) == 0:
                missing.append("Evaluation Criteria Factors")
            if not cost.get('quote_due_datetime_local'):
                missing.append("Quote Due Date")
            
            if missing:
                print(f"   ❌ Eksik: {', '.join(missing)}")
            else:
                print(f"   ✅ Tüm kritik alanlar dolu!")

db.close()

