#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test autogen installation and imports"""
import sys

print("=" * 60)
print("AUTOGEN INSTALLATION TEST")
print("=" * 60)

# Test 1: Direct import
print("\n1. Testing direct pyautogen import...")
try:
    import pyautogen
    print(f"   [OK] pyautogen imported successfully")
    try:
        print(f"   [OK] Version: {pyautogen.__version__}")
    except:
        print(f"   [INFO] Version not available")
except ImportError as e:
    print(f"   [ERROR] pyautogen import failed: {e}")
    sys.exit(1)

# Test 2: Import AssistantAgent and UserProxyAgent
print("\n2. Testing AssistantAgent and UserProxyAgent imports...")
try:
    try:
        from autogen import AssistantAgent, UserProxyAgent
        print(f"   [OK] Imported from 'autogen' module")
        AUTOGEN_AVAILABLE = True
    except ImportError:
        from pyautogen import AssistantAgent, UserProxyAgent
        print(f"   [OK] Imported from 'pyautogen' module")
        AUTOGEN_AVAILABLE = True
    print(f"   [OK] AssistantAgent: {AssistantAgent}")
    print(f"   [OK] UserProxyAgent: {UserProxyAgent}")
except ImportError as e:
    print(f"   [ERROR] Agent imports failed: {e}")
    AUTOGEN_AVAILABLE = False
    sys.exit(1)

# Test 3: Test agent creation (without API key)
print("\n3. Testing agent creation (without API key)...")
try:
    # This should work even without API key (just creation, not execution)
    user = UserProxyAgent(
        name="TestUser",
        code_execution_config=False,
        human_input_mode="NEVER",
    )
    print(f"   [OK] UserProxyAgent created successfully")
    print(f"   [OK] Agent name: {user.name}")
except Exception as e:
    print(f"   [ERROR] Agent creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test from app agents
print("\n4. Testing app agent imports...")
try:
    from app.agents.sow_analyzer_agent import AUTOGEN_AVAILABLE as SOW_AUTOGEN
    from app.agents.rfq_3pass_orchestrator import AUTOGEN_AVAILABLE as RFQ_AUTOGEN
    from app.agents.hotel_matcher_agent import AUTOGEN_AVAILABLE as HOTEL_AUTOGEN
    print(f"   [OK] SOW Analyzer AUTOGEN_AVAILABLE: {SOW_AUTOGEN}")
    print(f"   [OK] RFQ Orchestrator AUTOGEN_AVAILABLE: {RFQ_AUTOGEN}")
    print(f"   [OK] Hotel Matcher AUTOGEN_AVAILABLE: {HOTEL_AUTOGEN}")
    
    if not (SOW_AUTOGEN and RFQ_AUTOGEN and HOTEL_AUTOGEN):
        print(f"   [WARNING] Some agents report AUTOGEN_AVAILABLE=False")
        print(f"   [INFO] This might be due to import issues in agent modules")
except Exception as e:
    print(f"   [ERROR] App agent import test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check API key
print("\n5. Checking API keys...")
import os
openai_key = os.getenv("OPENAI_API_KEY")
azure_key = os.getenv("AZURE_OPENAI_API_KEY")
if openai_key:
    print(f"   [OK] OPENAI_API_KEY is set (length: {len(openai_key)})")
else:
    print(f"   [INFO] OPENAI_API_KEY not set")
if azure_key:
    print(f"   [OK] AZURE_OPENAI_API_KEY is set (length: {len(azure_key)})")
else:
    print(f"   [INFO] AZURE_OPENAI_API_KEY not set")

if not openai_key and not azure_key:
    print(f"   [WARNING] No API key found. AutoGen agents may not work without API key.")

print("\n" + "=" * 60)
if AUTOGEN_AVAILABLE:
    print("[SUCCESS] Autogen is available and working!")
else:
    print("[WARNING] Autogen may not be fully available")
print("=" * 60)

