"""Check full analysis results including email status"""
import requests
import json

API_BASE = "http://localhost:8000"
SOW_ANALYSIS_ID = 321
HOTEL_ANALYSIS_ID = 324

print("=" * 70)
print("SOW ANALYSIS RESULTS")
print("=" * 70)

resp = requests.get(f"{API_BASE}/api/pipeline/results/{SOW_ANALYSIS_ID}")
if resp.status_code == 200:
    result = resp.json()
    print(f"Status: {result.get('status')}")
    print(f"PDF: {result.get('pdf_path', 'N/A')}")
    print(f"JSON: {result.get('json_path', 'N/A')}")
    
    result_json = result.get('result_json')
    if result_json:
        if isinstance(result_json, str):
            result_json = json.loads(result_json)
        
        sow_analysis = result_json.get('sow_analysis')
        if sow_analysis:
            locations = sow_analysis.get('Locations', []) or sow_analysis.get('locations', [])
            print(f"\nSOW Analysis Summary:")
            print(f"  Locations: {len(locations)}")
            if locations:
                print("  Cities:")
                for i, loc in enumerate(locations[:10], 1):
                    city = loc.get('city', 'N/A')
                    stadium = loc.get('stadium', 'N/A')
                    start_date = loc.get('start_date', 'N/A')
                    print(f"    {i}. {city} - {stadium} - {start_date}")

print("\n" + "=" * 70)
print("HOTEL MATCH ANALYSIS STATUS")
print("=" * 70)

resp = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}")
if resp.status_code == 200:
    result = resp.json()
    status = result.get('status')
    print(f"Status: {status}")
    
    if status == 'completed':
        print(f"PDF: {result.get('pdf_path', 'N/A')}")
        print(f"JSON: {result.get('json_path', 'N/A')}")
        
        result_json = result.get('result_json')
        if result_json:
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            
            hotels = result_json.get('hotels', [])
            print(f"\nHotel Match Results:")
            print(f"  Hotels found: {len(hotels)}")
            if hotels:
                for i, hotel in enumerate(hotels[:5], 1):
                    name = hotel.get('name', 'N/A')
                    score = hotel.get('score', 'N/A')
                    price = hotel.get('total_price', 'N/A')
                    print(f"    {i}. {name} - Score: {score}, Price: ${price}")
    else:
        print(f"Still {status}...")
else:
    print(f"Hotel match analysis not found or error: {resp.status_code}")

print("\n" + "=" * 70)
print("EMAIL STATUS")
print("=" * 70)
print("Checking if email was sent...")

# Check logs for email
resp = requests.get(f"{API_BASE}/api/pipeline/results/{SOW_ANALYSIS_ID}/logs?limit=50")
if resp.status_code == 200:
    logs = resp.json()
    email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
    if email_logs:
        print("Email-related logs:")
        for log in email_logs:
            print(f"  [{log.get('level')}] {log.get('message')}")
    else:
        print("  No email logs found yet")

# Check hotel match email logs too
if HOTEL_ANALYSIS_ID:
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{HOTEL_ANALYSIS_ID}/logs?limit=50")
    if resp.status_code == 200:
        logs = resp.json()
        email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
        if email_logs:
            print("\nHotel Match email logs:")
            for log in email_logs:
                print(f"  [{log.get('level')}] {log.get('message')}")

