#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resourceLinks ve attachments database kayıt kontrolü"""

import sys
import os
import io
import json

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from backend_utils import get_db_session, DB_AVAILABLE
from mergenlite_models import Opportunity

print("=" * 60)
print("resourceLinks ve attachments Database Kontrolu")
print("=" * 60)

if not DB_AVAILABLE:
    print("[ERROR] Database baglantisi yok!")
    sys.exit(1)

try:
    db = get_db_session()
    if not db:
        print("[ERROR] Database session olusturulamadi!")
        sys.exit(1)
    
    # Son 10 kayıt kontrolü
    opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(10).all()
    
    print(f"\nSon 10 kayit kontrol ediliyor...\n")
    
    has_resource_links = 0
    has_attachments = 0
    has_raw_data = 0
    
    for i, opp in enumerate(opps, 1):
        opp_id = opp.opportunity_id or 'N/A'
        title = (opp.title or 'Baslik Yok')[:40]
        
        # raw_data kontrolü
        raw_data = opp.raw_data
        has_raw = bool(raw_data)
        if has_raw:
            has_raw_data += 1
        
        # resourceLinks kontrolü
        resource_links = None
        attachments = None
        
        if raw_data:
            if isinstance(raw_data, dict):
                resource_links = raw_data.get('resourceLinks') or raw_data.get('resourceLinks')
                attachments = raw_data.get('attachments') or raw_data.get('attachments')
            elif isinstance(raw_data, str):
                try:
                    raw_dict = json.loads(raw_data)
                    resource_links = raw_dict.get('resourceLinks')
                    attachments = raw_dict.get('attachments')
                except:
                    pass
        
        has_rl = bool(resource_links)
        has_att = bool(attachments)
        
        if has_rl:
            has_resource_links += 1
        if has_att:
            has_attachments += 1
        
        # Detaylı göster
        print(f"{i}. {opp_id[:20]}...")
        print(f"   Baslik: {title}...")
        print(f"   raw_data: {'VAR' if has_raw else 'YOK'}")
        print(f"   resourceLinks: {'VAR' if has_rl else 'YOK'}", end='')
        if has_rl and isinstance(resource_links, list):
            print(f" ({len(resource_links)} adet)")
        else:
            print()
        print(f"   attachments: {'VAR' if has_att else 'YOK'}", end='')
        if has_att and isinstance(attachments, list):
            print(f" ({len(attachments)} adet)")
        else:
            print()
        print()
    
    db.close()
    
    print("=" * 60)
    print(f"OZET:")
    print(f"  raw_data: {has_raw_data}/10")
    print(f"  resourceLinks: {has_resource_links}/10")
    print(f"  attachments: {has_attachments}/10")
    print("=" * 60)
    
    if has_resource_links > 0 or has_attachments > 0:
        print("[OK] resourceLinks/attachments database'e kaydediliyor!")
    else:
        print("[WARN] resourceLinks/attachments database'e kaydedilmiyor olabilir!")

except Exception as e:
    print(f"\n[ERROR] Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

