#!/usr/bin/env python3
"""Check DATA_DIR configuration."""
from app.services.attachment_service import BASE_DATA_DIR
import os

print(f"BASE_DATA_DIR: {BASE_DATA_DIR}")
print(f"DATA_DIR env: {os.getenv('DATA_DIR', 'not set')}")
print(f"BASE_DATA_DIR exists: {BASE_DATA_DIR.exists()}")

# Check if attachments directory would be created
test_path = BASE_DATA_DIR / "opportunities" / "97c450b7d3554a738d0d4de07ffa0e0a" / "attachments"
print(f"Test attachments path: {test_path}")
print(f"Test path exists: {test_path.exists()}")

