#!/usr/bin/env python3
"""
MergenLite - Modern SAM.gov Opportunity Analysis Platform
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import os
import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_paths = ['mergen/.env', '/app/mergen/.env', '.env', '/app/.env']
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True, verbose=False)
            break
except ImportError:
    pass

SAM_RATE_LIMIT_SECONDS = float(os.getenv("SAM_RATE_LIMIT", "0") or 0)
_SAM_RATE_LIMIT_LOCK = Lock()
_LAST_SAM_CALL_TS = 0.0


def _respect_sam_rate_limit():
    """Simple rate limiter based on SAM_RATE_LIMIT env (seconds between requests)."""
    global _LAST_SAM_CALL_TS
    if SAM_RATE_LIMIT_SECONDS <= 0:
        return
    with _SAM_RATE_LIMIT_LOCK:
        now = time.time()
        wait_duration = SAM_RATE_LIMIT_SECONDS - (now - _LAST_SAM_CALL_TS)
        if wait_duration > 0:
            logger.info("SAM rate limit active; sleeping %.2f seconds before next request", wait_duration)
            time.sleep(wait_duration)
            now = time.time()
        _LAST_SAM_CALL_TS = now

# Local imports
try:
    from guided_analysis import render_guided_analysis_page
    from sam_integration import SAMIntegration
except ImportError:
    pass

# Database imports
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from mergenlite_models import Opportunity, Base, Hotel, EmailLog
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="MergenLite",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar'ı gizle, üstte navigation var
)

# Modern CSS - theme.css yükle (her zaman yükle, cache sorunlarını önlemek için)
css_loaded = False
try:
    from theme_loader import load_css
    if os.path.exists("theme.css"):
        load_css("theme.css")
        css_loaded = True
except (ImportError, FileNotFoundError) as e:
    logger.warning(f"theme_loader bulunamadı: {e}")

# Fallback: theme.css dosyasını doğrudan oku
if not css_loaded:
    try:
        if os.path.exists("theme.css"):
            with open("theme.css", "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            css_loaded = True
            logger.info("✅ theme.css doğrudan yüklendi")
    except Exception as e:
        logger.warning(f"theme.css yüklenemedi: {e}")

# Son fallback: Minimal inline CSS (her zaman yükle)
if not css_loaded:
    st.markdown("""
<style>
    /* Modern Dark Gradient Theme - Minimal Fallback */
    :root {
      --bg-950: #0b1220;
      --bg-900: #111827;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --border: #1f2a44;
      --primary: #7c3aed;
      --primary-2: #6d28d9;
      --blue: #3b82f6;
      --blue-400: #60a5fa;
      --blue-500: #3b82f6;
      --blue-600: #2563eb;
      --emerald: #10b981;
      --emerald-500: #10b981;
      --emerald-600: #059669;
      --orange: #f59e0b;
      --orange-500: #f59e0b;
      --orange-600: #d97706;
      --red: #ef4444;
      --red-500: #ef4444;
      --text-300: #cbd5e1;
      --text-400: #9ca3af;
      --border-700: #334155;
      --border-800: #1e293b;
    }
    .stApp { 
      background: radial-gradient(1200px 600px at 20% -10%, #1f2a44 0%, var(--bg-950) 40%), 
                  linear-gradient(180deg, var(--bg-950), var(--bg-900)); 
      color: var(--text); 
      min-height: 100vh;
    }
    .main .block-container { 
      padding-top: 16px; 
      padding-bottom: 24px; 
      max-width: 1400px;
      margin: 0 auto;
    }
    .main-header { 
      font-size: 28px; 
      font-weight: 700; 
      color: var(--text); 
      margin-bottom: 24px; 
      letter-spacing: -0.5px; 
      text-align: left;
    }
    .kpi-card { 
      border-radius: 12px; 
      padding: 24px; 
      backdrop-filter: blur(6px); 
      border: 0; 
      box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
      transition: transform .2s ease, box-shadow .2s ease; 
      cursor: pointer;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .kpi-card:hover { 
      transform: scale(1.02); 
      box-shadow: 0 14px 40px rgba(0,0,0,0.4); 
    }
    .kpi-blue { 
      background: linear-gradient(to bottom right, var(--blue-600), var(--blue-500)); 
      color: white; 
    }
    .kpi-emerald { 
      background: linear-gradient(to bottom right, var(--emerald-600), var(--emerald-500)); 
      color: white; 
    }
    .kpi-orange { 
      background: linear-gradient(to bottom right, var(--orange-600), var(--orange-500)); 
      color: white; 
    }
    .kpi-purple { 
      background: linear-gradient(to bottom right, #9333ea, #a855f7); 
      color: white; 
    }
    .op-card { 
      background: rgba(15, 23, 42, 0.5); 
      border: 1px solid var(--border-800); 
      border-radius: 10px; 
      padding: 24px; 
      backdrop-filter: blur(6px); 
      transition: all .2s ease;
      margin-bottom: 16px;
      position: relative;
      z-index: 1;
    }
    .op-card:hover { 
      border-color: rgba(59, 130, 246, 0.5); 
      background: rgba(15, 23, 42, 0.7); 
      box-shadow: 0 16px 32px rgba(0,0,0,0.3); 
      transform: translateY(-2px); 
    }
    .badge { display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; padding: 4px 10px; font-size: 11px; font-weight: 600; letter-spacing: .4px; border: 1px solid; white-space: nowrap; }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.5); }
    .badge-info { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border-color: rgba(59, 130, 246, 0.5); }
    .badge-warning { background: rgba(234, 179, 8, 0.2); color: #fbbf24; border-color: rgba(234, 179, 8, 0.5); }
    .badge-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: rgba(239, 68, 68, 0.5); }
    .badge-risk-low { background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.5); }
    .badge-risk-medium { background: rgba(234, 179, 8, 0.2); color: #fbbf24; border-color: rgba(234, 179, 8, 0.5); }
    .badge-risk-high { background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: rgba(239, 68, 68, 0.5); }
    .stButton>button { background: linear-gradient(to right, var(--blue-600), var(--blue-500)); color: white; border: 0; font-weight: 600; border-radius: 8px; padding: 10px 16px; transition: all .15s ease; }
    .stButton>button:hover { background: linear-gradient(to right, #1d4ed8, var(--blue-600)); transform: translateY(-1px); box-shadow: 0 8px 20px rgba(59, 130, 246, 0.35); }
    .alert { border-left: 4px solid; border-radius: 8px; padding: 10px 12px; margin: 8px 0; font-size: 14px; backdrop-filter: blur(6px); }
    .alert-success { background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.7); color: #a7f3d0; }
    .alert-info { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.7); color: #bfdbfe; }
    .alert-warning { background: rgba(234, 179, 8, 0.1); border-color: rgba(234, 179, 8, 0.7); color: #fde68a; }
    .alert-danger { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.7); color: #fecaca; }
    .modern-card { background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 12px; padding: 24px; backdrop-filter: blur(6px); transition: all .2s ease; }
    .modern-card:hover { background: rgba(15, 23, 42, 0.7); border-color: var(--border-700); }
    .nav-bar-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }
    .nav-bar-container > div[data-testid="column"] { padding-left: 0 !important; padding-right: 0 !important; }
    .nav-tab { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 12px 16px; background: transparent; border-radius: 6px; color: var(--text-400); font-size: 14px; font-weight: 500; transition: all .2s ease; cursor: pointer; position: relative; }
    .nav-tab:hover { background: rgba(59, 130, 246, 0.15); color: var(--blue-400); transform: translateY(-1px); }
    .nav-tab-active { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 12px 16px; background: linear-gradient(to right, var(--blue-600), var(--blue-500)); border-radius: 6px; color: white; font-size: 14px; font-weight: 600; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); transition: all .2s ease; }
    .nav-tab-active:hover { background: linear-gradient(to right, var(--blue-500), var(--blue-400)); box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4); transform: translateY(-1px); }
    button[key^="nav_"] { position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important; background: transparent !important; border: 0 !important; color: transparent !important; opacity: 0.01 !important; z-index: 100 !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; pointer-events: auto !important; }
    div[data-testid="column"]:has(button[key^="nav_"]) { position: relative !important; }
    table { width: 100%; border-collapse: collapse; }
    table th { text-align: left; font-weight: 600; color: var(--text-400); font-size: 13px; padding: 12px 16px; }
    table td { padding: 12px 16px; font-size: 13px; }
    table tbody tr { border-bottom: 1px solid var(--border-800); transition: background .2s ease; }
    table tbody tr:hover { background: rgba(59, 130, 246, 0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; border-bottom: 1px solid var(--border-800); }
    .stTabs [data-baseweb="tab"] { padding: 12px 20px; color: var(--text-400); font-size: 14px; font-weight: 500; border-bottom: 2px solid transparent; transition: all .2s ease; }
    .stTabs [aria-selected="true"] { color: var(--blue-400); border-bottom-color: var(--blue-500); font-weight: 600; }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-300); background: rgba(59, 130, 246, 0.05); }
    /* Navigation bar fix */
    .nav-bar-container { 
        position: relative; 
        width: 100%; 
        height: 48px; 
        margin-bottom: 24px;
        z-index: 10;
    }
    /* KPI cards alignment fix */
    div[data-testid="column"] { 
        display: flex; 
        flex-direction: column; 
    }
    .kpi-card { 
        flex: 1;
        min-height: 120px;
    }
    /* Opportunity card days left fix */
    .days-left-container {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 8px;
    }
    .days-left-label {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
    }
    /* PDF preview iframe fix */
    iframe[src*="application/pdf"] {
        border: 1px solid var(--border-800);
        border-radius: 8px;
        background: white;
    }
    /* Mail section spacing */
    .mail-section {
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid var(--border-800);
    }
    /* Input fields z-index and background fix */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: var(--text) !important;
        border: 1px solid var(--border-800) !important;
        z-index: 10 !important;
        position: relative !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--blue-500) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        z-index: 11 !important;
    }
    /* Label z-index fix */
    .stTextInput label,
    .stSelectbox label,
    .stTextArea label {
        color: var(--text-300) !important;
        z-index: 12 !important;
        position: relative !important;
    }
    /* Modern card içindeki input'lar için özel stil */
    .modern-card .stTextInput > div > div > input,
    .modern-card .stSelectbox > div > div > select {
        background-color: rgba(15, 23, 42, 0.9) !important;
        z-index: 20 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'DASHBOARD'
if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

# Database helper function
@st.cache_resource
def get_db_engine():
    """Veritabanı engine'ini al"""
    if not DB_AVAILABLE:
        return None
    
    try:
        # ENV-aware DB host: dev/local ise localhost, docker/container/compose ise 'db'
        env_mode = os.getenv('ENV', 'dev').lower().strip()
        db_host = os.getenv('DB_HOST')
        if not db_host:
            db_host = 'db' if env_mode in ('docker', 'container', 'compose') else 'localhost'
        elif db_host == 'db' and env_mode == 'dev':
            db_host = 'localhost'
        
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'postgres')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'mergenlite')
        
        logger.info(f"Database bağlantı bilgileri: host={db_host}, user={db_user}, port={db_port}, db={db_name}")
        
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Bağlantı testi yap
        try:
            engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
            # Test bağlantısı
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database bağlantısı başarılı: {db_name}")
        except Exception as conn_error:
            logger.error(f"❌ Database bağlantı hatası ({db_name}): {conn_error}")
            # Alternatif database adlarını dene
            alternative_dbs = ['ZGR_AI', 'mergenlite', 'postgres']
            for alt_db in alternative_dbs:
                if alt_db == db_name:
                    continue
                try:
                    alt_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{alt_db}"
                    alt_engine = create_engine(alt_url, connect_args={"connect_timeout": 5})
                    with alt_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.warning(f"⚠️ Ana database ({db_name}) bulunamadı, alternatif ({alt_db}) kullanılıyor")
                    engine = alt_engine
                    break
                except:
                    continue
            else:
                raise conn_error
        
        return engine
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {e}", exc_info=True)
        return None

