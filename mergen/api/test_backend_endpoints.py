#!/usr/bin/env python3
"""Test backend endpoints"""
from fastapi.testclient import TestClient
from mergen.api.app.main import app

client = TestClient(app)

print("=" * 60)
print("BACKEND ENDPOINTS TEST")
print("=" * 60)

# Test 1: Health
print("\n1. Testing /api/health...")
r = client.get('/api/health')
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print("   [OK] Health check passed")
else:
    print(f"   [ERROR] Response: {r.text[:200]}")

# Test 2: Dashboard stats
print("\n2. Testing /api/dashboard/stats...")
r = client.get('/api/dashboard/stats')
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   [OK] Dashboard stats")
    print(f"   Total opportunities: {data.get('total_opportunities', 0)}")
    print(f"   Today new: {data.get('today_new', 0)}")
    print(f"   Analyzed: {data.get('analyzed_count', 0)}")
else:
    print(f"   [ERROR] Response: {r.text[:200]}")

# Test 3: Recent activities
print("\n3. Testing /api/dashboard/recent-activities...")
r = client.get('/api/dashboard/recent-activities?limit=5')
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    activities = data.get('activities', [])
    print(f"   [OK] Recent activities: {len(activities)}")
else:
    print(f"   [ERROR] Response: {r.text[:200]}")

# Test 4: Opportunities
print("\n4. Testing /api/opportunities...")
r = client.get('/api/opportunities?limit=5')
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    opps = data.get('opportunities', [])
    total = data.get('total', 0)
    print(f"   [OK] Opportunities")
    print(f"   Total: {total}")
    print(f"   Returned: {len(opps)}")
else:
    print(f"   [ERROR] Response: {r.text[:200]}")

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)

