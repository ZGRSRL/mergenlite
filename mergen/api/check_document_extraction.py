#!/usr/bin/env python3
"""Doküman extract sorununu kontrol et."""
import requests
import json

API_BASE = "http://localhost:8000"

# Get analysis result 183
resp = requests.get(f"{API_BASE}/api/pipeline/results/183")
if resp.status_code != 200:
    print("❌ Analysis result bulunamadı!")
    exit(1)

data = resp.json()
result_json = json.loads(data['result_json']) if isinstance(data.get('result_json'), str) else data.get('result_json', {})

print("=== Doküman Extract Analizi ===\n")

# Check analyzed documents
docs = result_json.get('analyzed_documents', [])
print(f"Toplam Doküman: {len(docs)}\n")

for i, doc in enumerate(docs, 1):
    print(f"Doküman {i}:")
    print(f"  İsim: {doc.get('attachment_name', 'N/A')}")
    print(f"  Text Length: {doc.get('text_length', 0)}")
    print(f"  Word Count: {doc.get('word_count', 0)}")
    print(f"  Error: {doc.get('error', 'Yok')}")
    
    extracted = doc.get('extracted_text', '')
    if extracted:
        print(f"  Extracted Text (ilk 200 karakter): {extracted[:200]}")
    else:
        print(f"  Extracted Text: BOŞ!")
    print()

# Check attachments
print("\n=== Attachment Durumu ===\n")
att_resp = requests.get(f"{API_BASE}/api/opportunities/1/attachments")
if att_resp.status_code == 200:
    atts = att_resp.json()
    print(f"Toplam Attachment: {len(atts)}\n")
    
    for i, att in enumerate(atts[:5], 1):
        print(f"Attachment {i}:")
        print(f"  İsim: {att.get('name', 'N/A')}")
        print(f"  Downloaded: {att.get('downloaded', False)}")
        print(f"  Local Path: {att.get('local_path', 'N/A')}")
        print(f"  MIME Type: {att.get('mime_type', 'N/A')}")
        print()


"""Doküman extract sorununu kontrol et."""
import requests
import json

API_BASE = "http://localhost:8000"

# Get analysis result 183
resp = requests.get(f"{API_BASE}/api/pipeline/results/183")
if resp.status_code != 200:
    print("❌ Analysis result bulunamadı!")
    exit(1)

data = resp.json()
result_json = json.loads(data['result_json']) if isinstance(data.get('result_json'), str) else data.get('result_json', {})

print("=== Doküman Extract Analizi ===\n")

# Check analyzed documents
docs = result_json.get('analyzed_documents', [])
print(f"Toplam Doküman: {len(docs)}\n")

for i, doc in enumerate(docs, 1):
    print(f"Doküman {i}:")
    print(f"  İsim: {doc.get('attachment_name', 'N/A')}")
    print(f"  Text Length: {doc.get('text_length', 0)}")
    print(f"  Word Count: {doc.get('word_count', 0)}")
    print(f"  Error: {doc.get('error', 'Yok')}")
    
    extracted = doc.get('extracted_text', '')
    if extracted:
        print(f"  Extracted Text (ilk 200 karakter): {extracted[:200]}")
    else:
        print(f"  Extracted Text: BOŞ!")
    print()

# Check attachments
print("\n=== Attachment Durumu ===\n")
att_resp = requests.get(f"{API_BASE}/api/opportunities/1/attachments")
if att_resp.status_code == 200:
    atts = att_resp.json()
    print(f"Toplam Attachment: {len(atts)}\n")
    
    for i, att in enumerate(atts[:5], 1):
        print(f"Attachment {i}:")
        print(f"  İsim: {att.get('name', 'N/A')}")
        print(f"  Downloaded: {att.get('downloaded', False)}")
        print(f"  Local Path: {att.get('local_path', 'N/A')}")
        print(f"  MIME Type: {att.get('mime_type', 'N/A')}")
        print()

