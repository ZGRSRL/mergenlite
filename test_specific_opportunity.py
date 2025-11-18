#!/usr/bin/env python3
"""
Test: Belirli bir opportunity ID için resourceLinks kontrolü
Opportunity ID: 57cd76db400c4e7ca895d40bf6454173
SAM.gov Link: https://sam.gov/opp/57cd76db400c4e7ca895d40bf6454173/view
"""
import os
import sys
import json

# Opportunity ID
opportunity_id = "57cd76db400c4e7ca895d40bf6454173"

print(f"Testing Opportunity ID: {opportunity_id}")
print(f"SAM.gov Link: https://sam.gov/opp/{opportunity_id}/view")
print("=" * 60)

# 1. SAM Integration ile test
try:
    from sam_integration import SAMIntegration
    
    print("\n1. SAM Integration test...")
    sam = SAMIntegration()
    
    if not sam.api_key:
        print("   UYARI: API Key bulunamadi")
    else:
        print(f"   OK: API Key mevcut")
        
        # Opportunity ID ile arama
        opportunities = sam.search_by_any_id(opportunity_id)
        
        if opportunities:
            opp = opportunities[0]
            print(f"   OK: Firsat bulundu")
            print(f"   Title: {opp.get('title', 'N/A')[:60]}...")
            print(f"   Notice ID: {opp.get('noticeId', 'N/A')}")
            
            # resourceLinks kontrolü
            resource_links = opp.get('resourceLinks', [])
            attachments = opp.get('attachments', [])
            raw_data = opp.get('raw_data', {})
            
            print(f"\n   resourceLinks (ust seviye): {len(resource_links)} adet")
            print(f"   attachments (ust seviye): {len(attachments)} adet")
            print(f"   raw_data mevcut: {bool(raw_data)}")
            
            if raw_data:
                raw_resource_links = raw_data.get('resourceLinks', [])
                raw_attachments = raw_data.get('attachments', [])
                print(f"   raw_data.resourceLinks: {len(raw_resource_links)} adet")
                print(f"   raw_data.attachments: {len(raw_attachments)} adet")
                
                if raw_resource_links:
                    print(f"   OK: raw_data içinde resourceLinks mevcut!")
                    for i, link in enumerate(raw_resource_links[:5]):
                        if isinstance(link, dict):
                            url = link.get('url', link.get('link', link.get('downloadUrl', 'N/A')))
                            title = link.get('title', link.get('name', f'Link {i+1}'))
                        else:
                            url = str(link)
                            title = f'Link {i+1}'
                        print(f"      {i+1}. {title}: {url[:60]}...")
                elif raw_attachments:
                    print(f"   OK: raw_data içinde attachments mevcut!")
                    for i, att in enumerate(raw_attachments[:5]):
                        if isinstance(att, dict):
                            url = att.get('url', att.get('link', att.get('downloadUrl', 'N/A')))
                            title = att.get('title', att.get('name', f'Attachment {i+1}'))
                        else:
                            url = str(att)
                            title = f'Attachment {i+1}'
                        print(f"      {i+1}. {title}: {url[:60]}...")
                else:
                    print(f"   UYARI: raw_data içinde resourceLinks/attachments yok")
                    # raw_data keys'lerini göster
                    print(f"   raw_data keys: {list(raw_data.keys())[:20]}")
                    
                    # Belki farklı bir key altında
                    for key in ['attachments', 'links', 'documents', 'files', 'resources']:
                        if key in raw_data:
                            print(f"   {key} key'i bulundu: {type(raw_data[key])}")
                            if isinstance(raw_data[key], list) and len(raw_data[key]) > 0:
                                print(f"      {len(raw_data[key])} adet")
        else:
            print(f"   UYARI: Firsat bulunamadi")
            
except Exception as e:
    print(f"   Hata: {e}")
    import traceback
    traceback.print_exc()

# 2. GSA Client ile test
try:
    from gsa_opportunities_client import GSAOpportunitiesClient
    
    print("\n2. GSA Client test...")
    gsa = GSAOpportunitiesClient()
    
    if not gsa.api_key:
        print("   UYARI: API Key bulunamadi")
    else:
        # Notice ID ile arama (opportunity ID'den notice ID'yi çıkar)
        # Önce opportunity details çek
        opportunities = gsa.search_by_any_id(opportunity_id)
        
        if opportunities:
            opp = opportunities[0]
            print(f"   OK: Firsat bulundu (GSA)")
            
            resource_links = opp.get('resourceLinks', [])
            attachments = opp.get('attachments', [])
            raw_data = opp.get('raw_data', {})
            
            print(f"   resourceLinks: {len(resource_links)} adet")
            print(f"   attachments: {len(attachments)} adet")
            print(f"   raw_data mevcut: {bool(raw_data)}")
            
            if raw_data:
                raw_resource_links = raw_data.get('resourceLinks', [])
                if raw_resource_links:
                    print(f"   OK: raw_data içinde resourceLinks mevcut!")
                    for i, link in enumerate(raw_resource_links[:5]):
                        if isinstance(link, dict):
                            url = link.get('url', link.get('link', 'N/A'))
                            print(f"      {i+1}. {url[:60]}...")
                        else:
                            print(f"      {i+1}. {str(link)[:60]}...")
            
except Exception as e:
    print(f"   Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test tamamlandi!")

