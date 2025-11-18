#!/usr/bin/env python3
"""
Check Database Table Structures
Mevcut tablo yapılarını kontrol eder
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_structures():
    """Mevcut tablo yapılarını kontrol et"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'sam'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔍 Database Tablo Yapıları")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        print("✅ Database bağlantısı başarılı!")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check table structures
            tables = ['requirements', 'evidence', 'facility_features', 'pricing_items', 'past_performance', 'vector_chunks']
            
            for table in tables:
                print(f"\n📋 {table.upper()} Table Structure:")
                print("-" * 40)
                
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table,))
                exists = cur.fetchone()
                
                if exists['exists']:
                    # Get column information
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position;
                    """, (table,))
                    columns = cur.fetchall()
                    
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"  • {col['column_name']}: {col['data_type']} ({nullable}){default}")
                    
                    # Count records
                    cur.execute(f"SELECT COUNT(*) as count FROM {table};")
                    count = cur.fetchone()
                    print(f"  📊 Total records: {count['count']}")
                    
                else:
                    print(f"  ❌ Table does not exist")
        
        conn.close()
        print("\n✅ Tablo yapıları kontrol edildi!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    check_table_structures()
