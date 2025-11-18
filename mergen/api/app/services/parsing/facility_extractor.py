import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_facility_features(text: str) -> List[Dict[str, Any]]:
    """Extract facility features from facility document text"""
    features = []
    
    # Common facility feature patterns
    feature_patterns = {
        "shuttle": [
            r'shuttle\s+service',
            r'airport\s+shuttle',
            r'complimentary\s+shuttle',
            r'free\s+shuttle',
            r'transportation\s+service'
        ],
        "wifi": [
            r'wi-?fi',
            r'wireless\s+internet',
            r'high-?speed\s+internet',
            r'complimentary\s+wi-?fi',
            r'free\s+wi-?fi'
        ],
        "parking": [
            r'parking',
            r'valet\s+parking',
            r'self-?park',
            r'complimentary\s+parking',
            r'free\s+parking'
        ],
        "breakout_rooms": [
            r'breakout\s+room',
            r'meeting\s+room',
            r'conference\s+room',
            r'small\s+group\s+room'
        ],
        "boardroom": [
            r'boardroom',
            r'executive\s+room',
            r'board\s+room'
        ],
        "av_equipment": [
            r'audio\s+visual',
            r'projector',
            r'microphone',
            r'sound\s+system',
            r'video\s+conferencing',
            r'presentation\s+equipment'
        ],
        "restaurant": [
            r'restaurant',
            r'dining',
            r'food\s+service',
            r'catering',
            r'meal\s+service'
        ],
        "fitness": [
            r'fitness\s+center',
            r'gym',
            r'exercise\s+room',
            r'workout\s+facility'
        ],
        "pool": [
            r'pool',
            r'swimming\s+pool',
            r'outdoor\s+pool'
        ],
        "business_center": [
            r'business\s+center',
            r'computer\s+room',
            r'work\s+station'
        ]
    }
    
    text_lower = text.lower()
    
    for feature_type, patterns in feature_patterns.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                features.append({
                    "name": feature_type,
                    "value": context,
                    "confidence": 1.0 if "complimentary" in context.lower() or "free" in context.lower() else 0.8
                })
    
    return features


def extract_room_capacity(text: str) -> Dict[str, int]:
    """Extract room capacity information"""
    capacity_info = {}
    
    # Patterns for different room types
    room_patterns = {
        "main_room": [
            r'main\s+room.*?(\d+)\s+people',
            r'general\s+session.*?(\d+)\s+people',
            r'plenary.*?(\d+)\s+people'
        ],
        "breakout_room": [
            r'breakout\s+room.*?(\d+)\s+people',
            r'small\s+group.*?(\d+)\s+people'
        ],
        "boardroom": [
            r'boardroom.*?(\d+)\s+people',
            r'executive\s+room.*?(\d+)\s+people'
        ]
    }
    
    text_lower = text.lower()
    
    for room_type, patterns in room_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                capacity_info[room_type] = int(match.group(1))
                break
    
    return capacity_info


def extract_distance_info(text: str) -> Dict[str, Any]:
    """Extract distance information (e.g., to airport, restaurants)"""
    distance_info = {}
    
    # Airport distance
    airport_patterns = [
        r'(\d+(?:\.\d+)?)\s+miles?\s+to\s+airport',
        r'airport.*?(\d+(?:\.\d+)?)\s+miles?',
        r'(\d+(?:\.\d+)?)\s+mi\s+airport'
    ]
    
    for pattern in airport_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            distance_info["airport_distance"] = float(match.group(1))
            break
    
    # Restaurant distance
    restaurant_patterns = [
        r'(\d+(?:\.\d+)?)\s+miles?\s+to\s+restaurant',
        r'restaurant.*?(\d+(?:\.\d+)?)\s+miles?',
        r'(\d+(?:\.\d+)?)\s+mi\s+restaurant'
    ]
    
    for pattern in restaurant_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            distance_info["restaurant_distance"] = float(match.group(1))
            break
    
    return distance_info


def extract_av_equipment_list(text: str) -> List[str]:
    """Extract list of AV equipment"""
    av_equipment = []
    
    # Common AV equipment patterns
    equipment_patterns = [
        r'projector',
        r'microphone',
        r'speaker',
        r'screen',
        r'video\s+conferencing',
        r'wireless\s+microphone',
        r'podium',
        r'lectern',
        r'whiteboard',
        r'flip\s+chart'
    ]
    
    text_lower = text.lower()
    
    for pattern in equipment_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            av_equipment.append(pattern.replace(r'\s+', ' '))
    
    return av_equipment


def process_facility_document(text: str) -> Dict[str, Any]:
    """Process facility document and extract structured data"""
    logger.info("Processing facility document")
    
    # Extract facility features
    features = extract_facility_features(text)
    
    # Extract room capacity
    room_capacity = extract_room_capacity(text)
    
    # Extract distance information
    distance_info = extract_distance_info(text)
    
    # Extract AV equipment
    av_equipment = extract_av_equipment_list(text)
    
    return {
        "features": features,
        "room_capacity": room_capacity,
        "distance_info": distance_info,
        "av_equipment": av_equipment,
        "total_features": len(features)
    }



