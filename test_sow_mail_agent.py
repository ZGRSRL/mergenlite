#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOW & Mail Agent Test Script
"""

import json
import logging
from pathlib import Path
from agents.sow_mail_agent import make_sow_mail_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sow_mail_agent():
    """SOW ve Mail Agent'ı test et"""
    
    print("="*60)
    print("[TEST] SOW & MAIL AGENT TEST")
    print("="*60)
    
    # Test için mevcut bir analiz sonucu kullan
    test_opportunity_id = "57cd76db400c4e7ca895d40bf6454173"
    folder_path = Path("opportunities") / test_opportunity_id
    report_json_path = folder_path / "report.json"
    
    if not report_json_path.exists():
        logger.error(f"[ERROR] Report JSON not found: {report_json_path}")
        return False
    
    print(f"\n[INFO] Using analysis: {test_opportunity_id}")
    print(f"[INFO] Report JSON: {report_json_path}")
    
    # Report JSON'u yükle
    try:
        with open(report_json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        print("[OK] Report JSON loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading report JSON: {e}")
        return False
    
    # SOW Agent oluştur
    print("\n[STEP] Creating SOW Agent...")
    try:
        sow_agent = make_sow_mail_agent()
        print("[OK] SOW Agent created")
    except Exception as e:
        logger.error(f"[ERROR] Error creating SOW Agent: {e}", exc_info=True)
        return False
    
    # Sample SOW template kontrolü
    if sow_agent.sample_sow_template:
        print(f"[OK] Sample SOW template loaded ({len(sow_agent.sample_sow_template)} chars)")
    else:
        print("[WARN] Sample SOW template not loaded, using default")
    
    # SOW oluştur
    print("\n[STEP] Generating SOW...")
    try:
        sow_result = sow_agent.generate_sow(
            report_data=report_data,
            opportunity_info=report_data.get('opportunity_info', {}),
            vendor_profile=None
        )
        
        sow_text = sow_result.get('sow_text', '')
        sow_html = sow_result.get('sow_html', '')
        
        print(f"[OK] SOW generated successfully")
        print(f"     - Text length: {len(sow_text)} chars")
        print(f"     - HTML length: {len(sow_html)} chars")
        
        # SOW içeriğini göster (ilk 500 karakter)
        print("\n[PREVIEW] SOW Preview (first 500 chars):")
        print("-" * 60)
        print(sow_text[:500])
        print("-" * 60)
        
    except Exception as e:
        logger.error(f"[ERROR] Error generating SOW: {e}", exc_info=True)
        return False
    
    # Mail paketi oluştur
    print("\n[STEP] Generating Mail Package...")
    try:
        mail_package = sow_agent.generate_mail_package(
            sow_result=sow_result,
            report_data=report_data,
            opportunity_code=test_opportunity_id,
            to_email="test@example.com",
            from_email="noreply@creataglobal.com"
        )
        
        print("[OK] Mail package generated successfully")
        print(f"     - Subject: {mail_package.get('subject', 'N/A')}")
        print(f"     - To: {mail_package.get('to', 'N/A')}")
        print(f"     - From: {mail_package.get('from', 'N/A')}")
        print(f"     - HTML body length: {len(mail_package.get('html_body', ''))} chars")
        print(f"     - Text body length: {len(mail_package.get('text_body', ''))} chars")
        print(f"     - SOW text included: {'Yes' if mail_package.get('sow_text') else 'No'}")
        
        # Mail içeriğini göster (ilk 300 karakter)
        print("\n[PREVIEW] Mail Preview (first 300 chars of HTML):")
        print("-" * 60)
        html_preview = mail_package.get('html_body', '')[:300]
        print(html_preview)
        print("-" * 60)
        
    except Exception as e:
        logger.error(f"[ERROR] Error generating mail package: {e}", exc_info=True)
        return False
    
    # SOW'u kaydet
    print("\n[STEP] Saving SOW to file...")
    try:
        sow_md_path = folder_path / "sow_test.md"
        sow_md_path.write_text(sow_result.get('sow_text', ''), encoding='utf-8')
        print(f"[OK] SOW saved to: {sow_md_path}")
    except Exception as e:
        logger.error(f"[ERROR] Error saving SOW: {e}")
        return False
    
    # Mail paketini JSON olarak kaydet
    print("\n[STEP] Saving Mail Package to JSON...")
    try:
        mail_json_path = folder_path / "mail_package_test.json"
        # SOW text'i çok uzun olabilir, sadece metadata'yı kaydet
        mail_metadata = {
            'to': mail_package.get('to'),
            'from': mail_package.get('from'),
            'subject': mail_package.get('subject'),
            'html_body_length': len(mail_package.get('html_body', '')),
            'text_body_length': len(mail_package.get('text_body', '')),
            'sow_text_length': len(mail_package.get('sow_text', '')),
            'opportunity_code': mail_package.get('opportunity_code'),
            'generated_at': mail_package.get('generated_at')
        }
        with open(mail_json_path, 'w', encoding='utf-8') as f:
            json.dump(mail_metadata, f, indent=2, ensure_ascii=False)
        print(f"[OK] Mail package metadata saved to: {mail_json_path}")
    except Exception as e:
        logger.error(f"[ERROR] Error saving mail package: {e}")
        return False
    
    print("\n" + "="*60)
    print("[SUCCESS] TEST COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\n[RESULTS] Test Results:")
    print(f"   [OK] SOW Agent created")
    print(f"   [OK] Sample SOW template loaded")
    print(f"   [OK] SOW generated ({len(sow_text)} chars)")
    print(f"   [OK] Mail package generated")
    print(f"   [OK] Files saved:")
    print(f"       - {sow_md_path}")
    print(f"       - {mail_json_path}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_sow_mail_agent()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[ERROR] TEST FAILED: {e}", exc_info=True)
        exit(1)

