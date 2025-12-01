import requests
import json

def find_opportunities_with_attachments():
    try:
        # Get all opportunities
        response = requests.get("http://localhost:8001/api/opportunities?limit=50")
        opportunities = response.json()
        
        print(f"=== Checking {len(opportunities)} opportunities for attachments ===\n")
        
        opps_with_attachments = []
        
        for opp in opportunities:
            opp_id = opp.get('id')
            title = opp.get('title', 'N/A')[:50]
            
            # Check attachments
            att_response = requests.get(f"http://localhost:8001/api/opportunities/{opp_id}/attachments")
            attachments = att_response.json()
            
            if attachments and len(attachments) > 0:
                downloaded = [att for att in attachments if att.get('downloaded')]
                opps_with_attachments.append({
                    'id': opp_id,
                    'title': title,
                    'total_attachments': len(attachments),
                    'downloaded': len(downloaded)
                })
                print(f"✅ ID {opp_id}: {title}")
                print(f"   Attachments: {len(attachments)}, Downloaded: {len(downloaded)}")
                for att in attachments[:3]:  # Show first 3
                    print(f"     - {att.get('name')}: downloaded={att.get('downloaded')}")
        
        print(f"\n=== Summary ===")
        print(f"Total opportunities with attachments: {len(opps_with_attachments)}")
        
        if opps_with_attachments:
            best = max(opps_with_attachments, key=lambda x: x['downloaded'])
            print(f"\n🎯 Best opportunity for testing:")
            print(f"   ID: {best['id']}")
            print(f"   Title: {best['title']}")
            print(f"   Downloaded attachments: {best['downloaded']}/{best['total_attachments']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_opportunities_with_attachments()
