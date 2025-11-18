#!/usr/bin/env python3
"""
Check Documents Table Structure
Documents tablosunun yapısını kontrol eder
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_documents_table():
    """Documents tablosunun yapısını kontrol et"""
    
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'sam'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print('📋 DOCUMENTS Table Structure:')
            print('-' * 40)
            cur.execute('SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position;', ('documents',))
            columns = cur.fetchall()
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == "YES" else "NOT NULL"
                print(f'  • {col["column_name"]}: {col["data_type"]} ({nullable})')
            
            # Count records
            cur.execute('SELECT COUNT(*) as count FROM documents;')
            count = cur.fetchone()
            print(f'  📊 Total records: {count["count"]}')
            
            # Show sample records
            cur.execute('SELECT * FROM documents LIMIT 3;')
            samples = cur.fetchall()
            if samples:
                print('\n📄 Sample Records:')
                for sample in samples:
                    print(f'  • ID: {sample["id"]}, Title: {sample.get("title", "N/A")}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Hata: {e}')

if __name__ == "__main__":
    check_documents_table()
