#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API Key yükleme testi"""

import os
import sys
from dotenv import load_dotenv

print("="*60)
print("SAM_API_KEY Yükleme Testi")
print("="*60)

# Environment'i temizle
if 'SAM_API_KEY' in os.environ:
    del os.environ['SAM_API_KEY']
    print("[OK] Environment temizlendi")

# .env dosyasını yükle
env_path = 'mergen/.env'
if os.path.exists(env_path):
    abs_path = os.path.abspath(env_path)
    print(f"\n.env dosyasi bulundu: {abs_path}")
    load_dotenv(env_path, override=True, verbose=True)
    
    # API Key kontrolü
    api_key = os.getenv('SAM_API_KEY', '').strip()
    if not api_key:
        api_key = os.environ.get('SAM_API_KEY', '').strip()
    
    if api_key:
        print(f"\n[OK] SAM_API_KEY yuklendi!")
        print(f"   - Uzunluk: {len(api_key)} karakter")
        print(f"   - Preview: {api_key[:15]}...{api_key[-4:]}")
        print(f"   - Format: {'Gecerli' if api_key.startswith('SAM-') else 'Farkli format'}")
        
        # SAMIntegration testi
        try:
            from sam_integration import SAMIntegration
            sam = SAMIntegration()
            if sam.api_key:
                print(f"\n[OK] SAMIntegration API Key durumu: Yuklendi")
                print(f"   - Uzunluk: {len(sam.api_key)}")
                print(f"   - Preview: {sam.api_key[:15]}...{sam.api_key[-4:]}")
            else:
                print(f"\n[ERROR] SAMIntegration API Key yuklenemedi!")
        except Exception as e:
            print(f"\n[WARNING] SAMIntegration test hatasi: {e}")
    else:
        print(f"\n[ERROR] SAM_API_KEY bulunamadi!")
        print(f"   - os.getenv('SAM_API_KEY'): {os.getenv('SAM_API_KEY', 'NOT SET')}")
        print(f"   - os.environ.get('SAM_API_KEY'): {os.environ.get('SAM_API_KEY', 'NOT SET')}")
else:
    print(f"\n[ERROR] .env dosyasi bulunamadi: {env_path}")
    print(f"   - Mevcut dizin: {os.getcwd()}")

print("\n" + "="*60)

