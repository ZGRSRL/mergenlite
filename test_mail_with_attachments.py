#!/usr/bin/env python3
"""Test email sending with attachments"""
import sys
sys.path.insert(0, '/app')

import requests
from pathlib import Path
from app.config import settings
from app.services.mail_service import build_mail_package, send_email_via_smtp

print("=== Mail Gonderim Testi (Eklerle) ===\n")

# Check settings
print("1. Mail Ayarlari:")
print(f"   SMTP Host: {settings.smtp_host}")
print(f"   SMTP From: {settings.smtp_from_email}")
print(f"   SMTP To: {settings.pipeline_notification_email}")

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
    sys.exit(1)

print(f"   [OK] SOW analizi bulundu (ID: {sow_result['id']})")
print(f"   PDF: {sow_result.get('pdf_path', 'N/A')}")
print(f"   JSON: {sow_result.get('json_path', 'N/A')}")

# Check if files exist
pdf_path = Path(sow_result.get('pdf_path', ''))
json_path = Path(sow_result.get('json_path', ''))

print(f"\n3. Dosya Kontrolu:")
print(f"   PDF exists: {pdf_path.exists() if pdf_path else False}")
if pdf_path and pdf_path.exists():
    print(f"   PDF size: {pdf_path.stat().st_size} bytes")
print(f"   JSON exists: {json_path.exists() if json_path else False}")
if json_path and json_path.exists():
    print(f"   JSON size: {json_path.stat().st_size} bytes")

# Get analysis data
result_json = sow_result.get('result_json')
if isinstance(result_json, str):
    import json
    analysis_data = json.loads(result_json)
else:
    analysis_data = result_json

# Build mail package
notice_id = "97c450b7d3554a738d0d4de07ffa0e0a"
output_dir = Path("/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/outputs")

mail_package = build_mail_package(
    opportunity_code=notice_id,
    folder_path=str(output_dir),
    to_email=settings.pipeline_notification_email,
    from_email=settings.smtp_from_email,
    analysis_result_json=analysis_data,
)

# Add PDF and JSON if they exist
attachments = mail_package.get('attachments', [])
if pdf_path and pdf_path.exists():
    attachments.append({
        'path': str(pdf_path),
        'filename': f"sow_analysis_{sow_result['id']}.pdf",
        'mime_type': 'application/pdf'
    })
    print(f"\n4. PDF eklendi: {pdf_path.name}")
if json_path and json_path.exists():
    attachments.append({
        'path': str(json_path),
        'filename': f"sow_analysis_{sow_result['id']}.json",
        'mime_type': 'application/json'
    })
    print(f"   JSON eklendi: {json_path.name}")

mail_package['attachments'] = attachments

print(f"\n5. Mail paketi:")
print(f"   Subject: {mail_package.get('subject', 'N/A')}")
print(f"   To: {mail_package.get('to', 'N/A')}")
print(f"   From: {mail_package.get('from', 'N/A')}")
print(f"   Attachments: {len(attachments)}")

if len(attachments) == 0:
    print("   [UYARI] Ekler bulunamadi!")
else:
    for i, att in enumerate(attachments, 1):
        att_path = Path(att['path'])
        if att_path.exists():
            print(f"   Ek {i}: {att['filename']} ({att_path.stat().st_size} bytes) [OK]")
        else:
            print(f"   Ek {i}: {att['filename']} [X] Dosya bulunamadi: {att_path}")

print("\n6. Mail gonderiliyor...")
try:
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
        print(f"   Ekler: {len(attachments)} dosya")
    else:
        print("   [X] Mail gonderilemedi")
except Exception as e:
    print(f"   [ERROR] Mail gonderim hatasi: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Tamamlandi ===")

