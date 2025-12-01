#!/usr/bin/env python3
"""Check email status for pipeline 177."""
import requests
import json

API_BASE = "http://localhost:8000"

# Get logs
logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/177/logs")
if logs_resp.status_code == 200:
    logs = logs_resp.json()
    print("=== Pipeline 177 Logs (Email related) ===\n")
    email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or 'mail' in log.get('message', '').lower()]
    if email_logs:
        for log in email_logs:
            print(f"[{log.get('level')}] {log.get('message')}")
            print(f"  Step: {log.get('step')}, Time: {log.get('created_at')}\n")
    else:
        print("No email-related logs found. Checking all recent logs:\n")
        for log in logs[-10:]:
            print(f"[{log.get('level')}] {log.get('message')}")
            print(f"  Step: {log.get('step')}, Time: {log.get('created_at')}\n")
else:
    print(f"Error getting logs: {logs_resp.status_code}")

# Get result status
result_resp = requests.get(f"{API_BASE}/api/pipeline/results/177")
if result_resp.status_code == 200:
    result = result_resp.json()
    print(f"\n=== Pipeline 177 Status ===")
    print(f"Status: {result.get('status')}")
    print(f"PDF Path: {result.get('pdf_path')}")
    print(f"JSON Path: {result.get('json_path')}")


"""Check email status for pipeline 177."""
import requests
import json

API_BASE = "http://localhost:8000"

# Get logs
logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/177/logs")
if logs_resp.status_code == 200:
    logs = logs_resp.json()
    print("=== Pipeline 177 Logs (Email related) ===\n")
    email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or 'mail' in log.get('message', '').lower()]
    if email_logs:
        for log in email_logs:
            print(f"[{log.get('level')}] {log.get('message')}")
            print(f"  Step: {log.get('step')}, Time: {log.get('created_at')}\n")
    else:
        print("No email-related logs found. Checking all recent logs:\n")
        for log in logs[-10:]:
            print(f"[{log.get('level')}] {log.get('message')}")
            print(f"  Step: {log.get('step')}, Time: {log.get('created_at')}\n")
else:
    print(f"Error getting logs: {logs_resp.status_code}")

# Get result status
result_resp = requests.get(f"{API_BASE}/api/pipeline/results/177")
if result_resp.status_code == 200:
    result = result_resp.json()
    print(f"\n=== Pipeline 177 Status ===")
    print(f"Status: {result.get('status')}")
    print(f"PDF Path: {result.get('pdf_path')}")
    print(f"JSON Path: {result.get('json_path')}")

