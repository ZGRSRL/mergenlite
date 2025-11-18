#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOW & Mail Agent
Fırsat analizinden otomatik SOW ve mail şablonu oluşturur
Sample SOW formatını kullanarak profesyonel SOW ve mail hazırlar
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from llm_client import (
    call_logged_llm,
    extract_message_text,
    LLMNotAvailableError,
)

logger = logging.getLogger(__name__)

# AutoGen import
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, SOW generation will be limited")

# Document processing
try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    logger.warning("DocumentProcessor not available")


class SOWMailAgent:
    """SOW ve Mail oluşturan ajan"""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """
        Args:
            llm_config: LLM konfigürasyonu
        """
        self.llm_config = llm_config
        self.sample_sow_template = None
        self._load_sample_sow_template()
    
    def _load_sample_sow_template(self):
        """Sample SOW formatını yükle"""
        sample_sow_path = Path("samples") / "SAMPLE SOW FOR CHTGPT.pdf"
        
        if not sample_sow_path.exists():
            logger.warning("Sample SOW not found, using default template")
            self.sample_sow_template = self._get_default_template()
            return
        
        try:
            if DOCUMENT_PROCESSOR_AVAILABLE:
                processor = DocumentProcessor()
                result = processor.process_file_from_path(str(sample_sow_path))
                
                if result.get('success'):
                    self.sample_sow_template = result['data'].get('text', '')
                    logger.info(f"[SOW Agent] Loaded sample SOW template ({len(self.sample_sow_template)} chars)")
                else:
                    logger.warning(f"Failed to load sample SOW: {result.get('error')}")
                    self.sample_sow_template = self._get_default_template()
            else:
                # Fallback: PDF'den basit text extraction
                try:
                    import pdfplumber
                    with pdfplumber.open(sample_sow_path) as pdf:
                        text_parts = []
                        for page in pdf.pages[:5]:  # İlk 5 sayfa
                            text_parts.append(page.extract_text() or '')
                        self.sample_sow_template = '\n\n'.join(text_parts)
                        logger.info(f"[SOW Agent] Loaded sample SOW from PDF ({len(self.sample_sow_template)} chars)")
                except Exception as e:
                    logger.warning(f"PDF extraction failed: {e}")
                    self.sample_sow_template = self._get_default_template()
        except Exception as e:
            logger.error(f"Error loading sample SOW: {e}", exc_info=True)
            self.sample_sow_template = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Varsayılan SOW şablonu"""
        return """
STATEMENT OF WORK (SOW)
FOR HOTEL ACCOMMODATIONS AND MEETING SPACE

1. BACKGROUND
[Project background and purpose]

2. SCOPE OF WORK
2.1 Lodging Requirements
- Room block requirements
- Room types and quantities
- Check-in/check-out dates
- Special accommodations (ADA, etc.)

2.2 Meeting Space Requirements
- Conference room requirements
- AV equipment needs
- Setup requirements
- Capacity requirements

2.3 Additional Services
- Shuttle services
- Parking
- F&B requirements
- Other services

3. DELIVERABLES
[List of deliverables]

4. PERIOD OF PERFORMANCE
[Start date] through [End date]

5. LOCATION
[City, State, Address]

6. TERMS AND CONDITIONS
[Payment terms, cancellation policy, etc.]

