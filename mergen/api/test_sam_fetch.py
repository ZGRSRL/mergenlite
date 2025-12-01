#!/usr/bin/env python3
"""Test SAM.gov data fetching."""
import sys
sys.path.insert(0, '/app')

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("🔍 SAM.GOV VERİ ÇEKME KONTROLÜ")
print("=" * 70)
print()

# 1. Check SAM_API_KEY
print("1️⃣ SAM_API_KEY Kontrolü:")
sam_key = os.getenv('SAM_API_KEY', '').strip()
if sam_key:
    print(f"   ✅ SAM_API_KEY set (length: {len(sam_key)})")
    print(f"   Preview: {sam_key[:10]}...{sam_key[-5:]}")
else:
    print("   ❌ SAM_API_KEY not found!")
    print("   💡 Set SAM_API_KEY in environment or mergen/.env file")

# 2. Check SAMIntegration import
print(f"\n2️⃣ SAMIntegration Import Kontrolü:")
try:
    from sam_integration import SAMIntegration
    print("   ✅ SAMIntegration imported successfully")
    
    # 3. Test SAMIntegration initialization
    print(f"\n3️⃣ SAMIntegration Initialization:")
    try:
        sam = SAMIntegration()
        print("   ✅ SAMIntegration instance created")
        
        if sam.api_key:
            print(f"   ✅ API Key loaded: {sam.api_key[:10]}...{sam.api_key[-5:]}")
        else:
            print("   ❌ API Key not loaded in SAMIntegration instance")
        
        # 4. Test fetch (small test)
        print(f"\n4️⃣ Test Fetch (5 opportunities, 7 days):")
        try:
            opportunities = sam.fetch_opportunities(
                naics_codes=['721110'],
                days_back=7,
                limit=5
            )
            print(f"   ✅ Fetch successful!")
            print(f"   Opportunities found: {len(opportunities)}")
            
            if opportunities:
                print(f"\n   📋 Sample Opportunities:")
                for i, opp in enumerate(opportunities[:3], 1):
                    notice_id = opp.get('noticeId', 'N/A')
                    title = opp.get('title', 'N/A')[:50]
                    print(f"      {i}. {title}")
                    print(f"         Notice ID: {notice_id}")
        except Exception as fetch_error:
            print(f"   ❌ Fetch failed: {fetch_error}")
            import traceback
            traceback.print_exc()
            
    except Exception as init_error:
        print(f"   ❌ Initialization failed: {init_error}")
        import traceback
        traceback.print_exc()
        
except ImportError as import_error:
    print(f"   ❌ Import failed: {import_error}")
    print(f"   💡 Check if sam_integration.py is in project root")

# 5. Check .env file
print(f"\n5️⃣ Environment File Kontrolü:")
env_paths = [
    Path("/app/mergen/.env"),
    Path("/app/.env"),
    Path("/app/../mergen/.env"),
]
for env_path in env_paths:
    if env_path.exists():
        print(f"   ✅ Found: {env_path}")
        # Check if SAM_API_KEY is in file
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                if 'SAM_API_KEY' in content:
                    print(f"      ✅ SAM_API_KEY found in file")
                else:
                    print(f"      ⚠️ SAM_API_KEY not found in file")
        except Exception as e:
            print(f"      ⚠️ Could not read file: {e}")
        break
else:
    print("   ⚠️ No .env file found in common locations")

print()
print("=" * 70)

