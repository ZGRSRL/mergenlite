"""
Pipeline email gönderimini kontrol et
SMTP ayarlarını ve son pipeline çalışmalarını kontrol eder
"""
import os
import sys
from pathlib import Path

# Add mergen/api to path
sys.path.insert(0, str(Path(__file__).parent / "mergen" / "api"))

try:
    from app.config import settings
    from app.db import SessionLocal
    from app.models.db_models import AIAnalysisResult, Opportunity
    from sqlalchemy import desc
    import json
    from datetime import datetime, timedelta
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def check_smtp_settings():
    """SMTP ayarlarını kontrol et"""
    print("=" * 70)
    print("SMTP AYARLARI KONTROLÜ")
    print("=" * 70)
    print()
    
    required_settings = {
        'smtp_host': settings.smtp_host,
        'smtp_username': settings.smtp_username,
        'smtp_password': settings.smtp_password,
        'pipeline_notification_email': settings.pipeline_notification_email,
    }
    
    all_ok = True
    for key, value in required_settings.items():
        if value:
            print(f"✅ {key}: {'*' * min(len(str(value)), 20)}")
        else:
            print(f"❌ {key}: NOT SET")
            all_ok = False
    
    print()
    print(f"SMTP Port: {settings.smtp_port}")
    print(f"SMTP Use TLS: {settings.smtp_use_tls}")
    print(f"SMTP From Email: {settings.smtp_from_email}")
    print()
    
    if not all_ok:
        print("⚠️  SMTP ayarları eksik! Pipeline mail gönderemez.")
        print()
        print("Gerekli environment variables:")
        print("  - SMTP_HOST")
        print("  - SMTP_USERNAME")
        print("  - SMTP_PASSWORD")
        print("  - PIPELINE_NOTIFICATION_EMAIL")
        print()
    
    return all_ok

def check_recent_pipeline_runs():
    """Son pipeline çalışmalarını kontrol et"""
    print("=" * 70)
    print("SON PIPELINE ÇALIŞMALARI")
    print("=" * 70)
    print()
    
    db = SessionLocal()
    try:
        # Son 10 analiz sonucunu getir
        results = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.analysis_type.in_(["sow_draft", "sow", "hotel_match"])
        ).order_by(desc(AIAnalysisResult.created_at)).limit(10).all()
        
        if not results:
            print("❌ Hiç pipeline çalışması bulunamadı")
            return
        
        print(f"Bulunan {len(results)} son analiz:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Analysis ID: {result.id}")
            print(f"   Type: {result.analysis_type}")
            print(f"   Status: {result.status}")
            print(f"   Created: {result.created_at}")
            
            # Opportunity bilgisi
            opportunity = db.query(Opportunity).filter(Opportunity.id == result.opportunity_id).first()
            if opportunity:
                print(f"   Opportunity: {opportunity.title[:50]}...")
                print(f"   Notice ID: {opportunity.notice_id or 'N/A'}")
            
            # Log'larda email gönderim bilgisi ara
            if hasattr(result, 'analysis_logs'):
                email_logs = [log for log in result.analysis_logs if 'email' in log.message.lower() or 'mail' in log.message.lower()]
                if email_logs:
                    print(f"   Email Logs:")
                    for log in email_logs[-3:]:  # Son 3 email log
                        print(f"      - [{log.level}] {log.message[:80]}")
            
            # PDF ve JSON path kontrolü
            if result.pdf_path:
                pdf_exists = Path(result.pdf_path).exists() if result.pdf_path else False
                print(f"   PDF: {result.pdf_path} {'✅' if pdf_exists else '❌ MISSING'}")
            if result.json_path:
                json_exists = Path(result.json_path).exists() if result.json_path else False
                print(f"   JSON: {result.json_path} {'✅' if json_exists else '❌ MISSING'}")
            
            print()
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_pipeline_logs():
    """Pipeline log dosyalarını kontrol et"""
    print("=" * 70)
    print("PIPELINE LOG KONTROLÜ")
    print("=" * 70)
    print()
    
    log_files = [
        "app.log",
        "app_console.log",
        "mergen/api/app.log",
        "mergen/api/logs/pipeline.log"
    ]
    
    found_logs = False
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            found_logs = True
            print(f"📄 {log_file}:")
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Son 50 satırı kontrol et
                    email_lines = [line for line in lines[-50:] if 'email' in line.lower() or 'mail' in line.lower() or 'smtp' in line.lower()]
                    if email_lines:
                        print(f"   Son email ile ilgili loglar ({len(email_lines)} satır):")
                        for line in email_lines[-5:]:  # Son 5 email log
                            print(f"      {line.strip()[:100]}")
                    else:
                        print(f"   Email ile ilgili log bulunamadı (son 50 satır)")
            except Exception as e:
                print(f"   ❌ Log okuma hatası: {e}")
            print()
    
    if not found_logs:
        print("⚠️  Log dosyası bulunamadı")
        print()

def test_email_send():
    """Test email gönderimi dene"""
    print("=" * 70)
    print("TEST EMAIL GÖNDERİMİ")
    print("=" * 70)
    print()
    
    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password and settings.pipeline_notification_email):
        print("❌ SMTP ayarları eksik, test email gönderilemez")
        return False
    
    try:
        from app.services.mail_service import build_mail_package, send_email_via_smtp
        
        print("Test mail paketi oluşturuluyor...")
        mail_package = build_mail_package(
            opportunity_code="TEST-PIPELINE-CHECK",
            folder_path=str(Path("/tmp")),
            to_email=settings.pipeline_notification_email,
            from_email=settings.smtp_from_email or settings.smtp_username,
            analysis_result_json={
                "summary": "Pipeline Email Test",
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"To: {mail_package['to']}")
        print(f"From: {mail_package['from']}")
        print(f"Subject: {mail_package['subject']}")
        print()
        
        smtp_config = {
            'host': settings.smtp_host,
            'port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls,
        }
        
        print("SMTP üzerinden email gönderiliyor...")
        success = send_email_via_smtp(mail_package, smtp_config)
        
        if success:
            print("✅ Test email başarıyla gönderildi!")
            return True
        else:
            print("❌ Test email gönderilemedi")
            return False
            
    except Exception as e:
        print(f"❌ Test email hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    print("🔍 PIPELINE EMAIL KONTROLÜ")
    print()
    
    # 1. SMTP ayarları kontrolü
    smtp_ok = check_smtp_settings()
    print()
    
    # 2. Son pipeline çalışmaları
    check_recent_pipeline_runs()
    print()
    
    # 3. Log kontrolü
    check_pipeline_logs()
    print()
    
    # 4. Test email (opsiyonel)
    if smtp_ok:
        response = input("Test email göndermek ister misiniz? (y/n): ").strip().lower()
        if response == 'y':
            print()
            test_email_send()
            print()
    
    print("=" * 70)
    print("KONTROL TAMAMLANDI")
    print("=" * 70)





