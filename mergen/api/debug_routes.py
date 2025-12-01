
import sys
import os
from pathlib import Path

# Add the current directory to sys.path to make imports work
current_dir = Path("d:/Mergenlite/mergen/api")
sys.path.insert(0, str(current_dir))

try:
    from app.main import app
    print("App title:", app.title)
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Route: {route.path}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
