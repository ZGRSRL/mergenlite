
import os
import sys
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

# Load env
try:
    from dotenv import load_dotenv
    # Try loading from current directory explicitly
    env_path = Path(os.getcwd()) / ".env"
    print(f"📂 Loading .env from: {env_path}")
    load_dotenv(env_path, override=True)
except Exception as e:
    print(f"⚠️ Error loading .env: {e}")
    pass

def debug_sam_search():
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        print("❌ SAM_API_KEY not found!")
        return

    print(f"🔑 Using API Key: {api_key[:5]}...")

    # Params
    naics = "721110"
    days_back = 60
    
    # Date format: MM/DD/YYYY
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    params = {
        "api_key": api_key,
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "limit": 10,
        "naicsCode": naics,
        "active": "true" # Only active opportunities
    }
    
    print(f"🔍 Searching SAM.gov for NAICS {naics} from {params['postedFrom']} to {params['postedTo']}...")
    
    url = "https://api.sam.gov/opportunities/v2/search"
    
    try:
        response = requests.get(url, params=params)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return

        data = response.json()
        
        # Check structure
        if "opportunities" in data:
            opps = data["opportunities"]
            print(f"✅ Found {len(opps)} opportunities.")
            for opp in opps:
                print(f" - [{opp.get('solicitationNumber')}] {opp.get('title')} (Posted: {opp.get('postedDate')})")
        else:
            print("⚠️ No 'opportunities' key in response.")
            print(json.dumps(data, indent=2))
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_sam_search()
