"""Check email configuration and logs"""
import requests
import json

API_BASE = "http://localhost:8000"
SOW_ANALYSIS_ID = 321

print("=" * 70)
print("CHECKING EMAIL CONFIGURATION AND LOGS")
print("=" * 70)

# Get all logs
resp = requests.get(f"{API_BASE}/api/pipeline/results/{SOW_ANALYSIS_ID}/logs?limit=100")
if resp.status_code == 200:
    logs = resp.json()
    
    # Filter email-related logs
    email_logs = []
    config_logs = []
    
    for log in logs:
        message = log.get('message', '').lower()
        step = log.get('step', '')
        if 'email' in message or step == 'email':
            email_logs.append(log)
        if 'smtp' in message or 'notification' in message or 'configured' in message:
            config_logs.append(log)
    
    print("\nEmail Configuration Logs:")
    if config_logs:
        for log in config_logs:
            print(f"  [{log.get('level')}] {log.get('message')}")
    else:
        print("  No configuration logs found")
    
    print("\nEmail Sending Logs:")
    if email_logs:
        for log in email_logs:
            print(f"  [{log.get('level')}] Step: {log.get('step')}, Message: {log.get('message')}")
    else:
        print("  No email sending logs found")
        print("  This might mean:")
        print("    - SMTP settings are not configured")
        print("    - Email sending was skipped")
    
    print("\n" + "=" * 70)
    print("All Recent Logs (last 20):")
    print("=" * 70)
    for log in logs[-20:]:
        level = log.get('level', 'INFO')
        step = log.get('step', '')
        message = log.get('message', '')[:100]
        print(f"[{level}] {step}: {message}")
