
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
import logging

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Fix 'app' import
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

from mergen.api.app.config import settings

def reset_version():
    target_rev = "35fa6f5a770b"
    print(f"Resetting alembic version to: {target_rev}")
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{target_rev}')"))
        conn.commit()
    
    print("✅ Version reset complete.")

if __name__ == "__main__":
    reset_version()
