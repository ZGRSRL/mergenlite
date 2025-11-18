#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_analysis_results tablosunun şemasını kontrol et"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Windows encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

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

print("=" * 60)
print("ai_analysis_results Tablo Şeması Kontrolü")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Tablo var mı?
    if 'ai_analysis_results' in inspector.get_table_names():
        print("\n✅ Tablo mevcut: ai_analysis_results")
        
        # Kolonları listele
        columns = inspector.get_columns('ai_analysis_results')
        print("\n📋 Kolonlar:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']}, default: {col.get('default', 'None')})")
        
        # Primary key
        pk_constraint = inspector.get_pk_constraint('ai_analysis_results')
        if pk_constraint:
            print(f"\n🔑 Primary Key: {pk_constraint['constrained_columns']}")
        
        # Foreign keys
        fk_constraints = inspector.get_foreign_keys('ai_analysis_results')
        if fk_constraints:
            print("\n🔗 Foreign Keys:")
            for fk in fk_constraints:
                print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # Indexes
        indexes = inspector.get_indexes('ai_analysis_results')
        if indexes:
            print("\n📇 Indexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
        
        # Row count
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM ai_analysis_results"))
            count = result.scalar()
            print(f"\n📊 Toplam Kayıt: {count}")
    else:
        print("\n❌ Tablo bulunamadı: ai_analysis_results")
        print("\nMevcut tablolar:")
        for table in inspector.get_table_names():
            print(f"  - {table}")
    
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

