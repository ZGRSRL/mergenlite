#!/usr/bin/env python3
"""Check AutoGen and pipeline dependencies"""
import sys
from pathlib import Path

print("=" * 60)
print("AUTOGEN & PIPELINE DURUM KONTROLÜ")
print("=" * 60)

# 1. AutoGen kontrolü
print("\n1. AutoGen Modülü:")
try:
    import autogen
    version = getattr(autogen, '__version__', 'mevcut')
    print(f"   [OK] AutoGen yüklü: {version}")
except ImportError:
    print("   [ERROR] AutoGen yüklü değil")
    print("   Kurulum: pip install pyautogen")

# 2. D:/RFQ klasörü kontrolü
print("\n2. Pipeline Bağımlılıkları:")
rfq_path = Path("D:/RFQ")
if rfq_path.exists():
    print(f"   [OK] D:/RFQ klasörü mevcut: {rfq_path}")
    
    # Alt klasörleri kontrol et
    backend_services = rfq_path / "backend" / "services"
    backend_agents = rfq_path / "backend" / "agents"
    agents_dir = rfq_path / "agents"
    
    print(f"   Backend/services: {'[OK]' if backend_services.exists() else '[YOK]'}")
    print(f"   Backend/agents: {'[OK]' if backend_agents.exists() else '[YOK]'}")
    print(f"   Agents: {'[OK]' if agents_dir.exists() else '[YOK]'}")
    
    # Önemli dosyaları kontrol et
    important_files = [
        "backend/services/sow_pipeline_enhanced.py",
        "backend/agents/pipeline_v3.py",
        "agents/analyzer_agent.py",
        "agents/reviewer_agent.py",
        "backend/agents/sow_generator_agent_v3.py"
    ]
    
    print("\n   Önemli dosyalar:")
    for file_path in important_files:
        full_path = rfq_path / file_path
        status = "[OK]" if full_path.exists() else "[YOK]"
        print(f"     {status} {file_path}")
else:
    print(f"   [WARNING] D:/RFQ klasörü bulunamadı")
    print("   Pipeline çalışmayacak, PIPELINE_AVAILABLE=False olacak")

# 3. Mevcut agent dosyaları
print("\n3. Mevcut Agent Dosyaları (proje içi):")
agents_dir = Path("agents")
if agents_dir.exists():
    agent_files = list(agents_dir.glob("*.py"))
    if agent_files:
        print(f"   [OK] {len(agent_files)} agent dosyası bulundu:")
        for agent_file in agent_files[:5]:
            print(f"     - {agent_file.name}")
    else:
        print("   [WARNING] Agent dosyası bulunamadı")
else:
    print("   [WARNING] agents/ klasörü bulunamadı")

# 4. Pipeline import testi
print("\n4. Pipeline Import Testi:")
try:
    sys.path.insert(0, str(rfq_path))
    sys.path.insert(0, str(rfq_path / "backend" / "services"))
    sys.path.insert(0, str(rfq_path / "backend" / "agents"))
    sys.path.insert(0, str(rfq_path / "agents"))
    
    try:
        from backend.services.sow_pipeline_enhanced import process_rfq_to_sow_enhanced
        print("   [OK] sow_pipeline_enhanced import edildi")
    except ImportError as e:
        print(f"   [ERROR] sow_pipeline_enhanced import hatası: {e}")
    
    try:
        from backend.agents.pipeline_v3 import run_enterprise_pipeline
        print("   [OK] pipeline_v3 import edildi")
    except ImportError as e:
        print(f"   [ERROR] pipeline_v3 import hatası: {e}")
        
except Exception as e:
    print(f"   [ERROR] Pipeline import testi başarısız: {e}")

print("\n" + "=" * 60)
print("KONTROL TAMAMLANDI")
print("=" * 60)

