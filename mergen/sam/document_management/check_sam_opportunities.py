#!/usr/bin/env python3
"""
Check SAM Opportunities Table
SAM opportunities tablosunun yapısını kontrol eder
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_sam_opportunities():
    """SAM opportunities tablosunun yapısını kontrol et"""
    
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'sam',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print('📋 SAM OPPORTUNITIES Table Structure:')
            print('-' * 40)
            cur.execute('SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position;', ('opportunities',))
            columns = cur.fetchall()
            for col in columns:
                nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
                print(f'  • {col["column_name"]}: {col["data_type"]} ({nullable})')
            
            # Show sample record
            cur.execute('SELECT * FROM opportunities LIMIT 1;')
            sample = cur.fetchone()
            if sample:
                print('\n📄 Sample Record:')
                for key, value in sample.items():
                    print(f'  • {key}: {value}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Hata: {e}')

if __name__ == "__main__":
    check_sam_opportunities()
