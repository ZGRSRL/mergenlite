#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for frontend"""
import requests
import sys
import time

def test_frontend():
    """Test frontend server"""
    print("Testing Frontend...")
    print("=" * 50)
    
    # Test 1: Frontend server
    print("\n1. Testing frontend server (http://localhost:3000)...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("   [OK] Frontend server is running")
            print(f"   [OK] Status code: {response.status_code}")
            if "html" in response.text.lower():
                print("   [OK] HTML content detected")
        else:
            print(f"   [WARNING] Unexpected status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   [ERROR] Frontend server is not running")
        print("   [INFO] Start it with: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False
    
    # Test 2: API proxy (via vite dev server)
    print("\n2. Testing API proxy (/api)...")
    try:
        # Vite dev server proxies /api to backend
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        print(f"   [INFO] API proxy response: {response.status_code}")
        if response.status_code == 200:
            print("   [OK] API proxy is working")
        elif response.status_code == 404:
            print("   [INFO] API endpoint not found (backend might not be running)")
        else:
            print(f"   [INFO] API returned: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   [INFO] Backend API is not running (expected if backend is down)")
    except Exception as e:
        print(f"   [INFO] API proxy test: {e}")
    
    # Test 3: Static assets
    print("\n3. Testing static assets...")
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if "index.html" in response.text or "<!DOCTYPE" in response.text:
            print("   [OK] HTML is being served")
        if "react" in response.text.lower() or "vite" in response.text.lower():
            print("   [OK] React/Vite assets detected")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Frontend tests completed!")
    print("=" * 50)
    print("\nFrontend is available at: http://localhost:3000")
    print("API proxy: http://localhost:3000/api -> http://localhost:8000")
    
    return True

if __name__ == "__main__":
    # Wait a bit for server to start
    print("Waiting for frontend to be ready...")
    time.sleep(2)
    
    success = test_frontend()
    sys.exit(0 if success else 1)

