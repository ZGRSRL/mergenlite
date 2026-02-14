#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel Recommendation Agent
İlan içindeki adrese en yakın otelleri bulur ve önerir
"""

import json
import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Geocoding için geopy
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    logger.warning("geopy not available, distance calculation will be limited")

# AutoGen import
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, hotel recommendation will be limited")


class HotelRecommendationAgent:
    """Otel önerisi ajanı - adres bazlı mesafe hesaplama yapar"""
    
    def __init__(self, hotel_db=None):
        """
        Args:
            hotel_db: HotelDatabase instance
        """
        self.hotel_db = hotel_db
        self.geocoder = None
        if GEOPY_AVAILABLE:
            try:
                # Nominatim kullan (ücretsiz, rate limit var)
                self.geocoder = Nominatim(user_agent="mergenlite_hotel_agent")
            except Exception as e:
                logger.warning(f"Geocoder initialization failed: {e}")
    
    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Adresi koordinatlara çevir (lat, lon)
        
        Args:
            address: Adres string'i
            
        Returns:
            (latitude, longitude) tuple veya None
        """
        if not self.geocoder or not address:
            return None
        
        try:
            # Rate limit için kısa bekleme
            import time
            time.sleep(1)  # Nominatim rate limit: 1 request/second
            
            location = self.geocoder.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.warning(f"Geocoding failed for '{address}': {e}")
        
        return None
    
    def _calculate_distance(
        self, 
        coord1: Tuple[float, float], 
        coord2: Tuple[float, float]
    ) -> float:
        """
        İki koordinat arasındaki mesafeyi hesapla (miles)
        
        Args:
            coord1: (lat, lon) tuple
            coord2: (lat, lon) tuple
            
        Returns:
            Mesafe (miles)
        """
        if not GEOPY_AVAILABLE:
            # Basit Haversine formülü (yaklaşık)
            lat1, lon1 = coord1
            lat2, lon2 = coord2
            
            R = 3959  # Earth radius in miles
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        try:
            return geodesic(coord1, coord2).miles
        except Exception as e:
            logger.warning(f"Distance calculation failed: {e}")
            return float('inf')
    
    def _get_hotel_coordinates(self, hotel: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Otel bilgisinden koordinatları çıkar
        
        Args:
            hotel: Otel dict (name, city, state, address)
            
        Returns:
            (lat, lon) tuple veya None
        """
        # Önce tam adres dene
        address_parts = []
        if hotel.get('address'):
            address_parts.append(hotel['address'])
        if hotel.get('city'):
            address_parts.append(hotel['city'])
        if hotel.get('state'):
            address_parts.append(hotel['state'])
        
        if address_parts:
            full_address = ', '.join(address_parts) + ', USA'
            coords = self._geocode_address(full_address)
            if coords:
                return coords
        
        # Sadece şehir/eyalet ile dene
        if hotel.get('city') and hotel.get('state'):
            city_state = f"{hotel['city']}, {hotel['state']}, USA"
            coords = self._geocode_address(city_state)
            if coords:
                return coords
        
        # Sadece otel ismi + şehir ile dene
        if hotel.get('name') and hotel.get('city'):
            hotel_address = f"{hotel['name']}, {hotel['city']}, {hotel.get('state', '')}, USA"
            coords = self._geocode_address(hotel_address)
            if coords:
                return coords
        
        return None
    
    def recommend_hotels_by_distance(
        self,
        opportunity_address: str,
        event_requirements: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        İlan adresine en yakın otelleri bul
        
        Args:
            opportunity_address: İlan içindeki adres (place_of_performance veya location)
            event_requirements: Event gereksinimleri (participants, vb.)
            limit: Maksimum öneri sayısı
            
        Returns:
            Mesafeye göre sıralanmış otel listesi (distance_miles field ile)
        """
        if not self.hotel_db:
            logger.error("HotelDatabase not provided")
            return []
        
        # İlan adresini koordinatlara çevir
        opportunity_coords = self._geocode_address(opportunity_address)
        if not opportunity_coords:
            logger.warning(f"Could not geocode opportunity address: {opportunity_address}")
            # Fallback: Eski yöntemi kullan (şehir bazlı)
            return self._fallback_recommendation(event_requirements, limit)
        
        logger.info(f"Opportunity coordinates: {opportunity_coords}")
        
        # Event gereksinimlerinden lokasyon bilgisi al
        location = event_requirements.get('location', '') or opportunity_address
        participants = event_requirements.get('participants_target') or event_requirements.get('participants_min')
        
        # Lokasyon parse et
        city = None
        state = None
        if location:
            parts = location.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()
            else:
                city = location.strip()
        
        # Minimum oda sayısı hesapla
        min_rooms = None
        if participants:
            try:
                participants_int = int(participants) if isinstance(participants, (str, int, float)) else 0
                if participants_int > 0:
                    min_rooms = max(int(participants_int / 2), 10)
            except (ValueError, TypeError):
                min_rooms = 10
        
        # Otelleri ara (daha geniş arama)
        hotels = self.hotel_db.search_hotels(
            location=location,
            city=city,
            state=state,
            min_rooms=min_rooms,
            limit=limit * 3  # Daha fazla sonuç al, sonra mesafeye göre filtrele
        )
        
        # Her otel için mesafe hesapla
        hotels_with_distance = []
        for hotel in hotels:
            hotel_coords = self._get_hotel_coordinates(hotel)
            if hotel_coords:
                distance = self._calculate_distance(opportunity_coords, hotel_coords)
                hotel['distance_miles'] = round(distance, 2)
                hotel['coordinates'] = hotel_coords
                hotels_with_distance.append(hotel)
            else:
                # Koordinat bulunamadı, mesafe bilgisi yok
                hotel['distance_miles'] = None
                hotels_with_distance.append(hotel)
        
        # Mesafeye göre sırala (None olanlar en sonda)
        hotels_with_distance.sort(key=lambda x: (
            x.get('distance_miles') is None,  # None olanlar False (öncelikli değil)
            x.get('distance_miles') or float('inf')
        ))
        
        # En yakın otelleri döndür
        return hotels_with_distance[:limit]
    
    def _fallback_recommendation(
        self,
        event_requirements: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Geocoding başarısız olursa eski yöntemi kullan (şehir bazlı)
        """
        if not self.hotel_db:
            return []
        
        location = event_requirements.get('location', '')
        participants = event_requirements.get('participants_target') or event_requirements.get('participants_min')
        
        city = None
        state = None
        if location:
            parts = location.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()
            else:
                city = location.strip()
        
        min_rooms = None
        if participants:
            try:
                participants_int = int(participants) if isinstance(participants, (str, int, float)) else 0
                if participants_int > 0:
                    min_rooms = max(int(participants_int / 2), 10)
            except (ValueError, TypeError):
                min_rooms = 10
        
        hotels = self.hotel_db.search_hotels(
            location=location,
            city=city,
            state=state,
            min_rooms=min_rooms,
            limit=limit * 2
        )
        
        # Rating ve room_count'a göre sırala
        hotels.sort(key=lambda x: (
            x.get('rating', 0) or 0,
            x.get('room_count', 0) or 0
        ), reverse=True)
        
        return hotels[:limit]


def make_hotel_recommendation_agent(
    llm_config: Optional[Dict] = None,
    hotel_db=None
) -> Optional[HotelRecommendationAgent]:
    """
    Hotel Recommendation Agent oluştur
    
    Args:
        llm_config: LLM konfigürasyonu (opsiyonel, şu an kullanılmıyor)
        hotel_db: HotelDatabase instance
        
    Returns:
        HotelRecommendationAgent instance
    """
    return HotelRecommendationAgent(hotel_db=hotel_db)


