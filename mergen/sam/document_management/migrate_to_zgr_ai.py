#!/usr/bin/env python3
"""
SAM to ZGR_AI Database Migration Script
SAM veritabanından ZGR_AI veritabanına tabloları ve verileri kopyalar
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_sam_to_zgr_ai():
    """SAM veritabanından ZGR_AI veritabanına migrasyon"""
    
    # Database connection parameters
    sam_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'sam',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    zgr_ai_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'ZGR_AI',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔄 SAM to ZGR_AI Database Migration")
    print("=" * 60)
    
    try:
        # Connect to both databases
        sam_conn = psycopg2.connect(**sam_params)
        zgr_ai_conn = psycopg2.connect(**zgr_ai_params)
        
        print("✅ Database bağlantıları başarılı!")
        
        with sam_conn.cursor(cursor_factory=RealDictCursor) as sam_cur, \
             zgr_ai_conn.cursor(cursor_factory=RealDictCursor) as zgr_cur:
            
            # 1. Enable extensions in ZGR_AI
            print("\n🔧 Extensions etkinleştiriliyor...")
            zgr_cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            zgr_ai_conn.commit()
            print("✅ Extensions etkinleştirildi")
            
            # 2. Get all tables from SAM database
            print("\n📋 SAM tabloları listeleniyor...")
            sam_cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            sam_tables = sam_cur.fetchall()
            
            print(f"📊 SAM'de {len(sam_tables)} tablo bulundu:")
            for table in sam_tables:
                print(f"  • {table['table_name']}")
            
            # 3. Copy table structures and data
            tables_to_copy = [
                'opportunities',
                'manual_documents', 
                'document_analysis_results',
                'requirements',
                'evidence',
                'facility_features',
                'pricing_items',
                'past_performance',
                'vector_chunks',
                'documents',
                'opportunity_docs',
                'keywords',
                'naics_psc_filters',
                'proposal_templates',
                'sam_subcontracts'
            ]
            
            print(f"\n🔄 {len(tables_to_copy)} tablo kopyalanıyor...")
            
            for table_name in tables_to_copy:
                try:
                    print(f"\n📋 {table_name} tablosu işleniyor...")
                    
                    # Check if table exists in SAM
                    sam_cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, (table_name,))
                    exists = sam_cur.fetchone()
                    
                    if not exists['exists']:
                        print(f"  ⚠️ {table_name} SAM'de bulunamadı, atlanıyor")
                        continue
                    
                    # Get table structure
                    sam_cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position;
                    """, (table_name,))
                    columns = sam_cur.fetchall()
                    
                    if not columns:
                        print(f"  ⚠️ {table_name} kolonları bulunamadı")
                        continue
                    
                    # Create table in ZGR_AI
                    column_definitions = []
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        column_definitions.append(f"{col['column_name']} {col['data_type']} {nullable}{default}")
                    
                    create_table_sql = f"""
                        DROP TABLE IF EXISTS {table_name};
                        CREATE TABLE {table_name} (
                            {', '.join(column_definitions)}
                        );
                    """
                    
                    zgr_cur.execute(create_table_sql)
                    print(f"  ✅ {table_name} tablosu oluşturuldu")
                    
                    # Copy data
                    sam_cur.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                    count = sam_cur.fetchone()
                    
                    if count['count'] > 0:
                        sam_cur.execute(f"SELECT * FROM {table_name};")
                        rows = sam_cur.fetchall()
                        
                        if rows:
                            # Get column names
                            column_names = [col['column_name'] for col in columns]
                            
                            # Insert data
                            for row in rows:
                                values = []
                                for col_name in column_names:
                                    values.append(row.get(col_name))
                                
                                placeholders = ', '.join(['%s'] * len(values))
                                insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders});"
                                zgr_cur.execute(insert_sql, values)
                            
                            print(f"  ✅ {count['count']} kayıt kopyalandı")
                    else:
                        print(f"  ℹ️ {table_name} tablosunda veri yok")
                    
                except Exception as e:
                    print(f"  ❌ {table_name} hatası: {e}")
                    continue
            
            # 4. Create additional ZGR_AI specific tables
            print(f"\n🏗️ ZGR_AI özel tabloları oluşturuluyor...")
            
            # AI Analysis Results table
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_analysis_results (
                    id SERIAL PRIMARY KEY,
                    opportunity_id VARCHAR(255) NOT NULL,
                    analysis_type VARCHAR(100) NOT NULL,
                    result JSONB NOT NULL,
                    confidence FLOAT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # User Sessions table
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    page VARCHAR(100),
                    action VARCHAR(100),
                    data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # System Metrics table
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metric_unit VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            print("✅ ZGR_AI özel tabloları oluşturuldu")
            
            # 5. Create indexes
            print(f"\n🔍 Index'ler oluşturuluyor...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_opportunities_posted_date ON opportunities(posted_date);",
                "CREATE INDEX IF NOT EXISTS idx_manual_documents_notice_id ON manual_documents(notice_id);",
                "CREATE INDEX IF NOT EXISTS idx_requirements_rfq_id ON requirements(rfq_id);",
                "CREATE INDEX IF NOT EXISTS idx_evidence_requirement_id ON evidence(requirement_id);",
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_opportunity_id ON ai_analysis_results(opportunity_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);"
            ]
            
            for index_sql in indexes:
                try:
                    zgr_cur.execute(index_sql)
                    print(f"  ✅ Index oluşturuldu")
                except Exception as e:
                    print(f"  ⚠️ Index hatası: {e}")
            
            # Commit all changes
            zgr_ai_conn.commit()
            print("\n✅ Tüm değişiklikler kaydedildi!")
            
            # 6. Show final summary
            print(f"\n📊 ZGR_AI Veritabanı Özeti:")
            print("-" * 40)
            
            zgr_cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            zgr_tables = zgr_cur.fetchall()
            
            print(f"📋 Toplam {len(zgr_tables)} tablo:")
            for table in zgr_tables:
                zgr_cur.execute(f"SELECT COUNT(*) as count FROM {table['table_name']};")
                count = zgr_cur.fetchone()
                print(f"  • {table['table_name']}: {count['count']} kayıt")
        
        # Close connections
        sam_conn.close()
        zgr_ai_conn.close()
        
        print(f"\n🎉 SAM to ZGR_AI migration tamamlandı!")
        print(f"📊 ZGR_AI veritabanı hazır!")
        
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        if 'sam_conn' in locals():
            sam_conn.close()
        if 'zgr_ai_conn' in locals():
            zgr_ai_conn.close()

if __name__ == "__main__":
    migrate_sam_to_zgr_ai()
