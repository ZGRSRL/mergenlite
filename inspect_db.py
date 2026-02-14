import os
import sys
from sqlalchemy import inspect
from dotenv import load_dotenv

# Path ayarı
sys.path.append(os.getcwd())

# Access internal engine from backend_utils
import backend_utils
backend_utils._initialize_db_engine()
engine = backend_utils._db_engine

def inspect_table():
    inspector = inspect(engine)
    table_name = "ai_analysis_results"
    
    if hasattr(inspector, "has_table") and inspector.has_table(table_name):
        print(f"Table '{table_name}' exists.")
        columns = inspector.get_columns(table_name)
        print(f"Columns in '{table_name}':")
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
    else:
        try:
             columns = inspector.get_columns(table_name)
             print(f"Table '{table_name}' columns:")
             for column in columns:
                print(f"- {column['name']} ({column['type']})")
        except Exception as e:
            print(f"Error inspecting table: {e}")
            print("Existing tables:", inspector.get_table_names())

if __name__ == "__main__":
    inspect_table()
