#!/usr/bin/env python3
"""Check logs for hotel match 259 to see why no hotels were found."""
import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("📋 HOTEL MATCH 259 - LOGLAR")
print("=" * 70)
print()

# Get logs
logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/259/logs?limit=50")
if logs_resp.status_code == 200:
    logs = logs_resp.json()
    print(f"Toplam Log: {len(logs)}\n")
    
    for log in logs[-20:]:  # Son 20 log
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        step = log.get('step', '')
        
        # Color coding
        if level == 'ERROR':
            prefix = "❌"
        elif level == 'WARNING':
            prefix = "⚠️"
        elif 'hotel' in message.lower() or 'amadeus' in message.lower():
            prefix = "🏨"
        elif 'city' in message.lower() or 'location' in message.lower():
            prefix = "🏙️"
        else:
            prefix = "ℹ️"
        
        print(f"{prefix} [{level}] {step}: {message[:150]}")

print()
print("=" * 70)

