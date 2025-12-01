import requests
import time

# Test with opportunity 275 (has 3 attachments)
body = {
    "opportunity_id": 275,
    "analysis_type": "sow_draft",
    "pipeline_version": "v1"
}

print("=== 🚀 Testing Email Logging System ===")
print("Starting analysis for Opportunity 275...")

response = requests.post("http://localhost:8001/api/pipeline/run", json=body)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    analysis_id = result.get('analysis_result_id')
    print(f"✅ Analysis ID: {analysis_id} started\n")
    
    # Wait for completion
    print("Waiting for completion (this may take 1-2 minutes)...")
    for i in range(24):  # 24 * 5s = 2 minutes
        time.sleep(5)
        status_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}")
        status_data = status_response.json()
        status = status_data.get('status')
        
        if i % 4 == 0:  # Print every 20 seconds
            print(f"[{(i+1)*5}s] Status: {status}")
        
        if status in ['completed', 'failed']:
            print(f"\n=== Analysis {status.upper()} ===\n")
            
            # Check email logs in analysis logs
            logs_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}/logs?limit=100")
            logs = logs_response.json()
            
            email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
            print(f"📧 Email Logs from Analysis:")
            for log in email_logs:
                print(f"  [{log.get('level')}] {log.get('message')}")
            
            # NOW THE IMPORTANT PART: Check email_log table
            print(f"\n📊 Checking email_log database table...")
            opp_id = 275
            email_logs_response = requests.get(f"http://localhost:8001/api/opportunities/{opp_id}/emails")
            
            if email_logs_response.status_code == 200:
                db_emails = email_logs_response.json()
                print(f"\n✅ Total emails in database for Opp {opp_id}: {len(db_emails)}")
                
                if db_emails:
                    latest = db_emails[0]
                    print(f"\n📬 Latest Email Record:")
                    print(f"  ID: {latest.get('id')}")
                    print(f"  Direction: {latest.get('direction')}")
                    print(f"  Subject: {latest.get('subject')}")
                    print(f"  From: {latest.get('from_address')}")
                    print(f"  To: {latest.get('to_address')}")
                    print(f"  Created: {latest.get('created_at')}")
                    print(f"  Summary: {latest.get('parsed_summary', '')[:100]}...")
                else:
                    print("  ⚠️ No emails logged yet")
            else:
                print(f"  ❌ Failed to fetch emails: {email_logs_response.status_code}")
            
            break
    else:
        print("\n⏱️ Timeout - analysis still running")
