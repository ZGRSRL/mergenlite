#!/usr/bin/env python3
"""
Full Analysis Test Script
Terminal'de detaylı analiz testi
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test parametreleri
OPPORTUNITY_CODE = "3f38c706101242f6b97d200382c70e2e"
NOTICE_ID = "3f38c706101242f6b97d200382c70e2e"
OPPORTUNITY_ID = "3f38c706101242f6b97d200382c70e2e"

# Form data (detaylı analiz için)
FORM_DATA = {
    "company_name": "CREATA GLOBAL EVENT AGENCY LLC",
    "project_type": "Conference and Accommodation Services",
    "location": "Buenos Aires, Argentina",
    "dates": "2025-11-30",
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

def test_full_analysis():
    """Full analiz testi"""
    try:
        from opportunity_runner import analyze_opportunity
        
        logger.info("="*60)
        logger.info("🚀 FULL ANALİZ TESTİ BAŞLIYOR")
        logger.info("="*60)
        logger.info(f"Opportunity Code: {OPPORTUNITY_CODE}")
        logger.info(f"Notice ID: {NOTICE_ID}")
        logger.info(f"Form Data: {len(FORM_DATA.get('evaluation_focus', []))} kriter")
        logger.info("="*60)
        
        # Analiz başlat
        result = analyze_opportunity(
            base_dir=".",
            opportunity_code=OPPORTUNITY_CODE,
            notice_id=NOTICE_ID,
            opportunity_id=OPPORTUNITY_ID,
            form_data=FORM_DATA,
            download_from_sam_gov=False  # Mevcut dosyaları kullan (API quota limiti)
        )
        
        # Sonuçları göster
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
        
        # Report içeriğini göster
        if report_path.exists():
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            logger.info("\n📋 RAPOR ÖZETİ:")
            opp_info = report.get('opportunity_info', {})
            logger.info(f"  - Solicitation: {opp_info.get('solicitation_number', 'N/A')}")
            logger.info(f"  - Title: {opp_info.get('title', 'N/A')}")
            
            event_req = report.get('event_requirements', {})
            logger.info(f"  - Location: {event_req.get('location', 'N/A')}")
            logger.info(f"  - Date Range: {event_req.get('date_range', 'N/A')}")
            
            fit = report.get('fit_assessment', {})
            logger.info(f"  - Overall Score: {fit.get('overall_score', 0)}/100")
            logger.info(f"  - Strengths: {len(fit.get('strengths', []))}")
            logger.info(f"  - Risks: {len(fit.get('risks', []))}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ TEST TAMAMLANDI")
        logger.info("="*60)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ TEST HATASI: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    result = test_full_analysis()
    sys.exit(0 if result else 1)

