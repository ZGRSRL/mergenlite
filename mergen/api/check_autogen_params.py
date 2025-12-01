#!/usr/bin/env python3
"""Check AutoGen AssistantAgent parameters"""
try:
    from autogen import AssistantAgent
    import inspect
    sig = inspect.signature(AssistantAgent.__init__)
    print("AssistantAgent parameters:")
    for param in sig.parameters.values():
        print(f"  {param.name}: {param.kind}")
except Exception as e:
    print(f"Error: {e}")
    try:
        from autogen_agentchat.agents import AssistantAgent
        import inspect
        sig = inspect.signature(AssistantAgent.__init__)
        print("\nUsing autogen_agentchat.agents.AssistantAgent:")
        for param in sig.parameters.values():
            print(f"  {param.name}: {param.kind}")
    except Exception as e2:
        print(f"Error with autogen_agentchat: {e2}")

