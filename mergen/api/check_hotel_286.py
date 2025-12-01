#!/usr/bin/env python3
"""Check Hotel Match 286 details."""
from app.db import SessionLocal
from app.models import AIAnalysisResult, LLMCall
import json

db = SessionLocal()

# Check result
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 286).first()
if result:
    data = result.result_json if isinstance(result.result_json, dict) else json.loads(result.result_json) if result.result_json else {}
    hotels = data.get('hotels', [])
    fallback = data.get('fallback_used', False)
    
    print(f"Fallback used: {fallback}")
    print(f"Hotels count: {len(hotels)}")
    
    if hotels:
        print(f"\nFirst hotel structure:")
        print(json.dumps(hotels[0], indent=2, default=str)[:1000])
        
        # Check if offer exists
        if 'offer' in hotels[0]:
            offer = hotels[0]['offer']
            if 'hotel' in offer:
                print(f"\n✅ Offer içinde hotel var!")
                print(f"   Hotel name: {offer['hotel'].get('name', 'N/A')}")

# Check LLM call
call = db.query(LLMCall).filter(LLMCall.agent_run_id == 286).first()
if call:
    print(f"\nLLM Response length: {len(call.response) if call.response else 0}")

db.close()

