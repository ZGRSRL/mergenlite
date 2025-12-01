"""
Search SAM.gov API directly for opportunities by awardee name or keyword
"""
import os
import sys
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load API key from .env file
try:
    from dotenv import load_dotenv
    # Try multiple .env locations
    env_paths = [
        'mergen/.env',
        os.path.join('mergen', '.env'),
        '.env',
        '../.env',
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), 'mergen', '.env')
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            env_loaded = True
            break
    
    if not env_loaded:
        load_dotenv(override=True)  # Try current directory
except ImportError:
    pass  # python-dotenv not installed, continue with environment variables

SAM_API_KEY = os.getenv('SAM_API_KEY') or os.environ.get('SAM_API_KEY', '')
if not SAM_API_KEY:
    print("[ERROR] SAM_API_KEY not found")
    print("Please set it in .env file or environment variable:")
    print("  - Create/update .env file with: SAM_API_KEY=your-key")
    print("  - Or set environment variable: $env:SAM_API_KEY='your-key' (PowerShell)")
    sys.exit(1)

BASE_URL = "https://api.sam.gov/prod/opportunities/v2/search"

def search_sam_by_keyword(keyword: str, days_back: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """Search SAM.gov API by keyword (searches in title, description, etc.)"""
    
    headers = {
        "X-API-KEY": SAM_API_KEY,
        "Accept": "application/json"
    }
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    params = {
        "limit": min(limit, 1000),
        "offset": 0,
        "postedFrom": start_date.strftime("%m/%d/%Y"),
        "postedTo": end_date.strftime("%m/%d/%Y"),
        "keyword": keyword,
        "keywordRadio": "ALL",  # Search in all fields
        "sort": "-modifiedDate"
    }
    
    results = []
    
    try:
        print(f"[API] Searching SAM.gov for keyword: '{keyword}'")
        print(f"[API] Date range: {params['postedFrom']} to {params['postedTo']}")
        
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        opportunities = data.get("opportunitiesData", []) or data.get("data", [])
        total = data.get("totalRecords", len(opportunities))
        
        print(f"[API] Found {len(opportunities)} opportunities (total: {total})")
        
        for opp in opportunities:
            # Extract awardee information
            raw_data = opp
            awardee = None
            if isinstance(raw_data, dict):
                awardee = (
                    raw_data.get('awardee') or
                    raw_data.get('awardeeName') or
                    raw_data.get('contractorName') or
                    raw_data.get('vendorName') or
                    raw_data.get('awardeeNameText') or
                    raw_data.get('contractor') or
                    None
                )
            
            result = {
                'opportunity_id': opp.get('opportunityId', ''),
                'notice_id': opp.get('noticeId', ''),
                'title': opp.get('title', 'N/A'),
                'agency': opp.get('fullParentPathName', opp.get('organization', 'N/A')),
                'notice_type': opp.get('noticeType', ''),
                'posted_date': opp.get('postedDate', ''),
                'awardee': awardee,
                'sam_gov_link': opp.get('uiLink', f"https://sam.gov/opp/{opp.get('opportunityId', '')}/view"),
                'raw_data_sample': {k: v for k, v in opp.items() if k in ['awardee', 'awardeeName', 'contractorName', 'vendorName', 'title', 'noticeId', 'opportunityId']}
            }
            results.append(result)
        
        return results
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("[ERROR] Rate limit exceeded. Please wait and try again.")
        elif e.response.status_code == 401:
            print("[ERROR] Invalid API key. Check your SAM_API_KEY.")
        else:
            print(f"[ERROR] HTTP error: {e.response.status_code} - {e.response.text[:200]}")
        return []
    except Exception as e:
        print(f"[ERROR] API search error: {e}")
        import traceback
        traceback.print_exc()
        return []

def search_by_notice_id(notice_id: str, days_back: int = 365) -> Optional[Dict[str, Any]]:
    """Search for a specific notice by notice ID using noticedesc endpoint"""
    
    headers = {
        "X-API-KEY": SAM_API_KEY,
        "Accept": "application/json"
    }
    
    # Use noticedesc endpoint (doesn't require date ranges)
    noticedesc_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc"
    
    # Try different parameter names
    param_candidates = [
        {'noticeId': notice_id},
        {'solicitationNumber': notice_id}
    ]
    
    # If it looks like an opportunity ID (32 hex chars), try that too
    import re
    if re.fullmatch(r"[0-9a-fA-F]{32}", notice_id):
        param_candidates.append({'opportunityId': notice_id})
        param_candidates.append({'oppId': notice_id})
    
    try:
        print(f"[API] Searching for notice ID: {notice_id}")
        
        data = None
        notice_data = None
        last_error = None
        
        for params in param_candidates:
            try:
                response = requests.get(noticedesc_url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                d = response.json()
                if 'noticeData' in d and d['noticeData']:
                    data = d
                    notice_data = d['noticeData'][0]
                    print(f"[API] Found notice with params: {params}")
                    break
                else:
                    last_error = f"Empty noticeData with params {params}"
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    last_error = f"404 Not Found with params {params}"
                    continue
                else:
                    last_error = f"HTTP {e.response.status_code} with params {params}"
                    continue
            except Exception as ie:
                last_error = str(ie)
                continue
        
        if notice_data is None:
            print(f"[NOT FOUND] Notice ID {notice_id} not found. Last error: {last_error}")
            return None
        
        # Extract awardee information from notice data
        raw_data = notice_data
        awardee = None
        if isinstance(raw_data, dict):
            awardee = (
                raw_data.get('awardee') or
                raw_data.get('awardeeName') or
                raw_data.get('contractorName') or
                raw_data.get('vendorName') or
                raw_data.get('awardeeNameText') or
                raw_data.get('contractor') or
                None
            )
        
        return {
            'opportunity_id': notice_data.get('opportunityId', ''),
            'notice_id': notice_data.get('noticeId', notice_id),
            'title': notice_data.get('title', 'N/A'),
            'agency': notice_data.get('fullParentPathName', notice_data.get('organization', 'N/A')),
            'notice_type': notice_data.get('noticeType', notice_data.get('typeOfNotice', '')),
            'posted_date': notice_data.get('postedDate', ''),
            'awardee': awardee,
            'sam_gov_link': notice_data.get('uiLink', f"https://sam.gov/opp/{notice_data.get('opportunityId', notice_id)}/view"),
            'raw_data_sample': {k: v for k, v in notice_data.items() if k in ['awardee', 'awardeeName', 'contractorName', 'vendorName', 'title', 'noticeId', 'opportunityId', 'description', 'typeOfNotice', 'noticeType'] and v}
        }
        
    except Exception as e:
        print(f"[ERROR] API search error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Search SAM.gov API for opportunities')
    parser.add_argument('search_term', nargs='?', default='nmaiol', help='Search term (default: nmaiol)')
    parser.add_argument('--notice-id', help='Search by specific notice ID')
    parser.add_argument('--days-back', type=int, default=30, help='Days to look back (default: 30)')
    parser.add_argument('--limit', type=int, default=50, help='Maximum results (default: 50)')
    
    args = parser.parse_args()
    
    if args.notice_id:
        result = search_by_notice_id(args.notice_id, days_back=args.days_back)
        if result:
            print(f"\n[FOUND] Notice found:")
            print(f"   Notice ID: {result['notice_id']}")
            print(f"   Opportunity ID: {result['opportunity_id']}")
            print(f"   Title: {result['title']}")
            print(f"   Agency: {result['agency']}")
            print(f"   Notice Type: {result['notice_type']}")
            print(f"   Awardee: {result['awardee'] or 'N/A'}")
            print(f"   Posted Date: {result['posted_date']}")
            print(f"   SAM.gov Link: {result['sam_gov_link']}")
            if result.get('raw_data_sample'):
                print(f"\n   Raw Data Sample:")
                for k, v in result['raw_data_sample'].items():
                    if v:
                        print(f"      {k}: {v}")
        else:
            print(f"[NOT FOUND] Notice ID {args.notice_id} not found")
    else:
        results = search_sam_by_keyword(args.search_term, days_back=args.days_back, limit=args.limit)
        
        if results:
            print(f"\n[FOUND] Found {len(results)} result(s):\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. Notice ID: {result['notice_id']}")
                print(f"   Title: {result['title']}")
                print(f"   Agency: {result['agency']}")
                print(f"   Notice Type: {result['notice_type']}")
                print(f"   Awardee: {result['awardee'] or 'N/A'}")
                print(f"   Posted Date: {result['posted_date']}")
                print(f"   SAM.gov Link: {result['sam_gov_link']}")
                if result.get('raw_data_sample') and any(v for v in result['raw_data_sample'].values()):
                    print(f"   Raw Data: {', '.join(f'{k}={v}' for k, v in result['raw_data_sample'].items() if v)}")
                print()
        else:
            print(f"[NOT FOUND] No results found for '{args.search_term}'")
            print("\n[TIPS]")
            print("   - Try different spellings or partial matches")
            print("   - Check if the notice exists on SAM.gov")
            print("   - Search by notice ID: python search_sam_api.py --notice-id W50S8R26Q0003B")

