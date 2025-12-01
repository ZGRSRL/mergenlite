#!/usr/bin/env python3
"""Check autogen_agentchat available modules"""
import autogen_agentchat
import os
import pkgutil

print("autogen_agentchat path:", os.path.dirname(autogen_agentchat.__file__))
print("\nAvailable modules:")
for importer, modname, ispkg in pkgutil.iter_modules([os.path.dirname(autogen_agentchat.__file__)]):
    print(f"  {modname}")

