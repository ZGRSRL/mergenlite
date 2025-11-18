#!/usr/bin/env python3
"""
ZGR_AI Database Test
ZGR_AI veritabanını test eder
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_zgr_ai_database():
    """ZGR_AI veritabanını test et"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'ZGR_AI',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔍 ZGR_AI Database Test")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        print("✅ ZGR_AI database bağlantısı başarılı!")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # 1. List all tables
            print("\n📋 ZGR_AI Tabloları:")
            print("-" * 30)
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            for table in tables:
                cur.execute(f"SELECT COUNT(*) as count FROM {table['table_name']};")
                count = cur.fetchone()
                print(f"  • {table['table_name']}: {count['count']} kayıt")
            
            # 2. Test opportunities table
            print("\n🎯 Opportunities Test:")
            print("-" * 30)
            cur.execute("SELECT * FROM opportunities LIMIT 3;")
            opps = cur.fetchall()
            
            for opp in opps:
                print(f"  • {opp['title']} ({opp['opportunity_id']})")
                print(f"    Posted: {opp['posted_date']}")
                print(f"    Deadline: {opp['response_dead_line']}")
                print()
            
            # 3. Test manual_documents table
            print("\n📄 Manual Documents Test:")
            print("-" * 30)
            cur.execute("SELECT * FROM manual_documents LIMIT 3;")
            docs = cur.fetchall()
            
            for doc in docs:
                print(f"  • {doc['title']} ({doc['file_type']})")
                print(f"    Size: {doc['file_size']} bytes")
                print(f"    Status: {doc['analysis_status']}")
                print()
            
            # 4. Test past_performance table
            print("\n🏆 Past Performance Test:")
            print("-" * 30)
            cur.execute("SELECT * FROM past_performance LIMIT 3;")
            perfs = cur.fetchall()
            
            for perf in perfs:
                print(f"  • {perf['title']}")
                print(f"    Client: {perf['client']}")
                print(f"    Value: ${perf['value']:,.2f}" if perf['value'] else "    Value: N/A")
                print()
            
            # 5. Test keywords table
            print("\n🔑 Keywords Test:")
            print("-" * 30)
            cur.execute("SELECT * FROM keywords LIMIT 5;")
            keywords = cur.fetchall()
            
            for kw in keywords:
                print(f"  • {kw['keyword']} (Priority: {kw.get('priority', 'N/A')})")
            
            # 6. Test opportunity_docs table
            print("\n📎 Opportunity Docs Test:")
            print("-" * 30)
            cur.execute("SELECT * FROM opportunity_docs LIMIT 3;")
            opp_docs = cur.fetchall()
            
            for doc in opp_docs:
                print(f"  • {doc['document_name']}")
                print(f"    URL: {doc['document_url']}")
                print(f"    Processed: {doc['processed']}")
                print()
            
            # 7. Database statistics
            print("\n📊 Database Statistics:")
            print("-" * 30)
            
            # Total opportunities
            cur.execute("SELECT COUNT(*) as count FROM opportunities;")
            total_opps = cur.fetchone()
            print(f"  • Total Opportunities: {total_opps['count']}")
            
            # Recent opportunities (last 30 days)
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM opportunities 
                WHERE posted_date >= CURRENT_DATE - INTERVAL '30 days';
            """)
            recent_opps = cur.fetchone()
            print(f"  • Recent Opportunities (30 days): {recent_opps['count']}")
            
            # Manual documents
            cur.execute("SELECT COUNT(*) as count FROM manual_documents;")
            total_docs = cur.fetchone()
            print(f"  • Manual Documents: {total_docs['count']}")
            
            # Past performance records
            cur.execute("SELECT COUNT(*) as count FROM past_performance;")
            total_perfs = cur.fetchone()
            print(f"  • Past Performance Records: {total_perfs['count']}")
            
            # Keywords
            cur.execute("SELECT COUNT(*) as count FROM keywords;")
            total_keywords = cur.fetchone()
            print(f"  • Keywords: {total_keywords['count']}")
        
        conn.close()
        print("\n✅ ZGR_AI database test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    test_zgr_ai_database()
