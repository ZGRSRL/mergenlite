#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database bağlantısını test et"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from mergenlite_models import Opportunity

# Windows encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# .env yükle
env_paths = ['mergen/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"✅ .env yüklendi: {env_path}")
        break
else:
    load_dotenv(override=True)
    print("⚠️ .env dosyası bulunamadı, environment variable'lardan yüklendi")

print("=" * 60)
print("Database Baglanti Testi")
print("=" * 60)

# Environment variable'ları kontrol et
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'mergenlite')

print(f"\n📋 Environment Variables:")
print(f"   DB_HOST: {db_host}")
print(f"   DB_USER: {db_user}")
print(f"   DB_PASSWORD: {'*' * len(db_password) if db_password else 'YOK'}")
print(f"   DB_PORT: {db_port}")
print(f"   DB_NAME: {db_name}")

# Eğer db_host 'db' ise, localhost'a çevir
if db_host == 'db':
    db_host = 'localhost'
    print(f"\n⚠️ DB_HOST='db' bulundu, 'localhost' olarak değiştirildi")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
print(f"\n🔗 Database URL: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

# Bağlantı testi
print(f"\n🔌 Bağlantı testi yapılıyor...")
try:
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    
    with engine.connect() as conn:
        # Basit sorgu
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL bağlantısı başarılı!")
        print(f"   PostgreSQL Version: {version[:50]}...")
        
        # Opportunities tablosunu kontrol et
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM opportunities;"))
            count = result.fetchone()[0]
            print(f"\n✅ 'opportunities' tablosu bulundu!")
            print(f"   Toplam kayıt: {count}")
            
            # Tablo yapısını kontrol et
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'opportunities'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            print(f"\n📋 Tablo yapısı ({len(columns)} kolon):")
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")
            
            # notice_id alanını kontrol et
            has_notice_id = any(col[0] == 'notice_id' for col in columns)
            print(f"\n   notice_id alanı: {'✅ Var' if has_notice_id else '❌ YOK'}")
            
        except Exception as table_error:
            print(f"\n❌ 'opportunities' tablosu hatası: {table_error}")
            print("   Tablo yoksa oluşturulmalı!")
    
except Exception as e:
    print(f"\n❌ Database bağlantı hatası: {e}")
    print("\n💡 Olası nedenler:")
    print("   1. PostgreSQL çalışmıyor olabilir")
    print("   2. Database adı yanlış olabilir")
    print("   3. Kullanıcı adı/şifre yanlış olabilir")
    print("   4. Port yanlış olabilir")
    print("   5. Firewall/network sorunu olabilir")
    
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

