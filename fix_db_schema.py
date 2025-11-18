#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database schema düzeltme scripti"""

import os
from dotenv import load_dotenv

load_dotenv('mergen/.env', override=True)

from app import get_db_engine, DB_AVAILABLE
from sqlalchemy import text

if not DB_AVAILABLE:
    print("UYARI: Database baglantisi yok!")
    exit(1)

engine = get_db_engine()
if not engine:
    print("HATA: Database engine olusturulamadi!")
    exit(1)

# SQL komutları
sql_commands = [
    # notice_type kolonu ekle (eğer yoksa)
    """
    DO $$ 
    BEGIN 
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='notice_type'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN notice_type VARCHAR(100);
            RAISE NOTICE 'notice_type kolonu eklendi';
        ELSE
            RAISE NOTICE 'notice_type kolonu zaten var';
        END IF;
    END $$;
    """,
    # response_dead_line -> response_deadline (eğer response_dead_line varsa)
    """
    DO $$ 
    BEGIN 
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='response_dead_line'
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='response_deadline'
        ) THEN
            ALTER TABLE opportunities RENAME COLUMN response_dead_line TO response_deadline;
            RAISE NOTICE 'response_dead_line -> response_deadline olarak degistirildi';
        ELSE
            RAISE NOTICE 'response_deadline kolonu zaten dogru';
        END IF;
    END $$;
    """,
    # Eksik kolonları ekle
    """
    DO $$ 
    BEGIN 
        -- estimated_value
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='estimated_value'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN estimated_value NUMERIC(15, 2);
        END IF;
        
        -- place_of_performance
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='place_of_performance'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN place_of_performance VARCHAR(255);
        END IF;
        
        -- sam_gov_link
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='sam_gov_link'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN sam_gov_link VARCHAR(512);
        END IF;
        
        -- raw_data (JSONB)
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='raw_data'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN raw_data JSONB;
        END IF;
        
        -- created_at
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='created_at'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        -- updated_at
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='opportunities' AND column_name='updated_at'
        ) THEN
            ALTER TABLE opportunities ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        RAISE NOTICE 'Eksik kolonlar kontrol edildi ve eklendi';
    END $$;
    """
]

try:
    with engine.connect() as conn:
        for i, sql in enumerate(sql_commands, 1):
            if i == 1:
                print("notice_type kolonu kontrol ediliyor...")
            elif i == 2:
                print("response_deadline kolonu kontrol ediliyor...")
            elif i == 3:
                print("Eksik kolonlar kontrol ediliyor...")
            result = conn.execute(text(sql))
            conn.commit()
            print("Tamamlandi!")
        print("\nDatabase schema duzeltmesi tamamlandi!")
except Exception as e:
    print(f"HATA: {str(e)}")
    import traceback
    traceback.print_exc()

