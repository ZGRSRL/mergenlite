#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel SOW'u GPT/AutoGen formatına dönüştür
Sample SOW formatını referans alarak yapılandırılmış JSON formatına çevirir
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Document processor
try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    logger.warning("DocumentProcessor not available")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """PDF'den metin çıkar"""
    if not DOCUMENT_PROCESSOR_AVAILABLE:
        logger.error("DocumentProcessor not available")
        return ""
    
    try:
        processor = DocumentProcessor()
        result = processor.process_file_from_path(str(pdf_path))
        if result.get('success'):
            return result['data'].get('text', '')
        else:
            logger.error(f"Failed to extract text: {result.get('error')}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}", exc_info=True)
        return ""


def parse_sample_sow_structure(sample_text: str) -> Dict[str, Any]:
    """Sample SOW'dan yapıyı çıkar ve şablon oluştur"""
    structure = {
        "BACKGROUND": {},
        "MEETING_INFO": {
            "MEETING_NAME": "{MEETING_NAME}",
            "MEETING_DATES": "{MEETING_DATES}"
        },
        "SLEEPING_ROOM_REQUIREMENTS": {
            "Date_Range": "{DATE_RANGE}",
            "Room_Block": "{ROOM_BLOCK}",
            "Total_Participants": "{TOTAL_PARTICIPANTS}"
        },
        "FUNCTION_SPACE_REQUIREMENTS": {
            "Registration_Area": {
                "Setup": "{REGISTRATION_SETUP}",
                "WiFi": True
            },
            "General_Session": {
                "Capacity": "{GENERAL_SESSION_CAPACITY}",
                "Setup": "{GENERAL_SESSION_SETUP}",
                "AV_Requirements": {
                    "Projector_Lumens": "{PROJECTOR_LUMENS}",
                    "Screens": "{SCREEN_COUNT}",
                    "Microphones": ["{MICROPHONE_TYPES}"]
                }
            },
            "Breakout_Rooms": {
                "Count": "{BREAKOUT_ROOM_COUNT}",
                "Capacity_Per_Room": "{BREAKOUT_CAPACITY}",
                "Setup": "{BREAKOUT_SETUP}",
                "AV_Requirements": {
                    "Projector_Lumens": "{BREAKOUT_PROJECTOR_LUMENS}",
                    "Screens": "{BREAKOUT_SCREEN_COUNT}",
                    "Microphones": ["{BREAKOUT_MICROPHONE_TYPES}"]
                }
            },
            "Logistics_Room": {
                "Capacity": "{LOGISTICS_CAPACITY}",
                "Setup": "{LOGISTICS_SETUP}",
                "WiFi": True
            }
        },
        "REFRESHMENTS": {
            "Standard_Service": "{STANDARD_REFRESHMENT_SERVICE}",
            "AM_PM_Refreshments": "{AM_PM_REFRESHMENTS}",
            "Timing_Agreement": "{REFRESHMENT_TIMING}"
        },
        "LOGISTICS": {
            "Pre_con_Meeting": {
                "Date_Time": "{PRE_CON_DATE_TIME}",
                "Attendees": "{PRE_CON_ATTENDEES}",
                "Agenda": "{PRE_CON_AGENDA}",
                "Location": "{PRE_CON_LOCATION}"
            }
        },
        "TERMS_AND_CONDITIONS": {
            "Payment_Terms": "{PAYMENT_TERMS}",
            "Tax_Exempt": "{TAX_EXEMPT}",
            "E_Invoicing_IPP": "{E_INVOICING_IPP}",
            "Cancellation_Penalties": "{CANCELLATION_PENALTIES}"
        },
        "COMPLIANCE_REQUIREMENTS": {
            "FAR_52_212_4": "{FAR_52_212_4}",
            "FAR_52_212_5": "{FAR_52_212_5}",
            "FAR_52_204_24_25_26": "{FAR_52_204_24_25_26}",
            "Security_Telecom_Restrictions": "{SECURITY_TELECOM_RESTRICTIONS}",
            "Bytedance_Restriction": "{BYTEDANCE_RESTRICTION}",
            "SAM_Registration": "{SAM_REGISTRATION}",
            "Tax_Exemption_Clause": "{TAX_EXEMPTION_CLAUSE}"
        }
    }
    return structure


