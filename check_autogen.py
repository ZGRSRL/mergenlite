#!/usr/bin/env python3
"""Check AutoGen installation and compatibility"""
import sys

print("=== AutoGen Compatibility Check ===\n")

# 1. Check autogen version
try:
    import autogen
    try:
        version = autogen.__version__
        print(f"1. autogen version: {version}")
    except AttributeError:
        print("1. autogen version: (__version__ not found)")
    print("   [OK] autogen imported successfully")
except ImportError as e:
    print(f"1. autogen import error: {e}")
    sys.exit(1)

# 2. Check imports
try:
    from autogen import AssistantAgent, UserProxyAgent
    print("2. [OK] from autogen import AssistantAgent, UserProxyAgent")
except ImportError as e:
    print(f"2. [X] Import error: {e}")
    sys.exit(1)

# 3. Check autogen_agentchat
try:
    from autogen_agentchat.agents import AssistantAgent as NewAssistantAgent
    print("3. [INFO] autogen_agentchat available")
except ImportError:
    print("3. [INFO] autogen_agentchat not available")

# 4. Check AssistantAgent parameters
try:
    from autogen import AssistantAgent
    import inspect
    sig = inspect.signature(AssistantAgent.__init__)
    print("\n4. AssistantAgent.__init__ parameters:")
    for param_name, param in sig.parameters.items():
        if param_name != 'self':
            print(f"   {param_name}: {param.kind}")
except Exception as e:
    print(f"4. [ERROR] Could not inspect AssistantAgent: {e}")

# 5. Check API key
import os
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"\n5. [OK] OPENAI_API_KEY present (first 10 chars: {api_key[:10]}...)")
else:
    print("\n5. [X] OPENAI_API_KEY not found")

# 6. Test AssistantAgent creation
print("\n6. Testing AssistantAgent creation...")
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("   [SKIP] No API key, skipping test")
    else:
        llm_config = {
            "config_list": [{
                "model": "gpt-4o-mini",
                "api_key": api_key,
            }],
            "temperature": 0.2,
        }
        
        # Try with llm_config
        try:
            agent = AssistantAgent(
                name="TestAgent",
                system_message="Test",
                llm_config=llm_config,
            )
            print("   [OK] AssistantAgent created with llm_config")
        except TypeError as e:
            print(f"   [X] llm_config failed: {e}")
            # Try without tools
            try:
                agent = AssistantAgent(
                    name="TestAgent",
                    system_message="Test",
                    llm_config=llm_config,
                )
                print("   [OK] AssistantAgent created (retry)")
            except Exception as e2:
                print(f"   [X] Retry failed: {e2}")
except Exception as e:
    print(f"   [ERROR] Test failed: {e}")

print("\n=== Check Complete ===")