def get_db_session():
    """Veritabanı session'ını al"""
    engine = get_db_engine()
    if not engine:
        return None
    
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def load_opportunities_from_db(limit: int = 100):
    """Veritabanından fırsatları yükle"""
    if not DB_AVAILABLE:
        logger.warning("⚠️ DB_AVAILABLE = False, boş liste döndürülüyor")
        return []
    
    db = get_db_session()
    if not db:
        logger.warning("⚠️ Database session oluşturulamadı, boş liste döndürülüyor")
        return []
    
    try:
        opportunities = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(limit).all()
        logger.info(f"✅ Database'den {len(opportunities)} kayıt yüklendi")
        
        # SQLAlchemy objelerini dict'e dönüştür
        result = []
        for opp in opportunities:
            try:
                # Analiz durumunu kontrol et (relationship hatası olabilir, try-except ile koru)
                analyzed = False
                analysis_status = None
                try:
                    if opp.analyses:
                        latest_analysis = sorted(opp.analyses, key=lambda x: x.start_time, reverse=True)[0] if opp.analyses else None
                        if latest_analysis:
                            analyzed = latest_analysis.analysis_status == 'COMPLETED'
                            analysis_status = latest_analysis.analysis_status
                except Exception as analysis_error:
                    # Relationship hatası (tablo yapısı uyumsuz olabilir)
                    logger.debug(f"⚠️ Analysis relationship hatası (opportunity_id: {getattr(opp, 'opportunity_id', 'N/A')}): {analysis_error}")
                    analyzed = False
                    analysis_status = None
                
                # raw_data'dan opportunityId ve noticeId çek (eğer model'de yoksa)
                # PostgreSQL JSONB alanı string olarak dönebiliyor, parse et
                raw_data = opp.raw_data or {}
                if isinstance(raw_data, str):
                    try:
                        import json
                        raw_data = json.loads(raw_data)
                    except (json.JSONDecodeError, TypeError):
                        raw_data = {}
                elif not isinstance(raw_data, dict):
                    raw_data = {}
                
                opportunity_id = opp.opportunity_id or ''
                notice_id = getattr(opp, 'notice_id', None) or raw_data.get('noticeId', '') or ''
                
                # Eğer opportunityId yoksa, raw_data'dan çek
                if not opportunity_id and raw_data:
                    opportunity_id = raw_data.get('opportunityId', '') or raw_data.get('noticeId', '')
                
                # Eğer hala yoksa, notice_id'yi kullan (geçici çözüm)
                if not opportunity_id and notice_id:
                    opportunity_id = notice_id
                
                # SAM.gov view link oluştur (eğer yoksa)
                sam_gov_link = opp.sam_gov_link
                if not sam_gov_link:
                    if opportunity_id and len(opportunity_id) == 32:  # Opportunity ID (32 karakter hex)
                        sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
                    elif notice_id:
                        sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
                
                opp_dict = {
                    'opportunity_id': opportunity_id,
                    'opportunityId': opportunity_id,  # UI için
                    'notice_id': notice_id,
                    'noticeId': notice_id,  # UI için
                    'title': opp.title or 'Başlık Yok',
                    'notice_type': opp.notice_type,
                    'naics_code': opp.naics_code,
                    'response_deadline': opp.response_deadline,
                    'estimated_value': float(opp.estimated_value) if opp.estimated_value else None,
                    'place_of_performance': opp.place_of_performance,
                    'sam_gov_link': sam_gov_link,
                    'samGovLink': sam_gov_link,  # UI için alternatif key
                    'created_at': opp.created_at,
                    'updated_at': opp.updated_at,
                    'raw_data': raw_data,
                    'analyzed': analyzed,
                    'analysis_status': analysis_status
                }
                result.append(opp_dict)
            except Exception as opp_error:
                logger.warning(f"⚠️ Kayıt parse hatası (opportunity_id: {getattr(opp, 'opportunity_id', 'N/A')}): {opp_error}")
                continue
        
        logger.info(f"✅ {len(result)} kayıt başarıyla parse edildi")
        return result
    except Exception as e:
        logger.error(f"❌ Fırsat yükleme hatası: {e}", exc_info=True)
        return []
    finally:
        if db:
            db.close()

def open_opportunity_folder(opportunity_code: str):
    """Fırsat klasörünü oluştur ve aç (Windows için)"""
    try:
        from pathlib import Path
        import subprocess
        import platform
        
        # Klasörü oluştur
        base_dir = Path(".")
        folder = base_dir / "opportunities" / opportunity_code
        folder.mkdir(parents=True, exist_ok=True)
        
        # Klasörü aç (platform-specific)
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{folder.absolute()}"')
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(folder.absolute())])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(folder.absolute())])
        
        return str(folder.absolute())
    except Exception as e:
        logger.error(f"Klasör açma hatası: {e}", exc_info=True)
        st.error(f"❌ Klasör açma hatası: {str(e)}")
        return None

def download_opportunity_documents(notice_id: str):
    """Fırsat dökümanlarını indir"""
    try:
        sam = SAMIntegration()
        if not sam.api_key:
            st.error("⚠️ API Key bulunamadı!")
            return
        
        with st.spinner(f"📥 Dökümanlar indiriliyor: {notice_id}..."):
            # Dökümanları indir
            downloaded = sam.download_documents(notice_id, dest_dir="downloads")
            
            if downloaded:
                st.success(f"✅ {len(downloaded)} döküman indirildi!")
                return downloaded
            else:
                st.warning("⚠️ Döküman bulunamadı veya indirilemedi.")
                return []
    except Exception as e:
        logger.error(f"Döküman indirme hatası: {e}", exc_info=True)
        st.error(f"❌ Döküman indirme hatası: {str(e)}")
        return []

def sync_opportunities_from_sam(naics_code: str = "721110", days_back: int = 30, limit: int = 100, show_progress: bool = True):
    """SAM.gov'dan fırsatları senkronize et ve veritabanına kaydet (Optimize edilmiş)"""
    try:
        # SAMIntegration ile fırsatları çek
        sam = SAMIntegration()
        if not sam.api_key:
            st.error("⚠️ API Key bulunamadı! `.env` dosyasında `SAM_API_KEY` tanımlı olmalı.")
            logger.error("SAM_API_KEY not found in environment")
            return
        
        # Progress bar için
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text(f"🔄 SAM.gov API'ye bağlanılıyor (NAICS: {naics_code})...")
            progress_bar.progress(0.1)
        else:
            progress_bar = None
            status_text = None
        
        # API çağrısı - rate limiting otomatik yönetiliyor
        try:
            if show_progress and progress_bar:
                status_text.text(f"🔄 SAM.gov API çağrısı yapılıyor (NAICS: {naics_code}, Son {days_back} gün)...")
            _respect_sam_rate_limit()
            opportunities = sam.fetch_opportunities(
                naics_codes=[naics_code],
                days_back=days_back,
                limit=limit
            )
            
            logger.info(f"API çağrısı tamamlandı: {len(opportunities) if opportunities else 0} fırsat bulundu")
            
        except ValueError as api_error:
            # API key veya quota hatası
            error_msg = str(api_error)
            if show_progress and progress_bar:
                progress_bar.empty()
                status_text.empty()
            
            if "quota" in error_msg.lower() or "429" in error_msg or "rate limit" in error_msg.lower():
                st.error("❌ API Quota Limit Aşıldı! Lütfen daha sonra tekrar deneyin.")
            else:
                st.error(f"❌ API çağrısı başarısız: {error_msg}")
            logger.error(f"❌ API çağrısı hatası: {error_msg}", exc_info=True)
            return
        except Exception as api_error:
            logger.error(f"❌ API çağrısı hatası: {str(api_error)}", exc_info=True)
            if show_progress and progress_bar:
                progress_bar.empty()
                status_text.empty()
            st.error(f"❌ API çağrısı başarısız: {str(api_error)}")
            return
        
        if show_progress and progress_bar:
            progress_bar.progress(0.5)
            status_text.text(f"📊 {len(opportunities)} fırsat bulundu, veritabanına kaydediliyor...")
        else:
            logger.info(f"📊 {len(opportunities)} fırsat bulundu, veritabanına kaydediliyor...")
        
        if not opportunities:
            if show_progress and progress_bar:
                progress_bar.empty()
                status_text.empty()
            st.warning(f"⚠️ Hiç fırsat bulunamadı. Tarih aralığını genişletmeyi deneyin.")
            logger.warning(f"NAICS {naics_code} için son {days_back} günde fırsat bulunamadı")
            return
        
        # Veritabanına kaydet
        if not DB_AVAILABLE:
            st.session_state.opportunities = opportunities
            st.session_state.last_saved_count = len(opportunities)
            st.session_state.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.success(f"✅ {len(opportunities)} fırsat yüklendi.")
            return
        
        db = get_db_session()
        if not db:
            st.session_state.opportunities = opportunities
            st.session_state.last_saved_count = len(opportunities)
            st.session_state.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.success(f"✅ {len(opportunities)} fırsat yüklendi.")
            return
        
        try:
            count_new = 0
            count_updated = 0
            total = len(opportunities)
            
            # Batch processing - her 10 kayıtta bir commit
            batch_size = 10
            for idx, opp_data in enumerate(opportunities):
                # GSA API'ye göre: Opportunity ID zorunlu, Notice ID opsiyonel
                opportunity_id = opp_data.get('opportunityId', '').strip()
                notice_id = opp_data.get('noticeId', '').strip() or opp_data.get('solicitationNumber', '').strip()
                
                # Log: resourceLinks ve attachments sayısı (teşhis için)
                raw_data = opp_data.get('raw_data', opp_data)
                resource_links_count = len(raw_data.get('resourceLinks', [])) if isinstance(raw_data, dict) else 0
                attachments_count = len(raw_data.get('attachments', [])) if isinstance(raw_data, dict) else 0
                logger.info(f"[{idx+1}/{total}] Opportunity: {opportunity_id[:20]}... | resourceLinks: {resource_links_count} | attachments: {attachments_count}")
                
                # Opportunity ID yoksa, raw_data'dan veya noticeId'den çekmeyi dene
                if not opportunity_id:
                    # raw_data içinde olabilir
                    raw_data = opp_data.get('raw_data', {})
                    if isinstance(raw_data, dict):
                        opportunity_id = raw_data.get('opportunityId', '').strip()
                    
                    # Hala yoksa ve noticeId UUID formatındaysa, onu kullan
                    if not opportunity_id and notice_id:
                        if len(notice_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in notice_id):
                            opportunity_id = notice_id
                            logger.info(f"ℹ️ API'den opportunityId gelmedi, noticeId UUID formatında kullanılıyor: {notice_id[:20]}...")
                    
                    # Hala yoksa skip et
                    if not opportunity_id:
                        logger.warning(f"⚠️ Opportunity ID bulunamadı, atlanıyor. Notice ID: {notice_id}")
                        continue
                
                # Mevcut kaydı opportunity_id ile kontrol et (GSA API standardı)
                existing = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
                
                # Response deadline'ı parse et
                response_deadline = None
                if opp_data.get('responseDeadLine'):
                    try:
                        if isinstance(opp_data['responseDeadLine'], str):
                            response_deadline = datetime.strptime(opp_data['responseDeadLine'][:10], '%Y-%m-%d')
                        else:
                            response_deadline = opp_data['responseDeadLine']
                    except:
                        pass
    
                if existing:
                    # Güncelle - aynı opportunity, farklı notice olabilir
                    existing.title = opp_data.get('title', existing.title)
                    existing.notice_type = opp_data.get('noticeType', existing.notice_type)
                    existing.naics_code = opp_data.get('naicsCode', existing.naics_code) or naics_code
                    existing.response_deadline = response_deadline or existing.response_deadline
                    # Notice ID'yi de güncelle (aynı opportunity, farklı notice olabilir)
                    if notice_id and notice_id != existing.notice_id:
                        existing.notice_id = notice_id
                    if opp_data.get('solicitationNumber') and opp_data.get('solicitationNumber') != existing.solicitation_number:
                        existing.solicitation_number = opp_data.get('solicitationNumber')
                    # SAM.gov link'i güncelle
                    sam_gov_link = opp_data.get('samGovLink')
                    if not sam_gov_link:
                        if opportunity_id and len(opportunity_id) == 32:
                            sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
                        elif notice_id:
                            sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
                    if sam_gov_link and sam_gov_link != existing.sam_gov_link:
                        existing.sam_gov_link = sam_gov_link
                    # raw_data'yı koru - varsa opp_data'dan, yoksa mevcut raw_data'dan
                    existing.raw_data = opp_data.get('raw_data', opp_data)
                    existing.updated_at = datetime.now()
                    count_updated += 1
                else:
                    # SAM.gov view link oluştur
                    sam_gov_link = opp_data.get('samGovLink')
                    if not sam_gov_link:
                        if opportunity_id and len(opportunity_id) == 32:
                            sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
                        elif notice_id:
                            sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
                    
                    # Yeni kayıt oluştur - hem opportunity_id hem notice_id
                    # raw_data'yı koru - varsa opp_data'dan, yoksa opp_data'nın kendisi
                    new_opp = Opportunity(
                        opportunity_id=opportunity_id,
                        notice_id=notice_id,  # Notice ID'yi de kaydet
                        solicitation_number=opp_data.get('solicitationNumber', notice_id),
                        title=opp_data.get('title', 'Başlık Yok'),
                        notice_type=opp_data.get('noticeType'),
                        naics_code=opp_data.get('naicsCode') or naics_code,
                        response_deadline=response_deadline,
                        sam_gov_link=sam_gov_link,  # SAM.gov view link
                        raw_data=opp_data.get('raw_data', opp_data)  # Ham veriyi koru
                    )
                    db.add(new_opp)
                    count_new += 1
                
                # Her batch'te commit (rate limiting için)
                if (idx + 1) % batch_size == 0:
                    db.commit()
                    if show_progress and progress_bar:
                        progress = 0.5 + (0.4 * (idx + 1) / total)
                        progress_bar.progress(progress)
                        status_text.text(f"💾 {idx + 1}/{total} kayıt işlendi...")
            
            # Son commit
            db.commit()
            if show_progress and progress_bar:
                progress_bar.progress(1.0)
            
            # Session state'i güncelle
            st.session_state.opportunities = opportunities
            st.session_state.last_saved_count = count_new
            st.session_state.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if show_progress and progress_bar:
                progress_bar.empty()
                status_text.empty()
            
            st.success(f"✅ Senkronizasyon tamamlandı! Yeni: {count_new}, Güncellenen: {count_updated}, Toplam: {len(opportunities)}")
            
        except Exception as db_error:
            if db:
                db.rollback()
            logger.error(f"Veritabanı kayıt hatası: {db_error}")
            st.error(f"❌ Veritabanı kayıt hatası: {db_error}")
        finally:
            if db:
                db.close()
                
    except Exception as e:
        logger.error(f"❌ Senkronizasyon hatası: {e}", exc_info=True)
        if show_progress and progress_bar:
            progress_bar.empty()
            if status_text:
                status_text.empty()
        st.error(f"❌ **Senkronizasyon hatası:** {str(e)}")
        st.info("""
        **Hata detayları terminal loglarında görüntülenebilir.**
        
        **Olası nedenler:**
        - Veritabanı bağlantı sorunu
        - API çağrısı başarısız
        - Veri formatı hatası
        
        **Çözüm:**
        - Terminal loglarını kontrol edin
        - Veritabanı bağlantısını kontrol edin
        - API key'inizi kontrol edin
        """)

