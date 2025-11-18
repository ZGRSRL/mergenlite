#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel Database Manager
Otel veritabanı oluşturur ve yönetir
"""

import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class HotelDatabase:
    """Otel veritabanı yöneticisi"""
    
    def __init__(self, db_path: str = "hotel_database.json"):
        self.db_path = Path(db_path)
        self.hotels = self._load_database()
    
    def _load_database(self) -> List[Dict[str, Any]]:
        """Veritabanını yükle"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading hotel database: {e}")
                return []
        return []
    
    def _save_database(self):
        """Veritabanını kaydet"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.hotels, f, indent=2, ensure_ascii=False)
            logger.info(f"[Hotel DB] Saved {len(self.hotels)} hotels to {self.db_path}")
        except Exception as e:
            logger.error(f"Error saving hotel database: {e}")
    
    def load_from_excel(self, excel_path: str) -> int:
        """
        Excel dosyasından otel bilgilerini yükle
        
        Args:
            excel_path: Excel dosyası yolu
        
        Returns:
            Yüklenen otel sayısı
        """
        try:
            df = pd.read_excel(excel_path)
            logger.info(f"[Hotel DB] Loaded Excel: {df.shape[0]} rows, {df.shape[1]} columns")
            logger.info(f"[Hotel DB] Columns: {df.columns.tolist()}")
            
            hotels = []
            for idx, row in df.iterrows():
                hotel = self._parse_hotel_row(row, df.columns)
                if hotel:
                    hotels.append(hotel)
            
            # Mevcut veritabanına ekle (duplicate kontrolü ile)
            existing_names = {h.get('name', '').lower() for h in self.hotels}
            new_count = 0
            
            for hotel in hotels:
                hotel_name_lower = hotel.get('name', '').lower()
                if hotel_name_lower and hotel_name_lower not in existing_names:
                    self.hotels.append(hotel)
                    existing_names.add(hotel_name_lower)
                    new_count += 1
            
            self._save_database()
            logger.info(f"[Hotel DB] Added {new_count} new hotels, total: {len(self.hotels)}")
            return new_count
            
        except Exception as e:
            logger.error(f"[Hotel DB] Error loading from Excel: {e}", exc_info=True)
            return 0
    
    def _parse_hotel_row(self, row: pd.Series, columns: List[str]) -> Optional[Dict[str, Any]]:
        """Excel satırından otel bilgisi çıkar"""
        try:
            # Excel kolonları: 'Hotel Name', 'Contact Email', 'Contact Phone', 'First Name', 'Last Name', 'Status', 'Date'
            hotel_name = str(row.get('Hotel Name', '')).strip()
            
            # İlk satır header ise atla
            if hotel_name == 'Hotel Name' or not hotel_name:
                return None
            
            # İsim ve email'den şehir/eyalet çıkarmaya çalış
            city = None
            state = None
            
            # Hotel name'den şehir çıkarmaya çalış (örn: "Hampton Inn & Suites San Antonio Northwest")
            if 'San Antonio' in hotel_name:
                city = 'San Antonio'
                state = 'Texas'
            elif 'Los Angeles' in hotel_name:
                city = 'Los Angeles'
                state = 'California'
            elif 'Houston' in hotel_name:
                city = 'Houston'
                state = 'Texas'
            elif 'Orlando' in hotel_name:
                city = 'Orlando'
                state = 'Florida'
            
            contact_email = str(row.get('Contact Email', '')).strip()
            contact_phone = str(row.get('Contact Phone', '')).strip()
            first_name = str(row.get('First Name', '')).strip()
            last_name = str(row.get('Last Name', '')).strip()
            status = str(row.get('Status', '')).strip()
            
            # Contact person oluştur
            contact_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
            
            hotel = {
                'name': hotel_name,
                'address': '',  # Excel'de yok
                'city': city,
                'state': state,
                'phone': contact_phone if contact_phone and contact_phone != 'nan' else None,
                'email': contact_email if contact_email and contact_email != 'nan' else None,
                'website': None,
                'contact_person': contact_name if contact_name and contact_name != 'nan' else None,
                'status': status if status and status != 'nan' else None,
                'room_count': None,  # Excel'de yok
                'rating': None,  # Excel'de yok
                'raw_data': {str(col): str(row.get(col, '')) for col in columns},
                'source': 'excel',
                'imported_at': datetime.now().isoformat()
            }
            
            return hotel
            
        except Exception as e:
            logger.warning(f"[Hotel DB] Error parsing row: {e}")
            return None
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Sayı parse et"""
        try:
            if pd.isna(value):
                return None
            return float(value)
        except:
            return None
    
    def search_hotels(
        self,
        location: Optional[str] = None,
        min_rooms: Optional[int] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Otel ara
        
        Args:
            location: Lokasyon (şehir, eyalet veya adres)
            min_rooms: Minimum oda sayısı
            city: Şehir
            state: Eyalet
            limit: Maksimum sonuç sayısı
        
        Returns:
            Eşleşen oteller listesi
        """
        results = []
        
        for hotel in self.hotels:
            score = 0
            
            # Lokasyon eşleşmesi
            if location:
                location_lower = location.lower()
                hotel_location = f"{hotel.get('city', '')} {hotel.get('state', '')} {hotel.get('address', '')}".lower()
                if location_lower in hotel_location or hotel_location in location_lower:
                    score += 10
            
            # Şehir eşleşmesi
            if city and hotel.get('city'):
                if city.lower() in hotel.get('city', '').lower():
                    score += 5
            
            # Eyalet eşleşmesi
            if state and hotel.get('state'):
                if state.lower() in hotel.get('state', '').lower():
                    score += 5
            
            # Oda sayısı kontrolü
            if min_rooms and hotel.get('room_count'):
                if hotel.get('room_count', 0) >= min_rooms:
                    score += 3
                else:
                    continue  # Minimum oda sayısını karşılamıyorsa atla
            
            if score > 0:
                hotel_copy = hotel.copy()
                hotel_copy['match_score'] = score
                results.append(hotel_copy)
        
        # Score'a göre sırala
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return results[:limit]
    
    def get_recommended_hotels(
        self,
        event_requirements: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Event gereksinimlerine göre önerilen otelleri bul
        
        Args:
            event_requirements: Event gereksinimleri (location, participants_target, vb.)
            limit: Maksimum öneri sayısı
        
        Returns:
            Önerilen oteller listesi
        """
        location = event_requirements.get('location', '')
        participants = event_requirements.get('participants_target') or event_requirements.get('participants_min')
        
        # Lokasyon parse et (örn: "Houston, Texas" -> city="Houston", state="Texas")
        city = None
        state = None
        if location:
            parts = location.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()
            else:
                city = location.strip()
        
        # Minimum oda sayısı hesapla (participants / 2, en az 10)
        min_rooms = None
        if participants:
            try:
                # participants string olabilir, int'e çevir
                participants_int = int(participants) if isinstance(participants, (str, int, float)) else 0
                if participants_int > 0:
                    min_rooms = max(int(participants_int / 2), 10)
            except (ValueError, TypeError):
                min_rooms = 10  # Varsayılan
        
        # Otel ara
        hotels = self.search_hotels(
            location=location,
            city=city,
            state=state,
            min_rooms=min_rooms,
            limit=limit * 2  # Daha fazla sonuç al, sonra filtrele
        )
        
        # Rating ve room_count'a göre sırala
        hotels.sort(key=lambda x: (
            x.get('rating', 0) or 0,
            x.get('room_count', 0) or 0
        ), reverse=True)
        
        return hotels[:limit]

