#!/usr/bin/env python3
"""Script to help update API key in .env file"""

import os
from pathlib import Path

def find_env_file():
    """Find .env file location"""
    env_paths = [
        'mergen/.env',
        '.env',
        '../.env'
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            abs_path = os.path.abspath(env_path)
            print(f"[OK] Found .env file: {abs_path}")
            return abs_path
    
    print("[ERROR] No .env file found!")
    return None

def check_current_api_key():
    """Check current API key from environment"""
    try:
        from dotenv import load_dotenv
        load_dotenv('mergen/.env')
        load_dotenv('.env')
    except:
        pass
    
    api_key = os.getenv('SAM_API_KEY', '')
    if api_key:
        masked = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print(f"[OK] Current API Key: {masked}")
        print(f"[OK] Length: {len(api_key)}")
        return api_key
    else:
        print("[WARNING] No API key found in environment")
        return None

def show_update_instructions(env_path):
    """Show instructions for updating API key"""
    print("\n" + "="*60)
    print("API Key Güncelleme Talimatları")
    print("="*60)
    print(f"\n1. .env dosyasını açın: {env_path}")
    print("\n2. Şu satırı bulun:")
    print("   SAM_API_KEY=SAM-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    print("\n3. Yeni API key'inizle değiştirin:")
    print("   SAM_API_KEY=YENİ_API_KEY_BURAYA")
    print("\n4. Dosyayı kaydedin (Ctrl+S)")
    print("\n5. Streamlit'i yeniden başlatın:")
    print("   - Terminal'de Ctrl+C ile durdurun")
    print("   - streamlit run app.py ile yeniden başlatın")
    print("\n6. Test edin:")
    print("   python test_api_key.py")
    print("="*60)

if __name__ == "__main__":
    print("API Key Durumu Kontrolü\n")
    
    env_path = find_env_file()
    current_key = check_current_api_key()
    
    if env_path:
        show_update_instructions(env_path)
    else:
        print("\n[INFO] .env dosyası bulunamadı.")
        print("       mergen/.env veya .env dosyasını oluşturun ve şunu ekleyin:")
        print("       SAM_API_KEY=YENİ_API_KEY_BURAYA")



