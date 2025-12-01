#!/usr/bin/env python3
"""Test Settings object for email configuration."""
import sys
sys.path.insert(0, '/app')

from app.config import settings

print("=" * 70)
print("🔧 SETTINGS OBJESİ KONTROLÜ")
print("=" * 70)
print()

print("Settings attributes:")
attrs = [
    'smtp_host',
    'smtp_port',
    'smtp_username',
    'smtp_password',
    'smtp_use_tls',
    'smtp_from_email',
    'pipeline_notification_email'
]

for attr in attrs:
    try:
        value = getattr(settings, attr, None)
        if 'password' in attr.lower() and value:
            value = "***"
        print(f"   {attr}: {value}")
    except AttributeError as e:
        print(f"   {attr}: ❌ NOT FOUND - {e}")

print()
print("Email check condition:")
print(f"   pipeline_notification_email: {getattr(settings, 'pipeline_notification_email', None)}")
print(f"   smtp_host: {getattr(settings, 'smtp_host', None)}")
print(f"   smtp_username: {getattr(settings, 'smtp_username', None)}")

has_all = (
    getattr(settings, 'pipeline_notification_email', None) and
    getattr(settings, 'smtp_host', None) and
    getattr(settings, 'smtp_username', None)
)
print(f"\n   Email can be sent: {has_all}")

print()
print("=" * 70)

