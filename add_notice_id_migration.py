#!/usr/bin/env python3
"""
Veritabanı Migration: notice_id ve solicitation_number alanlarını ekle
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# .env yükle
env_paths = ['mergen/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        break
else:
    load_dotenv(override=True)

# Veritabanı bağlantısı
db_host = os.getenv('DB_HOST', 'localhost')
if db_host == 'db':
    db_host = 'localhost'

DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{db_host}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'mergenlite')}"

def run_migration():
    """Migration çalıştır"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Transaction başlat
        trans = conn.begin()
        
        try:
            # 1. notice_id alanını ekle (eğer yoksa)
            print("📝 notice_id alanı ekleniyor...")
            conn.execute(text("""
                ALTER TABLE opportunities 
                ADD COLUMN IF NOT EXISTS notice_id VARCHAR(100);
            """))
            
            # 2. solicitation_number alanını ekle (eğer yoksa)
            print("📝 solicitation_number alanı ekleniyor...")
            conn.execute(text("""
                ALTER TABLE opportunities 
                ADD COLUMN IF NOT EXISTS solicitation_number VARCHAR(100);
            """))
            
            # 3. Index'leri ekle
            print("📝 Index'ler ekleniyor...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_notice_id 
                ON opportunities(notice_id);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_opportunities_solicitation_number 
                ON opportunities(solicitation_number);
            """))
            
            # 4. Mevcut verileri güncelle (raw_data'dan noticeId çek)
            print("📝 Mevcut veriler güncelleniyor...")
            conn.execute(text("""
                UPDATE opportunities 
                SET notice_id = COALESCE(
                    raw_data->>'noticeId',
                    raw_data->>'solicitationNumber',
                    notice_id
                ),
                solicitation_number = COALESCE(
                    raw_data->>'solicitationNumber',
                    raw_data->>'noticeId',
                    solicitation_number
                )
                WHERE notice_id IS NULL 
                   OR solicitation_number IS NULL;
            """))
            
            # Commit
            trans.commit()
            print("✅ Migration başarıyla tamamlandı!")
            
            # İstatistikler
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(notice_id) as with_notice_id,
                    COUNT(solicitation_number) as with_solicitation_number
                FROM opportunities;
            """))
            
            stats = result.fetchone()
            print(f"\n📊 İstatistikler:")
            print(f"   Toplam kayıt: {stats[0]}")
            print(f"   notice_id olan: {stats[1]}")
            print(f"   solicitation_number olan: {stats[2]}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration hatası: {e}")
            raise

if __name__ == "__main__":
    # Windows encoding fix
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    
    print("Veritabani Migration Baslatiliyor...")
    print("=" * 60)
    run_migration()
    print("=" * 60)
    print("Tamamlandi!")

