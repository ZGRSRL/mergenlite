#!/usr/bin/env python3
"""
Background worker for ZgrBid
"""
import os
import sys
from rq import Worker, Connection
from redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from app.config import settings

def main():
    """Main worker function"""
    # Connect to Redis
    redis_conn = Redis.from_url(settings.redis_url)
    
    # Create worker
    with Connection(redis_conn):
        worker = Worker(['default'])
        print("Starting ZgrBid worker...")
        print(f"Redis URL: {settings.redis_url}")
        worker.work()

if __name__ == "__main__":
    main()



