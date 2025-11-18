#!/usr/bin/env python3
"""Test backend endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("BACKEND ENDPOINTS TEST")
print("=" * 60)

# Test 1: Health check
print(f"\n1. Testing /api/health...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    if response.status_code == 200:
        print(f"  [OK] Health check passed")
    else:
        print(f"  [ERROR] Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 2: Dashboard stats
print(f"\n2. Testing /api/dashboard/stats...")
try:
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  [OK] Dashboard stats endpoint works")
        print(f"  Total opportunities: {data.get('total_opportunities', 0)}")
        print(f"  Today new: {data.get('today_new', 0)}")
        print(f"  Analyzed: {data.get('analyzed_count', 0)}")
    else:
        print(f"  [ERROR] Status: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 3: Recent activities
print(f"\n3. Testing /api/dashboard/recent-activities...")
try:
    response = requests.get(f"{BASE_URL}/api/dashboard/recent-activities?limit=5", timeout=5)
    if response.status_code == 200:
        data = response.json()
        activities = data.get('activities', [])
        print(f"  [OK] Recent activities endpoint works")
        print(f"  Found {len(activities)} activities")
        if activities:
            print(f"  First activity: {activities[0].get('title', 'N/A')[:50]}...")
    else:
        print(f"  [ERROR] Status: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 4: Opportunities list
print(f"\n4. Testing /api/opportunities...")
try:
    response = requests.get(f"{BASE_URL}/api/opportunities?limit=5", timeout=5)
    if response.status_code == 200:
        data = response.json()
        opps = data.get('opportunities', [])
        print(f"  [OK] Opportunities endpoint works")
        print(f"  Total: {data.get('total', 0)}")
        print(f"  Returned: {len(opps)}")
        if opps:
            print(f"  First opportunity: {opps[0].get('title', 'N/A')[:50]}...")
    else:
        print(f"  [ERROR] Status: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
except Exception as e:
    print(f"  [ERROR] {e}")

print(f"\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)

