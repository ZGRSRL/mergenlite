#!/usr/bin/env python3
"""
MergenLite Veritabanı Oluşturma Scripti
Sadeleştirilmiş 4 tabloluk veritabanı şemasını oluşturur
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor
import sys
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Database connection parameters
# Not: Docker içinde 'db' host'u kullanılır, local'de 'localhost'
db_host = os.getenv('DB_HOST', 'localhost')
if db_host == 'db':
    # Docker host'u algılanırsa, local için localhost'a geç
    db_host = 'localhost'

DB_CONFIG = {
    'host': db_host,
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': 'mergenlite'  # MergenLite database
}

def create_database_if_not_exists():
    """MergenLite database'ini oluştur (eğer yoksa)"""
    # Önce postgres database'ine bağlan
    postgres_config = DB_CONFIG.copy()
    postgres_config['database'] = 'postgres'
    
    try:
        conn = psycopg2.connect(**postgres_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Database'in var olup olmadığını kontrol et
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'mergenlite'")
        exists = cursor.fetchone()
        
        if not exists:
            print("[INFO] MergenLite database'i olusturuluyor...")
            cursor.execute('CREATE DATABASE mergenlite')
            print("[OK] MergenLite database'i olusturuldu")
        else:
            print("[INFO] MergenLite database'i zaten mevcut")
        
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"[ERROR] Database olusturma hatasi: {e}")
        return False

def create_tables():
    """MergenLite tablolarını oluştur"""
    try:
        # MergenLite database'ine bağlan
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("[INFO] MergenLite Veritabani Semasi Olusturuluyor")
        print("="*60)
        
        # SQL dosyasını oku ve çalıştır
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_mergenlite_schema.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"[ERROR] SQL dosyasi bulunamadi: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL komutlarını çalıştır
        print("\n[INFO] SQL semasi calistiriliyor...")
        cursor.execute(sql_content)
        conn.commit()
        
        print("\n[OK] Tum tablolar basariyla olusturuldu!")
        
        # Tabloları listele
        print("\n[TABLES] Olusturulan Tablolar:")
        print("-" * 60)
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  [OK] {table[0]}")
        
        # Index'leri listele
        print("\n[INDEXES] Olusturulan Index'ler:")
        print("-" * 60)
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  [OK] {idx[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("[OK] MergenLite veritabani semasi basariyla olusturuldu!")
        print("="*60)
        return True
        
    except psycopg2.Error as e:
        print(f"\n[ERROR] Veritabani hatasi: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables():
    """Tabloların doğru oluşturulduğunu doğrula"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        expected_tables = ['opportunities', 'manual_documents', 'ai_analysis_results', 'system_sessions']
        
        print("\n[VERIFY] Tablo Dogrulamasi:")
        print("-" * 60)
        
        for table in expected_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                # Kolon sayısını al
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}';
                """)
                col_count = cursor.fetchone()[0]
                print(f"  [OK] {table:30} ({col_count} kolon)")
            else:
                print(f"  [ERROR] {table:30} BULUNAMADI!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Dogrulama hatasi: {e}")
        return False

if __name__ == "__main__":
    print("[START] MergenLite Veritabani Kurulumu Baslatiliyor...")
    print("="*60)
    
    # 1. Database'i oluştur
    if not create_database_if_not_exists():
        print("\n[ERROR] Database olusturulamadi. Cikiliyor...")
        sys.exit(1)
    
    # 2. Tabloları oluştur
    if not create_tables():
        print("\n[ERROR] Tablolar olusturulamadi. Cikiliyor...")
        sys.exit(1)
    
    # 3. Doğrula
    verify_tables()
    
    print("\n[SUCCESS] MergenLite veritabani kurulumu tamamlandi!")
    print("\n[NEXT] Sonraki Adimlar:")
    print("  1. Veritabani baglantisini test edin")
    print("  2. Sadelestirilmis ajan mimarisini olusturun")
    print("  3. Streamlit uygulamasini guncelleyin")

