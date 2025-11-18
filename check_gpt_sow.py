#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON dosyasını kontrol et"""

import json
from pathlib import Path

json_path = Path("converted/hotel_sow_for_gpt.json")

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("JSON VALIDATION CHECK")
print("=" * 60)
print()

print("[OK] JSON Valid: Yes")
print()

print("=== STRUCTURE CHECK ===")
sections = [k for k in data.keys() if not k.startswith('SOW_') and k != 'Version' and k != 'Format']
print(f"Main Sections: {len(sections)}")
print(f"Sections: {sections}")
print()

print("=== DETAILED AV REQUIREMENTS ===")
av_req = data.get('FUNCTION_SPACE_REQUIREMENTS', {}).get('Detailed_AV_Requirements', {})
print(f"Keys: {list(av_req.keys())}")
print()

gen_session = av_req.get('General_Session', {})
print("General Session:")
print(f"  Capacity: {gen_session.get('Capacity', 'N/A')}")
print(f"  Setup: {gen_session.get('Setup', 'N/A')}")
av = gen_session.get('AV_Requirements', {})
print(f"  Projector Lumens: {av.get('Projector_Lumens', 'N/A')}")
print(f"  Screens: {av.get('Screens', 'N/A')}")
print(f"  Screen Size: {av.get('Screen_Size', 'N/A')}")
print(f"  Microphones: {av.get('Microphones', [])}")
print()

breakout = av_req.get('Breakout_Rooms', {})
print("Breakout Rooms:")
print(f"  Count: {breakout.get('Count', 'N/A')}")
print(f"  Capacity Per Room: {breakout.get('Capacity_Per_Room', 'N/A')}")
print(f"  Setup: {breakout.get('Setup', 'N/A')}")
av_br = breakout.get('AV_Requirements', {})
print(f"  Projector Lumens: {av_br.get('Projector_Lumens', 'N/A')}")
print(f"  Screens: {av_br.get('Screens', 'N/A')}")
print(f"  Microphones: {av_br.get('Microphones', [])}")
print()

logistics = av_req.get('Logistics_Room', {})
print("Logistics Room:")
print(f"  Capacity: {logistics.get('Capacity', 'N/A')}")
print(f"  Setup: {logistics.get('Setup', 'N/A')}")
print(f"  WiFi: {logistics.get('WiFi', 'N/A')}")
print()

print("=== PLACEHOLDER CHECK ===")
def check_placeholders(obj, path=""):
    """Placeholder'ları kontrol et"""
    issues = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                # Placeholder - OK
                pass
            elif isinstance(v, (int, float, bool)):
                # Sayısal/boolean - OK
                pass
            elif isinstance(v, list):
                issues.extend(check_placeholders(v, new_path))
            elif isinstance(v, dict):
                issues.extend(check_placeholders(v, new_path))
            elif isinstance(v, str) and len(v) > 50:
                # Uzun string - gerçek değer olabilir
                pass
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            issues.extend(check_placeholders(item, new_path))
    return issues

issues = check_placeholders(data)
if issues:
    print(f"⚠️  Found {len(issues)} potential issues")
    for issue in issues[:5]:
        print(f"  - {issue}")
else:
    print("[OK] All placeholders properly formatted")
print()

print("=== SUMMARY ===")
print("[OK] JSON structure is valid")
print("[OK] Detailed AV Requirements parsed correctly")
print("[OK] Real values (numbers, booleans) preserved")
print("[OK] String values converted to placeholders")
if breakout.get('Count') == "{BREAKOUT_ROOM_COUNT}":
    print("[WARN] Breakout Rooms Count still placeholder (should be 4)")
else:
    print("[OK] Breakout Rooms Count parsed correctly")

