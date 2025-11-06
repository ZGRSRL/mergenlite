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

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available, using mock analysis")

class LLMAnalyzer:
    """LLM ile gereksinim analizi"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.use_openai = True
        else:
            self.use_openai = False
            logger.warning("OpenAI API key not set, using mock analysis")
    
    def extract_requirements(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Metinden gereksinimleri çıkar"""
        
        if self.use_openai:
            return self._extract_with_openai(text, rag_context)
        else:
            return self._extract_with_mock(text, rag_context)
    
    def _extract_with_openai(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """OpenAI ile gereksinim çıkarımı"""
        
        try:
            # RAG bağlamını birleştir
            context_text = ""
            if rag_context:
                context_text = "\n\n".join([ctx.get('text', '') for ctx in rag_context[:3]])
            
            # Prompt oluştur
            prompt = f"""
Aşağıdaki ilan dokümanını analiz ederek gereksinimleri JSON formatında çıkarın.

Metin:
{text[:3000]}

RAG Bağlamı:
{context_text[:1000]}

Lütfen aşağıdaki bilgileri JSON formatında çıkarın:
- room_count: Oda sayısı gereksinimi (sayı veya "belirtilmemiş")
- av_required: AV (Audio-Visual) gereksinimi var mı? (true/false)
- date_range: Tarih aralığı (örn: "2024-03-01 to 2024-03-05")
- location: Konum gereksinimi (şehir/ülke veya "belirtilmemiş")
- constraints: Kısıtlar listesi (örn: ["Alkol yasağı", "Sigara yasağı"])
- other_requirements: Diğer önemli gereksinimler (liste)

Sadece JSON çıktısı verin, başka açıklama yapmayın.
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Sen bir ilan analiz uzmanısın. JSON formatında yapılandırılmış veri çıkarırsın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
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
        
        except Exception as e:
            logger.error(f"Error with OpenAI extraction: {e}")
            return self._extract_with_mock(text, rag_context)
    
    def _extract_with_mock(self, text: str, rag_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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

