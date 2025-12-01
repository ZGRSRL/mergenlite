#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check email logs for analysis."""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 414

print(f"Checking logs for Analysis ID: {ANALYSIS_ID}")
print("=" * 70)

resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/logs?limit=100")
if resp.status_code == 200:
    logs = resp.json()
    print(f"Total logs: {len(logs)}")
    print()
    
    # Email-related logs
    email_logs = [l for l in logs if 'email' in l.get('message', '').lower() or 'smtp' in l.get('message', '').lower()]
    print(f"Email/SMTP related logs: {len(email_logs)}")
    print()
    
    for log in email_logs:
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        step = log.get('step', '')
        print(f"[{level}] [{step}] {message}")
    
    # Check for errors
    error_logs = [l for l in logs if l.get('level') == 'ERROR' or 'failed' in l.get('message', '').lower()]
    if error_logs:
        print()
        print("=" * 70)
        print("ERROR LOGS:")
        print("=" * 70)
        for log in error_logs:
            level = log.get('level', 'ERROR')
            message = log.get('message', '')
            step = log.get('step', '')
            print(f"[{level}] [{step}] {message}")
else:
    print(f"Failed to get logs: {resp.status_code}")

