#!/usr/bin/env python3
"""Check adults parameter for hotel match 275."""
from app.db import SessionLocal
from app.models import LLMCall, AIAnalysisResult
import json
import re

db = SessionLocal()

# Check requirements
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 275).first()
if result and result.result_json:
    reqs = result.result_json.get('requirements', {})
    print(f"Requirements adults: {reqs.get('adults', 'N/A')}")

# Check LLM call prompt
call = db.query(LLMCall).filter(LLMCall.id == 121).first()
if call and call.prompt:
    prompt = call.prompt
    # Find adults in prompt
    adults_match = re.search(r'"adults"\s*:\s*(\d+)', prompt)
    if adults_match:
        print(f"✅ Adults in LLM prompt: {adults_match.group(1)}")
    else:
        # Try without quotes
        adults_match = re.search(r'adults[\'"]?\s*:\s*(\d+)', prompt, re.IGNORECASE)
        if adults_match:
            print(f"✅ Adults in LLM prompt (alt format): {adults_match.group(1)}")
        else:
            print("❌ Adults not found in prompt")
            # Show requirements section
            reqs_start = prompt.find('"requirements"')
            if reqs_start > 0:
                reqs_section = prompt[reqs_start:reqs_start+500]
                print(f"Requirements section preview:\n{reqs_section}")
else:
    print("❌ LLM call not found or prompt is empty")

db.close()

