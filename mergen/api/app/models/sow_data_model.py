"""
SOWDataModel - Normalized Full Schema
Unified data model for RFQ analysis results.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class CalendarDay:
    """Represents a single day in the event calendar."""
    day: str  # e.g., "Day 1", "March 4"
    date: str  # YYYY-MM-DD format
    rooms: List[Dict[str, Any]] = field(default_factory=list)  # Room requirements for this day
    av_requirements: List[Dict[str, Any]] = field(default_factory=list)  # AV needs for this day
    fb_functions: List[Dict[str, Any]] = field(default_factory=list)  # F&B functions for this day


@dataclass
class SeatingLayout:
    """Structured seating layout from seating chart."""
    hollow_square: Optional[Dict[str, Any]] = None  # {capacity_min: int, capacity_max: int, location: str}
    classroom: List[Dict[str, Any]] = field(default_factory=list)  # [{location: str, capacity: int}]
    theater: Optional[Dict[str, Any]] = None  # {capacity: int, location: str}
    special_areas: List[Dict[str, Any]] = field(default_factory=list)  # Tech Team, AV Team, Court Reporter, etc.
    power_requirements: Optional[Dict[str, Any]] = None  # Extension cords, power strips, etc.


@dataclass
class SOWDataModel:
    """Normalized SOW data model - unified schema for all RFQ analysis results."""
    event_name: str
    agency: str
    solicitation_number: str
    dates: Dict[str, str]  # {start: "YYYY-MM-DD", end: "YYYY-MM-DD"}
    location: str
    
    # Core requirements
    sleeping_rooms: List[Dict[str, Any]] = field(default_factory=list)  # Daily breakdown
    function_space_calendar: List[CalendarDay] = field(default_factory=list)
    meeting_rooms: List[Dict[str, Any]] = field(default_factory=list)  # Meeting room setup details
    av_requirements: List[Dict[str, Any]] = field(default_factory=list)  # AV requirements
    food_beverage: List[Dict[str, Any]] = field(default_factory=list)  # F&B requirements
    
    # Commercial and compliance
    commercial_terms: Dict[str, Any] = field(default_factory=dict)
    compliance_clauses: Dict[str, Any] = field(default_factory=dict)  # {far_clauses: [...], edar_clauses: [...]}
    
    # Enhanced fields
    seating_layout: Optional[SeatingLayout] = None
    outreach_event: Optional[Dict[str, Any]] = None
    hybrid_meeting: Optional[Dict[str, Any]] = None
    court_reporter_audio: Optional[Dict[str, Any]] = None
    breakout_power: Optional[Dict[str, Any]] = None
    special_requirements: Optional[Dict[str, Any]] = None
    twenty_four_hour_hold: Optional[bool] = None
    
    # Metadata
    created_at: Optional[str] = None
    source_rfq_path: Optional[str] = None
    
    @classmethod
    def from_analyzer_json(
        cls,
        normalized_json: Dict[str, Any],
        seating_layout: Optional[Dict[str, Any]] = None,
    ) -> "SOWDataModel":
        """
        Create SOWDataModel from normalized analyzer JSON.
        
        Args:
            normalized_json: Normalized JSON from Pass 2 ReviewerAgent
            seating_layout: Optional seating layout dict from seating chart parser
            
        Returns:
            SOWDataModel instance
        """
        # Parse seating layout if provided
        parsed_seating_layout = None
        if seating_layout:
            parsed_seating_layout = SeatingLayout(
                hollow_square=seating_layout.get("hollow_square"),
                classroom=seating_layout.get("classroom", []),
                theater=seating_layout.get("theater"),
                special_areas=seating_layout.get("special_areas", []),
                power_requirements=seating_layout.get("power_requirements"),
            )
        
        # Parse function space calendar
        function_space_calendar = []
        function_space_data = normalized_json.get("function_space_calendar", [])
        if isinstance(function_space_data, list):
            for day_data in function_space_data:
                if isinstance(day_data, dict):
                    calendar_day = CalendarDay(
                        day=day_data.get("day", "TBD"),
                        date=day_data.get("date", "TBD"),
                        rooms=day_data.get("rooms", []),
                        av_requirements=day_data.get("av_requirements", []),
                        fb_functions=day_data.get("fb_functions", []),
                    )
                    function_space_calendar.append(calendar_day)
        
        # Extract dates
        dates = normalized_json.get("dates", {})
        if isinstance(dates, str):
            # If dates is a string, try to parse it
            dates = {"start": dates, "end": dates}
        elif not isinstance(dates, dict):
            dates = {}
        
        return cls(
            event_name=normalized_json.get("event_name", "TBD"),
            agency=normalized_json.get("agency", "TBD"),
            solicitation_number=normalized_json.get("solicitation_number", normalized_json.get("solicitation_number", "TBD")),
            dates=dates,
            location=normalized_json.get("location", "TBD"),
            sleeping_rooms=normalized_json.get("sleeping_rooms", []),
            function_space_calendar=function_space_calendar,
            meeting_rooms=normalized_json.get("meeting_rooms", []),
            av_requirements=normalized_json.get("av_requirements", []),
            food_beverage=normalized_json.get("food_beverage", normalized_json.get("f_and_b", [])),
            commercial_terms=normalized_json.get("commercial_terms", {}),
            compliance_clauses=normalized_json.get("compliance_clauses", {}),
            seating_layout=parsed_seating_layout,
            outreach_event=normalized_json.get("outreach_event"),
            hybrid_meeting=normalized_json.get("hybrid_meeting"),
            court_reporter_audio=normalized_json.get("court_reporter_audio"),
            breakout_power=normalized_json.get("breakout_power"),
            special_requirements=normalized_json.get("special_requirements"),
            twenty_four_hour_hold=normalized_json.get("twenty_four_hour_hold"),
            created_at=datetime.now().isoformat(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SOWDataModel to dictionary."""
        result = {
            "event_name": self.event_name,
            "agency": self.agency,
            "solicitation_number": self.solicitation_number,
            "dates": self.dates,
            "location": self.location,
            "sleeping_rooms": self.sleeping_rooms,
            "function_space_calendar": [
                {
                    "day": day.day,
                    "date": day.date,
                    "rooms": day.rooms,
                    "av_requirements": day.av_requirements,
                    "fb_functions": day.fb_functions,
                }
                for day in self.function_space_calendar
            ],
            "meeting_rooms": self.meeting_rooms,
            "av_requirements": self.av_requirements,
            "food_beverage": self.food_beverage,
            "commercial_terms": self.commercial_terms,
            "compliance_clauses": self.compliance_clauses,
        }
        
        if self.seating_layout:
            result["seating_layout"] = {
                "hollow_square": self.seating_layout.hollow_square,
                "classroom": self.seating_layout.classroom,
                "theater": self.seating_layout.theater,
                "special_areas": self.seating_layout.special_areas,
                "power_requirements": self.seating_layout.power_requirements,
            }
        
        if self.outreach_event:
            result["outreach_event"] = self.outreach_event
        if self.hybrid_meeting:
            result["hybrid_meeting"] = self.hybrid_meeting
        if self.court_reporter_audio:
            result["court_reporter_audio"] = self.court_reporter_audio
        if self.breakout_power:
            result["breakout_power"] = self.breakout_power
        if self.special_requirements:
            result["special_requirements"] = self.special_requirements
        if self.twenty_four_hour_hold is not None:
            result["twenty_four_hour_hold"] = self.twenty_four_hour_hold
        
        return result

