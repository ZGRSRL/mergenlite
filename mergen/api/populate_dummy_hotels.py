import sys
import os
import random
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models.db_models import Opportunity, Hotel

def populate_hotels():
    db = SessionLocal()
    try:
        # Find an active opportunity
        opportunity = db.query(Opportunity).filter(Opportunity.status == 'active').first()
        
        if not opportunity:
            print("No active opportunity found to populate hotels for.")
            return

        print(f"Populating hotels for Opportunity: {opportunity.title} (ID: {opportunity.id})")

        # Clear existing hotels for this opportunity to avoid duplicates if run multiple times
        db.query(Hotel).filter(Hotel.opportunity_id == opportunity.id).delete()
        db.commit()

        chains = ['Hilton', 'Marriott', 'Hyatt', 'Sheraton', 'Holiday Inn', 'Ritz Carlton', 'Four Seasons', 'Best Western']
        locations = ['Downtown', 'Airport', 'North', 'Conference Center', 'Resort', 'City Center', 'Grand']
        statuses = ['queued', 'sent', 'replied', 'negotiating', 'rejected']

        hotels_to_create = []
        for i in range(25):
            chain = random.choice(chains)
            loc = random.choice(locations)
            name = f"{chain} {loc} {i+1}"
            status = random.choice(statuses)
            
            # Generate realistic data based on status
            unread = 0
            price = None
            if status in ['replied', 'negotiating']:
                unread = random.randint(0, 3)
                price = f"${random.randint(120, 350)}"
            
            last_contact = datetime.utcnow() - timedelta(minutes=random.randint(1, 10000))

            hotel = Hotel(
                opportunity_id=opportunity.id,
                name=name,
                manager_name=f"Manager {i+1}",
                email=f"manager{i+1}@{chain.lower().replace(' ', '')}.com",
                phone=f"555-01{i:02d}",
                status=status,
                rating=round(random.uniform(3.5, 5.0), 1),
                price_quote=price,
                unread_count=unread,
                last_contact_at=last_contact
            )
            hotels_to_create.append(hotel)

        db.add_all(hotels_to_create)
        db.commit()
        print(f"Successfully added {len(hotels_to_create)} dummy hotels.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_hotels()
