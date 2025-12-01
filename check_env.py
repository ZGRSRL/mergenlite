
import os
from pathlib import Path

def check_env():
    env_path = Path("d:/Mergenlite/mergen/.env")
    if not env_path.exists():
        print("No .env file found at", env_path)
        return

    print(f"--- Checking {env_path} ---")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            key, value = line.split("=", 1) if "=" in line else (line, "")
            key = key.strip()
            value = value.strip()
            
            if "PASSWORD" in key or "SECRET" in key or "KEY" in key:
                print(f"{key}=***")
            else:
                print(f"{key}={value}")

if __name__ == "__main__":
    check_env()
