#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test SMTP email sending."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.services.mail_service import build_mail_package, send_email_via_smtp
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=" * 70)
print("SMTP EMAIL TEST")
print("=" * 70)
print()

# Check SMTP settings
print("SMTP Configuration:")
print(f"  Host: {settings.smtp_host}")
print(f"  Port: {settings.smtp_port}")
print(f"  Username: {settings.smtp_username}")
print(f"  Use TLS: {settings.smtp_use_tls}")
print(f"  Notification Email: {settings.pipeline_notification_email}")
print()

if not (settings.smtp_host and settings.smtp_username and settings.smtp_password):
    print("ERROR: SMTP settings are not configured!")
    sys.exit(1)

# Build test mail package
print("Building test mail package...")
mail_package = build_mail_package(
    opportunity_code="TEST-001",
    folder_path="/tmp",
    to_email=settings.pipeline_notification_email,
    from_email=settings.smtp_from_email or settings.smtp_username,
    analysis_result_json={
        "summary": "Test email from MergenLite",
        "fit_assessment": {
            "overall_score": 85,
            "summary": "This is a test email to verify SMTP configuration."
        }
    }
)

print(f"Mail package created:")
print(f"  To: {mail_package['to']}")
print(f"  From: {mail_package['from']}")
print(f"  Subject: {mail_package['subject']}")
print(f"  Attachments: {len(mail_package.get('attachments', []))}")
print()

# SMTP config
smtp_config = {
    'host': settings.smtp_host,
    'port': settings.smtp_port,
    'username': settings.smtp_username,
    'password': settings.smtp_password,
    'use_tls': settings.smtp_use_tls,
}

# Send email
print("Attempting to send email via SMTP...")
print()
try:
    result = send_email_via_smtp(mail_package, smtp_config)
    if result:
        print("=" * 70)
        print("SUCCESS: Email sent successfully!")
        print("=" * 70)
    else:
        print("=" * 70)
        print("FAILED: Email send returned False")
        print("=" * 70)
except Exception as e:
    print("=" * 70)
    print(f"EXCEPTION: {e}")
    print("=" * 70)
    import traceback
    traceback.print_exc()