@st.cache_data(ttl=60)  # 60 saniye cache
def get_dashboard_kpis():
    """Database'den KPI'ları çek"""
    if not DB_AVAILABLE:
        return {
            'total_cnt': len(st.session_state.get('opportunities', []) or []),
            'today_new': st.session_state.get('last_saved_count', 0) or 0,
            'analyzed_count': 0,
            'avg_time': 'N/A'
        }
    
    db = get_db_session()
    if not db:
        return {
            'total_cnt': len(st.session_state.get('opportunities', []) or []),
            'today_new': st.session_state.get('last_saved_count', 0) or 0,
            'analyzed_count': 0,
            'avg_time': 'N/A'
        }
    
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Toplam fırsat sayısı
        total_cnt = db.query(func.count(Opportunity.id)).scalar() or 0
        
        # Bugün eklenenler (created_at'e göre)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new = db.query(func.count(Opportunity.id)).filter(
            Opportunity.created_at >= today_start
        ).scalar() or 0
        
        # Tamamlanan analiz sayısı
        analyzed_count = 0
        try:
            # analyzed field varsa kullan
            if hasattr(Opportunity, 'analyzed'):
                analyzed_count = db.query(func.count(Opportunity.id)).filter(
                    Opportunity.analyzed == True
                ).scalar() or 0
            else:
                # Relationship üzerinden kontrol et
                from mergenlite_models import AIAnalysisResult
                analyzed_count = db.query(func.count(AIAnalysisResult.id)).filter(
                    AIAnalysisResult.analysis_status == 'COMPLETED'
                ).scalar() or 0
        except Exception:
            analyzed_count = 0
        
        # Ortalama analiz süresi (basit hesaplama)
        avg_time = '28sn'  # TODO: Gerçek hesaplama yapılabilir
        
        db.close()
        return {
            'total_cnt': total_cnt,
            'today_new': today_new,
            'analyzed_count': analyzed_count,
            'avg_time': avg_time
        }
    except Exception as e:
        logger.error(f"KPI hesaplama hatası: {e}")
        if db:
            db.close()
        return {
            'total_cnt': len(st.session_state.get('opportunities', []) or []),
            'today_new': st.session_state.get('last_saved_count', 0) or 0,
            'analyzed_count': 0,
            'avg_time': 'N/A'
        }

@st.cache_resource(ttl=3600)
def check_api_connection_cached():
    """API bağlantısını kontrol eder ve sonucu önbelleğe alır (1 saat)"""
    sam = SAMIntegration()
    return sam.test_connection()

@st.cache_resource(ttl=60)
def check_db_connection_cached():
    """DB bağlantısını kontrol eder ve sonucu önbelleğe alır (1 dakika)"""
    if not DB_AVAILABLE:
        return False, "Veritabanı modülü yüklü değil"
    
    try:
        db_check = get_db_session()
        if db_check:
            from sqlalchemy import text
            db_check.execute(text("SELECT 1"))
            db_check.close()
            return True, "Bağlantı başarılı"
        return False, "Session oluşturulamadı"
    except Exception as e:
        return False, str(e)

@st.cache_resource(ttl=3600)
def check_api_connection_cached():
    """API bağlantısını kontrol eder ve sonucu önbelleğe alır (1 saat)"""
    sam = SAMIntegration()
    return sam.test_connection()

@st.cache_resource(ttl=60)
def check_db_connection_cached():
    """DB bağlantısını kontrol eder ve sonucu önbelleğe alır (1 dakika)"""
    if not DB_AVAILABLE:
        return False, "Veritabanı modülü yüklü değil"
    
    try:
        db_check = get_db_session()
        if db_check:
            from sqlalchemy import text
            db_check.execute(text("SELECT 1"))
            db_check.close()
            return True, "Bağlantı başarılı"
        return False, "Session oluşturulamadı"
    except Exception as e:
        return False, str(e)

