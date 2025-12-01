#!/usr/bin/env python3
"""Test email with attachments from latest pipeline"""
import sys
sys.path.insert(0, '/app')

import requests
from pathlib import Path
from app.config import settings
from app.services.mail_service import build_mail_package, send_email_via_smtp

print("=== Mail Gonderim Testi (Eklerle) ===\n")

# Get all results
response = requests.get('http://localhost:8000/api/pipeline/opportunity/3/results?limit=20')
results = response.json()

# Find latest completed SOW
sow_result = None
for r in results:
    if r.get('analysis_type') == 'sow_draft' and r.get('status') == 'completed':
        sow_result = r
        break

if not sow_result:
    print("[X] Basarili SOW analizi bulunamadi")
    sys.exit(1)

print(f"[OK] SOW analizi bulundu (ID: {sow_result['id']})")

# Get full result
result = requests.get(f"http://localhost:8000/api/pipeline/results/{sow_result['id']}").json()

pdf_path_str = result.get('pdf_path', '')
json_path_str = result.get('json_path', '')

print(f"\nPDF Path: {pdf_path_str}")
print(f"JSON Path: {json_path_str}")

# Check files
pdf_path = Path(pdf_path_str) if pdf_path_str else None
json_path = Path(json_path_str) if json_path_str else None

# Try alternative paths
if pdf_path and not pdf_path.exists():
    alt_pdf = Path('/data') / pdf_path_str.lstrip('/')
    if alt_pdf.exists():
        pdf_path = alt_pdf
        print(f"PDF found at: {pdf_path}")

if json_path and not json_path.exists():
    alt_json = Path('/data') / json_path_str.lstrip('/')
    if alt_json.exists():
        json_path = alt_json
        print(f"JSON found at: {json_path}")

print(f"\nPDF exists: {pdf_path.exists() if pdf_path else False}")
print(f"JSON exists: {json_path.exists() if json_path else False}")

# Get analysis data
result_json = result.get('result_json')
if isinstance(result_json, str):
    import json
    analysis_data = json.loads(result_json)
else:
    analysis_data = result_json

# Build mail package
mail_package = build_mail_package(
    opportunity_code="97c450b7d3554a738d0d4de07ffa0e0a",
    folder_path="/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/outputs",
    to_email=settings.pipeline_notification_email,
    from_email=settings.smtp_from_email,
    analysis_result_json=analysis_data,
)

# Add attachments
attachments = mail_package.get('attachments', [])

if pdf_path and pdf_path.exists():
    attachments.append({
        'path': str(pdf_path),
        'filename': f"sow_analysis_{sow_result['id']}.pdf",
        'mime_type': 'application/pdf'
    })
    print(f"\n[OK] PDF eklendi: {pdf_path.name} ({pdf_path.stat().st_size} bytes)")

if json_path and json_path.exists():
    attachments.append({
        'path': str(json_path),
        'filename': f"sow_analysis_{sow_result['id']}.json",
        'mime_type': 'application/json'
    })
    print(f"[OK] JSON eklendi: {json_path.name} ({json_path.stat().st_size} bytes)")

mail_package['attachments'] = attachments

print(f"\nMail paketi:")
print(f"  Subject: {mail_package.get('subject', 'N/A')}")
print(f"  To: {mail_package.get('to', 'N/A')}")
print(f"  Attachments: {len(attachments)}")

# Send email
print("\nMail gonderiliyor...")
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
        print(f"\n[OK] Mail basariyla gonderildi!")
        print(f"  Alici: {settings.pipeline_notification_email}")
        print(f"  Ekler: {len(attachments)} dosya")
        for i, att in enumerate(attachments, 1):
            print(f"    {i}. {att['filename']}")
    else:
        print("\n[X] Mail gonderilemedi")
except Exception as e:
    print(f"\n[ERROR] Mail gonderim hatasi: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Tamamlandi ===")

