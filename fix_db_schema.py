
from sqlalchemy import create_engine, text, inspect
from mergenlite_models import Base, Hotel, EmailLog
import os
from dotenv import load_dotenv

# Load env
env_paths = ['mergen/.env', 'mergenlite/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"Loaded .env from {env_path}")
        break

def get_engine():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'mergenlite')
    
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Connecting to: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    return create_engine(url)

def fix_schema():
    engine = get_engine()
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # 1. Check/Add status column to opportunities
        columns = [c['name'] for c in inspector.get_columns('opportunities')]
        if 'status' not in columns:
            print("Adding 'status' column to opportunities...")
            conn.execute(text("ALTER TABLE opportunities ADD COLUMN status VARCHAR(50) DEFAULT 'active'"))
            print("✅ 'status' column added.")
        else:
            print("ℹ️ 'status' column already exists.")

        # 2. Check/Add agency, office, description if missing (just in case)
        if 'agency' not in columns:
            print("Adding 'agency' column...")
            conn.execute(text("ALTER TABLE opportunities ADD COLUMN agency VARCHAR(255)"))
        if 'office' not in columns:
             print("Adding 'office' column...")
             conn.execute(text("ALTER TABLE opportunities ADD COLUMN office VARCHAR(255)"))
        if 'description' not in columns:
             print("Adding 'description' column...")
             conn.execute(text("ALTER TABLE opportunities ADD COLUMN description TEXT"))

        # 3. Create missing tables (Hotel, EmailLog)
        existing_tables = inspector.get_table_names()
        
        if 'hotels' not in existing_tables:
            print("Creating 'hotels' table...")
            Hotel.__table__.create(engine)
            print("✅ 'hotels' table created.")
        else:
            print("ℹ️ 'hotels' table already exists.")
            
        if 'email_log' not in existing_tables:
            print("Creating 'email_log' table...")
            EmailLog.__table__.create(engine)
            print("✅ 'email_log' table created.")
        else:
             print("ℹ️ 'email_log' table already exists.")

if __name__ == "__main__":
    try:
        fix_schema()
        print("\n✅ Database schema fixed successfully!")
    except Exception as e:
        print(f"\n❌ Error fixing schema: {e}")
