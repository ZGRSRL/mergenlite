from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db import get_db
from app.models.db_models import Opportunity, Hotel, EmailLog

router = APIRouter()

# --- Pydantic Models for Response ---

class HotelResponse(BaseModel):
    id: int
    name: str
    manager: Optional[str] = None
    status: str
    rating: Optional[float] = None
    price: Optional[str] = None
    lastUpdate: Optional[str] = None
    unread: int = 0

    class Config:
        orm_mode = True

class OpportunityDashboardResponse(BaseModel):
    id: int
    noticeId: Optional[str] = None
    title: str
    agency: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    totalHotels: int
    contacted: int
    replies: int
    negotiating: int
    status: str
    hotels: List[HotelResponse]

    class Config:
        orm_mode = True

# --- Helper to format relative time ---
def format_relative_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    now = datetime.utcnow() # Assuming UTC for simplicity, should match DB timezone
    diff = now - dt
    
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    
    if minutes < 1:
        return "Şimdi"
    if minutes < 60:
        return f"{int(minutes)} dk önce"
    if hours < 24:
        return f"{int(hours)} sa önce"
    if days < 7:
        return f"{int(days)} gün önce"
    return dt.strftime("%d %b")

# --- Endpoints ---

@router.get("/dashboard", response_model=List[OpportunityDashboardResponse])
def get_communication_dashboard(db: Session = Depends(get_db)):
    """
    Fetches the dashboard data: Opportunities -> Hotels -> Stats.
    """
    # Fetch active opportunities with their hotels
    opportunities = db.query(Opportunity).options(joinedload(Opportunity.hotels)).filter(Opportunity.status != 'archived').all()
    
    dashboard_data = []
    
    for opp in opportunities:
        hotels = opp.hotels
        
        # Calculate stats
        total_hotels = len(hotels)
        contacted = sum(1 for h in hotels if h.status in ['sent', 'replied', 'negotiating', 'rejected', 'booked'])
        replies = sum(1 for h in hotels if h.status in ['replied', 'negotiating', 'booked'])
        negotiating = sum(1 for h in hotels if h.status == 'negotiating')
        
        # Format hotels
        hotel_list = []
        for h in hotels:
            hotel_list.append(HotelResponse(
                id=h.id,
                name=h.name,
                manager=h.manager_name,
                status=h.status,
                rating=h.rating,
                price=h.price_quote,
                lastUpdate=format_relative_time(h.last_contact_at), # You might need to adjust timezone handling
                unread=h.unread_count
            ))
            
        # Format Opportunity
        dashboard_data.append(OpportunityDashboardResponse(
            id=opp.id,
            noticeId=opp.notice_id,
            title=opp.title,
            agency=opp.agency,
            location=opp.place_of_performance, # Or parse from raw_data if needed
            deadline=opp.response_deadline.strftime("%d %b %Y") if opp.response_deadline else None,
            totalHotels=total_hotels,
            contacted=contacted,
            replies=replies,
            negotiating=negotiating,
            status=opp.status,
            hotels=hotel_list
        ))
        
    return dashboard_data


# --- Chat Endpoints ---

class MessageResponse(BaseModel):
    id: int
    type: str  # 'in', 'out', 'system'
    text: str
    time: str
    
    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    hotel_id: int
    text: str
    direction: str = "out"  # 'out' for user sending, 'in' for receiving (usually via webhook)

@router.get("/messages/{hotel_id}", response_model=List[MessageResponse])
def get_hotel_messages(hotel_id: int, db: Session = Depends(get_db)):
    """
    Fetch chat history for a specific hotel.
    """
    logs = db.query(EmailLog).filter(
        EmailLog.hotel_id == hotel_id
    ).order_by(EmailLog.created_at.asc()).all()
    
    messages = []
    for log in logs:
        msg_type = 'out' if log.direction == 'outbound' else 'in'
        # Simple logic to detect system messages if needed, or use a specific flag
        
        messages.append(MessageResponse(
            id=log.id,
            type=msg_type,
            text=log.raw_body or log.subject or "(No content)",
            time=format_relative_time(log.created_at)
        ))
        
    return messages

@router.post("/messages", response_model=MessageResponse)
def send_message(payload: MessageCreate, db: Session = Depends(get_db)):
    """
    Send a message (log it as outbound email/chat).
    In a real app, this would also trigger the email sending service.
    """
    # Verify hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == payload.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
        
    # Create log
    new_log = EmailLog(
        hotel_id=payload.hotel_id,
        opportunity_id=hotel.opportunity_id, # Link to parent opportunity
        direction='outbound' if payload.direction == 'out' else 'inbound',
        raw_body=payload.text,
        subject="Chat Message", # Placeholder
        created_at=datetime.utcnow()
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return MessageResponse(
        id=new_log.id,
        type=payload.direction,
        text=new_log.raw_body,
        time="Just now"
    )
