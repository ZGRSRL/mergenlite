#!/usr/bin/env python3
"""Check current database schema"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)

print("=" * 60)
print("OPPORTUNITIES TABLE SCHEMA")
print("=" * 60)

try:
    columns = inspector.get_columns('opportunities')
    print(f"\nTotal columns: {len(columns)}\n")
    
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col.get('default') else ""
        print(f"  {col['name']:30} {str(col['type']):30} {nullable}{default}")
    
    # Check primary key
    pk_constraint = inspector.get_pk_constraint('opportunities')
    print(f"\nPrimary Key: {pk_constraint.get('constrained_columns', [])}")
    
    # Check indexes
    indexes = inspector.get_indexes('opportunities')
    print(f"\nIndexes ({len(indexes)}):")
    for idx in indexes:
        print(f"  {idx['name']}: {idx['column_names']}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

