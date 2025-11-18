#!/usr/bin/env python3
"""
Correct SAM to ZGR_AI Migration
Doğru tablo yapılarına göre migration
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def correct_migration():
    """Doğru migration işlemi"""
    
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
    
    print("🔄 Correct SAM to ZGR_AI Migration")
    print("=" * 50)
    
    try:
        # Connect to both databases
        sam_conn = psycopg2.connect(**sam_params)
        zgr_ai_conn = psycopg2.connect(**zgr_ai_params)
        
        print("✅ Database bağlantıları başarılı!")
        
        with sam_conn.cursor(cursor_factory=RealDictCursor) as sam_cur, \
             zgr_ai_conn.cursor(cursor_factory=RealDictCursor) as zgr_cur:
            
            # Enable extensions
            zgr_cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            zgr_ai_conn.commit()
            
            # 1. Create opportunities table (SAM yapısına göre)
            print("\n📋 Opportunities tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id SERIAL PRIMARY KEY,
                    opportunity_id VARCHAR(255) UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    posted_date TIMESTAMP,
                    response_dead_line TIMESTAMP,
                    classification_code VARCHAR(50),
                    naics_code VARCHAR(50),
                    set_aside VARCHAR(100),
                    contract_type VARCHAR(100),
                    place_of_performance TEXT,
                    organization_type VARCHAR(100),
                    point_of_contact TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy opportunities data
            sam_cur.execute("SELECT * FROM opportunities LIMIT 100;")
            opps = sam_cur.fetchall()
            
            for opp in opps:
                zgr_cur.execute("""
                    INSERT INTO opportunities (opportunity_id, title, description, posted_date, response_dead_line, 
                                             classification_code, naics_code, set_aside, contract_type, 
                                             place_of_performance, organization_type, point_of_contact, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (opportunity_id) DO NOTHING;
                """, (
                    opp.get('opportunity_id'),
                    opp.get('title'),
                    opp.get('description'),
                    opp.get('posted_date'),
                    opp.get('response_dead_line'),
                    opp.get('classification_code'),
                    opp.get('naics_code'),
                    opp.get('set_aside'),
                    opp.get('contract_type'),
                    opp.get('place_of_performance'),
                    opp.get('organization_type'),
                    opp.get('point_of_contact'),
                    opp.get('created_at'),
                    opp.get('updated_at')
                ))
            
            print(f"✅ {len(opps)} opportunity kopyalandı")
            
            # 2. Create manual_documents table
            print("\n📄 Manual Documents tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS manual_documents (
                    id VARCHAR(255) PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    file_path VARCHAR(1000) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_size BIGINT NOT NULL,
                    upload_date TIMESTAMP NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    tags TEXT,
                    notice_id VARCHAR(255),
                    opportunity_title VARCHAR(500),
                    analysis_status VARCHAR(50) DEFAULT 'pending',
                    analysis_results JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy manual_documents data
            sam_cur.execute("SELECT * FROM manual_documents;")
            docs = sam_cur.fetchall()
            
            for doc in docs:
                zgr_cur.execute("""
                    INSERT INTO manual_documents (id, title, description, file_path, file_type, file_size, 
                                                upload_date, source, tags, notice_id, opportunity_title, 
                                                analysis_status, analysis_results, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (
                    doc.get('id'),
                    doc.get('title'),
                    doc.get('description'),
                    doc.get('file_path'),
                    doc.get('file_type'),
                    doc.get('file_size'),
                    doc.get('upload_date'),
                    doc.get('source'),
                    str(doc.get('tags', [])),  # Convert array to string
                    doc.get('notice_id'),
                    doc.get('opportunity_title'),
                    doc.get('analysis_status'),
                    Json(doc.get('analysis_results')) if doc.get('analysis_results') else None,
                    doc.get('created_at'),
                    doc.get('updated_at')
                ))
            
            print(f"✅ {len(docs)} manual document kopyalandı")
            
            # 3. Create requirements table
            print("\n📋 Requirements tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS requirements (
                    id SERIAL PRIMARY KEY,
                    rfq_id INTEGER NOT NULL,
                    code VARCHAR(20) NOT NULL,
                    text TEXT NOT NULL,
                    category VARCHAR(50),
                    priority VARCHAR(20) DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy requirements data
            sam_cur.execute("SELECT * FROM requirements;")
            reqs = sam_cur.fetchall()
            
            for req in reqs:
                zgr_cur.execute("""
                    INSERT INTO requirements (rfq_id, code, text, category, priority, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    req.get('rfq_id'),
                    req.get('code'),
                    req.get('text'),
                    req.get('category'),
                    req.get('priority'),
                    req.get('created_at')
                ))
            
            print(f"✅ {len(reqs)} requirement kopyalandı")
            
            # 4. Create evidence table
            print("\n🔍 Evidence tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id SERIAL PRIMARY KEY,
                    requirement_id INTEGER NOT NULL,
                    source_doc_id INTEGER NOT NULL,
                    snippet TEXT NOT NULL,
                    score FLOAT DEFAULT 0.0,
                    evidence_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy evidence data
            sam_cur.execute("SELECT * FROM evidence;")
            evids = sam_cur.fetchall()
            
            for evid in evids:
                zgr_cur.execute("""
                    INSERT INTO evidence (requirement_id, source_doc_id, snippet, score, evidence_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    evid.get('requirement_id'),
                    evid.get('source_doc_id'),
                    evid.get('snippet'),
                    evid.get('score'),
                    evid.get('evidence_type'),
                    evid.get('created_at')
                ))
            
            print(f"✅ {len(evids)} evidence kopyalandı")
            
            # 5. Create facility_features table
            print("\n🏢 Facility Features tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS facility_features (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    value TEXT,
                    source_doc_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy facility_features data
            sam_cur.execute("SELECT * FROM facility_features;")
            features = sam_cur.fetchall()
            
            for feature in features:
                zgr_cur.execute("""
                    INSERT INTO facility_features (name, value, source_doc_id, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    feature.get('name'),
                    feature.get('value'),
                    feature.get('source_doc_id'),
                    feature.get('created_at')
                ))
            
            print(f"✅ {len(features)} facility feature kopyalandı")
            
            # 6. Create pricing_items table
            print("\n💰 Pricing Items tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS pricing_items (
                    id SERIAL PRIMARY KEY,
                    rfq_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    qty FLOAT DEFAULT 1.0,
                    unit VARCHAR(50),
                    unit_price FLOAT NOT NULL,
                    total_price FLOAT,
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy pricing_items data
            sam_cur.execute("SELECT * FROM pricing_items;")
            items = sam_cur.fetchall()
            
            for item in items:
                zgr_cur.execute("""
                    INSERT INTO pricing_items (rfq_id, name, description, qty, unit, unit_price, total_price, category, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    item.get('rfq_id'),
                    item.get('name'),
                    item.get('description'),
                    item.get('qty'),
                    item.get('unit'),
                    item.get('unit_price'),
                    item.get('total_price'),
                    item.get('category'),
                    item.get('created_at')
                ))
            
            print(f"✅ {len(items)} pricing item kopyalandı")
            
            # 7. Create past_performance table
            print("\n🏆 Past Performance tablosu oluşturuluyor...")
            zgr_cur.execute("""
                CREATE TABLE IF NOT EXISTS past_performance (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    client VARCHAR(255),
                    scope TEXT,
                    period VARCHAR(100),
                    value FLOAT,
                    ref_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Copy past_performance data
            sam_cur.execute("SELECT * FROM past_performance;")
            perfs = sam_cur.fetchall()
            
            for perf in perfs:
                zgr_cur.execute("""
                    INSERT INTO past_performance (title, client, scope, period, value, ref_info, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    perf.get('title'),
                    perf.get('client'),
                    perf.get('scope'),
                    perf.get('period'),
                    perf.get('value'),
                    Json(perf.get('ref_info')) if perf.get('ref_info') else None,
                    perf.get('created_at')
                ))
            
            print(f"✅ {len(perfs)} past performance kopyalandı")
            
            # 8. Create ZGR_AI specific tables
            print("\n🤖 ZGR_AI özel tabloları oluşturuluyor...")
            
            # AI Analysis Results
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
            
            # User Sessions
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
            
            # System Metrics
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
            
            # 9. Create indexes
            print("\n🔍 Index'ler oluşturuluyor...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_opportunities_posted_date ON opportunities(posted_date);",
                "CREATE INDEX IF NOT EXISTS idx_manual_documents_notice_id ON manual_documents(notice_id);",
                "CREATE INDEX IF NOT EXISTS idx_requirements_rfq_id ON requirements(rfq_id);",
                "CREATE INDEX IF NOT EXISTS idx_evidence_requirement_id ON evidence(requirement_id);",
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_opportunity_id ON ai_analysis_results(opportunity_id);"
            ]
            
            for index_sql in indexes:
                try:
                    zgr_cur.execute(index_sql)
                except Exception as e:
                    print(f"  ⚠️ Index hatası: {e}")
            
            print("✅ Index'ler oluşturuldu")
            
            # Commit all changes
            zgr_ai_conn.commit()
            
            # Show final summary
            print(f"\n📊 ZGR_AI Veritabanı Özeti:")
            print("-" * 40)
            
            zgr_cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            zgr_tables = zgr_cur.fetchall()
            
            for table in zgr_tables:
                zgr_cur.execute(f"SELECT COUNT(*) as count FROM {table['table_name']};")
                count = zgr_cur.fetchone()
                print(f"  • {table['table_name']}: {count['count']} kayıt")
        
        # Close connections
        sam_conn.close()
        zgr_ai_conn.close()
        
        print(f"\n🎉 SAM to ZGR_AI migration tamamlandı!")
        
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        if 'sam_conn' in locals():
            sam_conn.close()
        if 'zgr_ai_conn' in locals():
            zgr_ai_conn.close()

if __name__ == "__main__":
    correct_migration()
