#!/usr/bin/env python3
"""Check if OpenAI responses are being saved to database correctly."""
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import LLMCall, AgentMessage, AgentRun, AIAnalysisResult
from sqlalchemy import desc
from datetime import datetime, timedelta

print("=" * 70)
print("📊 DATABASE LOG KONTROLÜ - OpenAI Yanıtları")
print("=" * 70)
print()

db = SessionLocal()

# Check recent analysis results
print("📄 Son Analiz Sonuçları:")
recent_results = db.query(AIAnalysisResult).order_by(desc(AIAnalysisResult.created_at)).limit(5).all()
for result in recent_results:
    print(f"\n   Analysis ID: {result.id}")
    print(f"   Type: {result.analysis_type}")
    print(f"   Status: {result.status}")
    print(f"   Created: {result.created_at}")
    print(f"   Result JSON: {'✅ Var' if result.result_json else '❌ Yok'}")

# Check LLM Calls
print("\n" + "=" * 70)
print("🤖 LLM Çağrıları (Son 10):")
llm_calls = db.query(LLMCall).order_by(desc(LLMCall.created_at)).limit(10).all()
if llm_calls:
    print(f"   Toplam LLM Çağrısı: {len(llm_calls)}")
    for call in llm_calls:
        print(f"\n   LLM Call ID: {call.id}")
        print(f"   Provider: {call.provider}")
        print(f"   Model: {call.model}")
        print(f"   Agent: {call.agent_name}")
        print(f"   Created: {call.created_at}")
        print(f"   Prompt: {'✅ Var' if call.prompt else '❌ Yok'} ({len(call.prompt) if call.prompt else 0} chars)")
        print(f"   Response: {'✅ Var' if call.response else '❌ Yok'} ({len(call.response) if call.response else 0} chars)")
        print(f"   Tokens: {call.prompt_tokens}/{call.completion_tokens}/{call.total_tokens}")
else:
    print("   ⚠️ Hiç LLM çağrısı kaydedilmemiş!")

# Check Agent Messages
print("\n" + "=" * 70)
print("💬 Agent Mesajları (Son 20):")
agent_messages = db.query(AgentMessage).order_by(desc(AgentMessage.created_at)).limit(20).all()
if agent_messages:
    print(f"   Toplam Agent Mesajı: {len(agent_messages)}")
    for msg in agent_messages[:10]:
        print(f"\n   Message ID: {msg.id}")
        print(f"   Agent: {msg.agent_name}")
        print(f"   Role: {msg.role}")
        print(f"   Type: {msg.message_type}")
        print(f"   Created: {msg.created_at}")
        print(f"   Content: {'✅ Var' if msg.content else '❌ Yok'} ({len(msg.content) if msg.content else 0} chars)")
        if msg.content and len(msg.content) > 0:
            print(f"   Preview: {msg.content[:100]}...")
else:
    print("   ⚠️ Hiç agent mesajı kaydedilmemiş!")

# Check Agent Runs
print("\n" + "=" * 70)
print("🏃 Agent Runs (Son 10):")
agent_runs = db.query(AgentRun).order_by(desc(AgentRun.started_at)).limit(10).all()
if agent_runs:
    print(f"   Toplam Agent Run: {len(agent_runs)}")
    for run in agent_runs:
        print(f"\n   Run ID: {run.id}")
        print(f"   Type: {run.run_type}")
        print(f"   Status: {run.status}")
        print(f"   Started: {run.started_at}")
        print(f"   Completed: {run.finished_at}")
        # Count messages for this run
        msg_count = db.query(AgentMessage).filter(AgentMessage.agent_run_id == run.id).count()
        print(f"   Messages: {msg_count}")
else:
    print("   ⚠️ Hiç agent run kaydedilmemiş!")

# Summary
print("\n" + "=" * 70)
print("📊 ÖZET:")
total_llm_calls = db.query(LLMCall).count()
total_agent_messages = db.query(AgentMessage).count()
total_agent_runs = db.query(AgentRun).count()
total_analyses = db.query(AIAnalysisResult).count()

print(f"   Toplam LLM Çağrısı: {total_llm_calls}")
print(f"   Toplam Agent Mesajı: {total_agent_messages}")
print(f"   Toplam Agent Run: {total_agent_runs}")
print(f"   Toplam Analiz: {total_analyses}")

if total_llm_calls == 0:
    print("\n   ⚠️ UYARI: Hiç LLM çağrısı kaydedilmemiş!")
    print("   Bu, AutoGen agent'ların LLM çağrılarını loglamadığı anlamına gelebilir.")
if total_agent_messages == 0:
    print("\n   ⚠️ UYARI: Hiç agent mesajı kaydedilmemiş!")
    print("   Bu, agent'ların mesajlarını kaydetmediği anlamına gelebilir.")

print()
print("=" * 70)

db.close()

