import os
from pathlib import Path

# Load .env
from dotenv import load_dotenv
project_root = Path(__file__).parent
mergen_env_path = project_root / "mergen" / ".env"
load_dotenv(mergen_env_path, override=True)

# Check what we get
print("=== Environment Variables ===")
print(f"SMTP_HOST: {os.getenv('SMTP_HOST')}")
print(f"SMTP_USERNAME: {os.getenv('SMTP_USERNAME')}")
print(f"SMTP_FROM_EMAIL: {os.getenv('SMTP_FROM_EMAIL')}")
print(f"PIPELINE_NOTIFICATION_EMAIL: {os.getenv('PIPELINE_NOTIFICATION_EMAIL')}")
print(f"pipeline_notification_email: {os.getenv('pipeline_notification_email')}")

# Check settings
from mergen.api.app.config import settings
print("\n=== Settings Object ===")
print(f"smtp_host: {settings.smtp_host}")
print(f"smtp_username: {settings.smtp_username}")
print(f"smtp_from_email: {settings.smtp_from_email}")
print(f"pipeline_notification_email: {settings.pipeline_notification_email}")
