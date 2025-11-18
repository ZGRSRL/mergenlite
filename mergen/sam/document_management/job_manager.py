"""
Jobs/Queue System - Background Processing
Manages analysis jobs with status tracking and background processing
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import time
import queue

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AnalysisJob:
    """Analysis job data structure"""
    id: Optional[int]
    notice_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    progress: int  # 0-100
    current_step: str
    result_data: Optional[Dict[str, Any]]

class JobManager:
    """Manages analysis jobs and background processing"""
    
    def __init__(self):
        self.job_queue = queue.Queue()
        self.running_jobs = {}
        self.worker_thread = None
        self.is_running = False
        
        # Database connection
        self.db_conn = None
        self._connect_database()
        
        # Initialize database tables
        self._create_tables()
        
        logger.info("Job Manager initialized")
    
    def _connect_database(self):
        """Connect to database"""
        try:
            self.db_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'sam'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
            logger.info("Database connected for Job Manager")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_conn = None
    
    def _create_tables(self):
        """Create necessary database tables"""
        if not self.db_conn:
            return
        
        try:
            with self.db_conn.cursor() as cur:
                # Analysis jobs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_jobs (
                        id SERIAL PRIMARY KEY,
                        notice_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'queued',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        finished_at TIMESTAMP,
                        error_message TEXT,
                        progress INTEGER DEFAULT 0,
                        current_step VARCHAR(255),
                        result_data JSONB
                    )
                """)
                
                # Analysis results table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id SERIAL PRIMARY KEY,
                        notice_id VARCHAR(255) NOT NULL,
                        job_id INTEGER REFERENCES analysis_jobs(id),
                        go_no_go_score NUMERIC(5,2),
                        confidence NUMERIC(3,2),
                        summary TEXT,
                        risks JSONB,
                        requirements JSONB,
                        missing_items JSONB,
                        action_items JSONB,
                        qa_pairs JSONB,
                        analysis_timestamp TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Job logs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_job_logs (
                        id SERIAL PRIMARY KEY,
                        job_id INTEGER REFERENCES analysis_jobs(id),
                        step VARCHAR(255),
                        message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.db_conn.commit()
                logger.info("Job Manager tables created")
                
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
    
    def enqueue_analysis(self, notice_id: str) -> str:
        """Enqueue a new analysis job"""
        try:
            # Create job record
            job_id = self._create_job_record(notice_id)
            
            # Add to queue
            job = AnalysisJob(
                id=job_id,
                notice_id=notice_id,
                status=JobStatus.QUEUED,
                created_at=datetime.now(),
                started_at=None,
                finished_at=None,
                error_message=None,
                progress=0,
                current_step="Queued",
                result_data=None
            )
            
            self.job_queue.put(job)
            logger.info(f"Job enqueued: {notice_id} (ID: {job_id})")
            
            return str(job_id)
            
        except Exception as e:
            logger.error(f"Job enqueue failed: {e}")
            return None
    
    def _create_job_record(self, notice_id: str) -> int:
        """Create job record in database"""
        if not self.db_conn:
            return None
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_jobs (notice_id, status, created_at, progress, current_step)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (notice_id, JobStatus.QUEUED.value, datetime.now(), 0, "Queued"))
                
                job_id = cur.fetchone()[0]
                self.db_conn.commit()
                
                return job_id
                
        except Exception as e:
            logger.error(f"Job record creation failed: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status"""
        try:
            if not self.db_conn:
                return {'error': 'Database not connected'}
            
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM analysis_jobs WHERE id = %s
                """, (job_id,))
                
                job = cur.fetchone()
                
                if job:
                    return {
                        'job_id': job['id'],
                        'notice_id': job['notice_id'],
                        'status': job['status'],
                        'progress': job['progress'],
                        'current_step': job['current_step'],
                        'created_at': job['created_at'].isoformat() if job['created_at'] else None,
                        'started_at': job['started_at'].isoformat() if job['started_at'] else None,
                        'finished_at': job['finished_at'].isoformat() if job['finished_at'] else None,
                        'error_message': job['error_message']
                    }
                else:
                    return {'error': 'Job not found'}
                    
        except Exception as e:
            logger.error(f"Get job status failed: {e}")
            return {'error': str(e)}
    
    def get_job_results(self, notice_id: str) -> Dict[str, Any]:
        """Get analysis results for a notice"""
        try:
            if not self.db_conn:
                return {'error': 'Database not connected'}
            
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ar.*, aj.status as job_status
                    FROM analysis_results ar
                    JOIN analysis_jobs aj ON ar.job_id = aj.id
                    WHERE ar.notice_id = %s
                    ORDER BY ar.created_at DESC
                    LIMIT 1
                """, (notice_id,))
                
                result = cur.fetchone()
                
                if result:
                    return {
                        'notice_id': result['notice_id'],
                        'go_no_go_score': float(result['go_no_go_score']) if result['go_no_go_score'] else 0,
                        'confidence': float(result['confidence']) if result['confidence'] else 0,
                        'summary': result['summary'],
                        'risks': result['risks'],
                        'requirements': result['requirements'],
                        'missing_items': result['missing_items'],
                        'action_items': result['action_items'],
                        'qa_pairs': result['qa_pairs'],
                        'analysis_timestamp': result['analysis_timestamp'].isoformat() if result['analysis_timestamp'] else None,
                        'job_status': result['job_status']
                    }
                else:
                    return {'error': 'No results found'}
                    
        except Exception as e:
            logger.error(f"Get job results failed: {e}")
            return {'error': str(e)}
    
    def update_job_status(self, job_id: int, status: JobStatus, progress: int = None, current_step: str = None, error_message: str = None):
        """Update job status"""
        try:
            if not self.db_conn:
                return
            
            with self.db_conn.cursor() as cur:
                update_fields = ['status = %s']
                values = [status.value]
                
                if progress is not None:
                    update_fields.append('progress = %s')
                    values.append(progress)
                
                if current_step is not None:
                    update_fields.append('current_step = %s')
                    values.append(current_step)
                
                if error_message is not None:
                    update_fields.append('error_message = %s')
                    values.append(error_message)
                
                if status == JobStatus.RUNNING:
                    update_fields.append('started_at = %s')
                    values.append(datetime.now())
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    update_fields.append('finished_at = %s')
                    values.append(datetime.now())
                
                values.append(job_id)
                
                cur.execute(f"""
                    UPDATE analysis_jobs 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, values)
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"Update job status failed: {e}")
    
    def log_job_step(self, job_id: int, step: str, message: str):
        """Log job step"""
        try:
            if not self.db_conn:
                return
            
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_job_logs (job_id, step, message, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (job_id, step, message, datetime.now()))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"Log job step failed: {e}")
    
    def save_analysis_result(self, job_id: int, result_data: Dict[str, Any]):
        """Save analysis result"""
        try:
            if not self.db_conn:
                return
            
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_results (
                        notice_id, job_id, go_no_go_score, confidence, summary,
                        risks, requirements, missing_items, action_items, qa_pairs,
                        analysis_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result_data['opportunity_id'],
                    job_id,
                    result_data['go_no_go_score'],
                    result_data['confidence'],
                    result_data['summary'],
                    json.dumps(result_data['risks']),
                    json.dumps(result_data['requirements']),
                    json.dumps(result_data['missing_items']),
                    json.dumps(result_data['action_items']),
                    json.dumps(result_data['qa_pairs']),
                    result_data['analysis_timestamp']
                ))
                
                self.db_conn.commit()
                
        except Exception as e:
            logger.error(f"Save analysis result failed: {e}")
    
    def start_worker(self):
        """Start background worker thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Job worker started")
    
    def stop_worker(self):
        """Stop background worker thread"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("Job worker stopped")
    
    def _worker_loop(self):
        """Background worker loop"""
        while self.is_running:
            try:
                # Get job from queue (with timeout)
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process job
                self._process_job(job)
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1)
    
    def _process_job(self, job: AnalysisJob):
        """Process a single job"""
        try:
            logger.info(f"Processing job: {job.notice_id}")
            
            # Update status to running
            self.update_job_status(job.id, JobStatus.RUNNING, 10, "Starting analysis")
            self.log_job_step(job.id, "start", f"Analysis started for {job.notice_id}")
            
            # Import here to avoid circular imports
            from autogen_orchestrator import run_full_analysis
            from sam_collector import get_opportunity_details
            from attachment_pipeline import process_document
            
            # Step 1: Get opportunity data
            self.update_job_status(job.id, JobStatus.RUNNING, 20, "Fetching opportunity data")
            self.log_job_step(job.id, "fetch", f"Fetching data for {job.notice_id}")
            
            opp_data = get_opportunity_details(job.notice_id)
            if not opp_data['success']:
                raise Exception(f"Failed to fetch opportunity data: {opp_data['error']}")
            
            # Step 2: Process documents
            self.update_job_status(job.id, JobStatus.RUNNING, 40, "Processing documents")
            self.log_job_step(job.id, "process", "Processing attachments")
            
            document_chunks = []
            attachments = opp_data.get('attachments', [])
            
            for attachment in attachments:
                # Download and process attachment
                # This would be implemented with actual file processing
                pass
            
            # Step 3: Run analysis
            self.update_job_status(job.id, JobStatus.RUNNING, 60, "Running AI analysis")
            self.log_job_step(job.id, "analyze", "Running AutoGen analysis")
            
            result = run_full_analysis(job.notice_id, opp_data['opportunity'], document_chunks)
            
            # Step 4: Save results
            self.update_job_status(job.id, JobStatus.RUNNING, 80, "Saving results")
            self.log_job_step(job.id, "save", "Saving analysis results")
            
            self.save_analysis_result(job.id, asdict(result))
            
            # Complete job
            self.update_job_status(job.id, JobStatus.COMPLETED, 100, "Analysis completed")
            self.log_job_step(job.id, "complete", "Analysis completed successfully")
            
            logger.info(f"Job completed: {job.notice_id}")
            
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            self.update_job_status(job.id, JobStatus.FAILED, error_message=str(e))
            self.log_job_step(job.id, "error", f"Analysis failed: {e}")

# Global instance
job_manager = JobManager()

def enqueue_analysis(notice_id: str) -> str:
    """Enqueue a new analysis job"""
    return job_manager.enqueue_analysis(notice_id)

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status"""
    return job_manager.get_job_status(job_id)

def get_job_results(notice_id: str) -> Dict[str, Any]:
    """Get analysis results for a notice"""
    return job_manager.get_job_results(notice_id)

def start_job_worker():
    """Start background job worker"""
    job_manager.start_worker()

def stop_job_worker():
    """Stop background job worker"""
    job_manager.stop_worker()

if __name__ == "__main__":
    # Test the job manager
    print("Job Manager Test")
    
    # Start worker
    start_job_worker()
    
    # Enqueue test job
    job_id = enqueue_analysis("TEST123")
    print(f"Job enqueued: {job_id}")
    
    # Check status
    status = get_job_status(job_id)
    print(f"Job status: {status}")
    
    # Stop worker
    stop_job_worker()

