
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

from mergen.api.app.config import settings

def find_deps():
    print(f"Connecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    table_names = inspector.get_table_names()
    print(f"Scanning {len(table_names)} tables for FK dependencies on 'opportunities'...")
    
    deps = []
    for table in table_names:
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            if fk['referred_table'] == 'opportunities':
                print(f"Found dependency: {table} -> {fk['referred_columns']} (FK: {fk['name']})")
                deps.append(table)
                
    print(f"\nTables dependent on opportunities: {list(set(deps))}")

if __name__ == "__main__":
    find_deps()
