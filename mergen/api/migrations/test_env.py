#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for env.py imports"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add the app directory to the Python path (same as env.py)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing imports from env.py...")
    print("-" * 50)
    
    # Test Base import
    print("1. Testing app.db.Base import...")
    from app.db import Base
    print("   [OK] Base imported successfully")
    print(f"   [OK] Base type: {type(Base)}")
    print(f"   [OK] Base metadata: {Base.metadata}")
    
    # Test settings import
    print("\n2. Testing app.config.settings import...")
    from app.config import settings
    print("   [OK] Settings imported successfully")
    print(f"   [OK] Database URL: {settings.database_url[:60]}...")
    print(f"   [OK] Environment: {settings.env}")
    
    # Test models import
    print("\n3. Testing app.models imports...")
    from app.models import (
        Opportunity,
        OpportunityAttachment,
        OpportunityHistory,
        AIAnalysisResult,
        AnalysisLog,
        AgentRun,
        AgentMessage,
    )
    print("   [OK] All models imported successfully")
    print(f"   [OK] Opportunity: {Opportunity}")
    print(f"   [OK] OpportunityAttachment: {OpportunityAttachment}")
    print(f"   [OK] OpportunityHistory: {OpportunityHistory}")
    print(f"   [OK] AIAnalysisResult: {AIAnalysisResult}")
    print(f"   [OK] AnalysisLog: {AnalysisLog}")
    print(f"   [OK] AgentRun: {AgentRun}")
    print(f"   [OK] AgentMessage: {AgentMessage}")
    
    # Test get_url function
    print("\n4. Testing get_url() function...")
    def get_url():
        """Get database URL from settings"""
        return settings.database_url
    
    url = get_url()
    print(f"   [OK] get_url() returned: {url[:60]}...")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] TUM TESTLER BASARILI!")
    print("=" * 50)
    
except ImportError as e:
    print(f"\n[ERROR] Import hatasi: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

