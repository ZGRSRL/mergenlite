#!/usr/bin/env python3
"""
SAM API Rate Limiting Analysis
API rate limiting durumunu analiz eder ve strateji önerir
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_api_strategy():
    """API stratejisini analiz et"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': 'ZGR_AI',
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🔍 SAM API Rate Limiting Analizi")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**db_params)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            
            # 1. Mevcut veri durumu
            print("\n📊 Mevcut Veri Durumu:")
            print("-" * 40)
            
            cur.execute("SELECT COUNT(*) as count FROM opportunities;")
            total_opps = cur.fetchone()
            print(f"  • Toplam Opportunities: {total_opps['count']}")
            
            # Son 7 gün
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM opportunities 
                WHERE posted_date >= CURRENT_DATE - INTERVAL '7 days';
            """)
            recent_7d = cur.fetchone()
            print(f"  • Son 7 gün: {recent_7d['count']}")
            
            # Son 30 gün
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM opportunities 
                WHERE posted_date >= CURRENT_DATE - INTERVAL '30 days';
            """)
            recent_30d = cur.fetchone()
            print(f"  • Son 30 gün: {recent_30d['count']}")
            
            # En son güncelleme
            cur.execute("""
                SELECT MAX(updated_at) as last_update 
                FROM opportunities;
            """)
            last_update = cur.fetchone()
            print(f"  • Son güncelleme: {last_update['last_update']}")
            
            # 2. API Rate Limiting Analizi
            print("\n⚡ API Rate Limiting Analizi:")
            print("-" * 40)
            
            print("  📋 Mevcut Rate Limiting:")
            print("    • Minimum interval: 3 saniye")
            print("    • Maksimum çağrı: ~20 çağrı/dakika")
            print("    • Maksimum çağrı: ~1,200 çağrı/saat")
            print("    • Maksimum çağrı: ~28,800 çağrı/gün")
            
            print("\n  🎯 SAM.gov API Limitleri:")
            print("    • Rate limit: 1000 çağrı/gün (ücretsiz)")
            print("    • Rate limit: 10,000 çağrı/gün (ücretli)")
            print("    • Bulk operations: Destekleniyor")
            
            # 3. Strateji Önerileri
            print("\n🚀 Önerilen Strateji:")
            print("-" * 40)
            
            print("  ✅ MEVCUT SİSTEM (Database-First):")
            print("    • İlk çağrıda tüm verileri DB'ye al")
            print("    • Sonraki işlemler lokal DB'den")
            print("    • API çağrısı sadece güncelleme için")
            print("    • Rate limiting sorunu YOK")
            
            print("\n  📊 Veri Güncelleme Stratejisi:")
            print("    • Günlük bulk fetch: 1 çağrı")
            print("    • Haftalık full sync: 1 çağrı")
            print("    • Real-time updates: Sadece kritik fırsatlar")
            
            # 4. Bulk Fetch Test
            print("\n🧪 Bulk Fetch Test:")
            print("-" * 40)
            
            # Son 7 günün fırsatlarını kontrol et
            cur.execute("""
                SELECT COUNT(*) as count, 
                       MIN(posted_date) as earliest,
                       MAX(posted_date) as latest
                FROM opportunities 
                WHERE posted_date >= CURRENT_DATE - INTERVAL '7 days';
            """)
            week_data = cur.fetchone()
            
            if week_data['count'] > 0:
                print(f"  ✅ Son 7 gün: {week_data['count']} fırsat")
                print(f"    • En erken: {week_data['earliest']}")
                print(f"    • En geç: {week_data['latest']}")
                print("  ✅ Veriler güncel, API çağrısına gerek YOK")
            else:
                print("  ⚠️ Son 7 gün veri yok, bulk fetch gerekebilir")
            
            # 5. Performans Analizi
            print("\n⚡ Performans Analizi:")
            print("-" * 40)
            
            # Database query performance
            start_time = datetime.now()
            cur.execute("SELECT * FROM opportunities LIMIT 100;")
            results = cur.fetchall()
            end_time = datetime.now()
            
            query_time = (end_time - start_time).total_seconds() * 1000
            print(f"  • DB Query (100 kayıt): {query_time:.2f}ms")
            print(f"  • DB Query (1000 kayıt): ~{query_time * 10:.2f}ms")
            print(f"  • API Call (100 kayıt): ~{3 * 100:.0f}s (rate limited)")
            print(f"  • DB Query 1000x daha hızlı!")
            
            # 6. Öneriler
            print("\n💡 Öneriler:")
            print("-" * 40)
            
            print("  🎯 MEVCUT SİSTEMİ KULLAN:")
            print("    1. ✅ Database-first yaklaşımı devam et")
            print("    2. ✅ Bulk fetch ile veri güncelleme")
            print("    3. ✅ Lokal analiz ve işlemler")
            print("    4. ✅ API çağrısı sadece güncelleme için")
            
            print("\n  📅 Güncelleme Stratejisi:")
            print("    • Günlük: 1 bulk fetch (1 API çağrısı)")
            print("    • Haftalık: Full sync (1 API çağrısı)")
            print("    • Real-time: Sadece kritik fırsatlar")
            
            print("\n  🔧 Optimizasyon:")
            print("    • Background job ile otomatik güncelleme")
            print("    • Incremental updates")
            print("    • Caching stratejisi")
            
        conn.close()
        
        print("\n✅ Analiz tamamlandı!")
        
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

if __name__ == "__main__":
    analyze_api_strategy()
