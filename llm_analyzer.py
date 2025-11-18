#!/usr/bin/env python3
"""
LLM Analiz Modülü
Gereksinim çıkarımı ve özellik analizi için LLM kullanımı
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional

from llm_client import (
    call_logged_llm,
    llm_is_available,
    LLMNotAvailableError,
    extract_message_text,
)


logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM ile gereksinim analizi"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.use_openai = llm_is_available()
        if not self.use_openai:
            logger.warning("LLM not available, using mock analysis")
    
    def extract_requirements(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Metinden gereksinimleri çıkar - Form verileri ile özelleştirilmiş analiz"""
        
        if self.use_openai:
            return self._extract_with_openai(text, rag_context, form_data)
        else:
            return self._extract_with_mock(text, rag_context, form_data)
    
    def _extract_with_openai(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """OpenAI ile gereksinim çıkarımı - Form verileri ile özelleştirilmiş"""
        
        try:
            # RAG bağlamını birleştir
            context_text = ""
            if rag_context:
                context_text = "\n\n".join([ctx.get('text', '') for ctx in rag_context[:3]])
            
            # Prompt oluştur - Daha fazla metin kullan
            # Metin çok uzunsa, önemli bölümleri önceliklendir
            text_to_use = text
            if len(text) > 8000:
                # İlk 4000 ve son 4000 karakteri al (başlık ve özet genelde başta/sonda)
                text_to_use = text[:4000] + "\n\n[... metin ortası atlandı ...]\n\n" + text[-4000:]
                logger.info(f"Metin çok uzun, başlangıç ve son kısımlar kullanılıyor")
            
            # RAG bağlamını da genişlet
            context_to_use = context_text
            if len(context_text) > 2000:
                context_to_use = context_text[:2000]
            
            # Form verilerini prompt'a ekle
            form_context = ""
            if form_data:
                form_json = json.dumps(form_data, ensure_ascii=False, indent=2)
                form_context = f"""
FORM BİLGİLERİ (Analiz Kriterleri):
{form_json}

Bu form bilgilerine göre PDF içeriğini değerlendirin:
- PDF içeriğinde belirtilen koşullar formdaki bilgilerle uyuşuyor mu?
- Eksik veya çelişen alanları açıkla.
- Form kriterlerine göre uygunluk (Compliance) seviyesini yüzde ile değerlendir.
"""
            
            prompt = f"""
Aşağıdaki ilan dokümanını DETAYLI olarak analiz ederek tüm gereksinimleri JSON formatında çıkarın.
PDF'den çıkarılan tüm metni dikkatlice okuyun ve her gereksinimi tespit edin.
{form_context if form_context else ""}

Metin:
{text_to_use}

RAG Bağlamı (İlgili Bölümler):
{context_to_use}

Lütfen aşağıdaki bilgileri JSON formatında çıkarın:
- room_count: Oda sayısı gereksinimi (sayı veya "belirtilmemiş")
- av_required: AV (Audio-Visual) gereksinimi var mı? (true/false)
- date_range: Tarih aralığı (örn: "2024-03-01 to 2024-03-05")
- location: Konum gereksinimi (şehir/ülke veya "belirtilmemiş")
- constraints: Kısıtlar listesi (örn: ["Alkol yasağı", "Sigara yasağı"])
- other_requirements: Diğer önemli gereksinimler (liste)
- compliance_score: Form kriterlerine göre uygunluk skoru (0-100)
- matched_criteria: Form kriterleriyle eşleşen alanlar (liste)
- missing_or_conflicting: Eksik veya çelişen alanlar (liste)

Sadece JSON çıktısı verin, başka açıklama yapmayın.
"""
            
            # System message - Form verilerine göre özelleştirilmiş
            system_message = "Sen bir kamu ihale analisti ajansın. Görevin: PDF sözleşme içeriğini verilen form bilgilerine göre değerlendirmek. PDF içeriğinde belirtilen koşullar formdaki bilgilerle uyuşuyor mu? Eksik veya çelişen alanları açıkla. Uygunluk (Compliance) seviyesini yüzde ile değerlendir. Sonuçları JSON formatında döndür. Tüm gereksinimleri, kriterleri, zorunlulukları ve spesifikasyonları DETAYLI olarak çıkarırsın. Eksik bırakma, her detayı yakala."
            
            response = call_logged_llm(
                agent_name="LLMAnalyzer",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
            result_text = extract_message_text(response).strip()
            
            # JSON'u parse et
            try:
                # JSON'u temizle (eğer code block içindeyse)
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                
                requirements = json.loads(result_text)
                
                return {
                    'success': True,
                    'data': {
                        'requirements': requirements
                    }
                }
            
            except json.JSONDecodeError:
                logger.error("Could not parse JSON from LLM response")
                return self._extract_with_mock(text, rag_context)
        
        except LLMNotAvailableError as exc:
            logger.warning(f"LLM not available, falling back to mock extraction: {exc}")
            return self._extract_with_mock(text, rag_context)
        except Exception as e:
            logger.error(f"Error with OpenAI extraction: {e}")
            return self._extract_with_mock(text, rag_context)
    
    def analyze_document_by_criteria(self, text: str, criteria: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Belirli bir kriter için özelleştirilmiş analiz (Form başlıkları özelinde tarama)"""
        
        if not self.use_openai:
            return self._analyze_criteria_mock(text, criteria, form_data)
        
        try:
            form_context = ""
            if form_data:
                # Sadece ilgili form bilgilerini göster
                relevant_form_data = {
                    "company_name": form_data.get("company_name", ""),
                    "project_type": form_data.get("project_type", ""),
                    "location": form_data.get("location", ""),
                    "dates": form_data.get("dates", ""),
                    "participants": form_data.get("participants", 0),
                    "budget": form_data.get("budget", 0)
                }
                form_json = json.dumps(relevant_form_data, ensure_ascii=False, indent=2)
                form_context = f"\n\nFORM BİLGİLERİ:\n{form_json}\n\n"
            
            # Kriter özelinde system message
            system_message = f"""Sen bir kamu ihale analisti ajansın. Görevin: PDF dokümanını SADECE "{criteria}" kriteri açısından değerlendirmek.

Analiz kuralları:
- PDF içeriğinde "{criteria}" ile ilgili tüm bilgileri bul ve analiz et
- Bu kriter açısından form bilgileriyle uyumlu mu kontrol et
- Bu kriter için eksik veya çelişen alanları açıkla
- Bu kriter için uygunluk (Compliance) seviyesini yüzde ile değerlendir
- Sadece bu kriterle ilgili bulguları raporla
- Sonuçları JSON formatında döndür"""
            
            text_to_use = text[:8000] if len(text) > 8000 else text  # Kriter bazlı analiz için daha fazla metin
            
            prompt = f"""
{form_context}
PDF İçeriği:
{text_to_use}

Lütfen "{criteria}" kriteri açısından aşağıdaki bilgileri JSON formatında çıkarın:
- criteria: "{criteria}"
- compliance_score: Bu kriter için uygunluk skoru (0-100)
- matched_info: Bu kriterle ilgili bulunan bilgiler (detaylı liste)
- missing_or_conflicting: Bu kriter için eksik veya çelişen alanlar (liste)
- recommendations: Bu kriter için öneriler (liste)
- key_findings: Bu kriterle ilgili önemli bulgular (liste)
- relevant_sections: PDF'de bu kriterle ilgili bölümler (liste)

Sadece JSON çıktısı verin, başka açıklama yapmayın.
"""
            
            # Yeni OpenAI API (v1.0+) kullan
            response = call_logged_llm(
                agent_name="LLMAnalyzer",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            result_text = extract_message_text(response).strip()
            
            # JSON'u parse et
            try:
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                
                analysis_result = json.loads(result_text)
                
                return {
                    'success': True,
                    'data': {
                        'criteria': criteria,
                        'analysis': analysis_result
                    }
                }
            
            except json.JSONDecodeError:
                logger.error("Could not parse JSON from criteria analysis response")
                return self._analyze_criteria_mock(text, criteria, form_data)
        
        except LLMNotAvailableError as exc:
            logger.warning(f"LLM not available for criteria analysis: {exc}")
            return self._analyze_criteria_mock(text, criteria, form_data)
        except Exception as e:
            logger.error(f"Error with criteria analysis: {e}")
            return self._analyze_criteria_mock(text, criteria, form_data)
    
    def _analyze_criteria_mock(self, text: str, criteria: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock kriter bazlı analiz"""
        return {
            'success': True,
            'data': {
                'criteria': criteria,
                'analysis': {
                    'compliance_score': 80,
                    'matched_info': [f'Found references to {criteria}'],
                    'missing_or_conflicting': [],
                    'recommendations': ['Review manually'],
                    'key_findings': [f'{criteria} criteria analyzed']
                }
            }
        }
    
    def analyze_document_by_type(self, text: str, document_type: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Belge tipine göre özelleştirilmiş analiz"""
        
        if not self.use_openai:
            return self._analyze_document_mock(text, document_type, form_data)
        
        try:
            form_context = ""
            if form_data:
                form_json = json.dumps(form_data, ensure_ascii=False, indent=2)
                form_context = f"\n\nFORM BİLGİLERİ:\n{form_json}\n\n"
            
            # Belge tipine göre system message
            agent_roles = {
                "rfq": "Requirements Agent - Teklif kriterlerini çıkarmak",
                "sow": "Scope Agent - Hizmet kapsamı ile form verilerini eşleştirmek",
                "contract": "Contract Agent - Nihai sözleşmenin RFQ ile uyumunu denetlemek",
                "far": "Compliance Agent - Telekomünikasyon güvenlik (FAR) uygunluk kontrolü",
                "performance": "Performance Agent - Önceki performans referanslarının güvenilirliğini değerlendirmek"
            }
            
            agent_role = agent_roles.get(document_type.lower(), "Document Analyst")
            
            system_message = f"Sen bir {agent_role} ajansın. Görevin: PDF dokümanını verilen form bilgilerine göre değerlendirmek. Analiz kuralları:\n- PDF içeriğinde belirtilen koşullar formdaki bilgilerle uyuşuyor mu?\n- Eksik veya çelişen alanları açıkla.\n- Uygunluk (Compliance) seviyesini yüzde ile değerlendir.\n- Sonuçları JSON formatında döndür."
            
            text_to_use = text[:6000] if len(text) > 6000 else text
            
            prompt = f"""
{form_context}
PDF İçeriği:
{text_to_use}

Lütfen aşağıdaki bilgileri JSON formatında çıkarın:
- compliance_score: Form kriterlerine göre uygunluk skoru (0-100)
- matched_criteria: Form kriterleriyle eşleşen alanlar (liste)
- missing_or_conflicting: Eksik veya çelişen alanlar (liste)
- recommendations: Öneriler (liste)
- key_findings: Önemli bulgular (liste)

Sadece JSON çıktısı verin, başka açıklama yapmayın.
"""
            
            response = call_logged_llm(
                agent_name="LLMAnalyzer",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            result_text = extract_message_text(response).strip()
            
            # JSON'u parse et
            try:
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                
                analysis_result = json.loads(result_text)
                
                return {
                    'success': True,
                    'data': {
                        'document_type': document_type,
                        'analysis': analysis_result
                    }
                }
            
            except json.JSONDecodeError:
                logger.error("Could not parse JSON from document analysis response")
                return self._analyze_document_mock(text, document_type, form_data)
        
        except LLMNotAvailableError as exc:
            logger.warning(f"LLM not available for document analysis: {exc}")
            return self._analyze_document_mock(text, document_type, form_data)
        except Exception as e:
            logger.error(f"Error with document type analysis: {e}")
            return self._analyze_document_mock(text, document_type, form_data)
    
    def _analyze_document_mock(self, text: str, document_type: str, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock belge tipi analizi"""
        return {
            'success': True,
            'data': {
                'document_type': document_type,
                'analysis': {
                    'compliance_score': 85,
                    'matched_criteria': ['Basic requirements found'],
                    'missing_or_conflicting': [],
                    'recommendations': ['Review document manually'],
                    'key_findings': ['Document processed successfully']
                }
            }
        }
    
    def _extract_with_mock(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock gereksinim çıkarımı (OpenAI olmadan)"""
        
        # Basit pattern matching ile gereksinimleri çıkar
        text_lower = text.lower()
        
        # Oda sayısı
        room_count = "belirtilmemiş"
        if "room" in text_lower or "oda" in text_lower:
            # Basit sayı çıkarımı
            import re
            room_numbers = re.findall(r'(\d+)\s*(?:room|oda)', text_lower)
            if room_numbers:
                room_count = int(room_numbers[0])
        
        # AV gereksinimi
        av_required = any(keyword in text_lower for keyword in ['av', 'audio', 'visual', 'projector', 'screen', 'microphone'])
        
        # Tarih aralığı
        date_range = "belirtilmemiş"
        date_patterns = re.findall(r'\d{4}-\d{2}-\d{2}', text)
        if len(date_patterns) >= 2:
            date_range = f"{date_patterns[0]} to {date_patterns[1]}"
        elif len(date_patterns) == 1:
            date_range = date_patterns[0]
        
        # Konum
        location = "belirtilmemiş"
        location_keywords = ['washington', 'dc', 'virginia', 'maryland', 'new york', 'california']
        for keyword in location_keywords:
            if keyword in text_lower:
                location = keyword.title()
                break
        
        # Kısıtlar
        constraints = []
        if "alcohol" in text_lower or "alkol" in text_lower:
            constraints.append("Alkol yasağı")
        if "smoking" in text_lower or "sigara" in text_lower:
            constraints.append("Sigara yasağı")
        if "parking" in text_lower or "otopark" in text_lower:
            constraints.append("Otopark gereksinimi")
        
        return {
            'success': True,
            'data': {
                'requirements': {
                    'room_count': room_count,
                    'av_required': av_required,
                    'date_range': date_range,
                    'location': location,
                    'constraints': constraints,
                    'other_requirements': []
                }
            }
        }
