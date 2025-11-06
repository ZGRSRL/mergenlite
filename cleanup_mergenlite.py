#!/usr/bin/env python3
"""
MergenLite Kod Temizliği Scripti
Gereksiz FastAPI, eski ajan ve test dosyalarını kaldırır
"""

import os
import shutil
from pathlib import Path

# Kaldırılacak dosya ve klasörler
FILES_TO_REMOVE = [
    # FastAPI dosyaları
    "mergen/api/app/main.py",
    "mergen/api/app/db.py",
    "mergen/api/app/deps.py",
    "mergen/api/app/config.py",
    "mergen/api/app/schemas.py",
    "mergen/api/app/models.py",
    
    # FastAPI routes
    "mergen/api/app/routes/health.py",
    "mergen/api/app/routes/ingest.py",
    "mergen/api/app/routes/compliance.py",
    "mergen/api/app/routes/pricing.py",
    "mergen/api/app/routes/proposal.py",
    "mergen/api/app/routes/search.py",
    "mergen/api/app/routes/sam_gov.py",
    
    # Eski API server
    "mergen/sam/document_management/api_server.py",
    
    # Eski Streamlit dosyaları
    "mergen/sam/document_management/app.py",
    "mergen/sam/document_management/opportunity_analysis.py",
]

# Kaldırılacak klasörler
DIRS_TO_REMOVE = [
    "mergen/api/app/routes",  # Tüm routes klasörü
]

# Test dosyaları (pattern)
TEST_FILE_PATTERNS = [
    "test_*.py",
    "*_backup.py",
    "simple_*.py",
    "check_*.py",
    "update_*.py",
]

def remove_file(file_path: str):
    """Dosyayı kaldır"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"  [OK] Kaldırıldı: {file_path}")
            return True
        else:
            print(f"  [SKIP] Bulunamadı: {file_path}")
            return False
    except Exception as e:
        print(f"  [ERROR] Hata: {file_path} - {e}")
        return False

def remove_dir(dir_path: str):
    """Klasörü kaldır"""
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"  [OK] Kaldırıldı: {dir_path}")
            return True
        else:
            print(f"  [SKIP] Bulunamadı: {dir_path}")
            return False
    except Exception as e:
        print(f"  [ERROR] Hata: {dir_path} - {e}")
        return False

def find_test_files(root_dir: str = "."):
    """Test dosyalarını bul"""
    test_files = []
    
    for pattern in TEST_FILE_PATTERNS:
        # Basit glob pattern matching
        import glob
        files = glob.glob(os.path.join(root_dir, pattern))
        test_files.extend(files)
    
    return test_files

def main():
    """Ana temizlik fonksiyonu"""
    print("="*60)
    print("MergenLite Kod Temizliği Başlatılıyor...")
    print("="*60)
    
    removed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Dosyaları kaldır
    print("\n[1] Dosyalar kaldırılıyor...")
    for file_path in FILES_TO_REMOVE:
        if remove_file(file_path):
            removed_count += 1
        else:
            skipped_count += 1
    
    # Klasörleri kaldır
    print("\n[2] Klasörler kaldırılıyor...")
    for dir_path in DIRS_TO_REMOVE:
        if remove_dir(dir_path):
            removed_count += 1
        else:
            skipped_count += 1
    
    # Test dosyalarını bul ve kaldır
    print("\n[3] Test dosyaları aranıyor...")
    test_files = find_test_files()
    
    # Root'taki test dosyalarını kaldır (mergen klasöründekileri koru)
    root_test_files = [f for f in test_files if not f.startswith("mergen/")]
    
    for file_path in root_test_files:
        # Önemli dosyaları koru
        if "create_mergenlite" in file_path or "mergenlite" in file_path:
            print(f"  [SKIP] Korunuyor: {file_path}")
            skipped_count += 1
            continue
        
        if remove_file(file_path):
            removed_count += 1
        else:
            skipped_count += 1
    
    # Özet
    print("\n" + "="*60)
    print("Temizlik Tamamlandı!")
    print("="*60)
    print(f"Kaldırılan: {removed_count}")
    print(f"Atlanan: {skipped_count}")
    print(f"Hatalar: {error_count}")
    print("\n[INFO] Temizlik tamamlandı. Lütfen değişiklikleri kontrol edin.")
    print("[INFO] Önemli: Bu script geri alınamaz. Git commit yapmadan önce kontrol edin!")

if __name__ == "__main__":
    # Onay iste
    print("⚠️  UYARI: Bu script dosyaları kalıcı olarak silecektir!")
    response = input("Devam etmek istiyor musunuz? (yes/no): ")
    
    if response.lower() in ['yes', 'y', 'evet', 'e']:
        main()
    else:
        print("İşlem iptal edildi.")

