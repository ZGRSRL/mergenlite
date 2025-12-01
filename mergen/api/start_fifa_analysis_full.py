#!/usr/bin/env python3
"""Start full SOW analysis for FIFA opportunity with Excel/CSV support."""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"
OPP_ID = 3  # FIFA World Cup opportunity

print("=" * 70)
print("🚀 FIFA OPPORTUNITY - TAM ANALİZ (Excel/CSV Desteği ile)")
print("=" * 70)
print()

# Step 1: Check attachments
print("📋 Step 1: Attachments kontrol ediliyor...")
attachments_resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
if attachments_resp.status_code == 200:
    attachments = attachments_resp.json()
    print(f"   ✅ {len(attachments)} attachment bulundu")
    
    # Check file types
    pdf_count = sum(1 for att in attachments if att.get('mime_type', '').lower().startswith('application/pdf'))
    excel_count = sum(1 for att in attachments if 'excel' in att.get('mime_type', '').lower() or 'spreadsheet' in att.get('mime_type', '').lower())
    csv_count = sum(1 for att in attachments if 'csv' in att.get('mime_type', '').lower() or att.get('name', '').endswith('.csv'))
    docx_count = sum(1 for att in attachments if 'word' in att.get('mime_type', '').lower() or att.get('name', '').endswith('.docx'))
    
    print(f"   📄 PDF: {pdf_count}")
    print(f"   📊 Excel: {excel_count}")
    print(f"   📋 CSV: {csv_count}")
    print(f"   📝 DOCX: {docx_count}")
    
    # Show attachment names
    print(f"\n   📎 Attachment Names:")
    for att in attachments[:10]:  # First 10
        name = att.get('name', 'N/A')
        mime = att.get('mime_type', 'N/A')
        downloaded = "✅" if att.get('downloaded') else "❌"
        print(f"      {downloaded} {name} ({mime})")

# Step 2: Start SOW Analysis
print(f"\n📄 Step 2: SOW Analysis başlatılıyor...")
print(f"   (Excel/CSV dosyaları da analiz edilecek)")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": OPP_ID, "analysis_type": "sow_draft"}
)
if resp.status_code == 200:
    result = resp.json()
    sow_analysis_id = result.get("analysis_result_id")
    print(f"   ✅ Analysis ID: {sow_analysis_id}")
    print()
    
    # Wait for completion
    print("⏳ Analiz tamamlanması bekleniyor...")
    print("   (Excel/CSV dosyalarından Layout, AV, F&B detayları çıkarılacak)")
    print()
    
    max_wait = 300  # 5 minutes
    for i in range(max_wait // 30):  # Check every 30 seconds
        time.sleep(30)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            
            print(f"   Status: {status} ({i*30}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Analiz {status}!")
                break
    
    # Check results
    print("\n" + "=" * 70)
    print("📊 SOW ANALYSIS SONUÇLARI")
    print("=" * 70)
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
    if resp.status_code == 200:
        result = resp.json()
        
        # PDF
        pdf_path = result.get('pdf_path')
        if pdf_path:
            print(f"✅ PDF: {pdf_path}")
            if Path(pdf_path).exists():
                print(f"   PDF Size: {Path(pdf_path).stat().st_size:,} bytes")
        
        # Document Analysis
        doc_analysis = result.get('result_json', {}).get('document_analysis', {})
        print(f"\n📄 Document Analysis:")
        print(f"   Documents: {doc_analysis.get('documents_analyzed', 0)}")
        print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
        print(f"   Chars: {doc_analysis.get('total_text_length', 0):,}")
        print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
        
        # SOW Analysis
        sow_analysis = result.get('result_json', {}).get('sow_analysis', {})
        if sow_analysis:
            print(f"\n📋 SOW Analysis:")
            
            # Locations
            locations = sow_analysis.get('Locations', [])
            print(f"   🏙️ Locations: {len(locations)}")
            
            # Function Space Requirements
            func_space = sow_analysis.get('FunctionSpaceRequirements', {})
            setup_reqs = func_space.get('setup_requirements', [])
            if setup_reqs:
                print(f"   📐 Setup Requirements: {len(setup_reqs)}")
                for req in setup_reqs[:3]:
                    print(f"      - {req}")
            
            # AV Requirements
            av_reqs = sow_analysis.get('AVRequirements', {})
            room_reqs = av_reqs.get('room_requirements', [])
            if room_reqs:
                print(f"   🎤 AV Requirements: {len(room_reqs)}")
                for req in room_reqs[:3]:
                    print(f"      - {req}")
            
            # F&B Requirements
            fb_reqs = sow_analysis.get('FoodAndBeverageRequirements', {})
            daily_breakdown = fb_reqs.get('daily_breakdown', [])
            if daily_breakdown:
                print(f"   🍽️ F&B Daily Breakdown: {len(daily_breakdown)}")
                for item in daily_breakdown[:3]:
                    print(f"      - {item}")
            
            # Data Quality Issues
            data_quality = sow_analysis.get('data_quality_issues', [])
            if data_quality:
                print(f"\n⚠️ Data Quality Issues: {len(data_quality)}")
                for issue in data_quality[:3]:
                    print(f"      - {issue}")
            else:
                print(f"\n✅ Data Quality: No issues reported")
        else:
            print("   ❌ SOW Analysis yok!")
    else:
        print("❌ SOW Analysis sonuçları alınamadı.")
else:
    print("❌ SOW Analysis başlatılamadı.")

print()
print("=" * 70)

