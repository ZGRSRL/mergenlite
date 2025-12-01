#!/usr/bin/env python3
"""Test AutoGen imports"""
print("Testing autogen import...")
try:
    from autogen import AssistantAgent
    print("✓ autogen import: SUCCESS")
    autogen_works = True
except Exception as e:
    print(f"✗ autogen import: FAILED - {e}")
    autogen_works = False

print("\nTesting autogen_agentchat import...")
try:
    from autogen_agentchat.agents import AssistantAgent
    print("✓ autogen_agentchat import: SUCCESS")
    agentchat_works = True
except Exception as e:
    print(f"✗ autogen_agentchat import: FAILED - {e}")
    agentchat_works = False

print(f"\nResult: autogen={autogen_works}, autogen_agentchat={agentchat_works}")

