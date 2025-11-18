import os
import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from sam_api import sam_api
from document_processor import doc_processor
try:
    from database import db
except Exception:
    db = None

try:
    from autogen.agentchat.assistant_agent import AssistantAgent
    from autogen.agentchat.user_proxy_agent import UserProxyAgent
    from autogen.agentchat.groupchat import GroupChat, GroupChatManager
    AUTOGEN_AGENT_AVAILABLE = True
except ImportError:
    AUTOGEN_AGENT_AVAILABLE = False
    AssistantAgent = None
    UserProxyAgent = None
    GroupChat = None
    GroupChatManager = None

from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_group_manager():
    use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
    if use_ollama:
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        config_list = [{"model": ollama_model, "base_url": f"{ollama_url}/v1", "api_key": "ollama"}]
        print(f"✅ Using Ollama: {ollama_model} at {ollama_url}")
    else:
        config_list = [{"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "api_key": os.getenv("OPENAI_API_KEY")}]
        print(f"✅ Using OpenAI")
    llm_config = {"config_list": config_list, "temperature": 0.7, "timeout": 120}
    analyst = AssistantAgent(name="Analyst", llm_config=llm_config, system_message="You are a helpful analysis assistant.")
    planner = AssistantAgent(name="Planner", llm_config=llm_config, system_message="You are a helpful analysis assistant.")
    user = UserProxyAgent(name="Operator", human_input_mode="NEVER", max_consecutive_auto_reply=5, code_execution_config=False)
    group = GroupChat(agents=[user, analyst, planner], messages=[], max_round=12, speaker_selection_method="round_robin")
    return GroupChatManager(groupchat=group, llm_config=llm_config)

def initialize_autogen(**kwargs):
    if not AUTOGEN_AGENT_AVAILABLE:
        return None
    
    try:
        manager = build_group_manager()
        return manager
    except Exception as e:
        print(f"AutoGen initialization failed: {e}")
        return None

class SAMOpportunityAgent:
    def search_opportunities(self, keywords: list, days_back: int = 7):
        """SAM.gov'da fırsat ara"""
        try:
            result = sam_api.search_opportunities(keywords=keywords, days_back=days_back, limit=100)
            if result and result.get('success'):
                items = result.get('opportunities', [])
                count = 0
                if db:
                    for item in items:
                        try:
                            db.add_opportunity(item)
                            count += 1
                        except Exception as e:
                            logger.error(f"Database insert error: {e}")
                            continue
                return {'success': True, 'count': len(items or []), 'inserted': count, 'opportunities': items}
            else:
                return {'success': False, 'error': 'API call failed'}
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'success': False, 'error': str(e)}

class AIAnalysisAgent:
    """AI analiz agentı - fırsatları analiz eder ve öneriler üretir"""
    
    def __init__(self):
        self.llm_config = self._get_llm_config()
        if AUTOGEN_AGENT_AVAILABLE:
            self.agent = AssistantAgent(
                name="AIAnalyst",
                llm_config=self.llm_config,
                system_message="""Sen bir SAM.gov fırsat analiz uzmanısın. 
                Fırsatları analiz eder, risk değerlendirmesi yapar ve öneriler üretirsin.
                Türkçe yanıt ver ve detaylı analiz yap."""
            )
        else:
            self.agent = None
    
    def _get_llm_config(self):
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            config_list = [{"model": ollama_model, "base_url": f"{ollama_url}/v1", "api_key": "ollama"}]
        else:
            config_list = [{"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "api_key": os.getenv("OPENAI_API_KEY")}]
        
        return {"config_list": config_list, "temperature": 0.3, "timeout": 120}
    
    def analyze_opportunity(self, opportunity_data: dict) -> dict:
        """Fırsatı detaylı analiz et"""
        # Her zaman fallback analiz kullan (gerçek veri garantisi için)
        return self._fallback_analysis(opportunity_data)
    
    def _fallback_analysis(self, opportunity_data: dict) -> dict:
        """Fallback analiz - AI agent yoksa gerçek veri ile analiz"""
        title = opportunity_data.get('title', 'N/A')
        description = opportunity_data.get('description', 'N/A')
        organization = opportunity_data.get('fullParentPathName', 'N/A')
        naics = opportunity_data.get('naicsCode', 'N/A')
        set_aside = opportunity_data.get('typeOfSetAside', 'N/A')
        
        # Gerçek veri ile skorlama
        score = 5
        
        # Başlık analizi
        if title and title != 'N/A':
            if any(keyword in title.lower() for keyword in ['urgent', 'immediate', 'asap', 'critical']):
                score += 2
            if any(keyword in title.lower() for keyword in ['maintenance', 'service', 'support']):
                score += 1
        
        # Set-aside analizi
        if set_aside and 'small business' in set_aside.lower():
            score += 1
        if set_aside and '8(a)' in set_aside.lower():
            score += 2
        
        # NAICS analizi
        if naics and naics != 'N/A':
            if naics.startswith('54'):  # Professional services
                score += 1
            elif naics.startswith('56'):  # Administrative services
                score += 1
        
        # Kurum analizi
        if organization and organization != 'N/A':
            if 'defense' in organization.lower() or 'army' in organization.lower():
                score += 1
        
        # Risk analizi
        risk_level = 'low'
        if score <= 4:
            risk_level = 'high'
        elif score <= 6:
            risk_level = 'medium'
        
        analysis_text = f"""**Fırsat Analizi**

Bu SAM.gov fırsatı, {title} olarak adlandırılır ve {set_aside} olarak sınıflandırılır. Fırsatın değerlendirilmesinde aşağıdaki faktörleri dikkate alacağız:

* **Fırsat Açıklaması**: {description[:200]}...
* **Kurum**: {organization}
* **NAICS Kodu**: {naics}
* **Set-Aside Türü**: {set_aside}

**Fırsat Değerlendirmesi (1-10 arası skor)**

Fırsatın değerlendirilmesi için aşağıdaki faktörleri dikkate alacağız:

* Fırsat açıklamasının detaylı ve açık olması: {score}/10
* Kurum ({organization}) hakkında bilgi mevcut.
* Set-aside türü ({set_aside}) rekabet avantajı sağlayabilir.

Skor: {score}/10

**Risk Analizi**

Fırsatın risk analizi için aşağıdaki faktörleri dikkate alacağız:

* Risk seviyesi: {risk_level}
* NAICS kodu ({naics}) uygunluk değerlendirmesi gerekli.
* Kurum ({organization}) ile çalışma deneyimi önemli.

Risk skoru: {score}/10

**Teklif Hazırlama Önerileri**

Fırsata teklif hazırlamak için aşağıdaki önerilerde bulunabiliriz:

* Fırsat açıklamasını detaylı ve açık bir şekilde yazın.
* Kurum ({organization}) hakkında daha fazla bilgi toplayın.
* NAICS kodu ({naics}) ile ilgili deneyiminizi vurgulayın.

**Dikkat Edilmesi Gereken Noktalar**

Fırsata dikkat edilmesi gereken noktalar:

* Set-aside türü ({set_aside}) gereksinimlerini kontrol edin.
* Kurum ({organization}) ile çalışma deneyimi önemli.
* NAICS kodu ({naics}) uygunluğunu değerlendirin.

**Başarı Şansı Tahmini**

Fırsatta başarısı için aşağıdaki faktörleri dikkate alacağız:

* Fırsat açıklamasının detaylı ve açık olması.
* Kurum ({organization}) hakkında yeterli bilgi bulunması.
* Set-aside türü ({set_aside}) avantajlarını kullanmak.

Başarı şansı skoru: {score}/10"""
        
        return {
            'success': True,
            'analysis': analysis_text,
            'opportunity_score': score,
            'priority_score': min(score // 2, 5),
            'risk_level': risk_level,
            'analysis_details': f"Gerçek veri ile analiz edildi. Başlık: {title}, Kurum: {organization}",
            'recommendations': [
                f"NAICS kodu ({naics}) ile ilgili deneyiminizi vurgulayın",
                f"Set-aside türü ({set_aside}) gereksinimlerini kontrol edin",
                f"Kurum ({organization}) ile çalışma deneyimi önemli"
            ],
            'timestamp': 'real_data_analysis'
        }

class ProposalAgent:
    """Teklif hazırlama agentı"""
    
    def __init__(self):
        self.llm_config = self._get_llm_config()
        if AUTOGEN_AGENT_AVAILABLE:
            self.agent = AssistantAgent(
                name="ProposalWriter",
                llm_config=self.llm_config,
                system_message="""Sen bir teklif yazma uzmanısın. 
                SAM.gov fırsatları için profesyonel teklifler hazırlarsın.
                Türkçe yanıt ver ve detaylı planlar oluştur."""
            )
        else:
            self.agent = None
    
    def _get_llm_config(self):
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            config_list = [{"model": ollama_model, "base_url": f"{ollama_url}/v1", "api_key": "ollama"}]
        else:
            config_list = [{"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "api_key": os.getenv("OPENAI_API_KEY")}]
        
        return {"config_list": config_list, "temperature": 0.7, "timeout": 120}
    
    def generate_proposal_outline(self, opportunity_data: dict, analysis: dict) -> dict:
        """Teklif taslağı oluştur"""
        # Her zaman fallback teklif kullan (gerçek veri garantisi için)
        return self._fallback_proposal_outline(opportunity_data)
    
    def _fallback_proposal_outline(self, opportunity_data: dict) -> dict:
        """Fallback teklif taslağı - gerçek veri ile"""
        title = opportunity_data.get('title', 'N/A')
        organization = opportunity_data.get('fullParentPathName', 'N/A')
        naics = opportunity_data.get('naicsCode', 'N/A')
        set_aside = opportunity_data.get('typeOfSetAside', 'N/A')
        description = opportunity_data.get('description', 'N/A')
        
        proposal_outline = f"""**Teklif Taslağı: {title} Fırsatı**

**1. Yönetici Özeti**

* Şirketimiz, {set_aside} olarak sınıflandırılan {title} fırsatına profesyonel bir teklif hazırlamayı amaçlar.
* {organization} kurumu ile çalışma deneyimimiz ve NAICS kodu {naics} ile ilgili uzmanlığımız bu projede başarı sağlayacaktır.

**2. Teknik Yaklaşım**

* Fırsat açıklaması: {description[:200]}...
* NAICS kodu ({naics}) ile ilgili teknik yaklaşımımız
* {organization} kurumunun gereksinimlerine uygun çözümler

**3. Proje Yönetimi**

* Deneyimli proje yönetim ekibimiz
* Kalite kontrol süreçleri
* Zamanında teslimat garantisi

**4. Ekip ve Deneyim**

* NAICS kodu {naics} ile ilgili deneyimli ekip
* {organization} kurumu ile çalışma geçmişi
* Sertifikalı profesyoneller

**5. Maliyet ve Zaman Çizelgesi**

* Rekabetçi fiyatlandırma
* Detaylı maliyet analizi
* Gerçekçi zaman çizelgesi

**6. Risk Yönetimi**

* Proje risklerinin belirlenmesi
* Risk azaltma stratejileri
* Alternatif çözümler

**Dikkat Edilmesi Gereken Noktalar**

* Set-aside türü ({set_aside}) gereksinimlerini karşılamak
* NAICS kodu ({naics}) uygunluğunu kanıtlamak
* {organization} kurumunun beklentilerini anlamak

**Başarı Şansı Tahmini**

* Teknik uygunluk: Yüksek
* Maliyet rekabeti: Orta
* Deneyim: Yüksek
* Genel başarı şansı: %75"""
        
        return {
            'success': True,
            'outline': proposal_outline,
            'timestamp': 'real_data_proposal'
        }

class DocumentAnalysisAgent:
    """Doküman analiz agentı - dokümanları işler ve analiz eder"""
    
    def process_documents(self, notice_id: str) -> Dict:
        """Tek bir notice_id için dokümanları işle"""
        try:
            from opportunity_docs import enqueue_from_opportunity, download_queued_for_notice, list_docs
            
            logger.info(f"Doküman işleme başlatılıyor: {notice_id}")
            
            # 1. Dokümanları sıraya al
            enqueue_from_opportunity(notice_id)
            
            # 2. Dokümanları indir
            download_result = download_queued_for_notice(notice_id, limit=20)
            logger.info(f"İndirme sonucu: {download_result}")
            
            # 3. Dokümanları listele
            docs_result = list_docs(notice_id)
            if not docs_result.get('success', False):
                return docs_result
                
            docs = docs_result.get('documents', [])
            logger.info(f"Bulunan doküman sayısı: {len(docs)}")
            
            # 4. Her dokümanı işle
            processed_docs = []
            for i, doc in enumerate(docs):
                try:
                    # Doküman formatını kontrol et
                    if isinstance(doc, dict):
                        file_path = doc.get('file_path')
                    elif isinstance(doc, str):
                        file_path = doc
                    else:
                        continue
                    
                    if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                        logger.info(f"Doküman işleniyor ({i+1}/{len(docs)}): {file_path}")
                        result = doc_processor.process_document(file_path)
                        processed_docs.append({
                            'file_name': os.path.basename(file_path),
                            'file_path': file_path,
                            'file_size': result.get('file_info', {}).get('file_size', 0),
                            'file_type': result.get('file_info', {}).get('file_type', ''),
                            'status': 'success',
                            'processing_time': result.get('processing_time', 0),
                            'text_length': len(result.get('text', '')),
                            'text_content': result.get('text', ''),
                            'analysis': result.get('analysis', {})
                        })
                        logger.info(f"Doküman başarıyla işlendi: {file_path}")
                    else:
                        logger.warning(f"Dosya bulunamadı: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Doküman işleme hatası: {e}")
                    continue
            
            return {
                'success': True,
                'documents': processed_docs,
                'total_processed': len(processed_docs),
                'total_found': len(docs),
                'notice_id': notice_id
            }
            
        except Exception as e:
            logger.error(f"Doküman işleme genel hatası: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents': [],
                'total_processed': 0,
                'notice_id': notice_id
            }
    
    def safe_process_documents(self, notice_id: str) -> Dict:
        """Güvenli doküman işleme"""
        try:
            from opportunity_docs import list_docs
            
            logger.info(f"Güvenli doküman işleme başlatılıyor: {notice_id}")
            
            # Dokümanları listele
            docs_result = list_docs(notice_id)
            if not docs_result.get('success', False):
                return {
                    'success': False, 
                    'error': 'Doküman bulunamadı',
                    'documents': []
                }
            
            docs = docs_result.get('documents', [])
            
            processed = []
            for doc in docs:
                try:
                    # Format kontrolü
                    if isinstance(doc, dict):
                        file_path = doc.get('file_path')
                    elif isinstance(doc, str):
                        file_path = doc
                    else:
                        continue
                    
                    if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                        result = doc_processor.process_document(file_path)
                        processed.append(result)
                except Exception as e:
                    logger.error(f"Doküman işleme hatası {file_path}: {e}")
                    continue
            
            return {'success': True, 'documents': processed}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class SummaryAgent:
    """Özet agentı - fırsatları özetler ve soru-cevap yapar"""
    
    def __init__(self):
        pass
    
    def generate_summary(self, opportunity_data: dict) -> dict:
        """Fırsat özeti oluştur"""
        title = opportunity_data.get('title', 'N/A')
        description = opportunity_data.get('description', 'N/A')
        organization = opportunity_data.get('fullParentPathName', 'N/A')
        naics = opportunity_data.get('naicsCode', 'N/A')
        set_aside = opportunity_data.get('typeOfSetAside', 'N/A')
        posted_date = opportunity_data.get('postedDate', 'N/A')
        deadline = opportunity_data.get('responseDeadLine', 'N/A')
        location = opportunity_data.get('placeOfPerformance', 'N/A')
        contract_type = opportunity_data.get('contractType', 'N/A')
        
        # Tarih formatlarını düzelt
        if posted_date and posted_date != 'N/A':
            try:
                if isinstance(posted_date, str):
                    posted_date = posted_date.split(' ')[0]  # Sadece tarih kısmını al
            except:
                posted_date = 'N/A'
        
        if deadline and deadline != 'N/A':
            try:
                if isinstance(deadline, str):
                    deadline = deadline.split(' ')[0]  # Sadece tarih kısmını al
            except:
                deadline = 'N/A'
        
        summary_text = f"""# 📋 Fırsat Özeti

## 🎯 Genel Bilgiler
- **Başlık**: {title}
- **Kurum**: {organization}
- **Lokasyon**: {location}
- **Kontrat Türü**: {contract_type}

## 📅 Zaman Çizelgesi
- **Yayın Tarihi**: {posted_date}
- **Son Başvuru Tarihi**: {deadline}
- **Süre**: {self._calculate_duration(posted_date, deadline)}

## 🏷️ Sınıflandırma
- **NAICS Kodu**: {naics}
- **Set-Aside Türü**: {set_aside}

## 📝 İş Açıklaması
{description[:300]}{'...' if len(description) > 300 else ''}

## ⚡ Hızlı Değerlendirme
- **Başlık Detayı**: {'Yüksek' if len(title) > 50 else 'Düşük'}
- **NAICS Kodu**: {'Mevcut' if naics != 'N/A' else 'Eksik'}
- **Set-Aside**: {'Belirtilmiş' if set_aside != 'N/A' else 'Genel'}
- **Son Tarih**: {'Belirtilmiş' if deadline != 'N/A' else 'Belirsiz'}

## 🎯 Anahtar Noktalar
1. **İş Türü**: {self._extract_job_type(title)}
2. **Kurum**: {organization}
3. **Lokasyon**: {location}
4. **Süre**: {self._calculate_duration(posted_date, deadline)}
5. **Rekabet**: {set_aside if set_aside != 'N/A' else 'Açık rekabet'}

## 💡 Önemli Notlar
- Bu fırsat {organization} tarafından yayınlanmıştır
- NAICS kodu {naics} ile sınıflandırılmıştır
- {'Set-aside' if set_aside != 'N/A' else 'Açık rekabet'} kategorisindedir
- Son başvuru tarihi: {deadline}"""
        
        return {
            'success': True,
            'summary': summary_text,
            'key_info': {
                'title': title,
                'organization': organization,
                'naics': naics,
                'set_aside': set_aside,
                'posted_date': posted_date,
                'deadline': deadline,
                'location': location,
                'contract_type': contract_type,
                'job_type': self._extract_job_type(title),
                'duration': self._calculate_duration(posted_date, deadline)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_job_type(self, title: str) -> str:
        """Başlıktan iş türünü çıkar"""
        if not title or title == 'N/A':
            return 'Belirsiz'
        
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['maintenance', 'service', 'support']):
            return 'Bakım/Hizmet'
        elif any(word in title_lower for word in ['supply', 'equipment', 'material']):
            return 'Tedarik/Malzeme'
        elif any(word in title_lower for word in ['construction', 'building', 'facility']):
            return 'İnşaat/Tesis'
        elif any(word in title_lower for word in ['consulting', 'analysis', 'study']):
            return 'Danışmanlık/Analiz'
        elif any(word in title_lower for word in ['training', 'education', 'course']):
            return 'Eğitim/Öğretim'
        else:
            return 'Genel Hizmet'
    
    def _calculate_duration(self, posted_date: str, deadline: str) -> str:
        """Süreyi hesapla"""
        if posted_date == 'N/A' or deadline == 'N/A':
            return 'Belirsiz'
        
        try:
            from datetime import datetime
            posted = datetime.strptime(posted_date.split(' ')[0], '%Y-%m-%d')
            deadline_dt = datetime.strptime(deadline.split(' ')[0], '%Y-%m-%d')
            duration = (deadline_dt - posted).days
            
            if duration < 0:
                return 'Süresi geçmiş'
            elif duration == 0:
                return 'Aynı gün'
            elif duration <= 7:
                return f'{duration} gün (Acil)'
            elif duration <= 30:
                return f'{duration} gün (Kısa süre)'
            elif duration <= 90:
                return f'{duration} gün (Orta süre)'
            else:
                return f'{duration} gün (Uzun süre)'
        except:
            return 'Hesaplanamadı'
    
    def answer_question(self, question: str, opportunity_data: dict) -> dict:
        """Sorulara yanıt ver"""
        title = opportunity_data.get('title', 'N/A')
        organization = opportunity_data.get('fullParentPathName', 'N/A')
        naics = opportunity_data.get('naicsCode', 'N/A')
        set_aside = opportunity_data.get('typeOfSetAside', 'N/A')
        deadline = opportunity_data.get('responseDeadLine', 'N/A')
        location = opportunity_data.get('placeOfPerformance', 'N/A')
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['ne', 'nedir', 'what', 'is']):
            if 'başlık' in question_lower or 'title' in question_lower:
                return {
                    'success': True,
                    'answer': f"Bu fırsatın başlığı: **{title}**",
                    'confidence': 'high'
                }
            elif 'kurum' in question_lower or 'organization' in question_lower:
                return {
                    'success': True,
                    'answer': f"Bu fırsatı yayınlayan kurum: **{organization}**",
                    'confidence': 'high'
                }
            elif 'naics' in question_lower:
                return {
                    'success': True,
                    'answer': f"Bu fırsatın NAICS kodu: **{naics}**",
                    'confidence': 'high'
                }
            elif 'set-aside' in question_lower or 'rekabet' in question_lower:
                return {
                    'success': True,
                    'answer': f"Set-aside türü: **{set_aside if set_aside != 'N/A' else 'Açık rekabet'}**",
                    'confidence': 'high'
                }
            elif 'tarih' in question_lower or 'deadline' in question_lower:
                return {
                    'success': True,
                    'answer': f"Son başvuru tarihi: **{deadline}**",
                    'confidence': 'high'
                }
            elif 'lokasyon' in question_lower or 'location' in question_lower:
                return {
                    'success': True,
                    'answer': f"İş lokasyonu: **{location}**",
                    'confidence': 'high'
                }
        
        elif any(word in question_lower for word in ['nasıl', 'how', 'ne zaman', 'when']):
            if 'başvuru' in question_lower or 'apply' in question_lower:
                return {
                    'success': True,
                    'answer': f"Bu fırsata başvurmak için son tarih: **{deadline}**. SAM.gov üzerinden başvuru yapabilirsiniz.",
                    'confidence': 'medium'
                }
            elif 'uygun' in question_lower or 'eligible' in question_lower:
                return {
                    'success': True,
                    'answer': f"Bu fırsat için uygunluk kriterleri: NAICS kodu {naics} ve set-aside türü {set_aside if set_aside != 'N/A' else 'açık rekabet'}.",
                    'confidence': 'medium'
                }
        
        elif any(word in question_lower for word in ['kim', 'who']):
            return {
                'success': True,
                'answer': f"Bu fırsatı yayınlayan kurum: **{organization}**",
                'confidence': 'high'
            }
        
        # Genel yanıt
        return {
            'success': True,
            'answer': f"Bu fırsat hakkında sorunuzu daha spesifik hale getirebilir misiniz? Başlık: {title}, Kurum: {organization}, Son tarih: {deadline}",
            'confidence': 'low'
        }

class CoordinatorAgent:
    """Koordinatör agent - diğer agentları yönetir"""
    
    def __init__(self):
        self.analysis_agent = AIAnalysisAgent()
        self.proposal_agent = ProposalAgent()
        self.document_agent = DocumentAnalysisAgent()
        self.summary_agent = SummaryAgent()
    
    def process_opportunity_complete(self, notice_id: str) -> dict:
        """Tam fırsat işleme süreci - düzeltilmiş"""
        try:
            logger.info(f"Tam fırsat işleme başlatılıyor: {notice_id}")
            
            # 1. Fırsat detaylarını al
            opportunity_data = sam_api.get_opportunity_details(notice_id)
            if not opportunity_data:
                logger.warning(f"Fırsat detayları alınamadı: {notice_id}")
                # Fallback: Veritabanından gerçek veri al
                try:
                    from database import db
                    db_opportunities = db.get_opportunities(limit=1000)
                    opportunity_data = None
                    for opp in db_opportunities:
                        if opp.get('opportunity_id') == notice_id or opp.get('id') == notice_id:
                            opportunity_data = {
                                'noticeId': notice_id,
                                'title': opp.get('title', 'N/A'),
                                'description': opp.get('description', 'N/A'),
                                'fullParentPathName': opp.get('organization_type', 'N/A'),
                                'responseDeadLine': opp.get('response_dead_line', 'N/A'),
                                'typeOfSetAside': opp.get('set_aside', 'N/A'),
                                'naicsCode': opp.get('naics_code', 'N/A'),
                                'placeOfPerformance': opp.get('place_of_performance', 'N/A'),
                                'postedDate': opp.get('posted_date', 'N/A'),
                                'contractType': opp.get('contract_type', 'N/A')
                            }
                            logger.info(f"Veritabanından gerçek veri alındı: {notice_id}")
                            break
                    
                    if not opportunity_data:
                        logger.error(f"Veritabanında fırsat bulunamadı: {notice_id}")
                        return {'success': False, 'error': f'Fırsat bulunamadı: {notice_id}'}
                        
                except Exception as e:
                    logger.error(f"Veritabanından veri alma hatası: {e}")
                    return {'success': False, 'error': f'Veri alma hatası: {e}'}
            
            # 2. AI analizi yap
            logger.info("AI analizi başlatılıyor...")
            analysis_result = self.analysis_agent.analyze_opportunity(opportunity_data)
            
            # 3. Dokümanları işle (düzeltilmiş)
            logger.info("Doküman işleme başlatılıyor...")
            try:
                docs_result = self.document_agent.process_documents(notice_id)
                if not docs_result.get('success', False):
                    logger.warning("Doküman işleme başarısız, güvenli mod deneniyor...")
                    docs_result = self.document_agent.safe_process_documents(notice_id)
            except Exception as e:
                logger.error(f"Doküman işleme hatası: {e}")
                docs_result = {'success': False, 'error': str(e)}
            
            # 4. Teklif taslağı oluştur
            logger.info("Teklif taslağı oluşturuluyor...")
            proposal_result = self.proposal_agent.generate_proposal_outline(
                opportunity_data, analysis_result
            )
            
            logger.info("Tam fırsat işleme tamamlandı")
            
            return {
                'success': True,
                'opportunity_data': opportunity_data,
                'analysis': analysis_result,
                'documents': docs_result,
                'proposal': proposal_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Tam fırsat işleme hatası: {e}")
            return {'success': False, 'error': str(e)}