def render_dashboard():
    """Modern Dashboard - KPI'lar ve hızlı aksiyonlar"""
    st.markdown('<h1 class="main-header">🏠 MergenLite Dashboard</h1>', unsafe_allow_html=True)
    
    # API Bağlantı Testi (Cached)
    api_status_html = ""
    try:
        connection_result = check_api_connection_cached()
        
        if connection_result["success"]:
            api_status_html = """
            <div class="alert alert-success" style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">✅</span>
                <div>
                    <strong>SAM.gov Bağlantısı Aktif</strong>
                    <div style="font-size: 12px; opacity: 0.8;">API Key geçerli ve servis yanıt veriyor.</div>
                </div>
            </div>
            """
        else:
            api_status_html = f"""
            <div class="alert alert-danger" style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">❌</span>
                <div>
                    <strong>Bağlantı Hatası (403):</strong> {connection_result.get('error')}
                </div>
            </div>
            """
    except Exception as e:
        api_status_html = f"""
        <div class="alert alert-danger" style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">⚠️</span>
            <div>
                <strong>API Kontrol Hatası:</strong> {str(e)}
            </div>
        </div>
        """
    
    st.markdown(api_status_html, unsafe_allow_html=True)
    
    # DB Bağlantı Testi (Cached)
    db_status_html = ""
    is_db_connected, db_msg = check_db_connection_cached()
    
    if is_db_connected:
        db_status_html = """
        <div class="alert alert-success" style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
            <span style="font-size: 20px;">🗄️</span>
            <div>
                <strong>Veritabanı Bağlantısı Aktif</strong>
                <div style="font-size: 12px; opacity: 0.8;">PostgreSQL bağlantısı çalışıyor.</div>
            </div>
        </div>
        """
    else:
        db_status_html = f"""
        <div class="alert alert-danger" style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
            <span style="font-size: 20px;">❌</span>
            <div>
                <strong>Veritabanı Hatası:</strong> {db_msg}
            </div>
        </div>
        """
    
    st.markdown(db_status_html, unsafe_allow_html=True)
    
    # KPI Data - Database'den çek
    kpis = get_dashboard_kpis()
    total_cnt = kpis['total_cnt']
    saved_cnt = kpis['today_new']
    analyzed_count = kpis['analyzed_count']
    avg_time = kpis['avg_time']
    
    # Modern KPI Cards
    st.markdown("### 📊 Sistem Durumu")
    c1, c2, c3, c4 = st.columns(4)
    
    kpi_cards = [
        ("Toplam Fırsat", total_cnt, "📊", "kpi-blue"),
        ("Bugün Eklenen", saved_cnt, "📈", "kpi-emerald"),
        ("Tamamlanan Analiz", analyzed_count, "✅", "kpi-purple"),
        ("Ort. Analiz Süresi", avg_time, "⏱️", "kpi-orange")
    ]
    
    for col, (label, value, icon, color_class) in zip([c1, c2, c3, c4], kpi_cards):
        with col:
            st.markdown(f"""
            <div class="kpi-card {color_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
                        <div style="font-size: 28px; font-weight: 800; line-height: 1.1;">{value}</div>
                    </div>
                    <div style="font-size: 24px; opacity: 0.8;">{icon}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alt Bölüm: Ajanlar ve Aktiviteler
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("### 🤖 Aktif Ajanlar")
        agents = [
            {"name": "Mergen Core", "role": "Orchestrator", "status": "active", "icon": "🧠"},
            {"name": "Data Miner", "role": "SAM.gov Integration", "status": "active", "icon": "⛏️"},
            {"name": "Analyst", "role": "Opportunity Evaluation", "status": "idle", "icon": "📊"},
            {"name": "Reporter", "role": "Output Generation", "status": "idle", "icon": "📝"}
        ]
        
        for agent in agents:
            status_color = "#10b981" if agent["status"] == "active" else "#64748b"
            st.markdown(f"""
            <div class="modern-card" style="margin-bottom: 12px; padding: 12px 16px; display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 20px;">{agent['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 14px; color: var(--text);">{agent['name']}</div>
                    <div style="font-size: 11px; color: var(--text-400);">{agent['role']}</div>
                </div>
                <div style="width: 8px; height: 8px; border-radius: 50%; background: {status_color}; box-shadow: 0 0 8px {status_color}40;"></div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 📋 Son Aktiviteler")
        recent_opportunities = load_opportunities_from_db(limit=4)
        
        if recent_opportunities:
            for opp in recent_opportunities:
                # Risk ve gün hesaplamaları (basitleştirilmiş)
                title = opp.get('title', 'Başlık Yok')
                if len(title) > 65: title = title[:65] + "..."
                
                opp_id = opp.get('opportunityId') or opp.get('noticeId') or 'N/A'
                
                st.markdown(f"""
                <div class="modern-card" style="margin-bottom: 10px; padding: 12px 16px; transition: transform 0.2s;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-family: monospace; font-size: 11px; color: var(--blue-400); background: rgba(59, 130, 246, 0.1); padding: 2px 6px; border-radius: 4px;">{opp_id}</span>
                        <span style="font-size: 11px; color: var(--text-400);">{str(opp.get('created_at', ''))[:10]}</span>
                    </div>
                    <div style="font-size: 14px; font-weight: 500; color: var(--text-200);">{title}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Henüz görüntülenecek aktivite yok. Yeni fırsat araması yapın.")

    # Hızlı Aksiyonlar (Fab Button Inspired)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Hızlı Analiz Başlat", use_container_width=True, type="primary"):
            st.session_state.current_page = 'OPPORTUNITY_CENTER'
            st.rerun()
    with c2:
        if st.button("🔄 Verileri Yenile", use_container_width=True):
            st.rerun()

def render_opportunity_center():
    """Opportunity Center - İlan Merkezi (Figma tasarımına uygun)"""
    st.markdown('<h1 class="main-header" style="text-align: left;">📋 İlan Merkezi</h1>', unsafe_allow_html=True)

    # API Bağlantı Durumu (En üstte göster)
    try:
        sam = SAMIntegration()
        connection_result = sam.test_connection()
        if not connection_result["success"]:
             st.markdown(f"""
            <div class="alert alert-danger" style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <span style="font-size: 20px;">❌</span>
                <div>
                    <strong>API Bağlantı Hatası:</strong> {connection_result.get('error')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    except:
        pass
    
    # Arama ve Filtreleme Bölümü
    st.markdown("""
    <div class="modern-card" style="margin-bottom: 24px; padding: 20px; background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid var(--border-700);">
        <div style="font-size: 14px; font-weight: 600; color: var(--text-300); margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
            <span>🔍</span> Fırsat Arama Kriterleri
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([1.2, 0.8, 1.5, 1, 1])
    
    with col1:
        notice_id = st.text_input("Notice ID", placeholder="SAM-...", key="search_notice_id")
    
    with col2:
        naics_code = st.text_input("NAICS", value="721110", key="search_naics")
    
    with col3:
        keyword = st.text_input("Anahtar Kelime", placeholder="Hotel, lodging...", key="search_keyword")
    
    with col4:
        # Tarih aralığı seçimi
        days_back = st.selectbox(
            "Tarih Aralığı",
            options=[7, 14, 30, 60, 90, 180, 365],
            format_func=lambda x: f"Son {x} gün",
            index=3,  # Varsayılan: 60 gün
            key="search_days_back"
        )
    
    with col5:
        st.markdown("<div style='margin-top: 24px;'>", unsafe_allow_html=True)
        if st.button("🔍 Ara", use_container_width=True, key="search_btn"):
            # Gerçek API araması yap
            opportunities = []
            search_params = {}
            clean_params = {}
            
            with st.spinner("🔍 Fırsatlar aranıyor..."):
                try:
                    sam = SAMIntegration()
                    if not sam.api_key:
                        st.error("⚠️ API Key bulunamadı!")
                    else:
                        # 429 hatası kontrolü için özel exception handling
                        try:
                            # Arama parametrelerini hazırla
                            search_params = {
                                'naics_codes': [naics_code] if naics_code else ['721110'],  # Default: 721110
                                'days_back': days_back,  # Kullanıcının seçtiği tarih aralığı
                                'limit': 100
                            }
                            
                            if keyword:
                                # Keywords'ü listeye çevir (virgülle ayrılmış string'den)
                                keyword_list = [k.strip() for k in keyword.split(',') if k.strip()] if keyword else None
                                if keyword_list:
                                    search_params['keywords'] = keyword_list
                            
                            # clean_params'ı önceden tanımla (her durumda kullanılabilir)
                            clean_params = {k: v for k, v in search_params.items() if v is not None}
                            
                            if notice_id and notice_id.strip():
                                # Notice ID ile direkt arama
                                logger.info(f"Notice ID ile arama: {notice_id.strip()}")
                                opportunities = sam.search_by_any_id(notice_id.strip())
                            else:
                                # Normal arama - parametreleri temizle
                                logger.info(f"Arama parametreleri: {clean_params}")
                                
                                opportunities = sam.fetch_opportunities(**clean_params)
                        
                        except ValueError as quota_error:
                            # Quota/rate limit hatası
                            error_msg = str(quota_error)
                            if "quota" in error_msg.lower() or "429" in error_msg or "rate limit" in error_msg.lower():
                                st.error("❌ API Quota Limit Aşıldı! Lütfen daha sonra tekrar deneyin.")
                            else:
                                st.error(f"❌ API hatası: {error_msg}")
                            logger.error(f"API quota/rate limit hatası: {error_msg}")
                            opportunities = []
                            clean_params = search_params  # Fallback için
                        
                        except Exception as api_exception:
                            # Genel exception handling - spinner'ın takılı kalmasını önle
                            error_msg = str(api_exception)
                            logger.error(f"API çağrısı genel hatası: {error_msg}", exc_info=True)
                            st.error(f"❌ Arama hatası: {error_msg}")
                            opportunities = []
                            clean_params = search_params if search_params else {'naics_codes': ['721110'], 'days_back': days_back, 'limit': 100}
                        
                        logger.info(f"Arama sonucu: {len(opportunities) if opportunities else 0} fırsat bulundu")
                        if 'clean_params' in locals():
                            logger.info(f"API çağrısı parametreleri: naics_codes={clean_params.get('naics_codes')}, days_back={clean_params.get('days_back')}, limit={clean_params.get('limit')}")
                        
                        if not opportunities or len(opportunities) == 0:
                            clean_params_local = clean_params if clean_params else search_params
                            logger.warning(f"API çağrısı başarılı ama sonuç yok. Parametreler: {clean_params_local}")
                        
                except Exception as outer_exception:
                    # En dış exception handling - kesinlikle spinner'ı kapat
                    error_msg = str(outer_exception)
                    logger.error(f"Dış seviye exception: {error_msg}", exc_info=True)
                    st.error(f"❌ Beklenmeyen hata: {error_msg}")
                    opportunities = []
                
                # API çağrısı sonrası işlemler
                if opportunities and len(opportunities) > 0:
                    # Database'e kaydet
                    if DB_AVAILABLE:
                        db = get_db_session()
                        if db:
                            try:
                                count_new = 0
                                count_skipped_no_id = 0
                                count_existing = 0
                                
                                for opp_data in opportunities:
                                    # GSA API'ye göre: Opportunity ID zorunlu
                                    opportunity_id = opp_data.get('opportunityId', '').strip()
                                    notice_id_val = opp_data.get('noticeId', '').strip() or opp_data.get('solicitationNumber', '').strip()
                                    
                                    # Opportunity ID yoksa, raw_data'dan veya noticeId'den çekmeyi dene
                                    if not opportunity_id:
                                        # raw_data içinde olabilir
                                        raw_data = opp_data.get('raw_data', {})
                                        if isinstance(raw_data, dict):
                                            opportunity_id = raw_data.get('opportunityId', '').strip()
                                        
                                        # Hala yoksa ve noticeId UUID formatındaysa, onu kullan (geçici çözüm)
                                        if not opportunity_id and notice_id_val:
                                            if len(notice_id_val) == 32 and all(c in '0123456789abcdefABCDEF' for c in notice_id_val):
                                                opportunity_id = notice_id_val
                                                logger.warning(f"⚠️ API'den opportunityId gelmedi, noticeId UUID formatında kullanılıyor: {notice_id_val[:20]}...")
                                        
                                        # Hala yoksa skip et
                                        if not opportunity_id:
                                            count_skipped_no_id += 1
                                            logger.warning(f"⚠️ Opportunity ID bulunamadı, atlanıyor. Notice ID: {notice_id_val}")
                                            continue
                                    
                                    existing = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
                                    
                                    if existing:
                                        count_existing += 1
                                        # Mevcut kayıt var, güncelle
                                        if notice_id_val and notice_id_val != existing.notice_id:
                                            existing.notice_id = notice_id_val
                                        # raw_data'yı koru - varsa opp_data'dan, yoksa mevcut raw_data'dan
                                        existing.raw_data = opp_data.get('raw_data', opp_data)
                                        existing.updated_at = datetime.now()
                                        continue
                                    
                                    if not existing:
                                        response_deadline = None
                                        if opp_data.get('responseDeadLine'):
                                            try:
                                                if isinstance(opp_data['responseDeadLine'], str):
                                                    response_deadline = datetime.strptime(opp_data['responseDeadLine'][:10], '%Y-%m-%d')
                                                else:
                                                    response_deadline = opp_data['responseDeadLine']
                                            except:
                                                pass
                                        
                                        # SAM.gov view link oluştur
                                        sam_gov_link = opp_data.get('samGovLink')
                                        if not sam_gov_link:
                                            if opportunity_id and len(opportunity_id) == 32:
                                                sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
                                            elif notice_id_val:
                                                sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id_val}"
                                        
                                        new_opp = Opportunity(
                                            opportunity_id=opportunity_id,
                                            notice_id=notice_id_val,  # Notice ID'yi de kaydet
                                            solicitation_number=opp_data.get('solicitationNumber', notice_id_val),
                                            title=opp_data.get('title', 'Başlık Yok'),
                                            notice_type=opp_data.get('noticeType'),
                                            naics_code=opp_data.get('naicsCode') or naics_code or '721110',
                                            response_deadline=response_deadline,
                                            sam_gov_link=sam_gov_link,  # SAM.gov view link
                                            raw_data=opp_data.get('raw_data', opp_data)  # Ham veriyi koru
                                        )
                                        db.add(new_opp)
                                        count_new += 1
                                
                                db.commit()
                                
                                # Detaylı mesaj
                                if count_new > 0:
                                    st.success(f"✅ {len(opportunities)} fırsat bulundu, {count_new} yeni kayıt eklendi!")
                                elif count_existing > 0:
                                    st.success(f"✅ {len(opportunities)} fırsat bulundu, {count_existing} kayıt güncellendi.")
                                elif count_skipped_no_id > 0:
                                    st.warning(f"⚠️ {len(opportunities)} fırsat bulundu, ancak {count_skipped_no_id} kayıt atlandı.")
                                else:
                                    st.success(f"✅ {len(opportunities)} fırsat bulundu!")
                            except Exception as e:
                                db.rollback()
                                logger.error(f"Database kayıt hatası: {e}")
                                st.warning(f"⚠️ Fırsatlar bulundu ama database'e kaydedilemedi: {e}")
                            finally:
                                db.close()
                    else:
                        st.success(f"✅ {len(opportunities)} fırsat bulundu!")
                    
                    st.session_state.opportunities = opportunities
                    # st.rerun() kaldırıldı - otomatik güncellenecek
                else:
                    # Daha detaylı bilgi ver
                    if notice_id and notice_id.strip():
                        st.warning(f"⚠️ Notice ID '{notice_id.strip()}' için fırsat bulunamadı.")
                    elif naics_code:
                        st.warning(f"⚠️ NAICS {naics_code} için son {days_back} günde fırsat bulunamadı.")
                    else:
                        st.warning("⚠️ Hiç fırsat bulunamadı.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # API Durum Alert - Gerçek durum
    try:
        sam = SAMIntegration()
        api_key_ok = bool(sam.api_key)
        if api_key_ok:
            api_status = "✅ SAM.gov API bağlantısı aktif"
            api_class = "alert-info"
        else:
            api_status = "⚠️ SAM.gov API Key bulunamadı"
            api_class = "alert-warning"
    except Exception as e:
        api_status = f"❌ API bağlantı hatası: {str(e)[:50]}"
        api_class = "alert-danger"
    
    st.markdown(f"""
    <div class="alert {api_class}" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">ℹ️</span>
            <span>{api_status}</span>
        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
    # Gerçek database'den fırsatları yükle
    opportunities = load_opportunities_from_db()
    
    # Eğer database'de veri yoksa ama session_state'de varsa, onu kullan
    if not opportunities and 'opportunities' in st.session_state and st.session_state.opportunities:
        opportunities = st.session_state.opportunities
        st.info("ℹ️ Database'de fırsat bulunamadı, anlık arama sonuçları gösteriliyor.")
    
    # Eğer hala veri yoksa, kullanıcıyı bilgilendir ve senkronizasyon butonu göster
    if not opportunities:
        st.info("Database'de fırsat bulunamadı.")
        
        # Senkronizasyon butonu
        col_sync1, col_sync2, col_sync3 = st.columns([1, 2, 1])
        with col_sync2:
            if st.button("🔄 SAM.gov'dan Yeni Fırsatları Çek (721110)", use_container_width=True, key="sync_from_opportunity_center"):
                with st.spinner("🔄 Fırsatlar SAM.gov'dan çekiliyor..."):
                    sync_opportunities_from_sam("721110", days_back=30, limit=100, show_progress=False)
                    st.rerun()
        
        return
    
    # Database verilerini UI formatına dönüştür
    formatted_opportunities = []
    for opp in opportunities:
        # Tarih hesaplamaları
        response_deadline = opp.get('response_deadline')
        days_left = 0
        if response_deadline:
            try:
                if isinstance(response_deadline, str):
                    deadline_date = datetime.strptime(response_deadline[:10], '%Y-%m-%d')
                else:
                    deadline_date = response_deadline
                days_left = (deadline_date - datetime.now()).days
            except:
                days_left = 0
        
        # Opportunity ID: opportunityId veya opportunity_id'den hangisi varsa
        opp_id = opp.get('opportunityId') or opp.get('opportunity_id', 'N/A')
        notice_id = opp.get('noticeId') or opp.get('notice_id', 'N/A')
        
        # SAM.gov view link oluştur
        sam_gov_link = opp.get('sam_gov_link') or opp.get('samGovLink')
        if not sam_gov_link:
            if opp_id and len(str(opp_id)) == 32:  # Opportunity ID (32 karakter hex)
                sam_gov_link = f"https://sam.gov/opp/{opp_id}/view"
            elif notice_id and notice_id != 'N/A':
                sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
        
        formatted_opp = {
            "opportunityId": opp_id,
            "noticeId": notice_id,
            "title": opp.get('title', 'Başlık Yok'),
            "publishedDate": str(opp.get('created_at', ''))[:10] if opp.get('created_at') else 'N/A',
            "responseDeadline": str(response_deadline)[:10] if response_deadline else 'N/A',
            "daysLeft": max(0, days_left),
            "analyzed": opp.get('analyzed', False),
            "analysis_status": opp.get('analysis_status'),
            "samGovLink": sam_gov_link,  # SAM.gov view link
            "raw_data": opp.get('raw_data', {})
        }
        
        # Risk seviyesi (analiz edilmişse)
        if formatted_opp['analyzed']:
            if days_left <= 5:
                formatted_opp['risk'] = 'high'
            elif days_left <= 15:
                formatted_opp['risk'] = 'medium'
            else:
                formatted_opp['risk'] = 'low'
        
        formatted_opportunities.append(formatted_opp)
    
    # Sıralama: En fazla gün kalan üstte, 0 gün kalan altta (azalan sırada)
    opportunities = sorted(formatted_opportunities, key=lambda x: x['daysLeft'], reverse=True)
    
    # Fırsatları göster
    st.markdown(f"### 📋 Toplam {len(opportunities)} Fırsat Bulundu")
    
    for idx, opp in enumerate(opportunities):
        # Risk seviyesi ve renkler
        risk_level = opp.get('risk', 'low')
        if not opp.get('analyzed'): risk_level = 'unknown'
        
        # Gün sayısı badge
        days_left = opp['daysLeft']
        if days_left <= 0:
            days_html = '<span class="badge badge-danger">Süresi Doldu</span>'
        elif days_left <= 5:
            days_html = f'<span class="badge badge-danger">{days_left} gün kaldı</span>'
        elif days_left <= 15:
            days_html = f'<span class="badge badge-warning">{days_left} gün kaldı</span>'
        else:
            days_html = f'<span class="badge badge-success">{days_left} gün kaldı</span>'

        # SAM Link
        sam_url = opp.get('samGovLink')
        sam_link_html = f'<a href="{sam_url}" target="_blank" style="color:var(--blue-400);text-decoration:none;font-weight:600;">🔗 SAM.gov</a>' if sam_url else ""
        
        # Ana Kart
        # Opportunity ID ve butonlar için - benzersiz key oluştur
        opp_id = opp.get('opportunityId') or opp.get('noticeId') or 'unknown'
        opportunity_code = opp_id if len(str(opp_id)) == 32 else (opp.get('noticeId') or opp.get('solicitationNumber') or opp_id)
        # Döngü indeksini ekleyerek benzersiz key oluştur
        unique_key_suffix = f"{opp_id}_{idx}"

        st.markdown(f"""
        <div class="op-card" style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span class="badge" style="background:rgba(255,255,255,0.05);color:var(--text-300);">{opp.get('opportunityId') or opp.get('noticeId')}</span>
                    {days_html}
                </div>
                {sam_link_html}
            </div>
            
            <h3 style="color:var(--text);font-size:18px;margin-bottom:8px;line-height:1.4;">{opp.get('title')}</h3>
            
            <div style="display:flex;gap:20px;font-size:13px;color:var(--text-400);margin-bottom:12px;">
                <span>📅 Yayın: {opp.get('publishedDate')}</span>
                <span>⏱️ Bitiş: {opp.get('responseDeadline', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons & Expanders (Container içinde değil ayrı, görsel olarak bütünleşik)
        
        # Açıklama
        description = opp.get('description') or opp.get('summary') or ''
        if description:
            with st.expander("📄 Fırsat Detayları ve Açıklama"):
                st.markdown(description, unsafe_allow_html=True)
        
        # Butonlar kartın hemen altında (görsel olarak kart içinde görünecek)
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-top: none; border-radius: 0 0 8px 8px; padding: 16px; margin-top: 8px; margin-bottom: 16px;">
        """, unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        with btn_col1:
            if st.button("▶ Analizi Başlat", key=f"analyze_{unique_key_suffix}", use_container_width=True):
                # Otomatik doküman indirme ve analiz başlatma
                with st.spinner("📥 Dokümanlar indiriliyor ve analiz başlatılıyor..."):
                    try:
                        from pathlib import Path
                        from opportunity_runner import download_from_sam
                        
                        # Klasör oluştur
                        safe_notice_id = "".join(c for c in str(opportunity_code).strip() if c.isalnum() or c in ("_", "-"))
                        folder = Path(".") / "opportunities" / safe_notice_id
                        folder.mkdir(parents=True, exist_ok=True)
                        
                        # DB'den resourceLinks ile otomatik indir
                        notice_id = opp.get('noticeId') or opp.get('solicitationNumber') or opp.get('opportunityId', '')
                        opportunity_id = opp.get('opportunityId', '')
                        
                        downloaded = download_from_sam(
                            folder=folder,
                            notice_id=notice_id,
                            opportunity_id=opportunity_id
                        )
                        
                        if downloaded:
                            st.success(f"✅ {len(downloaded)} döküman otomatik indirildi!")
                        else:
                            st.info("ℹ️ Döküman bulunamadı veya zaten mevcut. Analiz devam ediyor...")
                        
                        # Analiz için hazırla
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.session_state.analysis_stage = 1
                        st.session_state.analysis_data = {}
                        
                        # Analiz otomatik başlatılacak (guided_analysis.py'de)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Otomatik doküman indirme hatası: {e}", exc_info=True)
                        st.warning(f"⚠️ Doküman indirme hatası: {str(e)}. Analiz manuel olarak devam edebilir.")
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.rerun()
        
        with btn_col2:
            if st.button("📤 Döküman Yükle", key=f"upload_{opp_id}", use_container_width=True):
                st.session_state[f'upload_mode_{opp_id}'] = True
                st.session_state.selected_opportunity = opp
                st.rerun()
        
        with btn_col3:
            if st.button("📁 Klasörü Aç", key=f"folder_{opp_id}", use_container_width=True):
                folder_path = open_opportunity_folder(opportunity_code)
                if folder_path:
                    st.success(f"✅ Klasör açıldı: {folder_path}")
        
        with btn_col4:
            if st.button("📥 Döküman İndir", key=f"download_{opp_id}", use_container_width=True):
                notice_id = opp.get('noticeId') or opp.get('solicitationNumber') or opp.get('opportunityId', '')
                if notice_id:
                    # Notice ID ile klasör oluştur
                    from pathlib import Path
                    # Notice ID'yi temizle (güvenli klasör adı için)
                    safe_notice_id = "".join(c for c in str(notice_id).strip() if c.isalnum() or c in ("_", "-"))
                    folder = Path(".") / "opportunities" / safe_notice_id
                    folder.mkdir(parents=True, exist_ok=True)
                    folder_path = str(folder.absolute())
                    
                    # Klasörü aç
                    open_opportunity_folder(safe_notice_id)
                    st.success(f"✅ Klasör oluşturuldu ve açıldı: {folder_path}")
                    
                    # SAM.gov'dan dökümanları indir
                    with st.spinner(f"📥 Dökümanlar indiriliyor: {notice_id}..."):
                        try:
                            from opportunity_runner import download_from_sam
                            downloaded = download_from_sam(
                                folder=folder,
                                notice_id=notice_id,
                                opportunity_id=opp.get('opportunityId')
                            )
                            if downloaded:
                                st.success(f"✅ {len(downloaded)} döküman indirildi: {folder_path}")
                            else:
                                st.warning("⚠️ Döküman bulunamadı veya indirilemedi.")
                        except Exception as e:
                            logger.error(f"Döküman indirme hatası: {e}", exc_info=True)
                            st.error(f"❌ Döküman indirme hatası: {str(e)}")
                else:
                    st.warning("⚠️ Notice ID bulunamadı.")
        
        # Upload mode kontrolü
        if st.session_state.get(f'upload_mode_{opp_id}', False):
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### 📤 Döküman Yükleme ve Seçme")
            
            from pathlib import Path
            folder = Path(".") / "opportunities" / opportunity_code
            folder.mkdir(parents=True, exist_ok=True)
            
            # Klasördeki mevcut dosyaları listele
            existing_files = []
            if folder.exists():
                existing_files = (
                    list(folder.glob("*.pdf")) + 
                    list(folder.glob("*.docx")) + 
                    list(folder.glob("*.doc")) +
                    list(folder.glob("*.txt")) +
                    list(folder.glob("*.zip")) +
                    list(folder.glob("*.xls")) +
                    list(folder.glob("*.xlsx"))
                )
                # analysis_report.pdf'yi hariç tut
                existing_files = [f for f in existing_files if f.name != 'analysis_report.pdf']
            
            if existing_files:
                st.markdown("#### 📁 Klasördeki Mevcut Dökümanlar")
                file_dict = {f.name: f for f in existing_files}
                selected_existing = st.multiselect(
                    "Analiz için kullanılacak dosyaları seçin:",
                    options=list(file_dict.keys()),
                    default=list(file_dict.keys()),  # Tümünü varsayılan olarak seç
                    key=f"select_existing_{opp_id}",
                    help="Klasördeki mevcut dosyalardan analiz için kullanmak istediklerinizi seçin."
                )
                
                if selected_existing:
                    st.markdown(f"**✅ {len(selected_existing)} dosya seçildi:**")
                    for filename in selected_existing:
                        file_path = file_dict[filename]
                        size_kb = file_path.stat().st_size / 1024
                        st.markdown(f"  - `{filename}` ({size_kb:.1f} KB)")
                    
                    if st.button("🚀 Seçili Dosyalarla Analiz Başlat", key=f"analyze_selected_{opp_id}", type="primary", use_container_width=True):
                        # Upload mode'u kapat
                        st.session_state[f'upload_mode_{opp_id}'] = False
                        # Fırsatı seç ve analiz sayfasına yönlendir
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.session_state['uploaded_files_ready'] = True
                        st.rerun()
            
            st.markdown("---")
            st.markdown("#### 📤 Yeni Döküman Yükle")
            
            uploaded_files = st.file_uploader(
                "Yeni dökümanları seçin (PDF, DOCX, TXT, ZIP, XLS, XLSX)",
                type=['pdf', 'docx', 'doc', 'txt', 'zip', 'xls', 'xlsx'],
                accept_multiple_files=True,
                key=f"file_uploader_{opp_id}",
                help="Birden fazla dosya seçebilirsiniz. Yükleme sonrası otomatik olarak analiz sayfasına yönlendirileceksiniz."
            )
            
            if uploaded_files:
                uploaded_count = 0
                for uploaded_file in uploaded_files:
                    try:
                        # Dosyayı kaydet
                        file_path = folder / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # ZIP dosyası ise ayıkla
                        if uploaded_file.name.lower().endswith('.zip'):
                            from opportunity_runner import extract_zip_to_folder
                            extracted = extract_zip_to_folder(file_path, folder)
                            if extracted:
                                st.success(f"✅ {uploaded_file.name} yüklendi ve {len(extracted)} dosya ayıklandı")
                            else:
                                st.success(f"✅ {uploaded_file.name} yüklendi")
                        else:
                            st.success(f"✅ {uploaded_file.name} yüklendi")
                        uploaded_count += 1
                    except Exception as e:
                        st.error(f"❌ {uploaded_file.name} yüklenirken hata: {str(e)}")
                
                if uploaded_count > 0:
                    st.success(f"🎉 {uploaded_count} döküman başarıyla yüklendi!")
                    # Upload mode'u kapat
                    st.session_state[f'upload_mode_{opp_id}'] = False
                    # Fırsatı seç ve analiz sayfasına yönlendir
                    st.session_state.selected_opportunity = opp
                    st.session_state.current_page = 'GUIDED_ANALYSIS'
                    st.session_state['uploaded_files_ready'] = True
                    st.rerun()
        else:
            st.markdown("</div>", unsafe_allow_html=True)

def render_results_page():
    """Results page - Veritabanından gerçek verilerle"""
    # Analiz Geçmişi - Veritabanından çek
    st.markdown("### 📊 Analiz Geçmişi")
    
    analysis_history = []
    
    if DB_AVAILABLE:
        try:
            db = get_db_session()
            if db:
                from mergenlite_models import AIAnalysisResult, Opportunity
                from sqlalchemy import or_
                import json
                
                # Optimized: Single query that returns both models (no re-query in loop)
                # Note: opportunity_id FK değil, manuel join
                # Opportunity ID veya Notice ID ile eşleştir (her ikisi de olabilir)
                analyses = db.query(AIAnalysisResult, Opportunity).outerjoin(
                    Opportunity, 
                    or_(
                        AIAnalysisResult.opportunity_id == Opportunity.opportunity_id,
                        AIAnalysisResult.opportunity_id == Opportunity.notice_id
                    )
                ).order_by(AIAnalysisResult.timestamp.desc()).limit(50).all()
                
                for analysis, opp in analyses:
                    
                    # Skor hesapla (result JSONB'dan) - Normalize JSONB handling
                    skor = "N/A"
                    skor_class = "badge-info"
                    result_data = analysis.result
                    
                    # Handle JSONB: may be string in some environments
                    if isinstance(result_data, str):
                        try:
                            result_data = json.loads(result_data)
                        except (json.JSONDecodeError, TypeError):
                            result_data = {}
                    
                    if result_data and isinstance(result_data, dict):
                        # Opportunity Runner sonuçları için: data.compliance veya data.proposal içinde olabilir
                        # Önce data.compliance kontrol et
                        data_compliance = result_data.get('data', {}).get('compliance', {})
                        # Sonra direkt compliance kontrol et
                        compliance = result_data.get('compliance', {}) or data_compliance
                        
                        # fit_assessment'ten overall_score al (Opportunity Runner için)
                        fit_assessment = result_data.get('data', {}).get('proposal', {}) or result_data.get('fit_assessment', {})
                        if fit_assessment and fit_assessment.get('overall_score'):
                            score = fit_assessment.get('overall_score', 0)
                            if isinstance(score, str):
                                try:
                                    score = int(float(score))
                                except (ValueError, TypeError):
                                    score = 0
                            else:
                                score = int(score or 0)
                            
                            if score >= 80:
                                skor = "Mükemmel"
                                skor_class = "badge-success"
                            elif score >= 60:
                                skor = "İyi"
                                skor_class = "badge-info"
                            elif score >= 40:
                                skor = "Orta"
                                skor_class = "badge-warning"
                            else:
                                skor = "Düşük"
                                skor_class = "badge-danger"
                        elif compliance:
                            score = compliance.get('score', 0)
                            # Safe cast: handle None or string
                            if isinstance(score, str):
                                try:
                                    score = int(float(score))
                                except (ValueError, TypeError):
                                    score = 0
                            else:
                                score = int(score or 0)
                            
                            if score >= 80:
                                skor = "Mükemmel"
                                skor_class = "badge-success"
                            elif score >= 60:
                                skor = "İyi"
                                skor_class = "badge-info"
                            elif score >= 40:
                                skor = "Orta"
                                skor_class = "badge-warning"
                            else:
                                skor = "Düşük"
                                skor_class = "badge-danger"
                        # Confidence'dan da skor çıkarabiliriz
                        elif analysis.confidence is not None:
                            conf_score = float(analysis.confidence) * 100
                            if conf_score >= 80:
                                skor = "Mükemmel"
                                skor_class = "badge-success"
                            elif conf_score >= 60:
                                skor = "İyi"
                                skor_class = "badge-info"
                            elif conf_score >= 40:
                                skor = "Orta"
                                skor_class = "badge-warning"
                            else:
                                skor = "Düşük"
                                skor_class = "badge-danger"
                    
                    # Süre hesapla - timestamp kullan
                    sure = "N/A"
                    if analysis.timestamp:
                        # created_at ile karşılaştır
                        if analysis.created_at:
                            delta = analysis.created_at - analysis.timestamp
                            if delta.total_seconds() > 0:
                                sure = f"{delta.total_seconds():.0f}sn"
                    
                    analysis_history.append({
                        "analizId": f"AN-{analysis.id}",
                        "noticeId": opp.notice_id if opp and opp.notice_id else analysis.opportunity_id[:20],
                        "title": opp.title if opp else "Başlık Yok",
                        "tarih": analysis.timestamp.strftime("%Y-%m-%d %H:%M") if analysis.timestamp else "N/A",
                        "sure": sure,
                        "skor": skor,
                        "skorClass": skor_class,
                        "analysis_id": str(analysis.id),
                        "opportunity_id": analysis.opportunity_id,
                        "status": analysis.analysis_type,  # analysis_type -> status
                        "consolidated_output": result_data  # result -> consolidated_output (UI uyumluluğu için)
                    })
                
                db.close()
        except Exception as e:
            logger.error(f"Analiz geçmişi yükleme hatası: {e}", exc_info=True)
            st.warning(f"⚠️ Veritabanından analiz geçmişi yüklenirken hata: {str(e)}")
    
    # Eğer veritabanından veri yoksa, örnek veri göster
    if not analysis_history:
        st.info("Henüz analiz sonucu bulunmuyor.")
        analysis_history = [
            {
                "analizId": "Örnek-001",
                "noticeId": "Örnek Notice ID",
                "title": "Örnek Analiz - Henüz analiz yapılmadı",
                "tarih": "N/A",
                "sure": "N/A",
                "skor": "N/A",
                "skorClass": "badge-info"
            }
        ]
    
    # Tablo başlığı
    st.markdown("""
    <div class="modern-card" style="margin-bottom: 24px; padding: 0; overflow-x: auto; background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 12px;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="border-bottom: 1px solid var(--border-800);">
                    <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Analiz ID</th>
                    <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Notice ID</th>
                    <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Başlık</th>
                    <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Tarih</th>
                    <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Süre</th>
                    <th style="padding: 12px 16px; text-align: center; color: var(--text-400); font-size: 13px; font-weight: 600;">Skor</th>
                    <th style="padding: 12px 16px; text-align: center; color: var(--text-400); font-size: 13px; font-weight: 600;">Durum</th>
                    <th style="padding: 12px 16px; text-align: center; color: var(--text-400); font-size: 13px; font-weight: 600;">Aksiyonlar</th>
                </tr>
            </thead>
            <tbody>
    """, unsafe_allow_html=True)
    
    # Seçili analiz için state
    if 'selected_analysis_id' not in st.session_state:
        st.session_state.selected_analysis_id = None
    
    for idx, analysis in enumerate(analysis_history):
        # Durum badge
        status_text = "Tamamlandı"
        status_color = "var(--emerald-500)"
        if analysis.get('status') == 'IN_PROGRESS':
            status_text = "Devam Ediyor"
            status_color = "var(--amber-500)"
        elif analysis.get('status') == 'FAILED':
            status_text = "Başarısız"
            status_color = "var(--red-500)"
        
        # SAM.gov link
        sam_link_html = ""
        opp_id = analysis.get('opportunity_id', '')
        if opp_id and len(opp_id) == 32:
            sam_link = f"https://sam.gov/opp/{opp_id}/view"
            sam_link_html = f'<a href="{sam_link}" target="_blank" style="color: var(--blue-400); text-decoration: none; font-size: 11px; margin-left: 4px;">🔗</a>'
        
        # Tablo satırı için gerçek Streamlit widget kullan
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2, 4, 2, 2, 2, 2, 1])
        
        with col1:
            st.markdown(f"<span style='color: var(--blue-400); font-size: 13px; font-weight: 500;'>{analysis['analizId']}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color: var(--text-300); font-size: 13px;'>{analysis['noticeId']}</span>{sam_link_html}", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color: var(--text); font-size: 13px;'>{analysis['title'][:60]}{'...' if len(analysis['title']) > 60 else ''}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<span style='color: var(--text-400); font-size: 13px;'>📅 {analysis['tarih']}</span>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<span style='color: var(--text-400); font-size: 13px;'>⏱️ {analysis['sure']}</span>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<span class='badge {analysis['skorClass']}'>{analysis['skor']}</span>", unsafe_allow_html=True)
        with col7:
            st.markdown(f"<span style='color: {status_color}; font-size: 13px; display: inline-flex; align-items: center; gap: 4px;'>✅ <span>{status_text}</span></span>", unsafe_allow_html=True)
        with col8:
            if st.button("📄", key=f"select_analysis_{idx}", help=f"Analiz {analysis['analizId']} seç"):
                st.session_state.selected_analysis_id = analysis.get('analysis_id')
                st.session_state.selected_analysis_data = analysis
                st.rerun()
    
    st.markdown("</tbody></table></div>", unsafe_allow_html=True)
    
    # Detaylı Görünüm
    st.markdown("### 🔍 Detaylı Görünüm")
    
    # Seçili analizi göster veya ilk analizi varsayılan olarak göster
    if 'selected_analysis_data' in st.session_state and st.session_state.selected_analysis_data:
        selected_analysis = st.session_state.selected_analysis_data
    elif analysis_history:
        selected_analysis = analysis_history[0]
    else:
        return
    
    col_title, col_actions = st.columns([3, 1])
    with col_title:
        st.markdown(f"""
        <div style="margin-bottom: 20px; display: flex; align-items: center; height: 100%;">
            <h4 style="color: var(--text); font-size: 16px; font-weight: 600; margin: 0;">{selected_analysis['noticeId']} - {selected_analysis['title']}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_actions:
        col_pdf, col_json = st.columns(2)
        with col_pdf:
            # Seçili analiz için PDF dosyasını bul ve indir
            pdf_data = None
            pdf_filename = None
            if st.session_state.selected_analysis_data:
                analysis_data = st.session_state.selected_analysis_data
                consolidated = analysis_data.get('consolidated_output', {})
                
                # PDF path'i bul
                pdf_path = None
                if isinstance(consolidated, dict):
                    pdf_path = consolidated.get('report_pdf_path') or consolidated.get('metadata', {}).get('report_pdf_path')
                
                # Eğer path yoksa, output_dir'den bul
                if not pdf_path and isinstance(consolidated, dict):
                    output_dir = consolidated.get('output_dir')
                    if output_dir:
                        from pathlib import Path
                        pdf_path = str(Path(output_dir) / "analysis_report.pdf")
                
                # PDF dosyasını oku
                if pdf_path:
                    try:
                        from pathlib import Path
                        pdf_file_path = Path(pdf_path)
                        if pdf_file_path.exists():
                            with open(pdf_file_path, "rb") as f:
                                pdf_data = f.read()
                            pdf_filename = f"analysis_report_{analysis_data.get('analizId', 'unknown')}.pdf"
                    except Exception as e:
                        logger.warning(f"PDF okuma hatası: {e}")
            
            if pdf_data:
                st.download_button(
                    "⬇️ PDF İndir",
                    data=pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf"
                )
            else:
                st.button("⬇️ PDF İndir", use_container_width=True, key="download_pdf_disabled", disabled=True)
        
        with col_json:
            # Seçili analiz için JSON dosyasını bul ve indir
            json_data = None
            json_filename = None
            if st.session_state.selected_analysis_data:
                analysis_data = st.session_state.selected_analysis_data
                consolidated = analysis_data.get('consolidated_output', {})
                
                # JSON path'i bul
                json_path = None
                if isinstance(consolidated, dict):
                    json_path = consolidated.get('report_json_path') or consolidated.get('metadata', {}).get('report_json_path')
                
                # Eğer path yoksa, output_dir'den bul
                if not json_path and isinstance(consolidated, dict):
                    output_dir = consolidated.get('output_dir')
                    if output_dir:
                        from pathlib import Path
                        json_path = str(Path(output_dir) / "detailed_analysis_report.json")
                
                # JSON dosyasını oku veya data'dan oluştur
                if json_path:
                    try:
                        from pathlib import Path
                        json_file_path = Path(json_path)
                        if json_file_path.exists():
                            with open(json_file_path, "r", encoding="utf-8") as f:
                                json_data = f.read()
                            json_filename = f"analysis_report_{analysis_data.get('analizId', 'unknown')}.json"
                    except Exception as e:
                        logger.warning(f"JSON okuma hatası: {e}")
                elif consolidated:
                    # Path yoksa, data'dan JSON oluştur
                    try:
                        import json
                        json_data = json.dumps(consolidated, indent=2, ensure_ascii=False)
                        json_filename = f"analysis_report_{analysis_data.get('analizId', 'unknown')}.json"
                    except Exception as e:
                        logger.warning(f"JSON oluşturma hatası: {e}")
            
            if json_data:
                st.download_button(
                    "📄 JSON Export",
                    data=json_data,
                    file_name=json_filename,
                    mime="application/json",
                    use_container_width=True,
                    key="export_json"
                )
            else:
                st.button("📄 JSON Export", use_container_width=True, key="export_json_disabled", disabled=True)
    
    # Fırsat Bilgileri
    st.markdown("#### 📋 Analiz Edilen Fırsat")
    opp_info_col1, opp_info_col2 = st.columns(2)
    with opp_info_col1:
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="color: var(--text-400); font-size: 12px; margin-bottom: 4px;">Notice ID</div>
            <div style="color: var(--blue-400); font-size: 14px; font-weight: 600;">{selected_analysis['noticeId']}</div>
        </div>
        """, unsafe_allow_html=True)
    with opp_info_col2:
        sam_link_result = ""
        opp_id_result = selected_analysis.get('opportunity_id', '')
        if opp_id_result and len(opp_id_result) == 32:
            sam_link_result = f"https://sam.gov/opp/{opp_id_result}/view"
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="color: var(--text-400); font-size: 12px; margin-bottom: 4px;">SAM.gov Link</div>
                <div><a href="{sam_link_result}" target="_blank" style="color: var(--blue-400); text-decoration: none; font-size: 14px; font-weight: 600;">🔗 SAM.gov'da Görüntüle</a></div>
            </div>
            """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 İşlenen Dokümanlar", "🔍 Gereksinimler Özeti", "🛡️ Compliance Matrisi", "✍️ Teklif Taslağı"])
    
    # Consolidated output'u bir kez parse et
    consolidated = selected_analysis.get('consolidated_output', {})
    import json
    if isinstance(consolidated, str):
        try:
            consolidated = json.loads(consolidated)
        except (json.JSONDecodeError, TypeError):
            consolidated = {}
    
    with tab1:
        # İşlenen dokümanları göster - İndirilebilir şekilde
        documents = consolidated.get('data', {}).get('documents', []) if isinstance(consolidated, dict) else []
        if not documents and isinstance(consolidated, dict):
            documents = consolidated.get('documents', [])
        
        # Opportunity klasöründen dökümanları bul
        opportunity_id = selected_analysis.get('opportunity_id', '')
        opportunity_code = selected_analysis.get('noticeId', '') or opportunity_id[:20] if opportunity_id else ''
        
        # Klasör yolunu oluştur
        from pathlib import Path
        opp_folder = Path("opportunities") / opportunity_code if opportunity_code else None
        
        if documents:
            st.markdown(f"### 📚 Analiz Edilen Dökümanlar ({len(documents)} adet)")
            st.markdown("---")
            
            # Grid layout - 2 sütun
            cols = st.columns(2)
            
            for idx, doc in enumerate(documents):
                col = cols[idx % 2]
                
                with col:
                    doc_name = doc.get('filename', doc.get('name', f'Doküman {idx+1}'))
                    doc_path = doc.get('path', '')
                    page_count = doc.get('page_count', 0)
                    text_length = len(doc.get('text', ''))
                    doc_type = doc.get('document_type', 'general')
                    
                    # Belge tipi analiz sonuçlarını göster
                    doc_analysis = doc.get('document_analysis', {})
                    compliance_score = 0
                    if doc_analysis:
                        analysis = doc_analysis.get('analysis', {})
                        compliance_score = analysis.get('compliance_score', 0)
                        doc_type = doc_analysis.get('document_type', doc_type)
                    
                    # Dosya yolunu bul
                    file_path = None
                    if doc_path and Path(doc_path).exists():
                        file_path = Path(doc_path)
                    elif opp_folder and opp_folder.exists():
                        # Klasörde dosyayı ara
                        for pdf_file in opp_folder.glob("*.pdf"):
                            if doc_name.lower() in pdf_file.name.lower() or pdf_file.name.lower() in doc_name.lower():
                                file_path = pdf_file
                                break
                        # PDF bulunamazsa diğer formatları dene
                        if not file_path:
                            for doc_file in opp_folder.glob("*"):
                                if doc_name.lower() in doc_file.name.lower() or doc_file.name.lower() in doc_name.lower():
                                    file_path = doc_file
                                    break
                    
                    # Document type badge renkleri
                    type_colors = {
                        'rfq': 'rgba(59, 130, 246, 0.2)',
                        'sow': 'rgba(16, 185, 129, 0.2)',
                        'contract': 'rgba(245, 158, 11, 0.2)',
                        'compliance': 'rgba(239, 68, 68, 0.2)',
                        'performance': 'rgba(139, 92, 246, 0.2)'
                    }
                    type_color = type_colors.get(doc_type.lower(), 'rgba(59, 130, 246, 0.1)')
                    
                    # Card HTML
                    card_html = f"""
                    <div style="background: linear-gradient(135deg, {type_color}, rgba(15, 23, 42, 0.8)); border: 1px solid var(--border-800); border-radius: 12px; padding: 20px; margin-bottom: 16px; transition: transform 0.2s, box-shadow 0.2s;" 
                         onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 16px rgba(0,0,0,0.3)'" 
                         onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <div style="display: flex; align-items: start; gap: 12px; margin-bottom: 12px;">
                            <div style="font-size: 32px; flex-shrink: 0;">📄</div>
                            <div style="flex: 1;">
                                <div style="color: var(--text); font-size: 16px; font-weight: 600; margin-bottom: 4px; word-break: break-word;">{doc_name}</div>
                                <div style="display: inline-block; background: rgba(59, 130, 246, 0.2); color: var(--blue-400); padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-top: 4px; text-transform: uppercase;">{doc_type}</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 16px; color: var(--text-400); font-size: 12px; margin-bottom: 12px; flex-wrap: wrap;">
                            <span style="display: flex; align-items: center; gap: 4px;">📊 <span>{page_count} sayfa</span></span>
                            <span style="display: flex; align-items: center; gap: 4px;">📝 <span>{text_length:,} karakter</span></span>
                        </div>
                    """
                    
                    # Analiz skoru varsa göster
                    if compliance_score > 0:
                        card_html += f"""
                        <div style="background: rgba(59, 130, 246, 0.15); border-left: 3px solid var(--blue-400); border-radius: 4px; padding: 8px; margin-bottom: 12px;">
                            <div style="color: var(--blue-400); font-size: 12px; font-weight: 600; margin-bottom: 4px;">📊 Analiz Skoru</div>
                            <div style="color: var(--text-300); font-size: 14px; font-weight: 600;">{compliance_score}% Uygunluk</div>
                        </div>
                        """
                    
                    card_html += "</div>"
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # İndirme butonu
                    if file_path and file_path.exists():
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            file_ext = file_path.suffix.lower()
                            mime_types = {
                                '.pdf': 'application/pdf',
                                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                '.doc': 'application/msword',
                                '.txt': 'text/plain',
                                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                '.xls': 'application/vnd.ms-excel'
                            }
                            mime_type = mime_types.get(file_ext, 'application/octet-stream')
                            
                            st.download_button(
                                label=f"⬇️ {doc_name} İndir",
                                data=file_data,
                                file_name=file_path.name,
                                mime=mime_type,
                                use_container_width=True,
                                key=f"download_doc_{idx}"
                            )
    
    with tab2:
        # Gereksinimleri consolidated_output'dan çek
        requirements = []
        
        # Handle JSONB: may be string in some environments
        import json
        if isinstance(consolidated, str):
            try:
                consolidated = json.loads(consolidated)
            except (json.JSONDecodeError, TypeError):
                consolidated = {}
        
        if consolidated and isinstance(consolidated, dict):
            # Opportunity Runner sonuçları için: data.requirements veya event_requirements
            # Önce event_requirements kontrol et (Opportunity Runner formatı)
            event_req = consolidated.get('data', {}).get('requirements', {}) if isinstance(consolidated.get('data'), dict) else {}
            if not event_req:
                event_req = consolidated.get('event_requirements', {})
            
            # Requirements extractor çıktısından gereksinimleri al
            req_data = consolidated.get('data', {}).get('requirements', []) if isinstance(consolidated.get('data'), dict) else []
            if not req_data:
                req_data = consolidated.get('requirements', [])
            
            # Eğer event_requirements dict ise, listeye çevir
            if isinstance(event_req, dict) and event_req:
                # event_requirements dict'inden bilgileri çıkar
                if event_req.get('location'):
                    requirements.append({
                        "kategori": "Konum",
                        "gereksinim": f"Lokasyon: {event_req.get('location')}",
                        "oncelik": "Yüksek",
                        "oncelikClass": "badge-danger",
                        "durum": "Belirtilmiş",
                        "durumClass": "badge-success"
                    })
                if event_req.get('date_range'):
                    requirements.append({
                        "kategori": "Tarih",
                        "gereksinim": f"Tarih Aralığı: {event_req.get('date_range')}",
                        "oncelik": "Yüksek",
                        "oncelikClass": "badge-danger",
                        "durum": "Belirtilmiş",
                        "durumClass": "badge-success"
                    })
                if event_req.get('participants_target'):
                    requirements.append({
                        "kategori": "Kapasite",
                        "gereksinim": f"Hedef Katılımcı: {event_req.get('participants_target')}",
                        "oncelik": "Yüksek",
                        "oncelikClass": "badge-danger",
                        "durum": "Belirtilmiş",
                        "durumClass": "badge-success"
                    })
                if event_req.get('av_requirements'):
                    requirements.append({
                        "kategori": "AV Gereksinimleri",
                        "gereksinim": event_req.get('av_requirements'),
                        "oncelik": "Orta",
                        "oncelikClass": "badge-warning",
                        "durum": "Belirtilmiş",
                        "durumClass": "badge-success"
                    })
            if isinstance(req_data, list):
                for req in req_data:
                    if isinstance(req, dict):
                        requirements.append({
                            "kategori": req.get('category', 'Genel'),
                            "gereksinim": req.get('requirement', req.get('description', 'N/A')),
                            "oncelik": req.get('priority', 'Orta'),
                            "oncelikClass": "badge-danger" if req.get('priority') == 'Yüksek' else ("badge-warning" if req.get('priority') == 'Orta' else "badge-info"),
                            "durum": req.get('status', 'İnceleniyor'),
                            "durumClass": "badge-success" if req.get('status') == 'Karşılanıyor' else ("badge-warning" if req.get('status') == 'İnceleniyor' else "badge-danger")
                        })
        
        # Eğer gereksinim yoksa örnek göster
        if not requirements:
            requirements = [
                {"kategori": "Bilgi", "gereksinim": "Analiz sonuçları henüz işlenmedi", "oncelik": "N/A", "oncelikClass": "badge-info", "durum": "Beklemede", "durumClass": "badge-info"}
            ]
        
        st.markdown("""
        <div class="modern-card" style="padding: 0; overflow-x: auto; background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 12px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid var(--border-800);">
                        <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Kategori</th>
                        <th style="padding: 12px 16px; text-align: left; color: var(--text-400); font-size: 13px; font-weight: 600;">Gereksinim</th>
                        <th style="padding: 12px 16px; text-align: center; color: var(--text-400); font-size: 13px; font-weight: 600;">Öncelik</th>
                        <th style="padding: 12px 16px; text-align: center; color: var(--text-400); font-size: 13px; font-weight: 600;">Durum</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)
        
        for req in requirements:
            st.markdown(f"""
            <tr style="border-bottom: 1px solid var(--border-800); transition: background .2s ease;" onmouseover="this.style.background='rgba(59, 130, 246, 0.05)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 12px 16px; text-align: left;"><span style="color: var(--blue-400); font-size: 13px; font-weight: 500;">{req['kategori']}</span></td>
                <td style="padding: 12px 16px; text-align: left;"><span style="color: var(--text-300); font-size: 13px;">{req['gereksinim']}</span></td>
                <td style="padding: 12px 16px; text-align: center;"><span class="badge {req['oncelikClass']}">{req['oncelik']}</span></td>
                <td style="padding: 12px 16px; text-align: center;"><span class="badge {req['durumClass']}">{req['durum']}</span></td>
            </tr>
            """, unsafe_allow_html=True)
        
        st.markdown("</tbody></table></div>", unsafe_allow_html=True)
    
    with tab3:
        # Compliance matrisini consolidated_output'dan çek
        compliance_data = consolidated.get('data', {}).get('compliance', {}) if isinstance(consolidated, dict) and isinstance(consolidated.get('data'), dict) else {}
        if not compliance_data and isinstance(consolidated, dict):
            compliance_data = consolidated.get('compliance', {})
        
        if compliance_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                score = compliance_data.get('score', 0)
                # Safe cast
                if isinstance(score, str):
                    try:
                        score = int(float(score))
                    except (ValueError, TypeError):
                        score = 0
                else:
                    score = int(score or 0)
                st.metric("Uyumluluk Skoru", f"{score}%")
            with col2:
                risk_level = compliance_data.get('risk_level', 'N/A')
                risk_class = "badge-success" if risk_level == 'low' else ("badge-warning" if risk_level == 'medium' else "badge-danger")
                st.markdown(f"**Risk Seviyesi:** <span class='badge {risk_class}'>{risk_level.upper()}</span>", unsafe_allow_html=True)
            with col3:
                issues_count = len(compliance_data.get('issues', []))
                st.metric("Tespit Edilen Sorun", issues_count)
            
            # Sorunlar listesi
            issues = compliance_data.get('issues', [])
            if issues:
                st.markdown("#### 🚨 Tespit Edilen Sorunlar")
                for issue in issues:
                    st.warning(f"**{issue.get('type', 'Sorun')}**: {issue.get('description', 'N/A')}")
            
            # Compliance detayları
            with st.expander("📋 Detaylı Compliance Bilgileri"):
                st.json(compliance_data)
    
    with tab4:
        # Teklif taslağını consolidated_output'dan çek
        proposal_data = consolidated.get('data', {}).get('proposal', {}) if isinstance(consolidated, dict) and isinstance(consolidated.get('data'), dict) else {}
        if not proposal_data and isinstance(consolidated, dict):
            proposal_data = consolidated.get('proposal', {})
        
        if proposal_data:
            st.markdown("#### ✍️ Teklif Özeti")
            
            # Öneriler
            recommendations = proposal_data.get('recommendations', [])
            if recommendations:
                st.markdown("**Öneriler:**")
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
            
            # Teklif durumu
            proposal_status = proposal_data.get('status', 'N/A')
            st.markdown(f"**Durum:** {proposal_status}")
            
            # Teklif içeriği
            proposal_content = proposal_data.get('content', proposal_data.get('draft', ''))
            if proposal_content:
                st.markdown("#### 📄 Teklif İçeriği")
                st.text_area("Teklif Taslağı", proposal_content, height=300, disabled=True)
            
            # Detaylı bilgiler
            with st.expander("📋 Detaylı Teklif Bilgileri"):
                st.json(proposal_data)

def render_mail_dashboard():
    """İletişim/Mail Dashboard Ekranı - Premium Dark Design"""
    st.markdown("""
    <style>
        /* Dashboard Container */
        .mail-dashboard-container {
            font-family: 'Inter', sans-serif;
            color: #e2e8f0;
        }
        
        /* Panel Headers */
        .panel-header {
            font-size: 14px;
            font-weight: 600;
            color: #94a3b8;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Search Box Custom */
        .custom-search input {
            background: #0f172a !important;
            border: 1px solid #1e293b !important;
            color: #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
        }
        
        /* Operation Card */
        .op-list-item {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .op-list-item:hover {
            border-color: #3b82f6;
            transform: translateY(-1px);
        }
        .op-list-item.active {
            background: linear-gradient(145deg, rgba(59, 130, 246, 0.1), rgba(15, 23, 42, 0.6));
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }
        
        /* Progress Bar */
        .custom-progress {
            height: 4px;
            background: #334155;
            border-radius: 2px;
            margin-top: 12px;
            overflow: hidden;
        }
        .custom-progress-bar {
            height: 100%;
            background: #10b981;
            border-radius: 2px;
        }
        
        /* Hotel List Item */
        .hotel-list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            border-bottom: 1px solid #1e293b;
            cursor: pointer;
            transition: background 0.2s;
        }
        .hotel-list-item:hover {
            background: rgba(59, 130, 246, 0.05);
        }
        .hotel-list-item.active {
            background: rgba(59, 130, 246, 0.1);
            border-left: 3px solid #3b82f6;
        }
        
        /* Status Badge */
        .status-pill {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .status-sent { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        .status-negotiating { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .status-replied { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .status-queued { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; }
        
        /* Chat Area */
        .chat-container {
            background: #0b1120;
            border-radius: 16px;
            border: 1px solid #1e293b;
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            padding: 16px 24px;
            border-bottom: 1px solid #1e293b;
            background: rgba(15, 23, 42, 0.8);
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        /* Chat Bubbles */
        .msg-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
            position: relative;
        }
        .msg-out {
            align_self: flex-end;
            background: #3b82f6;
            color: white;
            border-bottom-right-radius: 4px;
            margin-left: auto;
        }
        .msg-in {
            align_self: flex-start;
            background: #1e293b;
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .msg-time {
            font-size: 10px;
            opacity: 0.7;
            margin-top: 4px;
            text-align: right;
        }
        .msg-ai {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
        }
        
        /* Input Area */
        .chat-input-area {
            padding: 16px;
            border-top: 1px solid #1e293b;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 0 0 16px 16px;
        }
        
        /* AI Suggestion Chip */
        .ai-chip {
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid rgba(124, 58, 237, 0.3);
            color: #a78bfa;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .ai-chip:hover {
            background: rgba(124, 58, 237, 0.2);
            border-color: #7c3aed;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">İletişim Merkezi</h1>', unsafe_allow_html=True)
    st.markdown('<div style="color: #94a3b8; margin-top: -16px; margin-bottom: 24px; font-size: 14px;">Fırsat bazlı otel iletişim yönetimi</div>', unsafe_allow_html=True)
    
    col_ops, col_hotels, col_chat = st.columns([22, 28, 50], gap="medium")
    
    db = get_db_session()
    if not db:
        st.error("Veritabanı bağlantısı yok.")
        return

    # Initialize Session States
    if 'mail_selected_opp_id' not in st.session_state:
        st.session_state.mail_selected_opp_id = None
    if 'mail_selected_hotel_id' not in st.session_state:
        st.session_state.mail_selected_hotel_id = None

    try:
        # --- LEFT PANEL: Active Operations ---
        with col_ops:
            st.markdown('<div class="panel-header">📝 Aktif Operasyonlar</div>', unsafe_allow_html=True)
            
            # Custom Search Input
            search_val = st.text_input("Fırsat Ara...", key="mail_opp_search", label_visibility="collapsed", placeholder="🔍 Fırsat Ara...")
            
            ops_query = db.query(Opportunity).filter(Opportunity.status != 'archived')
            if search_val:
                ops_query = ops_query.filter(Opportunity.title.ilike(f"%{search_val}%"))
            
            opportunities = ops_query.order_by(Opportunity.updated_at.desc()).limit(15).all()
            
            st.markdown('<div style="height: 650px; overflow-y: auto; padding-right: 4px;">', unsafe_allow_html=True)
            
            for opp in opportunities:
                is_active = (st.session_state.mail_selected_opp_id == opp.id)
                active_class = "active" if is_active else ""
                
                # Metrics (Mock logic for demo mostly, but connected to DB)
                hotel_count = db.query(Hotel).filter(Hotel.opportunity_id == opp.id).count()
                sent_count = db.query(Hotel).filter(Hotel.opportunity_id == opp.id, Hotel.status == 'sent').count()
                progress_pct = int((sent_count / hotel_count * 100)) if hotel_count > 0 else 0
                
                # Card HTML
                st.markdown(f"""
                <div class="op-list-item {active_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 10px; color: #64748b; font-family: monospace;">{opp.opportunity_id[-12:] if opp.opportunity_id else 'N/A'}</span>
                        <span style="font-size: 10px; background: #334155; padding: 2px 6px; border-radius: 4px; color: #f1f5f9;">{hotel_count} Otel</span>
                    </div>
                    <div style="font-size: 13px; font-weight: 600; color: #f8fafc; line-height: 1.4; margin-bottom: 12px;">
                        {opp.title[:55]}...
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8;">
                        <span>İletişim Kapsamı</span>
                        <span>{sent_count}/{hotel_count} Gönderildi</span>
                    </div>
                    <div class="custom-progress">
                        <div class="custom-progress-bar" style="width: {progress_pct}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Invisible full-overlay button for selection
                if st.button(f"select_opp_{opp.id}", key=f"btn_opp_{opp.id}", use_container_width=True):
                    st.session_state.mail_selected_opp_id = opp.id
                    st.session_state.mail_selected_hotel_id = None
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

        # --- MIDDLE PANEL: Target Hotels ---
        with col_hotels:
            if st.session_state.mail_selected_opp_id:
                # Header context
                sel_opp = db.query(Opportunity).get(st.session_state.mail_selected_opp_id)
                opp_title = sel_opp.title[:30] + "..." if sel_opp else "Seçili Fırsat"
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div class="panel-header" style="margin-bottom: 0;">🏢 Hedef Oteller</div>
                    <div style="font-size: 11px; color: #64748b;">{opp_title}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hotel List
                hotels = db.query(Hotel).filter(Hotel.opportunity_id == st.session_state.mail_selected_opp_id).all()
                
                if not hotels:
                    st.info("Otel bulunamadı.")
                
                st.markdown('<div class="modern-card" style="padding: 0; background: #0f172a; border: 1px solid #1e293b; overflow: hidden; height: 650px; display: flex; flex-direction: column;">', unsafe_allow_html=True)
                st.markdown('<div style="overflow-y: auto; flex: 1;">', unsafe_allow_html=True)
                
                for hotel in hotels:
                    is_active = (st.session_state.mail_selected_hotel_id == hotel.id)
                    active_class = "active" if is_active else ""
                    
                    status_map = {
                        'queued': ('Sırada', 'status-queued'),
                        'sent': ('İletildi', 'status-sent'),
                        'replied': ('Yanıtladı', 'status-replied'),
                        'negotiating': ('Pazarlık', 'status-negotiating'),
                        'rejected': ('Red', 'badge-danger')
                    }
                    lbl, cls = status_map.get(hotel.status, ('Sırada', 'status-queued'))
                    
                    # Time formatting
                    time_str = hotel.last_contact_at.strftime("%H:%M") if hotel.last_contact_at else "Now"
                    if hotel.last_contact_at and (datetime.now() - hotel.last_contact_at).days > 0:
                         time_str = hotel.last_contact_at.strftime("%d %b")

                    st.markdown(f"""
                    <div class="hotel-list-item {active_class}">
                        <div style="flex: 1;">
                            <div style="font-weight: 500; font-size: 13px; color: #f1f5f9; margin-bottom: 4px;">{hotel.name}</div>
                            <div style="font-size: 11px; color: #64748b;">{hotel.price_quote if hotel.price_quote else 'Fiyat Bekleniyor'}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 10px; color: #64748b; margin-bottom: 4px;">{time_str}</div>
                            <span class="status-pill {cls}">{lbl}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"sel_hotel_{hotel.id}", key=f"btn_h_{hotel.id}", use_container_width=True):
                        st.session_state.mail_selected_hotel_id = hotel.id
                        st.rerun()
                
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("👈 İşlem yapmak için soldan bir fırsat seçin.")

        # --- RIGHT PANEL: Chat Interface ---
        with col_chat:
            if st.session_state.mail_selected_hotel_id:
                hotel = db.query(Hotel).get(st.session_state.mail_selected_hotel_id)
                
                # Chat Container Start
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                
                # Header
                st.markdown(f"""
                <div class="chat-header">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 36px; height: 36px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; color: white;">
                            {hotel.name[:2].upper()}
                        </div>
                        <div>
                            <div style="font-weight: 600; font-size: 14px; color: #f8fafc;">{hotel.name}</div>
                            <div style="font-size: 11px; color: #94a3b8;">{hotel.manager_name or 'Resepsiyon'} • <span style="color: #fbbf24;">★ {hotel.rating or 4.5}</span></div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 12px;">
                        <button style="background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; padding: 6px 10px; cursor: pointer;">📞</button>
                        <button style="background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; padding: 6px 10px; cursor: pointer;">📹</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Messages Area - We construct one big HTML block for the scrollable area
                messages = db.query(EmailLog).filter(EmailLog.hotel_id == hotel.id).order_by(EmailLog.created_at.asc()).all()
                
                msgs_html = '<div class="chat-messages">'
                
                # Welcome placeholder if empty
                if not messages:
                    msgs_html += '<div style="text-align: center; color: #64748b; margin-top: 40px; font-size: 13px;">Görüşme henüz başlamadı.</div>'
                
                for msg in messages:
                    is_out = (msg.direction == 'outbound')
                    cls = "msg-out" if is_out else "msg-in"
                    align_style = "margin-left: auto;" if is_out else "margin-right: auto;"
                    
                    time_s = msg.created_at.strftime('%H:%M') if msg.created_at else ''
                    
                    msgs_html += f"""
                    <div class="msg-bubble {cls}" style="{align_style} width: fit-content; max-width: 75%;">
                        {msg.raw_body or msg.subject}
                        <div class="msg-time">{time_s}</div>
                    </div>
                    """
                
                msgs_html += '</div>' # End chat-messages
                st.markdown(msgs_html, unsafe_allow_html=True)
                
                # Close Chat Container Div (visual wrapper only)
                st.markdown('</div>', unsafe_allow_html=True) 
                
                # Input Area (Outside the visual wrapper because Streamlit forms cannot be nested perfectly in HTML blocks easily without custom components)
                # But we style it to look attached
                
                st.markdown('<div style="margin-top: -65px; position: relative; z-index: 10; padding: 0 16px;">', unsafe_allow_html=True)
                with st.form(key="chat_form", clear_on_submit=True):
                    # AI Chips
                    st.markdown("""
                    <div style="display: flex; gap: 8px; margin-bottom: 8px; overflow-x: auto;">
                        <span class="ai-chip">✨ Fiyat Teklifi İste</span>
                        <span class="ai-chip">📅 Müsaitlik Sor</span>
                        <span class="ai-chip">📄 SOW Gönder</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    cols = st.columns([10, 1])
                    with cols[0]:
                        txt = st.text_input("Mesaj", label_visibility="collapsed", placeholder="Mesajınızı yazın...")
                    with cols[1]:
                        sent = st.form_submit_button("➤")
                    
                    if sent and txt:
                        new_log = EmailLog(
                            hotel_id=hotel.id,
                            opportunity_id=hotel.opportunity_id,
                            direction='outbound',
                            raw_body=txt,
                            subject="Manual Chat",
                            created_at=datetime.utcnow()
                        )
                        db.add(new_log)
                        hotel.last_contact_at = datetime.utcnow()
                        db.commit()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                 st.markdown("""
                 <div style="background: #0b1120; border-radius: 16px; border: 1px solid #1e293b; height: 600px; display: flex; align-items: center; justify-content: center; flex-direction: column; color: #475569;">
                    <div style="font-size: 40px; margin-bottom: 16px; opacity: 0.5;">💬</div>
                    <div>Görüşme geçmişini görüntülemek için bir otel seçin.</div>
                 </div>
                 """, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Mail Dashboard Render Error: {e}", exc_info=True)
        st.error(f"Görünüm hatası: {e}")
    finally:
        db.close()

def render_top_navigation():
    """Üst navigasyon çubuğu - Figma tasarımına uygun"""
    try:
        current_page = st.session_state.current_page
    except Exception as e:
        logger.error(f"render_top_navigation hatası: {e}", exc_info=True)
        current_page = 'DASHBOARD'
    
    # Header - Sola hizalı
    st.markdown("""
    <div style="margin-bottom: 20px; text-align: left;">
        <div style="margin-bottom: 12px;">
            <h1 style="color: white; font-size: 24px; font-weight: 700; margin: 0 0 4px 0; text-align: left;">MergenLite</h1>
            <p style="color: var(--text-400); font-size: 14px; margin: 0; text-align: left;">SAM.gov Otomatik Teklif Analiz Platformu</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation Tabs
    pages = [
        {"icon": "🏠", "label": "Dashboard", "value": "DASHBOARD"},
        {"icon": "🔍", "label": "Fırsat Arama", "value": "OPPORTUNITY_CENTER"},
        {"icon": "🤖", "label": "AI Analiz", "value": "GUIDED_ANALYSIS"},
        {"icon": "📄", "label": "Sonuçlar", "value": "RESULTS"},
        {"icon": "📨", "label": "İletişim Merkezi", "value": "MAIL_DASHBOARD"}
    ]
    
    # Navigation bar - Sola hizalı ve optimize edilmiş
    st.markdown("""
    <div class="nav-bar-container" style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 8px; padding: 4px; margin-bottom: 24px; width: 100%; max-width: 100%;">
    """, unsafe_allow_html=True)
    
    # JavaScript - Sadece hover efektleri için
    if 'nav_js_loaded' not in st.session_state:
        st.session_state.nav_js_loaded = True
        st.markdown("""
        <script>
        (function() {
            if (window.navHoverSetup) return;
            window.navHoverSetup = true;
            
            function setupNavHover() {
                document.querySelectorAll('button[key^="nav_"]').forEach(function(btn) {
                    if (btn.dataset.hoverSetup === 'true') return;
                    btn.dataset.hoverSetup = 'true';
                    
                    const parent = btn.closest('[data-testid="column"]');
                    if (!parent) return;
                    const tab = parent.querySelector('.nav-tab, .nav-tab-clickable');
                    if (!tab) return;
                    
                    btn.addEventListener('mouseenter', function() {
                        if (!tab.classList.contains('nav-tab-active')) {
                            tab.style.background = 'rgba(59, 130, 246, 0.15)';
                            tab.style.color = 'rgb(96, 165, 250)';
                            tab.style.transform = 'translateY(-1px)';
                        }
                    });
                    
                    btn.addEventListener('mouseleave', function() {
                        if (!tab.classList.contains('nav-tab-active')) {
                            tab.style.background = 'transparent';
                            tab.style.color = 'rgb(156, 163, 175)';
                            tab.style.transform = 'translateY(0)';
                        }
                    });
                });
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupNavHover);
            } else {
                setupNavHover();
            }
            
            const observer = new MutationObserver(function() {
                setTimeout(setupNavHover, 100);
            });
            observer.observe(document.body, { childList: true, subtree: true });
        })();
        </script>
        """, unsafe_allow_html=True)
    
    # Tab container - Streamlit columns ile
    cols = st.columns(5)
    for idx, page in enumerate(pages):
        with cols[idx]:
            is_active = current_page == page['value']
            # Container div
            st.markdown(f"""
            <div style="position: relative; width: 100%; min-height: 48px;">
            """, unsafe_allow_html=True)
            
            if is_active:
                st.markdown(f"""
                <div class="nav-tab-active" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; gap: 6px; z-index: 1;">
                    <span>{page['icon']}</span>
                    <span>{page['label']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="nav-tab-clickable" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; gap: 6px; z-index: 1; pointer-events: none;">
                    <span>{page['icon']}</span>
                    <span>{page['label']}</span>
                </div>
                """, unsafe_allow_html=True)
                # Görünmez Streamlit butonu - tıklama için
                button_key = f"nav_{page['value']}"
                if st.button("", key=button_key, use_container_width=True):
                    st.session_state.current_page = page['value']
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main app function"""
    try:
        # Üst Navigasyon
        try:
            render_top_navigation()
        except Exception as nav_error:
            st.error(f"❌ Navigasyon hatası: {str(nav_error)}")
            logger.error(f"Navigasyon hatası: {nav_error}", exc_info=True)
            # Fallback: Basit navigasyon
            st.markdown("### Navigasyon")
            if st.button("Dashboard", key="nav_dash_fallback"):
                st.session_state.current_page = 'DASHBOARD'
                st.rerun()
            if st.button("Fırsat Arama", key="nav_search_fallback"):
                st.session_state.current_page = 'OPPORTUNITY_CENTER'
                st.rerun()
        
        # Sidebar'da sadece API Key durumu (gizli, gerektiğinde gösterilebilir)
        # API Key durumu kontrolü (gizli sidebar'da)
        try:
            sam = SAMIntegration()
            api_key_ok = bool(sam.api_key)
        except Exception:
            api_key_ok = False
        
        # Page routing
        try:
            if st.session_state.current_page == 'DASHBOARD':
                render_dashboard()
            elif st.session_state.current_page == 'OPPORTUNITY_CENTER':
                render_opportunity_center()
            elif st.session_state.current_page == 'GUIDED_ANALYSIS':
                if st.session_state.selected_opportunity:
                    try:
                        render_guided_analysis_page(st.session_state.selected_opportunity)
                    except Exception as e:
                        st.error(f"Analiz sayfası yüklenemedi: {str(e)}")
                        logger.error(f"Analiz sayfası hatası: {e}", exc_info=True)
                else:
                    st.warning("⚠️ Lütfen önce bir ilan seçin.")
                    if st.button("← İlan Merkezine Dön", key="analysis_back_btn"):
                        st.session_state.current_page = 'OPPORTUNITY_CENTER'
                        st.rerun()
            elif st.session_state.current_page == 'RESULTS':
                render_results_page()
            elif st.session_state.current_page == 'MAIL_DASHBOARD':
                render_mail_dashboard()
            else:
                render_dashboard()
        except Exception as page_error:
            st.error(f"❌ Sayfa render hatası: {str(page_error)}")
            logger.error(f"Sayfa render hatası: {page_error}", exc_info=True)
            st.exception(page_error)
            # Fallback: Basit dashboard
            st.markdown("### Dashboard")
    except Exception as e:
        st.error(f"❌ Sayfa yüklenirken hata oluştu: {str(e)}")
        logger.error(f"Main fonksiyonu hatası: {e}", exc_info=True)
        st.exception(e)

if __name__ == "__main__":
    main()