7. COMPLIANCE REQUIREMENTS
- FAR clauses
- Tax exemption
- IPP invoicing
- Other compliance items
"""
    
    def generate_sow(
        self,
        report_data: Dict[str, Any],
        opportunity_info: Optional[Dict[str, Any]] = None,
        vendor_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analiz sonuçlarından SOW oluştur
        
        Args:
            report_data: Analiz raporu (report.json içeriği)
            opportunity_info: Fırsat bilgileri
            vendor_profile: Vendor profile bilgileri
        
        Returns:
            {
                'sow_text': str,  # SOW metni (Markdown)
                'sow_html': str,  # SOW HTML formatı
                'sow_pdf_path': Optional[str]  # PDF yolu (eğer oluşturulduysa)
            }
        """
        # Verileri hazırla
        opp_info = opportunity_info or report_data.get('opportunity_info', {})
        event_req = report_data.get('event_requirements', {})
        commercial = report_data.get('commercial_terms', {})
        compliance = report_data.get('compliance', {})
        
        # LLM ile SOW oluştur
        if AUTOGEN_AVAILABLE and self.llm_config:
            sow_text = self._generate_sow_with_llm(
                report_data, opp_info, vendor_profile
            )
        else:
            # Fallback: Template-based generation
            sow_text = self._generate_sow_from_template(
                opp_info, event_req, commercial, compliance, vendor_profile
            )
        
        # HTML formatı oluştur
        sow_html = self._convert_markdown_to_html(sow_text)
        
        # PDF oluşturma (opsiyonel - output_folder varsa)
        sow_pdf_path = None
        sow_pdf_hotel_path = None
        
        return {
            'sow_text': sow_text,
            'sow_html': sow_html,
            'sow_pdf_path': sow_pdf_path,  # Internal PDF
            'sow_pdf_hotel_path': sow_pdf_hotel_path  # Hotel PDF
        }
    
    def generate_sow_pdfs(
        self,
        sow_result: Dict[str, Any],
        output_folder: str,
        opportunity_code: str,
        report_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        İki PDF oluştur: biri internal (kullanıcıya), diğeri hotel için (otellere gönderilecek)
        Ayrıca GPT formatında Hotel SOW PDF'i de oluşturur (analiz verileriyle doldurulmuş)
        
        Args:
            sow_result: generate_sow() çıktısı
            output_folder: Çıktı klasörü
            opportunity_code: Fırsat kodu
            report_data: Analiz verileri (GPT formatı PDF için)
        
        Returns:
            {
                'internal_pdf': str,  # Internal PDF yolu
                'hotel_pdf': str,  # Hotel PDF yolu (markdown'dan)
                'hotel_gpt_pdf': str  # Hotel GPT formatı PDF yolu (analiz verileriyle doldurulmuş)
            }
        """
        from pathlib import Path
        from sow_pdf_generator import markdown_to_pdf, generate_gpt_style_sow_pdf
        
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        sow_text = sow_result.get('sow_text', '')
        
        # Internal PDF (kullanıcıya - tüm detaylar dahil)
        internal_pdf_path = folder / f"sow_internal_{opportunity_code}.pdf"
        try:
            markdown_to_pdf(
                markdown_text=sow_text,
                output_path=str(internal_pdf_path),
                title=f"Statement of Work (SOW) - Internal - {opportunity_code}"
            )
            logger.info(f"[SOW PDF] Internal PDF created: {internal_pdf_path}")
        except Exception as e:
            logger.error(f"[SOW PDF] Error creating internal PDF: {e}", exc_info=True)
            internal_pdf_path = None
        
        # Hotel PDF (otellere gönderilecek - markdown'dan)
        hotel_sow_text = self._create_hotel_version_sow(sow_text)
        hotel_pdf_path = folder / f"sow_hotel_{opportunity_code}.pdf"
        try:
            logger.info(f"[SOW PDF] Creating hotel PDF: {hotel_pdf_path}")
            logger.info(f"[SOW PDF] Hotel SOW text length: {len(hotel_sow_text) if hotel_sow_text else 0}")
            
            if not hotel_sow_text or len(hotel_sow_text.strip()) == 0:
                logger.warning(f"[SOW PDF] Hotel SOW text is empty, using full SOW text")
                hotel_sow_text = sow_text
            
            logger.info(f"[SOW PDF] Calling markdown_to_pdf for hotel PDF...")
            success = markdown_to_pdf(
                markdown_text=hotel_sow_text,
                output_path=str(hotel_pdf_path),
                title=f"Statement of Work (SOW) - {opportunity_code}"
            )
            logger.info(f"[SOW PDF] markdown_to_pdf returned: {success}")
            logger.info(f"[SOW PDF] Hotel PDF exists: {hotel_pdf_path.exists()}")
            
            if success and hotel_pdf_path.exists():
                file_size = hotel_pdf_path.stat().st_size
                logger.info(f"[SOW PDF] ✅ Hotel PDF created successfully: {hotel_pdf_path} ({file_size} bytes)")
            else:
                logger.error(f"[SOW PDF] ❌ Hotel PDF creation failed - success={success}, exists={hotel_pdf_path.exists()}")
                if hotel_pdf_path.exists():
                    file_size = hotel_pdf_path.stat().st_size
                    logger.warning(f"[SOW PDF] File exists but success=False, size={file_size} bytes")
                    # Dosya varsa kullan
                else:
                    hotel_pdf_path = None
        except Exception as e:
            logger.error(f"[SOW PDF] ❌ Error creating hotel PDF: {e}", exc_info=True)
            import traceback
            logger.error(f"[SOW PDF] Traceback: {traceback.format_exc()}")
            hotel_pdf_path = None
        
        # GPT formatında Hotel SOW PDF (analiz verileriyle doldurulmuş)
        hotel_gpt_pdf_path = folder / f"sow_hotel_gpt_{opportunity_code}.pdf"
        try:
            logger.info(f"[SOW PDF] ========== Creating GPT format Hotel SOW PDF ==========")
            logger.info(f"[SOW PDF] Output path: {hotel_gpt_pdf_path}")
            logger.info(f"[SOW PDF] Report data available: {report_data is not None}")
            logger.info(f"[SOW PDF] SOW text available: {bool(sow_text)}")
            
            # Analiz verilerinden ve SOW metninden SOW verilerini çıkar
            if report_data:
                logger.info(f"[SOW PDF] Extracting SOW data from report_data and sow_text...")
                sow_data = self._extract_sow_data_for_gpt_pdf(report_data, sow_text)
                logger.info(f"[SOW PDF] Extracted SOW data keys: {list(sow_data.keys()) if sow_data else 'None'}")
            else:
                logger.warning(f"[SOW PDF] No report_data provided, using placeholder data")
                sow_data = None
            
            logger.info(f"[SOW PDF] Calling generate_gpt_style_sow_pdf...")
            success = generate_gpt_style_sow_pdf(
                output_path=str(hotel_gpt_pdf_path),
                opportunity_code=opportunity_code,
                sow_data=sow_data
            )
            logger.info(f"[SOW PDF] generate_gpt_style_sow_pdf returned: {success}")
            logger.info(f"[SOW PDF] File exists check: {hotel_gpt_pdf_path.exists()}")
            
            if success and hotel_gpt_pdf_path.exists():
                file_size = hotel_gpt_pdf_path.stat().st_size
                logger.info(f"[SOW PDF] ✅✅✅ GPT format Hotel SOW PDF created successfully!")
                logger.info(f"[SOW PDF] File: {hotel_gpt_pdf_path}")
                logger.info(f"[SOW PDF] Size: {file_size} bytes")
            else:
                logger.error(f"[SOW PDF] ❌❌❌ GPT format Hotel SOW PDF creation failed!")
                logger.error(f"[SOW PDF] Success: {success}, Exists: {hotel_gpt_pdf_path.exists()}")
                hotel_gpt_pdf_path = None
        except Exception as e:
            logger.error(f"[SOW PDF] ❌❌❌ Exception creating GPT format Hotel SOW PDF: {e}", exc_info=True)
            import traceback
            logger.error(f"[SOW PDF] Traceback: {traceback.format_exc()}")
            hotel_gpt_pdf_path = None
        
        return {
            'internal_pdf': str(internal_pdf_path) if internal_pdf_path else None,
            'hotel_pdf': str(hotel_pdf_path) if hotel_pdf_path else None,
            'hotel_gpt_pdf': str(hotel_gpt_pdf_path) if hotel_gpt_pdf_path else None
        }
    
    def _extract_sow_data_for_gpt_pdf(self, report_data: Dict[str, Any], sow_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiz verilerinden ve SOW metninden GPT formatı PDF için SOW verilerini çıkar
        
        Args:
            report_data: Analiz raporu verileri
            sow_text: LLM tarafından oluşturulan SOW metni (opsiyonel, daha detaylı bilgi için)
        
        Returns:
            GPT formatı PDF için SOW verileri
        """
        opp_info = report_data.get('opportunity_info', {})
        event_req = report_data.get('event_requirements', {})
        commercial = report_data.get('commercial_terms', {})
        compliance = report_data.get('compliance', {})
        
        # Date range'i parse et
        date_range = event_req.get('date_range', 'TBD')
        start_date = self._parse_start_date(date_range)
        end_date = self._parse_end_date(date_range)
        
        # Participants
        participants_raw = event_req.get('participants_target', 'unknown')
        try:
            participants_int = int(participants_raw) if participants_raw and str(participants_raw).lower() not in ['unknown', 'tbd', ''] else 0
        except (ValueError, TypeError):
            participants_int = 0
        
        # Haftalık tablo verileri için tarihleri hazırla
        sow_data = {
            'solicitation_number': opp_info.get('solicitation_number', 'TBD'),
            'agency': opp_info.get('agency', 'TBD'),
            'event_title': opp_info.get('title', 'TBD'),
            'meeting_name': opp_info.get('title', 'TBD'),
            'meeting_dates': date_range,
            'date_range': date_range,
            'room_block': event_req.get('room_block_plan', 'TBD'),
            'total_participants': str(participants_int) if participants_int > 0 else 'TBD',
            'room_block_notes': f"Room block requested may be amended slightly. Room Block of {participants_int if participants_int > 0 else 'TBD'} participants. If fewer than {participants_int if participants_int > 0 else 'TBD'} rooms are reserved by the hold end date, no attrition or any other fees or penalties will be assessed.",
            'payment_terms': commercial.get('payment_terms', 'Net 30 days'),
            'tax_exempt': 'Yes' if commercial.get('tax_exempt', False) else 'No',
            'e_invoicing_ipp': 'Yes' if commercial.get('e_invoicing_ipp', False) else 'No',
            'cancellation_penalties': commercial.get('cancellation_penalties', 'As specified in contract'),
            'far_52_212_4': 'Yes' if compliance.get('far_52_212_4', False) else 'No',
            'far_52_212_5': 'Yes' if compliance.get('far_52_212_5', False) else 'No',
            'far_52_204_24_25_26': 'Yes' if compliance.get('far_52_204_24_25_26', False) else 'No',
            'security_telecom_restrictions': 'Yes' if compliance.get('security_telecom_restrictions', False) else 'No',
            'bytedance_restriction': 'Yes' if compliance.get('bytedance_restriction', False) else 'No',
            'other_mandatory_clauses': ', '.join(compliance.get('other_mandatory_clauses', [])) if isinstance(compliance.get('other_mandatory_clauses'), list) else str(compliance.get('other_mandatory_clauses', 'N/A')),
            'refreshments': event_req.get('fnb_requirements', 'Light refreshments provided once in the morning and once during a PM break each meeting day.'),
            'pre_con_meeting': event_req.get('special_logistics', 'Pre-conference meeting with hotel staff.'),
            # Analiz verilerinden ve SOW metninden detaylı bilgileri çıkar
            'registration_area_details': self._extract_registration_area_details(event_req, participants_int, sow_text),
            'general_session_details': self._extract_general_session_details(event_req, participants_int, sow_text),
            'breakout_rooms_details': self._extract_breakout_rooms_details(event_req, sow_text),
            'logistics_room_details': self._extract_logistics_room_details(event_req, sow_text)
        }
        
        # Haftalık tablo verileri (eğer tarih bilgisi varsa)
        if date_range and date_range.lower() not in ['unknown', 'tbd', ''] and start_date and start_date != 'TBD' and end_date and end_date != 'TBD':
            try:
                from datetime import datetime, timedelta
                # Tarih formatını kontrol et
                try:
                    start_dt = datetime.strptime(start_date, '%B %d, %Y')
                except ValueError:
                    # Alternatif format dene
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"[SOW PDF] Could not parse start_date: {start_date}")
                        start_dt = None
                
                try:
                    end_dt = datetime.strptime(end_date, '%B %d, %Y')
                except ValueError:
                    # Alternatif format dene
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"[SOW PDF] Could not parse end_date: {end_date}")
                        end_dt = None
                
                if not start_dt or not end_dt:
                    logger.warning(f"[SOW PDF] Skipping weekly tables - invalid dates")
                    return sow_data
                
                weekdays = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
                current_date = start_dt
                
                # Sleeping Room tablosu için
                for i, weekday in enumerate(weekdays):
                    if current_date <= end_dt:
                        date_str = current_date.strftime('%m/%d/%y')
                        sow_data[f'date_{weekday}'] = date_str
                        # Varsayılan oda sayısı (participants / 2)
                        default_rooms = max(int(participants_int / 2) if participants_int > 0 else 0, 0)
                        sow_data[f'rooms_{weekday}'] = str(default_rooms)
                        if weekday != 'saturday':
                            current_date = current_date + timedelta(days=1)
                    else:
                        sow_data[f'date_{weekday}'] = ''
                        sow_data[f'rooms_{weekday}'] = '0'
                
                # Function Space tablosu için (Sunday-Friday)
                current_date = start_dt
                for i, weekday in enumerate(['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
                    if current_date <= end_dt:
                        date_str = current_date.strftime('%m/%d/%y')
                        sow_data[f'date_{weekday}_func'] = date_str
                        
                        # Registration Area
                        if weekday == 'monday':
                            sow_data[f'registration_{weekday}'] = '4:30pm to 7:00pm'
                        elif weekday == 'tuesday':
                            sow_data[f'registration_{weekday}'] = '6:30am-8:30am'
                        else:
                            sow_data[f'registration_{weekday}'] = 'None'
                        
                        # General Sessions Room
                        if weekday == 'monday':
                            sow_data[f'general_session_{weekday}'] = 'Available at 6pm'
                        elif weekday in ['tuesday', 'wednesday', 'thursday']:
                            sow_data[f'general_session_{weekday}'] = f'6:00am-7:00pm'
                        else:
                            sow_data[f'general_session_{weekday}'] = 'None'
                        
                        # Breakout Rooms
                        if weekday in ['wednesday', 'thursday']:
                            sow_data[f'breakout_{weekday}'] = '6:00am-7:00pm'
                        else:
                            sow_data[f'breakout_{weekday}'] = 'None'
                        
                        # Logistics Room
                        if weekday == 'monday':
                            sow_data[f'logistics_{weekday}'] = 'Available at 1pm until 7 pm'
                        elif weekday in ['tuesday', 'wednesday', 'thursday']:
                            sow_data[f'logistics_{weekday}'] = '6:00am-7:00pm'
                        else:
                            sow_data[f'logistics_{weekday}'] = 'None'
                        
                        if weekday != 'friday':
                            current_date = current_date + timedelta(days=1)
                    else:
                        sow_data[f'date_{weekday}_func'] = ''
                        sow_data[f'registration_{weekday}'] = 'None'
                        sow_data[f'general_session_{weekday}'] = 'None'
                        sow_data[f'breakout_{weekday}'] = 'None'
                        sow_data[f'logistics_{weekday}'] = 'None'
            except Exception as e:
                logger.warning(f"[SOW PDF] Could not parse dates for weekly tables: {e}")
        
        return sow_data
    
    def _extract_registration_area_details(self, event_req: Dict[str, Any], participants: int, sow_text: Optional[str] = None) -> str:
        """Analiz verilerinden ve SOW metninden Registration Area detaylarını çıkar"""
        # Önce SOW metninden çıkar (daha detaylı)
        if sow_text:
            reg_match = re.search(r'Registration Area[^:]*:\s*([^\n]+(?:\n(?!###|##|#|\*\*)[^\n]+)*)', sow_text, re.IGNORECASE | re.MULTILINE)
            if reg_match:
                details = reg_match.group(1).strip()
                # Markdown formatını temizle
                details = re.sub(r'\*\*([^*]+)\*\*', r'\1', details)  # Bold'u kaldır
                details = re.sub(r'^\s*[-*]\s*', '', details, flags=re.MULTILINE)  # Liste işaretlerini kaldır
                details = re.sub(r'\n+', ' ', details)  # Yeni satırları boşlukla değiştir
                details = details.strip()
                if len(details) > 50:  # Yeterince detaylıysa kullan
                    logger.info(f"[SOW PDF] Extracted Registration Area from SOW text: {details[:100]}...")
                    return details
        
        # SOW metninde bulunamazsa analiz verilerinden çıkar
        meeting_spaces = event_req.get('meeting_spaces', '')
        av_req = event_req.get('av_requirements', '')
        
        if 'registration' in meeting_spaces.lower() or 'registration area' in meeting_spaces.lower():
            details = 'One rectangular-style table provided with chairs to seat 3 people located in front of general session room. Table provided with a white tablecloth.'
            if 'wi-fi' in av_req.lower() or 'wifi' in av_req.lower() or 'wireless' in av_req.lower():
                details += ' Wi-Fi Available.'
            return details
        
        # Varsayılan
        return 'One rectangular-style table provided with chairs to seat 3 people located in front of general session room. Table provided with a white tablecloth. Wi-Fi Available.'
    
    def _extract_general_session_details(self, event_req: Dict[str, Any], participants: int, sow_text: Optional[str] = None) -> str:
        """Analiz verilerinden ve SOW metninden General Session detaylarını çıkar"""
        # Önce SOW metninden çıkar (daha detaylı)
        if sow_text:
            # General Sessions Room veya General Session bölümünü bul
            gen_match = re.search(r'General Sessions? Room[^:]*:\s*([^\n]+(?:\n(?!###|##|#|\*\*|Conference|Logistics)[^\n]+)*)', sow_text, re.IGNORECASE | re.MULTILINE)
            if gen_match:
                details = gen_match.group(1).strip()
                # Markdown formatını temizle
                details = re.sub(r'\*\*([^*]+)\*\*', r'\1', details)  # Bold'u kaldır
                details = re.sub(r'^\s*[-*]\s*', '', details, flags=re.MULTILINE)  # Liste işaretlerini kaldır
                # Çok fazla yeni satır varsa birleştir
                details = re.sub(r'\n{2,}', '. ', details)
                details = re.sub(r'\n', ' ', details)
                details = details.strip()
                if len(details) > 100:  # Yeterince detaylıysa kullan
                    logger.info(f"[SOW PDF] Extracted General Session from SOW text: {details[:150]}...")
                    return details
        
        # SOW metninde bulunamazsa analiz verilerinden çıkar
        meeting_spaces = event_req.get('meeting_spaces', '')
        av_req = event_req.get('av_requirements', '')
        
        # Capacity
        capacity = participants if participants > 0 else 'TBD'
        
        # Setup - analiz verilerinden çıkar
        setup = 'Classroom-style room arrangement'
        if 'classroom' in meeting_spaces.lower():
            setup = 'Classroom-style room arrangement'
        elif 'theater' in meeting_spaces.lower() or 'auditorium' in meeting_spaces.lower():
            setup = 'Theater-style room arrangement'
        elif 'banquet' in meeting_spaces.lower():
            setup = 'Banquet-style room arrangement'
        
        details = f"{setup} with tables and padded seating for {capacity} people. Presentation stage provided with podium with either mounted or wireless microphones and speakers."
        
        # AV requirements ekle
        if av_req:
            av_parts = []
            if 'projector' in av_req.lower():
                lumen_match = re.search(r'(\d+)[,\s]*lumen', av_req, re.IGNORECASE)
                if lumen_match:
                    av_parts.append(f"minimum {lumen_match.group(1)} lumen projector")
                else:
                    av_parts.append("projector")
            
            if 'screen' in av_req.lower():
                screen_match = re.search(r'(\d+)[\s]*[\'"]?\s*x\s*[\'"]?\s*(\d+)[\s]*[\'"]', av_req, re.IGNORECASE)
                if screen_match:
                    av_parts.append(f"{screen_match.group(1)}' x {screen_match.group(2)}' screens")
                elif 'two' in av_req.lower() or '2' in av_req:
                    av_parts.append("two screens")
                else:
                    av_parts.append("screens")
            
            if 'microphone' in av_req.lower() or 'mic' in av_req.lower():
                if 'handheld' in av_req.lower():
                    av_parts.append("handheld microphones")
                if 'podium' in av_req.lower():
                    av_parts.append("podium microphone")
            
            if 'wi-fi' in av_req.lower() or 'wifi' in av_req.lower():
                av_parts.append("high-speed Wi-Fi")
            
            if av_parts:
                details += f" AV Requirements: {', '.join(av_parts)}."
        
        return details
    
    def _extract_breakout_rooms_details(self, event_req: Dict[str, Any], sow_text: Optional[str] = None) -> str:
        """Analiz verilerinden ve SOW metninden Breakout Rooms detaylarını çıkar"""
        # Önce SOW metninden çıkar (daha detaylı)
        if sow_text:
            # Conference Breakout Rooms veya Breakout Rooms bölümünü bul
            breakout_match = re.search(r'Conference Breakout Rooms?[^:]*:\s*([^\n]+(?:\n(?!###|##|#|\*\*|Logistics|General)[^\n]+)*)', sow_text, re.IGNORECASE | re.MULTILINE)
            if breakout_match:
                details = breakout_match.group(1).strip()
                # Markdown formatını temizle
                details = re.sub(r'\*\*([^*]+)\*\*', r'\1', details)  # Bold'u kaldır
                details = re.sub(r'^\s*[-*]\s*', '', details, flags=re.MULTILINE)  # Liste işaretlerini kaldır
                # Çok fazla yeni satır varsa birleştir
                details = re.sub(r'\n{2,}', '. ', details)
                details = re.sub(r'\n', ' ', details)
                details = details.strip()
                if len(details) > 100:  # Yeterince detaylıysa kullan
                    logger.info(f"[SOW PDF] Extracted Breakout Rooms from SOW text: {details[:150]}...")
                    return details
        
        # SOW metninde bulunamazsa analiz verilerinden çıkar
        meeting_spaces = event_req.get('meeting_spaces', '')
        av_req = event_req.get('av_requirements', '')
        
        # Breakout room sayısını çıkar
        breakout_match = re.search(r'(\d+)\s*(?:separate\s*)?(?:conference\s*)?breakout\s*rooms?', meeting_spaces, re.IGNORECASE)
        room_count = breakout_match.group(1) if breakout_match else '4'
        
        # Capacity
        capacity_match = re.search(r'(\d+)\s*people', meeting_spaces, re.IGNORECASE)
        capacity = capacity_match.group(1) if capacity_match else '30'
        
        details = f"Location: Rooms should be near the General Session room. Quantity: Minimum of {room_count} separate rooms. Arrangement: Classroom-style. Capacity: Each room must hold at least {capacity} people."
        
        # AV requirements
        if av_req and ('projector' in av_req.lower() or 'screen' in av_req.lower()):
            av_parts = []
            if 'projector' in av_req.lower():
                lumen_match = re.search(r'(\d+)[,\s]*lumen', av_req, re.IGNORECASE)
                if lumen_match:
                    av_parts.append(f"minimum {lumen_match.group(1)} lumen projector")
            if 'screen' in av_req.lower():
                av_parts.append("screen")
            if av_parts:
                details += f" Equipment per room: {', '.join(av_parts)}."
        
        return details
    
    def _extract_logistics_room_details(self, event_req: Dict[str, Any], sow_text: Optional[str] = None) -> str:
        """Analiz verilerinden ve SOW metninden Logistics Room detaylarını çıkar"""
        # Önce SOW metninden çıkar (daha detaylı)
        if sow_text:
            # Logistics Room bölümünü bul
            logistics_match = re.search(r'Logistics Room[^:]*:\s*([^\n]+(?:\n(?!###|##|#|\*\*|General|Conference)[^\n]+)*)', sow_text, re.IGNORECASE | re.MULTILINE)
            if logistics_match:
                details = logistics_match.group(1).strip()
                # Markdown formatını temizle
                details = re.sub(r'\*\*([^*]+)\*\*', r'\1', details)  # Bold'u kaldır
                details = re.sub(r'^\s*[-*]\s*', '', details, flags=re.MULTILINE)  # Liste işaretlerini kaldır
                # Çok fazla yeni satır varsa birleştir
                details = re.sub(r'\n{2,}', '. ', details)
                details = re.sub(r'\n', ' ', details)
                details = details.strip()
                if len(details) > 50:  # Yeterince detaylıysa kullan
                    logger.info(f"[SOW PDF] Extracted Logistics Room from SOW text: {details[:150]}...")
                    return details
        
        # SOW metninde bulunamazsa analiz verilerinden çıkar
        meeting_spaces = event_req.get('meeting_spaces', '')
        special_logistics = event_req.get('special_logistics', '')
        
        # Capacity - special_logistics'ten çıkar
        capacity = '15'  # Varsayılan
        capacity_match = re.search(r'(\d+)\s*(?:people|laptops)', special_logistics, re.IGNORECASE)
        if capacity_match:
            capacity = capacity_match.group(1)
        
        details = f"Arrangement: Boardroom Style with tables and padded seating for {capacity} people. Connectivity: Room should have electrical outlets and power strips to accommodate {capacity} laptops"
        
        # Wi-Fi kontrolü
        if 'wi-fi' in special_logistics.lower() or 'wifi' in special_logistics.lower() or 'wireless' in special_logistics.lower():
            details += " and high-speed Wi-Fi"
        
        details += "."
        
        return details
    
    def _create_hotel_version_sow(self, full_sow_text: str) -> str:
        """
        Hotel versiyonu SOW oluştur (internal bilgileri çıkar)
        Hotel versiyonunda:
        - Tüm detaylar dahil
        - Compliance requirements basitleştirilmiş (tablo yerine liste)
        - Internal notlar çıkarılmış
        """
        lines = full_sow_text.split('\n')
        result_lines = []
        skip_compliance_table = False
        in_compliance_section = False
        
        for i, line in enumerate(lines):
            # Compliance Requirements bölümünü bul
            if '### COMPLIANCE REQUIREMENTS' in line:
                in_compliance_section = True
                result_lines.append(line)
                result_lines.append('')
                # Basitleştirilmiş liste formatı
                result_lines.append('- FAR 52.212-4: Required')
                result_lines.append('- FAR 52.212-5: Required')
                result_lines.append('- FAR 52.204-24/25/26: As specified')
                result_lines.append('- System for Award Management (SAM) registration: Required')
                result_lines.append('- Tax exemption clause: Required')
                result_lines.append('')
                skip_compliance_table = True
                continue
            
            if skip_compliance_table:
                # Tablo satırlarını ve separator'ları atla
                if line.strip().startswith('|'):
                    continue
                if line.strip() == '---':
                    # Bir sonraki boş olmayan satırda dur
                    continue
                # Boş olmayan bir satır geldiğinde tablo bitti demektir
                if line.strip() and not line.strip().startswith('|'):
                    skip_compliance_table = False
                    in_compliance_section = False
                    # Eğer bir sonraki bölüm başlığı değilse, satırı ekle
                    if not line.strip().startswith('#'):
                        result_lines.append(line)
                    continue
            
            # Compliance section dışındaysa veya tablo atlandıysa ekle
            if not skip_compliance_table:
                result_lines.append(line)
        
        result_text = '\n'.join(result_lines)
        
        # Eğer boşsa veya çok kısaysa, orijinal metni kullan
        if not result_text or len(result_text.strip()) < 100:
            logger.warning("[SOW] Hotel version is too short, using full SOW text")
            return full_sow_text
        
        return result_text
    
    def _generate_sow_with_llm(
        self,
        report_data: Dict[str, Any],
        opportunity_info: Dict[str, Any],
        vendor_profile: Optional[Dict[str, Any]]
    ) -> str:
        """LLM ile SOW oluştur"""
        try:
            # System message
            system_message = """
You are a Statement of Work (SOW) writing expert. You are preparing a professional SOW to be sent to hotels using RFQ analysis results.

IMPORTANT RULES:
1. NEVER use government contact information (name, email, phone, address) from the RFQ
2. Follow the Sample SOW format EXACTLY with the following structure:
   - BACKGROUND section
   - APPENDIX A section with:
     * Meeting Information table (MEETING NAME, MEETING DATES)
     * Sleeping Room Requirements table (with days of week, dates, rooms booked/night)
     * Function Space Requirements table (with days of week, dates, Registration Area, General Sessions Room, Conference Breakout Rooms, Logistics Room)
     * Detailed Setup/Audio Visual Requirements (for each room type)
     * LIGHT REFRESHMENTS section
     * Pre-con Meeting and Event Logistics section
   - TERMS AND CONDITIONS
   - COMPLIANCE REQUIREMENTS
3. Use MARKDOWN TABLES for all tabular data (Meeting Information, Sleeping Room Requirements, Function Space Requirements)
4. Specify all requirements clearly and in detail
5. Write in language that hotel management will understand
6. Always include critical information such as dates, room count, capacity
7. Include detailed AV requirements for each room type (General Sessions Room, Breakout Rooms, Logistics Room)
8. Mention FAR clauses and compliance requirements but you don't need to go into details
9. Use the same structure and format as the sample SOW

Output: Professional SOW text in Markdown format following the Sample SOW format EXACTLY. Return only the SOW text, no other explanations.
"""
            
            # Sample template'den ilk 2000 karakter
            sample_preview = self.sample_sow_template[:2000] if self.sample_sow_template else ""
            
            # Report data
            analysis_json = json.dumps(report_data, ensure_ascii=False, indent=2)
            opp_info_json = json.dumps(opportunity_info, ensure_ascii=False, indent=2)
            vendor_json = json.dumps(vendor_profile or {}, ensure_ascii=False, indent=2)
            
            user_prompt = f"""
Using the RFQ analysis results below, prepare a Statement of Work (SOW) to be sent to hotels.

SAMPLE SOW FORMAT (follow this structure exactly):
{sample_preview}

RFQ ANALYSIS RESULTS:
{analysis_json[:6000]}

OPPORTUNITY INFORMATION:
{opp_info_json}

VENDOR PROFILE:
{vendor_json}

Please follow the sample SOW format above EXACTLY and extract all requirements from the RFQ analysis results to create a professional SOW.

IMPORTANT:
- Include all date, room, capacity, location information
- Specify meeting space requirements in detail
- Explain AV requirements
- State compliance requirements
- Use clear language that hotel management will understand
- DO NOT USE government contact information
- Follow the sample format structure exactly
"""
            
            response = call_logged_llm(
                agent_name="SOWMailAgent",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            sow_text = extract_message_text(response).strip()
            
            # Markdown code block varsa temizle
            if sow_text.startswith("```"):
                lines = sow_text.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                sow_text = '\n'.join(lines)
            
            logger.info(f"[SOW Agent] Generated SOW with LLM ({len(sow_text)} chars)")
            return sow_text
            
        except LLMNotAvailableError as exc:
            logger.warning(f"[SOW Agent] LLM not available, falling back to template: {exc}")
            return self._generate_sow_from_template(
                opportunity_info,
                report_data.get('event_requirements', {}),
                report_data.get('commercial_terms', {}),
                report_data.get('compliance', {}),
                vendor_profile
            )
        except Exception as e:
            logger.error(f"[SOW Agent] LLM generation failed: {e}", exc_info=True)
            # Fallback
            return self._generate_sow_from_template(
                opportunity_info,
                report_data.get('event_requirements', {}),
                report_data.get('commercial_terms', {}),
                report_data.get('compliance', {}),
                vendor_profile
            )
    
    def _parse_date_to_weekday(self, date_str: str) -> tuple:
        """Tarihi parse et ve weekday bilgisini döndür"""
        try:
            from datetime import datetime as dt
            # "March 3, 2026" formatı
            date_obj = dt.strptime(date_str, '%B %d, %Y')
            weekday = date_obj.strftime('%A')
            return weekday, date_obj
        except:
            return None, None
    
    def _build_sleeping_room_table(self, date_range: str, room_block_plan: str, participants_target) -> str:
        """Sleeping Room Requirements tablosunu oluştur"""
        # Tarihleri parse et
        start_date = self._parse_start_date(date_range)
        end_date = self._parse_end_date(date_range)
        
        # Room block plan'dan günlük oda sayılarını çıkar
        room_block_plan_lower = room_block_plan.lower() if room_block_plan else ""
        
        # participants_target'ı integer'a çevir (string olabilir)
        try:
            participants_int = int(participants_target) if participants_target else 0
        except (ValueError, TypeError):
            participants_int = 0
        
        # Varsayılan: Tüm günler için aynı oda sayısı (participants_target / 2)
        default_rooms = max(int(participants_int / 2) if participants_int > 0 else 0, 0)
        
        # Room block plan'dan günlük oda sayılarını parse et
        daily_rooms = {}  # Key: date string (MM/DD/YY), Value: room count
        if room_block_plan:
            # "5 rooms on March 3, 45 rooms on March 4" formatını parse et
            # Önce yılı bul
            year_match = re.search(r'(\d{4})', date_range)
            year = year_match.group(1) if year_match else '2026'
            
            matches = re.findall(r'(\d+)\s+rooms?\s+on\s+(\w+\s+\d+)', room_block_plan, re.IGNORECASE)
            for rooms, date_part in matches:
                try:
                    date_obj = datetime.strptime(f"{date_part}, {year}", '%B %d, %Y')
                    date_key = date_obj.strftime('%m/%d/%y')
                    daily_rooms[date_key] = int(rooms)
                except:
                    pass
        
        # Tarih aralığını günlere böl
        try:
            start_dt = datetime.strptime(start_date, '%B %d, %Y')
            end_dt = datetime.strptime(end_date, '%B %d, %Y')
        except:
            # Fallback: Basit format
            participants_display = participants_int if participants_int > 0 else (str(participants_target) if participants_target else 'N/A')
            return f"**Date Range:** {date_range}\n**Room Block:** {room_block_plan or 'TBD'}\n**Total Participants:** {participants_display}"
        
        # Tablo başlığı
        table = "| | Sunday | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday |\n"
        table += "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        
        # Date satırı
        date_row = "| **Date:** |"
        rooms_row = "| **Rooms Booked/Night:** |"
        
        current_date = start_dt
        weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # İlk hafta
        for i, weekday in enumerate(weekdays):
            if current_date <= end_dt:
                date_str = current_date.strftime('%m/%d/%y')
                # Önce daily_rooms'tan tarih bazlı kontrol et, yoksa default kullan
                rooms = daily_rooms.get(date_str)
                if rooms is None:
                    # Eğer tarih aralığı içindeyse default kullan
                    rooms = default_rooms if current_date >= start_dt and current_date <= end_dt else 0
                date_row += f" {date_str} |"
                rooms_row += f" {rooms} |"
                if weekday != 'Saturday':
                    current_date = datetime.fromordinal(current_date.toordinal() + 1)
            else:
                date_row += " |"
                rooms_row += " |"
        
        table += date_row + "\n"
        table += rooms_row + "\n"
        
        # Notes
        participants_display = participants_int if participants_int > 0 else (str(participants_target) if participants_target else 'N/A')
        notes = f"Room block requested may be amended slightly. Room Block of {participants_display} participants. If fewer than {participants_display} rooms are reserved by the hold end date, no attrition or any other fees or penalties will be assessed."
        
        return f"{table}\n\n**NOTES:** {notes}"
    
    def _build_function_space_table(self, date_range: str, event_req: Dict[str, Any]) -> str:
        """Function Space Requirements tablosunu oluştur"""
        start_date = self._parse_start_date(date_range)
        end_date = self._parse_end_date(date_range)
        
        try:
            start_dt = datetime.strptime(start_date, '%B %d, %Y')
            end_dt = datetime.strptime(end_date, '%B %d, %Y')
        except:
            return f"**Meeting Spaces:** {event_req.get('meeting_spaces', 'TBD')}\n**AV Requirements:** {event_req.get('av_requirements', 'TBD')}"
        
        # Tablo başlığı
        table = "| | Sunday | Monday | Tuesday | Wednesday | Thursday | Friday |\n"
        table += "| --- | --- | --- | --- | --- | --- | --- |\n"
        
        # Date satırı
        date_row = "| **Date:** |"
        reg_row = "| **Registration Area:** |"
        gen_row = "| **General Sessions Room:** |"
        breakout_row = "| **Conference Breakout Rooms (4):** |"
        logistics_row = "| **Logistics Room (1):** |"
        
        current_date = start_dt
        weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # participants_target'ı integer'a çevir (string olabilir)
        participants_raw = event_req.get('participants_target', 0)
        try:
            participants = int(participants_raw) if participants_raw else 0
        except (ValueError, TypeError):
            participants = 0
        
        for i, weekday in enumerate(weekdays):
            if current_date <= end_dt:
                date_str = current_date.strftime('%m/%d/%y')
                date_row += f" {date_str} |"
                
                # Registration Area
                if weekday == 'Monday':
                    reg_row += " 4:30pm to 7:00pm |"
                elif weekday == 'Tuesday':
                    reg_row += " 6:30am-8:30am |"
                else:
                    reg_row += " None |"
                
                # General Sessions Room
                if weekday == 'Monday':
                    gen_row += " Available at 6pm |"
                elif weekday in ['Tuesday', 'Wednesday', 'Thursday']:
                    gen_row += f" 6:00am-7:00pm, Classroom style set for {participants} people |"
                else:
                    gen_row += " None |"
                
                # Breakout Rooms
                if weekday in ['Wednesday', 'Thursday']:
                    breakout_row += " 6:00am-7:00pm, Classroom style set for 30 people each |"
                else:
                    breakout_row += " None |"
                
                # Logistics Room
                if weekday == 'Monday':
                    logistics_row += " Available at 1pm until 7 pm |"
                elif weekday in ['Tuesday', 'Wednesday', 'Thursday']:
                    logistics_row += " 6:00am-7:00pm |"
                else:
                    logistics_row += " None |"
                
                if weekday != 'Friday':
                    current_date = datetime.fromordinal(current_date.toordinal() + 1)
            else:
                date_row += " |"
                reg_row += " |"
                gen_row += " |"
                breakout_row += " |"
                logistics_row += " |"
        
        table += date_row + "\n"
        table += reg_row + "\n"
        table += gen_row + "\n"
        table += breakout_row + "\n"
        table += logistics_row + "\n"
        
        return table
    
    def _build_detailed_av_requirements(self, event_req: Dict[str, Any]) -> str:
        """Detaylı AV ve setup gereksinimlerini oluştur"""
        # participants_target'ı integer'a çevir (string olabilir)
        participants_raw = event_req.get('participants_target', 120)
        try:
            participants = int(participants_raw) if participants_raw else 120
        except (ValueError, TypeError):
            participants = 120
        av_req = event_req.get('av_requirements', '')
        
        detailed = f"""**Meeting rooms must be booked on a 24-hour hold beginning from the day and time the Government takes possession of function space.**

### Registration Area (1):
- One rectangular-style table provided with chairs to seat 3 people located in front of general session room.
- Table provided with a white tablecloth.
- Wi-Fi Available.

### General Sessions Room (1):
- Classroom-style room arrangement with tables and padded seating for {participants} people.
- Presentation stage provided with podium with either mounted or wireless microphones and speakers.
- Presentation stage should accommodate a rectangular table with a white tablecloth and 5 chairs set up classroom style.
- 3 round tables and padded seating on the back of room for speakers with a charging station in each table.
- 2 - Handheld Mics
- **Projection:** Provide a minimum of 5,000 lumen projector and two 6' x 10' screens with Truss Dress Kit Black, Screen Frame, and front projector surface with black back that can be seen easily by everyone in the room. Both screens must be cloned to project the same image/presentation from the presenter's computer.
- High Speed Wi-Fi Access for presenter.
- Presenter laptop audio must be playable through speakers in the room.
- A variety of monitor cables and adapters (HDMI, DisplayPort, DVI, VDA) must be available for compatibility with government laptops.
- At least 10 Power strips and extension cords.
- 6 trashcans.
- 4 easels with a self-adhesive flip chart pad and a marker set.
- High speed Wi-Fi, audio-visual equipment, and room setup must be completed by 6:00 PM on the day prior to attendee occupancy.

### Conference Breakout Rooms (4):
- **Location:** Rooms should be near the General Session room.
- **Quantity:** Minimum of four separate rooms.
- **Arrangement:** Classroom-style.
- **Capacity:** Each room must hold at least 30 people.
- **Seating:** Include tables with padded seating.
- **Equipment per room:**
  - 2 Handheld mics.
  - 1 Standalone podium with mic (either mounted or wireless) connected to the room's speakers.
  - Laptop audio must be playable through speakers.
  - 1 minimum 5000 lumen projector.
  - 1 6' x 10' screen with Truss Dress Kit Black, Screen Frame, and a front projector surface with a black back that is easily visible to everyone.
  - The projector cart must be set up far enough from the screen to use the entire projection area and must not block audience view once the projector is seated on the cart.
  - A variety of adapters, monitor cables, and adapters (HDMI, DisplayPort, DVI, VDA) for government laptops.
  - Power strips and extension cords.
  - High speed Wi-Fi Access for presenter.
  - 2 trashcans provided for the duration of the event.
  - 1 easel with a self-adhesive flip chart pad and a marker set.
  - Post-it notes on the tables, provided on day one.
- High speed Wi-Fi, audio-visual equipment, and room setup must be completed by 6:00 PM on the day prior to attendee occupancy.

### Logistics Room (1):
- **Arrangement:** Boardroom Style with tables and padded seating for 15 people.
- **Connectivity:** Room should have electrical outlets and power strips to accommodate 15 laptops and high-speed Wi-Fi.
- **Waste:** A trashcan provided for the duration of the event.
- High speed Wi-Fi, equipment, and room setup must be completed by 1:00 PM on the day prior to attendee occupancy.

### General Obstruction Requirement:
**All meeting rooms must not have any obstructions that impede the view of attendees to the speaker's area, or screens, including no obstruction caused by projector cart.**
"""
        return detailed
    
    def _generate_sow_from_template(
        self,
        opp_info: Dict[str, Any],
        event_req: Dict[str, Any],
        commercial: Dict[str, Any],
        compliance: Dict[str, Any],
        vendor_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Template-based SOW oluştur (resimdeki formata göre)"""
        vendor_name = vendor_profile.get('company_name', 'CREATA GLOBAL MEETING & EVENTS') if vendor_profile else 'CREATA GLOBAL MEETING & EVENTS'
        
        # Date parsing
        date_range = event_req.get('date_range', 'TBD')
        start_date = self._parse_start_date(date_range)
        end_date = self._parse_end_date(date_range)
        
        # Meeting Information
        meeting_name = opp_info.get('title', 'N/A')
        meeting_dates = date_range
        
        # Sleeping Room Table
        # Eğer date_range "unknown" ise, tablo yerine basit format kullan
        if date_range and date_range.lower() not in ['unknown', 'tbd', '']:
            sleeping_room_table = self._build_sleeping_room_table(
                date_range,
                event_req.get('room_block_plan', ''),
                event_req.get('participants_target', 0)
            )
        else:
            # Basit format (tarih bilgisi yoksa)
            room_block = event_req.get('room_block_plan', 'TBD')
            participants_display = event_req.get('participants_target', 'TBD')
            if participants_display and str(participants_display).lower() not in ['unknown', 'tbd', '']:
                try:
                    participants_int = int(participants_display)
                    sleeping_room_table = f"**Date Range:** TBD\n**Room Block:** {room_block}\n**Total Participants:** {participants_int}"
                except:
                    sleeping_room_table = f"**Date Range:** TBD\n**Room Block:** {room_block}\n**Total Participants:** {participants_display}"
            else:
                sleeping_room_table = f"**Date Range:** TBD\n**Room Block:** {room_block}\n**Total Participants:** TBD"
        
        # Function Space Table
        # Eğer date_range "unknown" ise, basit format kullan
        if date_range and date_range.lower() not in ['unknown', 'tbd', '']:
            function_space_table = self._build_function_space_table(date_range, event_req)
        else:
            # Basit format (tarih bilgisi yoksa)
            meeting_spaces = event_req.get('meeting_spaces', 'TBD')
            av_req = event_req.get('av_requirements', 'TBD')
            if meeting_spaces and meeting_spaces.lower() not in ['unknown', 'tbd', '']:
                function_space_table = f"**Meeting Spaces:** {meeting_spaces}\n**AV Requirements:** {av_req}"
            else:
                function_space_table = f"**Meeting Spaces:** TBD\n**AV Requirements:** TBD"
        
        # Detailed AV Requirements
        detailed_av = self._build_detailed_av_requirements(event_req)
        
        # F&B Requirements
        fnb_req = event_req.get('fnb_requirements', 'Light refreshments, coffee service')
        
        # General Notes (F&B hakkında) - Her zaman ekle
        general_notes = "Light refreshments will be provided once in the morning (e.g., coffee, juice, nuts, fruit, muffin, and Danish) and a second time during a PM break (e.g., tea, sodas, crackers, chips, and cookies) each meeting day.\n\nThe Federal government is exempt from sales and other taxes on the goods and services it acquires through contract, and these taxes should be excluded from the cost for food and beverage."
        
        # "unknown" değerlerini daha uygun değerlerle değiştir
        solicitation_number = opp_info.get('solicitation_number', 'TBD')
        if solicitation_number and solicitation_number.lower() in ['unknown', 'n/a', '']:
            solicitation_number = 'TBD'
        
        meeting_name_display = meeting_name if meeting_name and meeting_name.lower() not in ['unknown', 'n/a'] else 'TBD'
        meeting_dates_display = meeting_dates if meeting_dates and meeting_dates.lower() not in ['unknown', 'tbd'] else 'TBD'
        
        # Compliance requirements tablosu için değerleri hazırla
        far_212_4_req = 'Evet' if compliance.get('far_52_212_4') else 'Hayır'
        far_212_5_req = 'Evet' if compliance.get('far_52_212_5') else 'Hayır'
        far_204_req = 'Evet' if compliance.get('far_52_204_24_25_26') else 'Hayır'
        security_req = 'Evet' if compliance.get('security_telecom_restrictions') else 'Hayır'
        bytedance_req = 'Evet' if compliance.get('bytedance_restriction') else 'Hayır'
        
        sow = f"""# STATEMENT OF WORK (SOW)
## FOR HOTEL ACCOMMODATIONS AND MEETING SPACE

### 1. BACKGROUND

This Statement of Work (SOW) outlines the requirements for hotel accommodations and meeting space services for a federal government event.

**Solicitation Number:** {solicitation_number}
**Agency:** {opp_info.get('agency', 'TBD')}
**Event Title:** {opp_info.get('title', 'TBD')}

---

### General Notes

{general_notes}

---

## APPENDIX A

### Meeting Information

| MEETING NAME | MEETING DATES |
| --- | --- |
| {meeting_name_display} | {meeting_dates_display} |

---

### Sleeping Room Requirements

{sleeping_room_table}

---

### Function Space Requirements

{function_space_table}

---

### Function Space Requirements (cont.)

#### MEETING ROOM SETUP/AUDIO VISUAL REQUIREMENTS

{detailed_av}

---

### LIGHT REFRESHMENTS

**Standard Service:** Water, coffee, and tea service in all meeting rooms throughout the event.

**AM/PM Refreshments:** Provided once in the morning (as selected by the Government) and a second time during a PM break (as selected by the Government) each meeting day.

**Timing Agreement:** Refreshment times will be agreed upon 15 days prior to the event.

**Breakout Room Logistics:** If breakout meeting rooms are not all located in the same area in the hotel, a snack area will be set up for each group area. The hotel must provide a logistics plan to ensure all participants have close access to AM/PM refreshments.

**Additional F&B Requirements:**
{fnb_req}

**Tax Exemption:** The Federal government is exempt from sales and other taxes on the goods and services it acquires through contract, and these taxes should be excluded from the cost for food and beverage.

---

### Pre-con Meeting and Event Logistics

**Pre-conference Meeting:** The Government requests a pre-conference meeting with the hotel sales, banquets, and AV staff managing the event.

**Date/Time:** Afternoon of the day prior to the event start date ({start_date if start_date and start_date.lower() not in ['unknown', 'tbd'] else 'TBD'}).

**Attendees:** Government project lead and the contractor lead (or assigned representatives).

**Agenda:** Review of banquet event orders for final approval and review of the hotel room block list.

**Location:** Can be in any location within the hotel.

**Additional Request:** The Government team would like a tour of the group's meeting rooms being used throughout the event.

---

### TERMS AND CONDITIONS

**Payment Terms:** {commercial.get('payment_terms', 'Net 30 days')}
**Tax Exempt:** {'Yes' if commercial.get('tax_exempt') else 'No'}
**E-Invoicing IPP:** {'Yes' if commercial.get('e_invoicing_ipp') else 'No'}
**Cancellation Penalties:** {commercial.get('cancellation_penalties', 'As specified in contract')}

---

### COMPLIANCE REQUIREMENTS

| Kısaltma | Anlam | İçerik / Yükümlülük | Ne Yarar | Gerekli |
| --- | --- | --- | --- | --- |
| FAR 52.212-4 | Contract Terms and Conditions—Commercial Items | Ticari kalemler için temel sözleşme koşulları (teslimat, garanti, fesih, ödeme) | Tüm ticari tekliflerde zorunlu | {far_212_4_req} |
| FAR 52.212-5 | Contract Terms and Conditions Required to Implement Statutes or Executive Orders | Federal yasa ve Başkanlık emirlerini uygulayan hükümler (ödeme, işyeri ayrımcılığı, vergi vs.) | Federal yasalara uyum | {far_212_5_req} |
| FAR 52.204-24/25/26 | Covered Telecommunications Equipment or Services | Huawei, ZTE vb. yasaklı telekom ekipmanlarını kullanmama beyanı | Güvenlik ve tedarik zinciri kontrolü | {far_204_req} |
| Security/Telecom Restrictions | — | Ek güvenlik veya telekom kısıtlamaları (ör. bulut/şifreleme) | Ek güvenlik gereksinimleri | {security_req} |
| Bytedance Restriction | — | TikTok/Bytedance yazılımlarına ilişkin yasak | Güvenlik ve veri koruma | {bytedance_req} |
| System for Award Management (SAM) registration requirement | — | SAM.gov'da kayıt zorunluluğu | Federal sözleşmeler için zorunlu | Evet |
| Tax exemption clause for federal government entity | — | Federal hükümet için vergi muafiyeti | Vergi muafiyeti | Evet |

---

**Prepared by:** {vendor_name}
**Date:** {datetime.now().strftime('%B %d, %Y')}
"""
        return sow
    
    def _parse_start_date(self, date_range: str) -> str:
        """Date range'den start date'i parse et"""
        if not date_range or date_range == 'TBD':
            return 'TBD'
        
        # "March 3-6, 2026" formatı
        match = re.search(r'(\w+\s+\d+)[-\s]+(\d+),\s*(\d{4})', date_range)
        if match:
            month_day = match.group(1)
            year = match.group(3)
            return f"{month_day}, {year}"
        
        # "March 3, 2026 to March 6, 2026" formatı
        if ' to ' in date_range:
            return date_range.split(' to ')[0].strip()
        
        # "2024-03-01 to 2024-03-05" formatı
        if re.match(r'\d{4}-\d{2}-\d{2}', date_range):
            parts = date_range.split(' to ')
            date_str = parts[0].strip()
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%B %d, %Y')
            except:
                return date_str
        
        return date_range.split('-')[0].strip() if '-' in date_range else date_range.strip()
    
    def _parse_end_date(self, date_range: str) -> str:
        """Date range'den end date'i parse et"""
        if not date_range or date_range == 'TBD':
            return 'TBD'
        
        # "March 3-6, 2026" formatı
        match = re.search(r'(\w+)\s+(\d+)[-\s]+(\d+),\s*(\d{4})', date_range)
        if match:
            month = match.group(1)
            end_day = match.group(3)
            year = match.group(4)
            return f"{month} {end_day}, {year}"
        
        # "March 3, 2026 to March 6, 2026" formatı
        if ' to ' in date_range:
            return date_range.split(' to ')[-1].strip()
        
        # "2024-03-01 to 2024-03-05" formatı
        if re.match(r'\d{4}-\d{2}-\d{2}', date_range):
            parts = date_range.split(' to ')
            date_str = parts[-1].strip()
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%B %d, %Y')
            except:
                return date_str
        
        return date_range.strip()
    
    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """Markdown'ı HTML'e çevir (basit)"""
        html = markdown_text
        
        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        return f"<div style='font-family: Arial, sans-serif; line-height: 1.6; padding: 20px;'>{html}</div>"
    
    def generate_mail_package(
        self,
        sow_result: Dict[str, Any],
        report_data: Dict[str, Any],
        opportunity_code: str,
        to_email: str,
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Mail paketi oluştur (SOW eki ile)
        
        Args:
            sow_result: generate_sow() çıktısı
            report_data: Analiz raporu
            opportunity_code: Fırsat kodu
            to_email: Alıcı e-posta
            from_email: Gönderen e-posta
            cc_emails: CC listesi
        
        Returns:
            Mail paketi dict
        """
        opp_info = report_data.get('opportunity_info', {})
        fit_assessment = report_data.get('fit_assessment', {})
        
        # Konu satırı
        subject = f"SOW Request - {opp_info.get('solicitation_number', opportunity_code)} - {opp_info.get('title', 'Hotel Accommodations')}"
        
        # Mail gövdesi (HTML)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #1e40af; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .sow-preview {{ margin: 20px 0; padding: 15px; background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 5px; }}
        .footer {{ margin-top: 30px; padding: 15px; background-color: #f3f4f6; font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Statement of Work (SOW) Request</h1>
        <p><strong>Solicitation Number:</strong> {opp_info.get('solicitation_number', 'N/A')}</p>
        <p><strong>Event Title:</strong> {opp_info.get('title', 'N/A')}</p>
    </div>
    
    <div class="content">
        <p>Dear Hotel Management,</p>
        
        <p>We are requesting a quote for hotel accommodations and meeting space services for a federal government event. Please find the detailed Statement of Work (SOW) attached.</p>
        
        <div class="sow-preview">
            <h3>SOW Summary:</h3>
            <p><strong>Location:</strong> {report_data.get('event_requirements', {}).get('location', 'TBD')}</p>
            <p><strong>Date Range:</strong> {report_data.get('event_requirements', {}).get('date_range', 'TBD')}</p>
            <p><strong>Participants:</strong> {report_data.get('event_requirements', {}).get('participants_target', 'N/A')}</p>
        </div>
        
        <p>Please review the attached SOW document and provide your quote at your earliest convenience.</p>
        
        <p>Thank you for your consideration.</p>
        
        <p>Best regards,<br>
        CREATA GLOBAL MEETING & EVENTS</p>
    </div>
    
    <div class="footer">
        <p>This SOW was generated by MergenLite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Please review the attached SOW document for complete details.</p>
    </div>
</body>
</html>
"""
        
        # Plain text body
        text_body = f"""
Statement of Work (SOW) Request
===============================

Solicitation Number: {opp_info.get('solicitation_number', 'N/A')}
Event Title: {opp_info.get('title', 'N/A')}

Dear Hotel Management,

We are requesting a quote for hotel accommodations and meeting space services for a federal government event. Please find the detailed Statement of Work (SOW) attached.

SOW Summary:
- Location: {report_data.get('event_requirements', {}).get('location', 'TBD')}
- Date Range: {report_data.get('event_requirements', {}).get('date_range', 'TBD')}
- Participants: {report_data.get('event_requirements', {}).get('participants_target', 'N/A')}

Please review the attached SOW document and provide your quote at your earliest convenience.

Thank you for your consideration.

Best regards,
CREATA GLOBAL MEETING & EVENTS

Generated by MergenLite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Attachments (hotel PDF varsa ekle)
        attachments = []
        hotel_pdf_path = sow_result.get('sow_pdf_hotel_path')
        if hotel_pdf_path and Path(hotel_pdf_path).exists():
            attachments.append({
                'path': hotel_pdf_path,
                'filename': f"sow_{opportunity_code}.pdf",
                'mime_type': 'application/pdf'
            })
        
        return {
            'to': to_email,
            'from': from_email or 'noreply@creataglobal.com',
            'cc': cc_emails or [],
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body,
            'attachments': attachments,
            'sow_text': sow_result.get('sow_text', ''),
            'sow_html': sow_result.get('sow_html', ''),
            'opportunity_code': opportunity_code,
            'generated_at': datetime.now().isoformat()
        }


def make_sow_mail_agent(llm_config: Optional[Dict] = None) -> SOWMailAgent:
    """
    SOW & Mail Agent oluştur
    
    Args:
        llm_config: LLM konfigürasyonu
    
    Returns:
        SOWMailAgent instance
    """
    return SOWMailAgent(llm_config=llm_config)


