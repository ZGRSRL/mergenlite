#!/usr/bin/env python3
"""
Insert Sample Data
Tablolara örnek veri ekler
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_sample_data():
    """Tablolara örnek veri ekle"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'sam'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("📊 Örnek Veri Ekleme")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        print("✅ Database bağlantısı başarılı!")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # 1. Documents tablosuna örnek veri ekle
            print("\n📄 Documents tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO documents (kind, title, path, meta_json) VALUES
                ('rfq', 'Hotel Conference Services RFQ', '/documents/rfq_001.pdf', '{"department": "GSA", "deadline": "2024-12-31"}'),
                ('proposal', 'ZGR Hotels Proposal', '/documents/proposal_001.pdf', '{"company": "ZGR Hotels", "submitted": "2024-11-15"}'),
                ('contract', 'Previous Hotel Contract', '/documents/contract_001.pdf', '{"value": 2500000, "duration": "3 years"}')
                ON CONFLICT DO NOTHING
                RETURNING id;
            """)
            doc_ids = cur.fetchall()
            print(f"✅ {len(doc_ids)} document eklendi")
            
            # 2. Requirements tablosuna örnek veri ekle
            print("\n📋 Requirements tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO requirements (rfq_id, code, text, category, priority) VALUES
                (1, 'REQ-001', 'Hotel must have conference facilities for 200+ people', 'Facilities', 'high'),
                (1, 'REQ-002', 'Minimum 100 guest rooms available', 'Capacity', 'high'),
                (1, 'REQ-003', '24/7 room service and concierge', 'Services', 'medium'),
                (1, 'REQ-004', 'Parking for 150+ vehicles', 'Parking', 'medium'),
                (1, 'REQ-005', 'High-speed internet throughout facility', 'Technology', 'high')
                ON CONFLICT DO NOTHING;
            """)
            print("✅ Requirements eklendi")
            
            # 3. Evidence tablosuna örnek veri ekle
            print("\n🔍 Evidence tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO evidence (requirement_id, source_doc_id, snippet, score, evidence_type) VALUES
                (1, 2, 'Our hotel features a 500-person conference hall with state-of-the-art AV equipment', 0.95, 'direct'),
                (2, 2, 'ZGR Hotels operates 150 luxury guest rooms with modern amenities', 0.90, 'direct'),
                (3, 2, '24/7 room service and concierge services available to all guests', 0.85, 'direct'),
                (4, 2, 'Complimentary parking for 200 vehicles with valet service', 0.80, 'direct'),
                (5, 2, 'High-speed fiber internet with 1Gbps bandwidth throughout the facility', 0.95, 'direct')
                ON CONFLICT DO NOTHING;
            """)
            print("✅ Evidence eklendi")
            
            # 4. Facility Features tablosuna örnek veri ekle
            print("\n🏢 Facility Features tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO facility_features (name, value, source_doc_id) VALUES
                ('Conference Hall', '500-person capacity with AV equipment', 2),
                ('Guest Rooms', '150 luxury rooms with modern amenities', 2),
                ('Restaurant', 'Full-service restaurant with bar', 2),
                ('Parking', '200-vehicle capacity with valet service', 2),
                ('Fitness Center', '24/7 fitness center with modern equipment', 2),
                ('Business Center', '24/7 business center with meeting rooms', 2)
                ON CONFLICT DO NOTHING;
            """)
            print("✅ Facility Features eklendi")
            
            # 5. Pricing Items tablosuna örnek veri ekle
            print("\n💰 Pricing Items tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO pricing_items (rfq_id, name, description, qty, unit, unit_price, total_price, category) VALUES
                (1, 'Guest Room', 'Standard guest room per night', 100, 'nights', 150.00, 15000.00, 'Accommodation'),
                (1, 'Conference Hall', 'Conference hall rental per day', 3, 'days', 500.00, 1500.00, 'Facilities'),
                (1, 'Breakfast', 'Breakfast buffet per person', 200, 'persons', 25.00, 5000.00, 'Food'),
                (1, 'Lunch', 'Lunch service per person', 200, 'persons', 35.00, 7000.00, 'Food'),
                (1, 'Dinner', 'Dinner service per person', 200, 'persons', 45.00, 9000.00, 'Food'),
                (1, 'AV Equipment', 'Audio-visual equipment rental', 3, 'days', 200.00, 600.00, 'Technology'),
                (1, 'Parking', 'Parking services per vehicle', 150, 'vehicles', 10.00, 1500.00, 'Services')
                ON CONFLICT DO NOTHING;
            """)
            print("✅ Pricing Items eklendi")
            
            # 6. Past Performance tablosuna örnek veri ekle (zaten var)
            print("\n🏆 Past Performance tablosu zaten dolu")
            
            # 7. Vector Chunks tablosuna örnek veri ekle
            print("\n🧠 Vector Chunks tablosuna veri ekleniyor...")
            cur.execute("""
                INSERT INTO vector_chunks (document_id, chunk, embedding, chunk_type, page_number) VALUES
                (1, 'Hotel Conference Services RFQ - Government contract for conference facilities', ARRAY[0.1, 0.2, 0.3], 'text', 1),
                (1, 'Requirements include 200+ person conference hall and 100+ guest rooms', ARRAY[0.4, 0.5, 0.6], 'text', 2),
                (2, 'ZGR Hotels proposal for government conference services', ARRAY[0.7, 0.8, 0.9], 'text', 1),
                (2, 'Our facility features 500-person conference hall and 150 guest rooms', ARRAY[0.2, 0.3, 0.4], 'text', 2)
                ON CONFLICT DO NOTHING;
            """)
            print("✅ Vector Chunks eklendi")
            
            # Commit all changes
            conn.commit()
            print("\n✅ Tüm veriler başarıyla eklendi!")
            
            # Show summary
            print("\n📊 Veri Özeti:")
            print("-" * 30)
            
            tables = ['documents', 'requirements', 'evidence', 'facility_features', 'pricing_items', 'past_performance', 'vector_chunks']
            for table in tables:
                cur.execute(f"SELECT COUNT(*) as count FROM {table};")
                count = cur.fetchone()
                print(f"• {table}: {count['count']} kayıt")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    insert_sample_data()