def extract_hotel_sow_data(hotel_sow_text: str) -> Dict[str, Any]:
    """Hotel SOW metninden verileri çıkar ve GPT formatına dönüştür"""
    
    data = {
        "BACKGROUND": {
            "Solicitation_Number": "{SOLICITATION_NUMBER}",
            "Agency": "{AGENCY}",
            "Event_Title": "{EVENT_TITLE}"
        },
        "MEETING_INFO": {
            "MEETING_NAME": "{MEETING_NAME}",
            "MEETING_DATES": "{MEETING_DATES}"
        },
        "SLEEPING_ROOM_REQUIREMENTS": {
            "Table_Format": "Weekly",
            "Days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "Dates": {},
            "Rooms_Booked_Night": {},
            "Notes": "{ROOM_BLOCK_NOTES}"
        },
        "FUNCTION_SPACE_REQUIREMENTS": {
            "Table_Format": "Weekly",
            "Days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "Dates": {},
            "Registration_Area": {},
            "General_Sessions_Room": {},
            "Conference_Breakout_Rooms": {},
            "Logistics_Room": {},
            "Detailed_AV_Requirements": {
                "Registration_Area": {
                    "Setup": "{REGISTRATION_SETUP}",
                    "WiFi": True
                },
                "General_Session": {
                    "Capacity": "{GENERAL_SESSION_CAPACITY}",
                    "Setup": "{GENERAL_SESSION_SETUP}",
                    "AV_Requirements": {
                        "Projector_Lumens": "{PROJECTOR_LUMENS}",
                        "Screens": "{SCREEN_COUNT}",
                        "Screen_Size": "{SCREEN_SIZE}",
                        "Microphones": ["{MICROPHONE_TYPES}"]
                    }
                },
                "Breakout_Rooms": {
                    "Count": "{BREAKOUT_ROOM_COUNT}",
                    "Capacity_Per_Room": "{BREAKOUT_CAPACITY}",
                    "Setup": "{BREAKOUT_SETUP}",
                    "AV_Requirements": {
                        "Projector_Lumens": "{BREAKOUT_PROJECTOR_LUMENS}",
                        "Screens": "{BREAKOUT_SCREEN_COUNT}",
                        "Microphones": ["{BREAKOUT_MICROPHONE_TYPES}"]
                    }
                },
                "Logistics_Room": {
                    "Capacity": "{LOGISTICS_CAPACITY}",
                    "Setup": "{LOGISTICS_SETUP}",
                    "WiFi": True
                }
            }
        },
        "REFRESHMENTS": {
            "Standard_Service": "{STANDARD_REFRESHMENT_SERVICE}",
            "AM_PM_Refreshments": "{AM_PM_REFRESHMENTS}",
            "Timing_Agreement": "{REFRESHMENT_TIMING}",
            "Breakout_Room_Logistics": "{BREAKOUT_ROOM_LOGISTICS}",
            "Tax_Exemption": "{TAX_EXEMPTION_NOTE}"
        },
        "LOGISTICS": {
            "Pre_con_Meeting": {
                "Date_Time": "{PRE_CON_DATE_TIME}",
                "Attendees": "{PRE_CON_ATTENDEES}",
                "Agenda": "{PRE_CON_AGENDA}",
                "Location": "{PRE_CON_LOCATION}",
                "Additional_Request": "{PRE_CON_ADDITIONAL_REQUEST}"
            }
        },
        "TERMS_AND_CONDITIONS": {
            "Payment_Terms": "{PAYMENT_TERMS}",
            "Tax_Exempt": "{TAX_EXEMPT}",
            "E_Invoicing_IPP": "{E_INVOICING_IPP}",
            "Cancellation_Penalties": "{CANCELLATION_PENALTIES}"
        },
        "COMPLIANCE_REQUIREMENTS": {
            "FAR_52_212_4": "{FAR_52_212_4}",
            "FAR_52_212_5": "{FAR_52_212_5}",
            "FAR_52_204_24_25_26": "{FAR_52_204_24_25_26}",
            "Security_Telecom_Restrictions": "{SECURITY_TELECOM_RESTRICTIONS}",
            "Bytedance_Restriction": "{BYTEDANCE_RESTRICTION}",
            "SAM_Registration": "{SAM_REGISTRATION}",
            "Tax_Exemption_Clause": "{TAX_EXEMPTION_CLAUSE}"
        }
    }
    
    # Meeting Information - Tablo formatından çıkar
    meeting_table_match = re.search(r'MEETING NAME[|\s]+MEETING DATES[|\s]+\n[|\s-]+\n[|\s]*([^\n|]+)[|\s]+([^\n|]+)', hotel_sow_text, re.IGNORECASE | re.MULTILINE)
    if meeting_table_match:
        data["MEETING_INFO"]["MEETING_NAME"] = meeting_table_match.group(1).strip()
        data["MEETING_INFO"]["MEETING_DATES"] = meeting_table_match.group(2).strip()
    else:
        # Alternatif: Satır bazlı arama
        meeting_match = re.search(r'MEETING NAME[:\s]*([^\n|]+)', hotel_sow_text, re.IGNORECASE)
        if meeting_match:
            data["MEETING_INFO"]["MEETING_NAME"] = meeting_match.group(1).strip()
        
        dates_match = re.search(r'MEETING DATES[:\s]*([^\n|]+)', hotel_sow_text, re.IGNORECASE)
        if dates_match:
            data["MEETING_INFO"]["MEETING_DATES"] = dates_match.group(1).strip()
    
    # Sleeping Room Requirements - Tablo formatından çıkar
    # Örnek: Sunday | Monday | Tuesday | ... formatında
    room_table_match = re.search(r'Sleeping Room Requirements[^\n]*(?:\n[^\n]*){0,5}\n(?:Sunday|Date)[|\s]+(?:Monday|Rooms)', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if room_table_match:
        # Tablo satırlarını parse et
        table_lines = room_table_match.group(0).split('\n')
        for line in table_lines:
            if '|' in line and not line.strip().startswith('---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2 and parts[0] and not parts[0].startswith('Date'):
                    day = parts[0]
                    if day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
                        if len(parts) >= 2:
                            data["SLEEPING_ROOM_REQUIREMENTS"]["Dates"][day] = parts[1] if len(parts) > 1 else "{DATE}"
                        if len(parts) >= 3:
                            rooms = parts[2].strip()
                            try:
                                data["SLEEPING_ROOM_REQUIREMENTS"]["Rooms_Booked_Night"][day] = int(rooms) if rooms.isdigit() else rooms
                            except:
                                data["SLEEPING_ROOM_REQUIREMENTS"]["Rooms_Booked_Night"][day] = rooms
    
    # Function Space Requirements - Tablo formatından çıkar
    func_table_match = re.search(r'Function Space Requirements[^\n]*(?:\n[^\n]*){0,10}', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if func_table_match:
        # Tablo satırlarını parse et
        pass  # İleride geliştirilebilir
    
    # Detailed AV Requirements - Registration Area
    reg_area_match = re.search(r'Registration Area[^:]*:\s*([^\n]+(?:\n(?!General|Conference|Logistics)[^\n]+)*)', hotel_sow_text, re.IGNORECASE | re.MULTILINE)
    if reg_area_match:
        reg_text = reg_area_match.group(1).strip()
        # Setup bilgisini çıkar
        setup_match = re.search(r'(rectangular|table|chairs|people)', reg_text, re.IGNORECASE)
        setup = reg_text[:150] if len(reg_text) > 150 else reg_text
        data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Registration_Area"]["Setup"] = setup
        data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Registration_Area"]["WiFi"] = "Wi-Fi" in reg_text or "WiFi" in reg_text
    
    # General Session Room - Detaylı AV
    gen_session_match = re.search(r'General Sessions Room[^:]*:\s*([^\n]+(?:\n(?!Conference|Logistics|Breakout)[^\n]+)*)', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if gen_session_match:
        gen_text = gen_session_match.group(1)
        capacity_match = re.search(r'(\d+)\s*(?:people|participants|attendees)', gen_text, re.IGNORECASE)
        if capacity_match:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["Capacity"] = int(capacity_match.group(1))
        
        # Projector lumens - önce "5,000" formatını dene
        projector_match3 = re.search(r'(\d{1,3}[,\s]?\d{3})[,\s]*lumen', gen_text, re.IGNORECASE)
        if projector_match3:
            lumens_str = projector_match3.group(1).replace(',', '').replace(' ', '')
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Projector_Lumens"] = int(lumens_str)
        else:
            # Alternatif: "minimum of" veya "at least" ile arama
            projector_match2 = re.search(r'(?:minimum|at least|min)[\s]*of[\s]*(\d+)[,\s]*lumen', gen_text, re.IGNORECASE)
            if projector_match2:
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Projector_Lumens"] = int(projector_match2.group(1))
            else:
                # Basit format: "5000 lumen"
                projector_match = re.search(r'(\d+)[,\s]*lumen', gen_text, re.IGNORECASE)
                if projector_match:
                    data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Projector_Lumens"] = int(projector_match.group(1))
        
        screen_match = re.search(r'(\d+)[\s]*[x\']\s*(\d+)[\']?\s*screen', gen_text, re.IGNORECASE)
        if screen_match:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Screens"] = int(screen_match.group(1))
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Screen_Size"] = f"{screen_match.group(1)}' x {screen_match.group(2)}'"
        else:
            # Alternatif: "two 6' x 10' screens" formatı
            screen_match2 = re.search(r'(?:two|2)[\s]*(\d+)[\']?\s*[x\']\s*(\d+)[\']?\s*screen', gen_text, re.IGNORECASE)
            if screen_match2:
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Screens"] = 2
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Screen_Size"] = f"{screen_match2.group(1)}' x {screen_match2.group(2)}'"
        
        mic_types = []
        if "handheld" in gen_text.lower() or "hand-held" in gen_text.lower():
            mic_types.append("Handheld")
        if "podium" in gen_text.lower():
            mic_types.append("Podium")
        if mic_types:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["AV_Requirements"]["Microphones"] = mic_types
        
        if "classroom" in gen_text.lower():
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["General_Session"]["Setup"] = "Classroom-style"
    
    # Breakout Rooms
    # Önce başlıktan count'u çıkar: "### Conference Breakout Rooms (4):"
    breakout_header_match = re.search(r'Breakout Rooms?[^(]*\((\d+)\)', hotel_sow_text, re.IGNORECASE)
    if breakout_header_match:
        data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["Count"] = int(breakout_header_match.group(1))
    
    breakout_match = re.search(r'Breakout Rooms?[^:]*:\s*([^\n]+(?:\n(?!Logistics|General)[^\n]+)*)', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if breakout_match:
        breakout_text = breakout_match.group(1)
        # Eğer başlıktan bulamadıysak, metinden ara
        if data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["Count"] == "{BREAKOUT_ROOM_COUNT}":
            room_count_match = re.search(r'(\d+)\s*(?:rooms?|separate)', breakout_text, re.IGNORECASE)
            if room_count_match:
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["Count"] = int(room_count_match.group(1))
        
        capacity_match = re.search(r'(\d+)\s*(?:people|participants)', breakout_text, re.IGNORECASE)
        if capacity_match:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["Capacity_Per_Room"] = int(capacity_match.group(1))
        
        if "classroom" in breakout_text.lower():
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["Setup"] = "Classroom-style"
        
        # Breakout rooms için projector lumens
        projector_match3 = re.search(r'(\d{1,3}[,\s]?\d{3})[,\s]*lumen', breakout_text, re.IGNORECASE)
        if projector_match3:
            lumens_str = projector_match3.group(1).replace(',', '').replace(' ', '')
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["AV_Requirements"]["Projector_Lumens"] = int(lumens_str)
        else:
            projector_match = re.search(r'(\d+)[,\s]*lumen', breakout_text, re.IGNORECASE)
            if projector_match:
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["AV_Requirements"]["Projector_Lumens"] = int(projector_match.group(1))
        
        # Breakout rooms için screen count
        screen_match = re.search(r'(\d+)[\s]*[x\']\s*(\d+)[\']?\s*screen', breakout_text, re.IGNORECASE)
        if screen_match:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["AV_Requirements"]["Screens"] = int(screen_match.group(1))
        else:
            # Alternatif: "1 6' x 10' screen" formatı
            screen_match2 = re.search(r'1[\s]*(\d+)[\']?\s*[x\']\s*(\d+)[\']?\s*screen', breakout_text, re.IGNORECASE)
            if screen_match2:
                data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["AV_Requirements"]["Screens"] = 1
        
        # Breakout rooms için microphones
        mic_types = []
        if "handheld" in breakout_text.lower() or "hand-held" in breakout_text.lower():
            mic_types.append("Handheld")
        if "podium" in breakout_text.lower():
            mic_types.append("Podium")
        if mic_types:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Breakout_Rooms"]["AV_Requirements"]["Microphones"] = mic_types
    
    # Logistics Room
    logistics_match = re.search(r'Logistics Room[^:]*:\s*([^\n]+(?:\n[^\n]+)*)', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if logistics_match:
        log_text = logistics_match.group(1)
        capacity_match = re.search(r'(\d+)\s*(?:people|participants)', log_text, re.IGNORECASE)
        if capacity_match:
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Logistics_Room"]["Capacity"] = int(capacity_match.group(1))
        
        if "boardroom" in log_text.lower():
            data["FUNCTION_SPACE_REQUIREMENTS"]["Detailed_AV_Requirements"]["Logistics_Room"]["Setup"] = "Boardroom Style"
    
    # Refreshments
    refreshment_match = re.search(r'LIGHT REFRESHMENTS[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n###|\n---|$)', hotel_sow_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if refreshment_match:
        refresh_text = refreshment_match.group(1)
        standard_match = re.search(r'Standard Service[:\s]*([^\n]+)', refresh_text, re.IGNORECASE)
        if standard_match:
            data["REFRESHMENTS"]["Standard_Service"] = standard_match.group(1).strip()
        
        am_pm_match = re.search(r'AM/PM Refreshments[:\s]*([^\n]+)', refresh_text, re.IGNORECASE)
        if am_pm_match:
            data["REFRESHMENTS"]["AM_PM_Refreshments"] = am_pm_match.group(1).strip()
    
    # Terms and Conditions
    payment_match = re.search(r'Payment Terms[:\s]*([^\n]+)', hotel_sow_text, re.IGNORECASE)
    if payment_match:
        data["TERMS_AND_CONDITIONS"]["Payment_Terms"] = payment_match.group(1).strip()
    
    tax_match = re.search(r'Tax Exempt[:\s]*([^\n]+)', hotel_sow_text, re.IGNORECASE)
    if tax_match:
        data["TERMS_AND_CONDITIONS"]["Tax_Exempt"] = tax_match.group(1).strip()
    
    # Compliance Requirements
    far_212_4_match = re.search(r'FAR 52\.212-4[:\s]*([^\n|]+)', hotel_sow_text, re.IGNORECASE)
    if far_212_4_match:
        value = far_212_4_match.group(1).strip()
        data["COMPLIANCE_REQUIREMENTS"]["FAR_52_212_4"] = "Yes" if "yes" in value.lower() or "evet" in value.lower() else "No"
    
    far_212_5_match = re.search(r'FAR 52\.212-5[:\s]*([^\n|]+)', hotel_sow_text, re.IGNORECASE)
    if far_212_5_match:
        value = far_212_5_match.group(1).strip()
        data["COMPLIANCE_REQUIREMENTS"]["FAR_52_212_5"] = "Yes" if "yes" in value.lower() or "evet" in value.lower() else "No"
    
    return data


def convert_to_gpt_format(hotel_sow_path: Path, sample_sow_path: Path, output_path: Path, use_markdown: bool = True) -> bool:
    """
    Hotel SOW'u GPT formatına dönüştür
    
    Args:
        hotel_sow_path: Hotel SOW PDF yolu
        sample_sow_path: Sample SOW PDF yolu (referans)
        output_path: Çıktı JSON dosyası yolu
    
    Returns:
        Başarılı ise True
    """
    try:
        logger.info(f"Reading sample SOW: {sample_sow_path}")
        sample_text = extract_text_from_pdf(sample_sow_path)
        if not sample_text:
            logger.error("Failed to extract sample SOW text")
            return False
        
        logger.info(f"Reading hotel SOW: {hotel_sow_path}")
        
        # Önce markdown dosyasını dene (daha temiz)
        hotel_md_path = hotel_sow_path.parent / 'sow.md'
        if use_markdown and hotel_md_path.exists():
            logger.info(f"Reading from markdown: {hotel_md_path}")
            with open(hotel_md_path, 'r', encoding='utf-8') as f:
                hotel_text = f.read()
        else:
            hotel_text = extract_text_from_pdf(hotel_sow_path)
        
        if not hotel_text:
            logger.error("Failed to extract hotel SOW text")
            return False
        
        # Sample SOW yapısını al
        sample_structure = parse_sample_sow_structure(sample_text)
        
        # Hotel SOW verilerini çıkar
        hotel_data = extract_hotel_sow_data(hotel_text)
        
        # Placeholder'ları ekle (gerçek değerler yerine)
        gpt_format = {
            "SOW_Template": "Hotel Accommodations and Meeting Space",
            "Version": "1.0",
            "Format": "GPT/AutoGen Compatible",
            **sample_structure
        }
        
        # Hotel SOW'dan çıkarılan verileri birleştir
        # Gerçek değerleri placeholder'lara dönüştür
        def replace_with_placeholders(value, placeholder_key):
            """Gerçek değerleri placeholder'lara dönüştür"""
            if isinstance(value, (int, float)):
                return value  # Sayısal değerleri koru
            if isinstance(value, bool):
                return value  # Boolean değerleri koru
            if isinstance(value, list):
                return [replace_with_placeholders(item, f"{placeholder_key}_ITEM") for item in value]
            if isinstance(value, dict):
                return {k: replace_with_placeholders(v, f"{placeholder_key}_{k.upper()}") for k, v in value.items()}
            # String değerleri placeholder'a dönüştür (eğer zaten placeholder değilse)
            if isinstance(value, str):
                if value.startswith("{") and value.endswith("}"):
                    return value  # Zaten placeholder
                if value and len(value.strip()) > 0:
                    # Gerçek değerleri placeholder'a dönüştür
                    return f"{{{placeholder_key}}}"
            return value
        
        # Hotel data'yı gpt_format'a merge et
        for key in hotel_data:
            if key in gpt_format:
                if isinstance(hotel_data[key], dict) and isinstance(gpt_format[key], dict):
                    # Nested dict'leri birleştir
                    for sub_key, sub_value in hotel_data[key].items():
                        if sub_key in gpt_format[key]:
                            # Gerçek değerleri placeholder'a dönüştür
                            if isinstance(gpt_format[key][sub_key], dict) and isinstance(sub_value, dict):
                                # Nested dict merge
                                for nested_key, nested_value in sub_value.items():
                                    if nested_key in gpt_format[key][sub_key]:
                                        # Placeholder'ı koru veya gerçek değeri kullan (sayısal/boolean ise)
                                        if isinstance(nested_value, (int, float, bool)):
                                            gpt_format[key][sub_key][nested_key] = nested_value
                                        elif isinstance(gpt_format[key][sub_key][nested_key], str) and gpt_format[key][sub_key][nested_key].startswith("{"):
                                            # Placeholder'ı koru
                                            pass
                                        else:
                                            gpt_format[key][sub_key][nested_key] = nested_value
                                    else:
                                        gpt_format[key][sub_key][nested_key] = nested_value
                            else:
                                # Basit değer: sayısal/boolean ise koru, string ise placeholder'a dönüştür
                                if isinstance(sub_value, (int, float, bool)):
                                    gpt_format[key][sub_key] = sub_value
                                elif isinstance(gpt_format[key][sub_key], str) and gpt_format[key][sub_key].startswith("{"):
                                    # Placeholder'ı koru
                                    pass
                                else:
                                    # Gerçek değeri placeholder'a dönüştür
                                    placeholder = gpt_format[key][sub_key] if gpt_format[key][sub_key].startswith("{") else f"{{{key.upper()}_{sub_key.upper()}}}"
                                    gpt_format[key][sub_key] = placeholder
                        else:
                            gpt_format[key][sub_key] = sub_value
        
        # Çıktı klasörünü oluştur
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON olarak kaydet
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(gpt_format, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ GPT format SOW saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting SOW to GPT format: {e}", exc_info=True)
        return False


def main():
    """Ana fonksiyon"""
    import sys
    
    # Logging ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Dosya yolları
    hotel_sow_path = Path("opportunities/380e50ec631e492b93b5572bf5938c34/sow_hotel_380e50ec631e492b93b5572bf5938c34.pdf")
    sample_sow_path = Path("samples/SAMPLE SOW FOR CHTGPT.pdf")
    output_path = Path("converted/hotel_sow_for_gpt.json")
    
    # Komut satırı argümanları
    if len(sys.argv) > 1:
        hotel_sow_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        sample_sow_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    
    # Dönüştür
    success = convert_to_gpt_format(hotel_sow_path, sample_sow_path, output_path)
    
    if success:
        print(f"Conversion successful! Output: {output_path}")
        return 0
    else:
        print(f"Conversion failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit(main())

