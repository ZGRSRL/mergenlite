import requests
import json

response = requests.get("http://localhost:8001/api/pipeline/results/10")
result = response.json()

print(f"Status: {result.get('status')}")
print(f"Analysis Type: {result.get('analysis_type')}")

result_json = result.get('result_json', {})
print(f"\n=== Result JSON Keys ===")
print(list(result_json.keys()))

# Document analysis
doc_analysis = result_json.get('document_analysis', {})
print(f"\n=== Document Analysis ===")
print(f"Documents analyzed: {doc_analysis.get('documents_analyzed', 0)}")
print(f"Total text length: {doc_analysis.get('total_text_length', 0)}")
print(f"Total word count: {doc_analysis.get('total_word_count', 0)}")

# SOW analysis
sow_analysis = result_json.get('sow_analysis')
if sow_analysis:
    print(f"\n✅ SOW Analysis PRESENT!")
    print(f"SOW Analysis keys: {list(sow_analysis.keys())}")
    
    # Event details
    event_details = sow_analysis.get('EventDetails', {})
    if event_details:
        print(f"\n Event Name: {event_details.get('EventName')}")
        print(f" Location: {event_details.get('Location')}")
        print(f" Dates: {event_details.get('Dates')}")
else:
    print(f"\n❌ SOW Analysis MISSING")

# Attachments
attachments = result_json.get('attachments', [])
print(f"\n=== Attachments ({len(attachments)}) ===")
for att in attachments:
    print(f"  - {att.get('name')}: downloaded={att.get('downloaded')}, size={att.get('size_bytes')}")

# Get logs
logs_response = requests.get("http://localhost:8001/api/pipeline/results/10/logs?limit=100")
logs = logs_response.json()

# Find SOW/AutoGen logs
sow_logs = [log for log in logs if 'sow' in log.get('message', '').lower() or 'autogen' in log.get('message', '').lower()]
print(f"\n=== SOW/AutoGen Logs ({len(sow_logs)}) ===")
for log in sow_logs:
    print(f"[{log.get('level')}] {log.get('message')[:200]}")
