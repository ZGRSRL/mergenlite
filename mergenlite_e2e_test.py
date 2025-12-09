
import sys
import os
import logging
from datetime import datetime
import uuid
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Fix 'app' import conflict (root app.py vs mergen.api.app package)
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from mergen.api.app.db import SessionLocal, engine, Base
from mergen.api.app.models import Opportunity, OpportunityAttachment, AIAnalysisResult
from mergen.api.app.services.pipeline_service import create_pipeline_job, run_pipeline_job

def test_e2e_pipeline():
    logger.info("Starting E2E Pipeline Test...")
    
    db = SessionLocal()
    try:
        # 1. Create Dummy Opportunity
        notice_id = f"TEST-{uuid.uuid4().hex[:8]}"
        opp = Opportunity(
            opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
            notice_id=notice_id,
            title="E2E Test Opportunity - Catering Services",
            description="Requirement for catering services for 500 people. Must include vegetarian options.",
            solicitation_number="SOL-123456",
            agency="Test Agency",
            posted_date=datetime.now(),
            response_deadline=datetime.now()
        )
        db.add(opp)
        db.commit()
        db.refresh(opp)
        logger.info(f"Created Opportunity: {opp.id} ({opp.notice_id})")

        # 2. Create Dummy Attachment File
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        test_file_path = data_dir / f"test_doc_{notice_id}.txt"
        test_file_path.write_text("This is a Statement of Work for catering services. \n\n1. Scope: Provide breakfast and lunch.\n2. Quantity: 500 pax.\n3. Requirements: Vegetarian options required.", encoding="utf-8")
        
        # 3. Add Attachment Record
        att = OpportunityAttachment(
            opportunity_id=opp.id,
            name="SOW.txt",
            attachment_type="document",
            local_path=str(test_file_path),
            downloaded=True,
            mime_type="text/plain",
            size_bytes=test_file_path.stat().st_size
        )
        db.add(att)
        db.commit()
        logger.info(f"Created Attachment: {att.id} ({att.local_path})")

        # 4. Create Pipeline Job
        logger.info("Creating Pipeline Job...")
        analysis_result, agent_run_id = create_pipeline_job(
            db=db,
            opportunity_id=opp.id,
            analysis_type="sow_draft",
            pipeline_version="v2-test",
            agent_name="e2e-tester",
            initial_options={"max_text_length": 1000}
        )
        logger.info(f"Job Created: Result ID {analysis_result.id}, Run ID {agent_run_id}")

        # 5. Run Job Synchronously
        payload = {
            "attachment_ids": [att.id],
            "options": {"max_text_length": 1000},
            "agent_run_id": agent_run_id
        }
        
        logger.info("Running Pipeline (Sync)...")
        run_pipeline_job(analysis_result.id, payload)

        # 6. Verify Result
        db.refresh(analysis_result)
        logger.info(f"Job Finished. Status: {analysis_result.status}")
        
        if analysis_result.status == "completed":
            logger.info("✅ E2E Test PASSED")
            logger.info(f"Result JSON: {analysis_result.result_json}")
            
            # Check if JSON file was created
            if analysis_result.json_path and os.path.exists(analysis_result.json_path):
                logger.info(f"✅ JSON Output verified at {analysis_result.json_path}")
            else:
                logger.warning("❌ JSON Output file missing")
                
        else:
            logger.error(f"❌ E2E Test FAILED. Status: {analysis_result.status}")
            sys.exit(1)

    except Exception as e:
        logger.exception("Test validation failed")
        sys.exit(1)
    finally:
        db.close()
        # Cleanup could go here (delete test files/db records), but keeping them for inspection is better

if __name__ == "__main__":
    test_e2e_pipeline()
