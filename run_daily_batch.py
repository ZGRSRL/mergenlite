
import time
import os
import sys
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from sam_integration import SAMIntegration
from backend_utils import get_db_session
from mergenlite_models import Opportunity

load_dotenv()
API_KEY = os.getenv("SAM_API_KEY")

def run_daily_batch():
    print(f"🚀 MERGENLITE DAILY BATCH RUN STARTED: {datetime.now()}")
    
    if not API_KEY:
        print("❌ Error: SAM_API_KEY not found in environment variables.")
        return

    # 1. Fetch from SAM.gov (Last 1 Day)
    sam = SAMIntegration()
    # Ensure usage of correct API key if not automatically loaded
    if not sam.api_key and API_KEY:
        sam.api_key = API_KEY
    
    print(f"📡 Scanning SAM.gov (Days Back: 1)...")
    
    # Use days_back=1 to get last 24h. Limit to 50 to be safe but getting all is the goal.
    opportunities = sam.fetch_opportunities(days_back=1, limit=50) 
    
    if not opportunities:
        print("📭 No new opportunities found for the last 24 hours.")
        return

    print(f"🌍 Found {len(opportunities)} potential opportunities. Starting processing...")

    processed_count = 0
    
    for opp_data in opportunities:
        # Extract Identifiers
        # sam_integration._parse_opportunity returns: opportunityId, noticeId, solicitationNumber
        # user model uses: opportunity_id, notice_id, solicitation_number
        
        opp_id = opp_data.get('opportunityId')
        notice_id = opp_data.get('noticeId')
        sol_num = opp_data.get('solicitationNumber')
        title = opp_data.get('title')
        
        # Identifier to check in DB (priority: opportunityId -> noticeId -> solicitationNumber)
        # Note: Mergenlite DB has opportunity_id as String(255) and NOT nullable.
        # Check specific field first.
        
        primary_id = opp_id or notice_id or sol_num
        
        if not primary_id:
            print(f"⚠️ Skipping item with no ID: {title}")
            continue

        # 2. Database Check
        db = get_db_session()
        if not db:
            print("❌ Database connection failed.")
            break
            
        exists = None
        if opp_id:
             exists = db.query(Opportunity).filter(Opportunity.opportunity_id == opp_id).first()
        elif notice_id:
             exists = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
        
        if exists:
            print(f"⏩ Already processed, skipping: {title} ({primary_id})")
            db.close()
            continue
            
        # 3. New Opportunity - Save and Trigger Pipeline
        print(f"\n⚡ NEW TARGET: {title}")
        print(f"   ID: {primary_id}")
        
        try:
            # Save "New" status to DB
            new_opp = Opportunity(
                opportunity_id=opp_id or primary_id, # Fallback to primary if opp_id is missing
                notice_id=notice_id,
                solicitation_number=sol_num,
                title=title,
                agency=opp_data.get('agency', ''), # agency field added in model check
                sam_gov_link=opp_data.get('samGovLink'),
                response_deadline=None, # Parse if available or let pipeline handle validation
                status="New",
                raw_data=opp_data
            )
            
            # Helper to parse date if needed, but keeping it simple as model allows nulls mostly
            if opp_data.get('postedDate'):
                # Try simple parse if possible, or leave for robust logic later
                pass

            db.add(new_opp)
            db.commit()
            print("   💾 Saved to DB.")
            
            # The pipeline script takes an ID argument.
            # It prefers NOTICE ID or OPPORTUNITY ID. 
            # run_full_analysis_pipeline.py uses requests.get(..., params={"notice_id": search_id}) usually
            # But let's check `run_full_analysis_pipeline.py` logic.
            # It sends `sys.argv[1]` to `search_by_any_id` in `sam_integration` logic via API? 
            # API endpoint `/api/opportunities` accepts `notice_id`. 
            # Let's pass the most reliable ID: notice_id if available, else opportunity_id.
            
            pipeline_arg = notice_id if notice_id else (opp_id if opp_id else sol_num)

            db.close()

            # TRIGGER PIPELINE
            print(f"   ⚙️ Starting Analysis Pipeline for {pipeline_arg}...")
            
            # run_full_analysis_pipeline.py takes 1 argument
            cmd = ["python", "run_full_analysis_pipeline.py", pipeline_arg]
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("   ✅ Pipeline Executed Successfully.")
                # We can print some of stdout if needed
                # print(result.stdout[:200] + "...")
                processed_count += 1
            else:
                print(f"   ❌ Pipeline Failed:\n{result.stderr}\nSTDOUT:\n{result.stdout}")

        except Exception as e:
            print(f"   ⚠️ Critical Error: {e}")
            if db:
                db.close()
            
        # 4. Rate Limit Cooling
        print("   ⏳ Cooling down (10s)...")
        time.sleep(10)

    print(f"\n🏁 DAILY BATCH COMPLETED. Total Processed: {processed_count}")

if __name__ == "__main__":
    run_daily_batch()
