#!/usr/bin/env python3
"""
Manuel Test - Mevcut PDF ile analiz
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test için manuel bir PDF oluştur (opportunity description'dan)
OPPORTUNITY_CODE = "3f38c706101242f6b97d200382c70e2e"
FOLDER = Path("opportunities") / OPPORTUNITY_CODE

# Manuel test dökümanı oluştur
test_doc_content = """Conference and Accommodation Services in Buenos Aires, Argentina

OPPORTUNITY DESCRIPTION:
The U.S. Government requires conference and accommodation services in Buenos Aires, Argentina for an upcoming event scheduled for November 30, 2025.

REQUIREMENTS:
- Conference facilities for up to 100 participants
- Accommodation for 100 participants
- Meeting rooms with AV equipment
- Catering services
- Transportation services
- Location: Buenos Aires, Argentina
- Dates: November 2025

COMPLIANCE:
- FAR 52.212-4 applies
- Small business set-aside
- NAICS Code: 721110
- Electronic invoicing (IPP) required

COMMERCIAL TERMS:
- Estimated value: $50,000
- Payment terms: Net 30
- Per diem limits apply
"""

def create_test_document():
    """Test dökümanı oluştur"""
    FOLDER.mkdir(parents=True, exist_ok=True)
    test_file = FOLDER / "opportunity_description.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_doc_content)
    logger.info(f"✅ Test dökümanı oluşturuldu: {test_file}")
    return test_file

if __name__ == "__main__":
    try:
        from opportunity_runner import analyze_opportunity
        
        # Test dökümanı oluştur
        create_test_document()
        
        FORM_DATA = {
            "company_name": "CREATA GLOBAL EVENT AGENCY LLC",
            "project_type": "Conference and Accommodation Services",
            "location": "Buenos Aires, Argentina",
            "dates": "November 2025",
            "participants": 100,
            "budget": 50000,
            "naics": "721110",
            "contract_type": "Fixed Price",
            "evaluation_focus": [
                "Room capacity and ADA compliance",
                "Conference space AV requirements",
                "FAR/DFAR compliance clauses",
                "Electronic invoicing (IPP)",
                "Small business eligibility"
            ]
        }
        
        logger.info("="*60)
        logger.info("🚀 MANUEL ANALİZ TESTİ")
        logger.info("="*60)
        
        result = analyze_opportunity(
            base_dir=".",
            opportunity_code=OPPORTUNITY_CODE,
            notice_id=OPPORTUNITY_CODE,
            opportunity_id=OPPORTUNITY_CODE,
            form_data=FORM_DATA,
            download_from_sam_gov=False  # Mevcut dosyaları kullan
        )
        
        logger.info("="*60)
        logger.info("✅ ANALİZ TAMAMLANDI")
        logger.info("="*60)
        
        metadata = result.get('metadata', {})
        logger.info(f"📁 Klasör: {metadata.get('folder')}")
        logger.info(f"📄 Döküman Sayısı: {metadata.get('documents_count', 0)}")
        logger.info(f"⏱️ Süre: {metadata.get('analysis_duration_seconds', 0):.2f} saniye")
        
        # Dosya kontrolü
        folder = Path(metadata.get('folder', ''))
        if folder.exists():
            logger.info("\n📂 Klasör İçeriği:")
            for file in sorted(folder.glob("*")):
                size = file.stat().st_size if file.is_file() else 0
                logger.info(f"  - {file.name} ({size:,} bytes)")
        
        # Report kontrolü
        report_path = folder / "report.json"
        summary_path = folder / "summary.md"
        pdf_path = folder / "analysis_report.pdf"
        
        logger.info("\n📊 Çıktı Dosyaları:")
        logger.info(f"  - report.json: {'✅' if report_path.exists() else '❌'}")
        logger.info(f"  - summary.md: {'✅' if summary_path.exists() else '❌'}")
        logger.info(f"  - analysis_report.pdf: {'✅' if pdf_path.exists() else '❌'}")
        
        if report_path.exists():
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            logger.info("\n📋 RAPOR ÖZETİ:")
            opp_info = report.get('opportunity_info', {})
            logger.info(f"  - Solicitation: {opp_info.get('solicitation_number', 'N/A')}")
            
            event_req = report.get('event_requirements', {})
            logger.info(f"  - Location: {event_req.get('location', 'N/A')}")
            logger.info(f"  - Participants: {event_req.get('participants_target', 'N/A')}")
            
            fit = report.get('fit_assessment', {})
            logger.info(f"  - Overall Score: {fit.get('overall_score', 0)}/100")
            logger.info(f"  - Strengths: {len(fit.get('strengths', []))}")
            logger.info(f"  - Risks: {len(fit.get('risks', []))}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ TEST TAMAMLANDI")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ TEST HATASI: {e}", exc_info=True)
        sys.exit(1)

