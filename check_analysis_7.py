import requests
import json

def check_analysis_details():
    analysis_id = 7
    
    try:
        # Get analysis result
        response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}")
        result = response.json()
        
        print(f"=== Analysis {analysis_id} Details ===")
        print(f"Status: {result.get('status')}")
        print(f"Type: {result.get('analysis_type')}")
        print(f"Created: {result.get('created_at')}")
        print(f"Completed: {result.get('completed_at')}")
        
        # Get result JSON
        result_json = result.get('result_json', {})
        if result_json:
            print(f"\n=== Analysis Results ===")
            print(f"Attachments: {result_json.get('attachment_count', 0)}")
            
            doc_analysis = result_json.get('document_analysis', {})
            print(f"Documents analyzed: {doc_analysis.get('documents_analyzed', 0)}")
            print(f"Total text length: {doc_analysis.get('total_text_length', 0)}")
            print(f"Total word count: {doc_analysis.get('total_word_count', 0)}")
            
            # Check SOW analysis
            sow = result_json.get('sow_analysis')
            if sow:
                print(f"\n✅ SOW Analysis PRESENT")
                print(f"SOW keys: {list(sow.keys())[:10]}")
            else:
                print(f"\n❌ SOW Analysis MISSING")
            
            # Check attachments
            attachments = result_json.get('attachments', [])
            print(f"\n=== Attachments ({len(attachments)}) ===")
            for att in attachments:
                print(f"  - {att.get('name')}: downloaded={att.get('downloaded')}, local_path={att.get('local_path')}")
        
        # Get all logs
        log_response = requests.get(f"http://localhost:8001/api/pipeline/results/{analysis_id}/logs?limit=100")
        logs = log_response.json()
        
        print(f"\n=== All Logs ({len(logs)}) ===")
        for log in logs:
            print(f"[{log.get('level')}] ({log.get('step')}): {log.get('message')[:200]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_analysis_details()
