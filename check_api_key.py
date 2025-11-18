#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Key Kontrol Scripti
Backend utils üzerinden API key'in doğru yüklendiğini kontrol eder
"""

import os
import sys

# Windows console encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_api_key():
    """API key'in yüklendiğini kontrol et"""
    print("=" * 60)
    print("API Key Kontrolü")
    print("=" * 60)
    
    # 1. Environment variable kontrolü
    api_key_env = os.getenv('SAM_API_KEY', '')
    if api_key_env:
        masked = api_key_env[:8] + "..." + api_key_env[-4:] if len(api_key_env) > 12 else "***"
        print(f"[OK] Environment variable SAM_API_KEY bulundu (length: {len(api_key_env)}, preview: {masked})")
    else:
        print("[WARN] Environment variable SAM_API_KEY bulunamadi")
    
    # 2. os.environ direkt kontrolü
    api_key_environ = os.environ.get('SAM_API_KEY', '')
    if api_key_environ:
        masked = api_key_environ[:8] + "..." + api_key_environ[-4:] if len(api_key_environ) > 12 else "***"
        print(f"[OK] os.environ SAM_API_KEY bulundu (length: {len(api_key_environ)}, preview: {masked})")
    else:
        print("[WARN] os.environ SAM_API_KEY bulunamadi")
    
    # 3. backend_utils.get_secret kontrolü
    try:
        from backend_utils import get_secret
        api_key_secret = get_secret('SAM_API_KEY', '')
        if api_key_secret:
            masked = api_key_secret[:8] + "..." + api_key_secret[-4:] if len(api_key_secret) > 12 else "***"
            print(f"[OK] backend_utils.get_secret() SAM_API_KEY bulundu (length: {len(api_key_secret)}, preview: {masked})")
        else:
            print("[WARN] backend_utils.get_secret() SAM_API_KEY bulunamadi")
    except ImportError as e:
        print(f"[ERROR] backend_utils import hatasi: {e}")
    
    # 4. SAMIntegration kontrolü
    try:
        from sam_integration import SAMIntegration
        sam = SAMIntegration()
        if sam.api_key:
            masked = sam.api_key[:8] + "..." + sam.api_key[-4:] if len(sam.api_key) > 12 else "***"
            print(f"[OK] SAMIntegration.api_key yuklendi (length: {len(sam.api_key)}, preview: {masked})")
        else:
            print("[ERROR] SAMIntegration.api_key bos!")
    except Exception as e:
        print(f"[ERROR] SAMIntegration yukleme hatasi: {e}")
    
    # 5. .env dosyası kontrolü
    env_paths = ['.env', 'mergen/.env', '../.env']
    found_env = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"[OK] .env dosyasi bulundu: {os.path.abspath(env_path)}")
            found_env = True
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    if 'SAM_API_KEY' in content:
                        print(f"   → .env dosyası SAM_API_KEY içeriyor")
                    else:
                        print(f"   → .env dosyası SAM_API_KEY içermiyor")
            except Exception as e:
                print(f"   → .env dosyası okunamadı: {e}")
    
    if not found_env:
        print("[WARN] .env dosyasi bulunamadi")
    
    print("=" * 60)
    
    # Sonuç özeti
    if api_key_env or api_key_environ or api_key_secret:
        print("[SUCCESS] API Key bulundu!")
        return True
    else:
        print("[FAIL] API Key bulunamadi!")
        return False

if __name__ == '__main__':
    success = check_api_key()
    sys.exit(0 if success else 1)
