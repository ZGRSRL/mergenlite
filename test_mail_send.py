#!/usr/bin/env python3
"""Test email sending functionality"""
import sys
sys.path.insert(0, '/app')

import requests
from pathlib import Path
from app.config import settings
from app.services.mail_service import build_mail_package, send_email_via_smtp

print("=== Mail Gonderim Testi ===\n")

# Check settings
print("1. Mail Ayarlari:")
print(f"   SMTP Host: {settings.smtp_host}")
print(f"   SMTP Port: {settings.smtp_port}")
print(f"   SMTP Username: {settings.smtp_username[:10]}..." if settings.smtp_username else "   SMTP Username: NOT SET")
print(f"   SMTP From: {settings.smtp_from_email}")
print(f"   SMTP To: {settings.pipeline_notification_email}")

if not settings.pipeline_notification_email:
    print("\n[X] Pipeline notification email not configured!")
    sys.exit(1)

# Get latest successful SOW analysis
print("\n2. Son basarili SOW analizi bulunuyor...")
response = requests.get('http://localhost:8000/api/pipeline/opportunity/3/results?limit=10')
results = response.json()

sow_result = None
for r in results:
    if r.get('analysis_type') == 'sow_draft' and r.get('status') == 'completed':
        sow_result = r
        break

if not sow_result:
    print("   [X] Basarili SOW analizi bulunamadi")
    print("   Test mail gonderiliyor (ornek verilerle)...")
    
    # Create test mail package
    test_analysis = {
        "opportunity": {
            "id": 3,
            "notice_id": "97c450b7d3554a738d0d4de07ffa0e0a",
            "title": "2026 FIFA World Cup Lodging - Hotel Room Block",
            "agency": "HOMELAND SECURITY, DEPARTMENT OF"
        },
        "analysis_type": "sow_draft",
        "document_analysis": {
            "documents_analyzed": 3,
            "total_word_count": 2193
        },
        "sow_analysis": {
            "EventDetails": {
                "EventName": "2026 FIFA World Cup Lodging",
                "Location": {"City": "Houston", "State": "TX"}
            }
        }
    }
    
    mail_package = build_mail_package(
        opportunity_code="97c450b7d3554a738d0d4de07ffa0e0a",
        folder_path="/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/outputs",
        to_email=settings.pipeline_notification_email,
        from_email=settings.smtp_from_email,
        analysis_result_json=test_analysis,
    )
    
    print(f"\n3. Mail paketi olusturuldu:")
    print(f"   Subject: {mail_package.get('subject', 'N/A')}")
    print(f"   To: {mail_package.get('to') or mail_package.get('to_email', 'N/A')}")
    print(f"   From: {mail_package.get('from', 'N/A')}")
    print(f"   Attachments: {len(mail_package.get('attachments', []))}")
    
    print("\n4. Mail gonderiliyor...")
    try:
        # Create SMTP config from settings
        smtp_config = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls,
        }
        success = send_email_via_smtp(mail_package, smtp_config)
        if success:
            print("   [OK] Mail basariyla gonderildi!")
        else:
            print("   [X] Mail gonderilemedi")
    except Exception as e:
        print(f"   [ERROR] Mail gonderim hatasi: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   [OK] SOW analizi bulundu (ID: {sow_result['id']})")
    print(f"   PDF: {sow_result.get('pdf_path', 'N/A')}")
    print(f"   JSON: {sow_result.get('json_path', 'N/A')}")
    
    # Get analysis data
    result_json = sow_result.get('result_json')
    if isinstance(result_json, str):
        import json
        analysis_data = json.loads(result_json)
    else:
        analysis_data = result_json
    
    # Build mail package
    notice_id = sow_result.get('opportunity_id', 3)
    output_dir = Path("/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/outputs")
    
    mail_package = build_mail_package(
        opportunity_code="97c450b7d3554a738d0d4de07ffa0e0a",
        folder_path=str(output_dir),
        to_email=settings.pipeline_notification_email,
        from_email=settings.smtp_from_email,
        analysis_result_json=analysis_data,
    )
    
    # Add PDF and JSON if they exist
    attachments = mail_package.get('attachments', [])
    if sow_result.get('pdf_path') and Path(sow_result['pdf_path']).exists():
        attachments.append({
            'path': sow_result['pdf_path'],
            'filename': f"sow_analysis_{sow_result['id']}.pdf",
            'mime_type': 'application/pdf'
        })
    if sow_result.get('json_path') and Path(sow_result['json_path']).exists():
        attachments.append({
            'path': sow_result['json_path'],
            'filename': f"sow_analysis_{sow_result['id']}.json",
            'mime_type': 'application/json'
        })
    mail_package['attachments'] = attachments
    
    print(f"\n3. Mail paketi olusturuldu:")
    print(f"   Subject: {mail_package.get('subject', 'N/A')}")
    print(f"   To: {mail_package.get('to_email')}")
    print(f"   Attachments: {len(attachments)}")
    
    print("\n4. Mail gonderiliyor...")
    try:
        # Create SMTP config from settings
        smtp_config = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls,
        }
        success = send_email_via_smtp(mail_package, smtp_config)
        if success:
            print("   [OK] Mail basariyla gonderildi!")
            print(f"   Mail alici: {settings.pipeline_notification_email}")
        else:
            print("   [X] Mail gonderilemedi")
    except Exception as e:
        print(f"   [ERROR] Mail gonderim hatasi: {e}")
        import traceback
        traceback.print_exc()

print("\n=== Test Tamamlandi ===")

