#!/usr/bin/env python3
"""
Database Connection Test
PostgreSQL bağlantısını test eder ve tabloları kontrol eder
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Database bağlantısını test et"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'sam'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔍 Database Bağlantı Testi")
    print("=" * 50)
    print(f"Host: {db_params['host']}")
    print(f"Database: {db_params['database']}")
    print(f"User: {db_params['user']}")
    print(f"Port: {db_params['port']}")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        print("✅ Database bağlantısı başarılı!")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Test query
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"📊 PostgreSQL Version: {version['version']}")
            
            # List all tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            print(f"\n📋 Mevcut Tablolar ({len(tables)} adet):")
            print("-" * 30)
            
            if tables:
                for table in tables:
                    table_name = table['table_name']
                    print(f"• {table_name}")
                    
                    # Count records in each table
                    try:
                        cur.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                        count = cur.fetchone()
                        print(f"  └─ {count['count']} kayıt")
                    except Exception as e:
                        print(f"  └─ Kayıt sayısı alınamadı: {e}")
            else:
                print("❌ Hiç tablo bulunamadı!")
            
            # Check specific tables for SAM system
            sam_tables = [
                'opportunities',
                'manual_documents', 
                'document_analysis_results',
                'vector_chunks',
                'requirements',
                'evidence',
                'facility_features',
                'pricing_items',
                'past_performance'
            ]
            
            print(f"\n🎯 SAM Sistemi Tabloları:")
            print("-" * 30)
            
            for table_name in sam_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                exists = cur.fetchone()
                
                if exists['exists']:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                    count = cur.fetchone()
                    print(f"✅ {table_name}: {count['count']} kayıt")
                else:
                    print(f"❌ {table_name}: Tablo yok")
            
            # Check for sample data
            print(f"\n📊 Örnek Veriler:")
            print("-" * 30)
            
            # Check opportunities table
            if any(table['table_name'] == 'opportunities' for table in tables):
                cur.execute("SELECT * FROM opportunities LIMIT 3;")
                sample_opps = cur.fetchall()
                if sample_opps:
                    print("🎯 Opportunities örnekleri:")
                    for opp in sample_opps:
                        print(f"  • {opp.get('title', 'N/A')} ({opp.get('opportunity_id', 'N/A')})")
                else:
                    print("❌ Opportunities tablosunda veri yok")
            
            # Check manual_documents table
            if any(table['table_name'] == 'manual_documents' for table in tables):
                cur.execute("SELECT * FROM manual_documents LIMIT 3;")
                sample_docs = cur.fetchall()
                if sample_docs:
                    print("📄 Manual Documents örnekleri:")
                    for doc in sample_docs:
                        print(f"  • {doc.get('title', 'N/A')} ({doc.get('file_type', 'N/A')})")
                else:
                    print("❌ Manual Documents tablosunda veri yok")
        
        conn.close()
        print("\n✅ Database testi tamamlandı!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database bağlantı hatası: {e}")
        print("\n💡 Çözüm önerileri:")
        print("1. PostgreSQL servisinin çalıştığından emin olun")
        print("2. Database credentials'ları kontrol edin")
        print("3. Environment variables'ları ayarlayın:")
        print("   export DB_HOST=localhost")
        print("   export DB_NAME=sam")
        print("   export DB_USER=postgres")
        print("   export DB_PASSWORD=postgres")
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    test_database_connection()
