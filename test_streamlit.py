#!/usr/bin/env python3
"""Test script to verify Streamlit can start"""

import sys
import os

print("Testing Streamlit setup...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    import streamlit as st
    print(f"[OK] Streamlit imported: version {st.__version__}")
except ImportError as e:
    print(f"[ERROR] Streamlit import error: {e}")
    sys.exit(1)

try:
    from guided_analysis import render_guided_analysis_page
    print("[OK] guided_analysis imported")
except ImportError as e:
    print(f"[ERROR] guided_analysis import error: {e}")

try:
    from sam_integration import SAMIntegration
    print("[OK] sam_integration imported")
except ImportError as e:
    print(f"[ERROR] sam_integration import error: {e}")

print("\n[OK] All imports successful! Streamlit should work.")

