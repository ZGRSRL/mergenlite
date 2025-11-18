#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analiz loglarını kontrol et"""

import logging
from pathlib import Path
from opportunity_runner import analyze_opportunity

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    opportunity_code = "57cd76db400c4e7ca895d40bf6454173"
    notice_id = "57cd76db400c4e7ca895d40bf6454173"
    
    logger.info("="*60)
    logger.info("🚀 ANALİZ BAŞLIYOR")
    logger.info("="*60)
    logger.info(f"Opportunity Code: {opportunity_code}")
    logger.info(f"Notice ID: {notice_id}")
    logger.info("="*60)
    
    try:
        result = analyze_opportunity(
            base_dir=".",
            opportunity_code=opportunity_code,
            notice_id=notice_id,
            opportunity_id=notice_id,
            form_data={'evaluation_focus': []},
            download_from_sam_gov=False
        )
        
        logger.info("="*60)
        logger.info("✅ ANALİZ TAMAMLANDI")
        logger.info("="*60)
        
        metadata = result.get('metadata', {})
        logger.info(f"📁 Klasör: {metadata.get('folder')}")
        logger.info(f"📄 Döküman Sayısı: {metadata.get('documents_count', 0)}")
        logger.info(f"⏱️ Süre: {metadata.get('analysis_duration_seconds', 0):.2f} saniye")
        
        # Klasör içeriğini göster
        folder = Path(metadata.get('folder', ''))
        if folder.exists():
            logger.info("\n📂 Klasör İçeriği:")
            for file in sorted(folder.glob("*")):
                size = file.stat().st_size if file.is_file() else 0
                logger.info(f"  - {file.name} ({size:,} bytes)")
        
    except Exception as e:
        logger.error(f"❌ ANALİZ HATASI: {e}", exc_info=True)

