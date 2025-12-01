"""Check agent response structure"""
import requests
import json

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 339

# Get agent outputs
resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/agent-outputs")
if resp.status_code == 200:
    outputs = resp.json()
    agent_outputs = outputs.get('agent_outputs', [])
    
    if agent_outputs:
        # Get last agent run
        last_run = agent_outputs[0]
        messages = last_run.get('messages', [])
        
        print(f"Total messages: {len(messages)}")
        
        # Show all messages
        print(f"\nAll messages:")
        for i, msg in enumerate(messages[-5:], 1):
            content = msg.get('content', '')
            print(f"\n--- Message {i} ---")
            print(f"Type: {msg.get('message_type')}")
            print(f"Content length: {len(content)}")
            print(f"Content preview (first 500 chars):")
            print(content[:500])
            
            # Try to find JSON in content
            if '{' in content:
                # Try to extract JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                if end > start:
                    json_str = content[start:end]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            print(f"\n✅ Found JSON object!")
                            print(f"Keys: {list(parsed.keys())}")
                            if 'hotels' in parsed:
                                hotels = parsed['hotels']
                                print(f"Hotels count: {len(hotels) if isinstance(hotels, list) else 'N/A'}")
                                if isinstance(hotels, list) and hotels:
                                    print(f"First hotel keys: {list(hotels[0].keys()) if isinstance(hotels[0], dict) else 'N/A'}")
                                    print(f"First hotel name: {hotels[0].get('name') if isinstance(hotels[0], dict) else 'N/A'}")
                    except:
                        pass

