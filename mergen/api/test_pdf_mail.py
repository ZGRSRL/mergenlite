from app.db import SessionLocal
from app.models import AIAnalysisResult
from pathlib import Path
import json

db = SessionLocal()

# En son analizi kontrol et
result = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3
).order_by(AIAnalysisResult.created_at.desc()).first()

if result:
    print(f"Analysis ID: {result.id}")
    print(f"Type: {result.analysis_type}")
    print(f"Status: {result.status}")
    print(f"\nPDF Path: {result.pdf_path}")
    if result.pdf_path:
        pdf = Path(result.pdf_path)
        print(f"PDF Exists: {pdf.exists()}")
        if pdf.exists():
            print(f"PDF Size: {pdf.stat().st_size:,} bytes")
    
    # Mail servisi test
    print(f"\n--- Mail Servisi Test ---")
    try:
        from app.services.mail_service import build_mail_package, send_email_via_smtp
        print("✅ Mail servisi import edilebildi")
    except ImportError as e:
        print(f"❌ Mail servisi import edilemedi: {e}")

db.close()

