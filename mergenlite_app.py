#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite - Sadeleştirilmiş İlan Analiz Platformu
Tek birleşik Streamlit uygulaması - Tüm özellikler tek dosyada
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
import requests

# Encoding fix for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

logger = logging.getLogger(__name__)

# .env dosyasını yükle (mergen klasöründen öncelikli) - Cache bypass
try:
    from dotenv import load_dotenv
    
    # Önce mergen klasöründeki .env dosyasını yükle (force reload)
    # Container içinde /app/mergen/.env veya /app/.env olabilir
    env_paths = [
        'mergen/.env',  # Root'tan çalıştırıldığında
        '/app/mergen/.env',  # Container içinde
        '.env',  # Root'ta
        '/app/.env'  # Container içinde root
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True, verbose=False)
            env_loaded = True
            logger.info(f"✅ .env dosyası yüklendi: {env_path}")
            break
    
    # Hiçbir dosya bulunamazsa, environment variable'lardan yükle (Docker Compose env_file)
    if not env_loaded:
        load_dotenv(override=True, verbose=False)
        # Environment variable'dan kontrol et
        if os.getenv('SAM_API_KEY'):
            logger.info("✅ SAM_API_KEY environment variable'dan yüklendi")
        else:
            logger.warning("⚠️ .env dosyası bulunamadı ve SAM_API_KEY environment variable'da yok")
except ImportError:
    pass
except Exception as e:
    logger.error(f"❌ .env yükleme hatası: {e}")

# MergenLite imports - Root'tan import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sam_integration import SAMIntegration
from document_processor import DocumentProcessor
from rag_service import RAGService
from llm_analyzer import LLMAnalyzer

# MergenLite veritabanı ve ajanlar
try:
    from mergenlite_models import Opportunity, ManualDocument, AIAnalysisResult, SystemSession, Base
    from mergenlite_agents import MergenLiteOrchestrator
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    MERGENLITE_DB_AVAILABLE = True
except ImportError as e:
    MERGENLITE_DB_AVAILABLE = False
    st.warning(f"⚠️ MergenLite veritabanı modülleri yüklenemedi: {e}")

# Configure page
st.set_page_config(
    page_title="MergenLite",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"  # Menüleri görmek için expanded
)

# Tema yükleme - theme_loader.py kullan
try:
    from theme_loader import load_css
    load_css("theme.css")
except (ImportError, FileNotFoundError):
    # Fallback: Eski inline CSS (theme.css bulunamazsa)
    st.warning("⚠️ theme.css bulunamadı, varsayılan tema kullanılıyor.")
    st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0b1220;
    }
    .main .block-container {
        background-color: #0b1220;
        color: #e5e7eb;
    }
    
    /* Typography */
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #e5e7eb;
        text-align: center;
        margin-bottom: 24px;
    }
    h1, h2, h3 {
        color: #e5e7eb;
    }
    p, div, small {
        color: #d1d5db;
        font-size: 14px;
    }
    
    /* Opportunity Cards - Compact & Modern */
    .opportunity-card {
        background: #131a2a;
        border: 1px solid #1f2a44;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .opportunity-card:hover {
        border-color: #7c3aed;
        box-shadow: 0 6px 20px rgba(124,58,237,0.15);
        transform: translateY(-2px);
    }
    .opportunity-card h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #e5e7eb;
    }
    .opportunity-card p {
        font-size: 13px;
        color: #9ca3af;
        margin: 4px 0;
        line-height: 1.5;
    }
    .opportunity-card p strong {
        color: #d1d5db;
        font-weight: 600;
    }

    /* Alert/Toast Components */
    .stAlert {
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        margin-bottom: 12px;
        border: 1px solid;
    }
    .st-emotion-cache-1wmy9hl { /* Success Alert */
        background: #0b2e26;
        border-color: #164e3f;
        color: #86efac;
    }
    .st-emotion-cache-ocqkz7 { /* Info Alert */
        background: #0b2030;
        border-color: #1b3a57;
        color: #7dd3fc;
    }
    .st-emotion-cache-l9i5vr { /* Warning Alert */
        background: #3d2817;
        border-color: #78350f;
        color: #fbbf24;
    }
    .st-emotion-cache-4z1n4g { /* Danger/Error Alert */
        background: #3d1a1a;
        border-color: #7f1d1d;
        color: #f87171;
    }

    /* Buttons */
    .stButton>button {
        background: #7c3aed;
        color: white;
        font-weight: 600;
        border: 1px solid #8b5cf6;
        border-radius: 6px;
        padding: 10px 16px;
        transition: all 0.2s ease;
        font-size: 14px;
        width: 100%;
    }
    .stButton>button:hover {
        background: #6d28d9;
        border-color: #7c3aed;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(124,58,237,0.3);
    }

    /* Form Elements */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        background-color: #131a2a;
        border: 1px solid #1f2a44;
        color: #e5e7eb;
        border-radius: 6px;
    }
    .stSlider>div>div>div {
        background-color: #131a2a;
    }

    /* Selected Opp Box */
    .selected-opp-box {
        background-color: #131a2a;
        border: 1px solid #1f2a44;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'DASHBOARD'  # DASHBOARD, OPPORTUNITY_CENTER, GUIDED_ANALYSIS

if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None

if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

if 'analysis_stage' not in st.session_state:
    st.session_state.analysis_stage = 1

if 'last_saved_count' not in st.session_state:
    st.session_state.last_saved_count = 0

if 'last_sync_at' not in st.session_state:
    st.session_state.last_sync_at = '-'

# Database connection helper
@st.cache_resource
def get_db_session():
    """Veritabanı bağlantısını al"""
    if not MERGENLITE_DB_AVAILABLE:
        return None
    
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        if db_host == 'db':
            db_host = 'localhost'
        
        DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{db_host}:{os.getenv('DB_PORT', '5432')}/mergenlite"
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return None

# ============================================================================
# DASHBOARD - Ana Dashboard
# ============================================================================

def render_dashboard():
    """Ana Dashboard - KPI'lar, hızlı aksiyonlar ve özet"""
    st.markdown('<h1 class="main-header">🚀 MergenLite - Dashboard</h1>', unsafe_allow_html=True)

    # KPI'lar
    total_cnt = len(st.session_state.get('opportunities', []) or [])
    saved_cnt = st.session_state.get('last_saved_count', 0) or 0
    last_sync = st.session_state.get('last_sync_at', '-')
    try:
        sam = SAMIntegration()
        api_key_ok = bool(sam.api_key)
    except Exception:
        api_key_ok = False

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card kpi-blue">
          <div style="font-size:12px;opacity:.8">Toplam Sonuç</div>
          <div style="font-size:28px;font-weight:700">{total_cnt}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-emerald">
          <div style="font-size:12px;opacity:.8">DB'ye Kaydedilen</div>
          <div style="font-size:28px;font-weight:700">{saved_cnt}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-orange">
          <div style="font-size:12px;opacity:.8">Son Senkron</div>
          <div style="font-size:20px;font-weight:700">{last_sync}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        badge = '<span class="badge badge-success">API Key OK</span>' if api_key_ok else '<span class="badge badge-danger">API Key Yok</span>'
        st.markdown(f"""
        <div class="kpi-card" style="background:rgba(17,24,39,.5)">
          <div style="font-size:12px;opacity:.8">SAM.gov</div>
          <div style="margin-top:6px;">{badge}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    left, right = st.columns([2, 3])
    with left:
        st.markdown("### 🤖 AI Ajan Durumu")
        st.markdown(
            """
            <div class="op-card">
              <div class="meta">Hazır ➜ İlan analizi, doküman indirme, teklif özeti</div>
              <div style="margin-top:8px">Öncelik: <span class="badge badge-info">721110 Hotels</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚡ Hızlı Başlangıç")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 721110 Senkronize Et", use_container_width=True, key="quick_sync_721110"):
                try:
                    api_url = os.getenv('PROXY_API_URL', 'http://localhost:8000')
                    resp = requests.get(
                        f"{api_url}/api/proxy/opportunities/search",
                        params={
                            'naics': '721110',
                            'days_back': 30,
                            'limit': 100,
                            'keyword': ''
                        },
                        timeout=30
                    )
                    if resp.ok:
                        data = resp.json()
                        st.session_state.opportunities = data.get('results', [])
                        st.session_state.last_saved_count = int(data.get('saved') or 0)
                        st.session_state.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        st.success(f"✅ Senkron tamam: {len(st.session_state.opportunities)} sonuç · Kaydedilen: {st.session_state.last_saved_count}")
                    else:
                        st.error(f"❌ Proxy hata: {resp.status_code}")
                except Exception as e:
                    st.error(f"❌ Hata: {e}")
        with col_b:
            if st.button("📋 İlan Merkezine Git", use_container_width=True, key="go_to_center"):
                st.session_state.current_page = 'OPPORTUNITY_CENTER'
                st.rerun()

    with right:
        st.markdown("### 📝 Son Aktiviteler")
        st.markdown(
            f"""
            <div class="op-card">
              <div class="meta">Son Senkron: <strong>{last_sync}</strong></div>
              <div class="meta">Toplam Sonuç: <strong>{total_cnt}</strong></div>
              <div class="meta">DB'ye Kaydedilen: <strong>{saved_cnt}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================================
# OPPORTUNITY CENTER - İlan Merkezi
# ============================================================================

def render_opportunity_center():
    """İlan Merkezi - Fırsatları listele ve analiz için seç"""
    
    st.markdown('<h1 class="main-header">🚀 MergenLite - İlan Merkezi</h1>', unsafe_allow_html=True)
    
    # Metrikler - Son arama istatistikleri
    if 'last_search_metrics' in st.session_state and st.session_state.last_search_metrics:
        metrics = st.session_state.last_search_metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Toplam Sonuç", metrics.get('total', 0))
        with col2:
            st.metric("Gösterilen", metrics.get('returned', 0))
        with col3:
            st.metric("DB'ye Kaydedilen", metrics.get('saved', 0))
        with col4:
            cache_label = "✅ Cache" if metrics.get('cache') == 'HIT' else "🌐 Canlı"
            st.metric("Kaynak", cache_label)
        st.markdown("---")
    
    # SAM API entegrasyonu
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv('.env', override=True)
        else:
            load_dotenv(override=True)
    except:
        pass
    
    sam = SAMIntegration()
    
    # API key durumu
    if not sam.api_key:
        st.error("⚠️ **API Key Yüklenemedi!** Lütfen `.env` dosyasında `SAM_API_KEY` değerini kontrol edin.")
    elif 'api_key_success_shown' not in st.session_state:
        st.success(f"✅ API Key yüklendi: {sam.api_key[:20]}...")
        st.session_state.api_key_success_shown = True
    
    # Akıllı ID arama
    st.markdown("### 🔎 İlan ID ile Direkt Arama")
    id_search = st.text_input(
        "Notice ID veya Opportunity ID",
        placeholder="W50S7526QA010",
        key="id_search"
    )
    
    if st.button("🔍 İlan ID ile Ara", key="search_by_id", use_container_width=True, type="primary"):
        if id_search:
            with st.spinner(f"ID {id_search} aranıyor..."):
                try:
                    opportunities = sam.search_by_any_id(id_search.strip())
                    
                    if opportunities:
                        st.session_state.opportunities = opportunities
                        st.success(f"✅ {len(opportunities)} fırsat bulundu!")
                    else:
                        st.error(f"❌ {id_search} bulunamadı.")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        else:
            st.warning("Lütfen bir ID girin.")
    
    st.markdown("---")
    
    # Genel arama
    st.markdown("### 📋 Genel Arama")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 İlan Ara", placeholder="Başlık veya anahtar kelime...", key="general_search")
    
    with col2:
        naics_code = st.text_input("NAICS Kodu", placeholder="721110", value="721110", key="naics_search")
    
    with col3:
        days_back = st.slider("Son Günler", 1, 90, 7, key="days_back")
    
    if st.button("🔍 Fırsatları Getir", use_container_width=True, type="primary", key="fetch_opportunities"):
        with st.spinner("Fırsatlar getiriliyor..."):
            try:
                opportunities = []
                saved_count = None
                total_count = None
                cache_status = None
                
                # Önce proxy/gateway üzerinden dene (DB kayıt + cache için)
                try:
                    api_url = os.getenv('PROXY_API_URL', 'http://localhost:8000')
                    resp = requests.get(
                        f"{api_url}/api/proxy/opportunities/search",
                        params={
                            'naics': naics_code or '721110',
                            'days_back': days_back or 30,
                            'limit': 100,
                            'keyword': (search_query or '').strip()
                        },
                        timeout=30
                    )
                    if resp.ok:
                        data = resp.json()
                        opportunities = data.get('results', [])
                        saved_count = data.get('saved', 0)
                        total_count = data.get('total', len(opportunities))
                        cache_status = resp.headers.get('X-Cache', 'MISS')
                        
                        # Başarı mesajı
                        if saved_count and saved_count > 0:
                            st.success(f"✅ {len(opportunities)} fırsat bulundu ({total_count} toplam) - {saved_count} kayıt DB'ye kaydedildi")
                        else:
                            st.success(f"✅ {len(opportunities)} fırsat bulundu ({total_count} toplam)")
                        
                        if cache_status == 'HIT':
                            st.info("📦 Cache'den yüklendi (Redis)")
                except Exception as api_error:
                    # Fallback: Direkt SAM client kullan
                    st.warning(f"⚠️ Proxy API kullanılamadı, direkt SAM client kullanılıyor: {str(api_error)[:50]}")
                    opportunities = sam.fetch_opportunities(
                        keywords=search_query if search_query else None,
                        naics_codes=[naics_code] if naics_code else None,
                        days_back=days_back,
                        limit=100
                    )
                    
                    if opportunities:
                        st.session_state.opportunities = opportunities
                        st.success(f"✅ {len(opportunities)} fırsat bulundu (direkt SAM)")
                    else:
                        st.warning("Fırsat bulunamadı.")
                
                if opportunities:
                    st.session_state.opportunities = opportunities
                    # Metrikleri session state'e kaydet
                    if saved_count is not None:
                        st.session_state.last_saved_count = int(saved_count)
                        st.session_state.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        st.session_state.last_search_metrics = {
                            'total': total_count or len(opportunities),
                            'returned': len(opportunities),
                            'saved': saved_count,
                            'cache': cache_status
                        }
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    
    # Fırsatları göster
    if 'opportunities' in st.session_state and st.session_state.opportunities:
        st.markdown("---")
        st.markdown("### 📋 Bulunan Fırsatlar")
        
        for i, opp in enumerate(st.session_state.opportunities):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    notice_id = opp.get('opportunityId', 'N/A')
                    title = opp.get('title', 'Başlık Yok')
                    org = opp.get('fullParentPathName', 'Organizasyon Yok')
                    posted_date = opp.get('postedDate', 'N/A')
                    deadline = opp.get('responseDeadLine', 'N/A')
                    
                    st.markdown(f"""
                    <div class="opportunity-card" id="card-{i}">
                        <h3>{title}</h3>
                        <p><strong>Notice ID:</strong> {notice_id} · <strong>Organizasyon:</strong> {org}</p>
                        <p>
                            <strong>Yayın Tarihi:</strong> {posted_date} · <strong>Son Teslim:</strong> {deadline}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📊 Analiz Et", key=f"analyze_{i}", use_container_width=True):
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.rerun()
    

# ============================================================================
# GUIDED ANALYSIS - Rehberli Analiz (4 Aşamalı)
# ============================================================================

def render_guided_analysis_page(opportunity: Dict[str, Any]):
    """Rehberli analiz sayfası - 4 aşamalı workflow"""
    
    st.markdown('<h1 class="main-header">📊 Rehberli Analiz - İlan Analizi</h1>', unsafe_allow_html=True)
    
    notice_id = opportunity.get('opportunityId', 'N/A')
    title = opportunity.get('title', 'Başlık Yok')
    
    st.markdown(f"""
    <div class="selected-opp-box">
        <h3>📋 Seçilen İlan</h3>
        <p><strong>Notice ID:</strong> {notice_id}</p>
        <p><strong>Başlık:</strong> {title}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 4 Aşamalı Workflow
    stages = {
        1: "📥 Aşama 1: Veri Çekme",
        2: "📄 Aşama 2: Doküman İşleme",
        3: "🤖 Aşama 3: RAG Muhakemesi",
        4: "📊 Aşama 4: Final Rapor"
    }
    
    progress = st.session_state.analysis_stage / 4
    st.progress(progress, text=f"{stages[st.session_state.analysis_stage]}")
    
    # Aşama 1: Metadata
    if st.session_state.analysis_stage >= 1:
        render_stage_1_metadata(opportunity)
    
    # Aşama 2: Doküman İşleme
    if st.session_state.analysis_stage >= 2:
        render_stage_2_document_processing(opportunity)
    
    # Aşama 3: RAG Muhakemesi
    if st.session_state.analysis_stage >= 3:
        render_stage_3_rag_reasoning(opportunity)
    
    # Aşama 4: Final Rapor
    if st.session_state.analysis_stage >= 4:
        render_stage_4_final_report(opportunity)

def render_stage_1_metadata(opportunity: Dict[str, Any]):
    """Aşama 1: Metadata ve Doküman İndirme"""
    
    st.markdown("---")
    
    with st.expander("📥 Aşama 1: Veri Çekme - Metadata ve Doküman İndirme", expanded=True):
        notice_id = opportunity.get('opportunityId', 'N/A')
        
        if st.button("🚀 Verileri Çek", key="fetch_metadata", use_container_width=True):
            with st.spinner("Metadata çekiliyor..."):
                try:
                    sam = SAMIntegration()
                    metadata_result = sam.get_opportunity_details(notice_id)
                    
                    if metadata_result.get('success'):
                        st.session_state.analysis_data['metadata'] = metadata_result.get('data', {})
                        st.session_state.analysis_data['notice_id'] = notice_id
                        
                        metadata = metadata_result.get('data', {})
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Notice ID", metadata.get('noticeId', notice_id))
                            st.metric("Son Teslim", metadata.get('responseDeadLine', 'N/A'))
                        with col2:
                            st.metric("Organizasyon", metadata.get('organization', 'N/A'))
                            st.metric("NAICS", metadata.get('naicsCode', 'N/A'))
                        
                        st.success("✅ Metadata başarıyla çekildi!")
                        
                        if st.button("➡️ Aşama 2'ye Geç", key="next_stage_2"):
                            st.session_state.analysis_stage = 2
                            st.rerun()
                    else:
                        st.error(f"❌ Hata: {metadata_result.get('error', 'Bilinmeyen hata')}")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        if 'metadata' in st.session_state.analysis_data:
            st.info("✅ Metadata zaten çekilmiş.")
            if st.button("➡️ Aşama 2'ye Geç", key="next_stage_2_alt"):
                st.session_state.analysis_stage = 2
                st.rerun()

def render_stage_2_document_processing(opportunity: Dict[str, Any]):
    """Aşama 2: Doküman İşleme"""
    
    st.markdown("---")
    
    with st.expander("📄 Aşama 2: Doküman İşleme", expanded=True):
        if 'metadata' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 1'i tamamlayın.")
            return
        
        uploaded_file = st.file_uploader("📁 Dosya Yükle (PDF, DOCX)", type=['pdf', 'docx', 'doc'])
        
        if uploaded_file and st.button("📊 Dosyayı İşle", key="process_uploaded"):
            with st.spinner("Dosya işleniyor..."):
                try:
                    processor = DocumentProcessor()
                    result = processor.process_uploaded_file(uploaded_file)
                    
                    if result.get('success'):
                        st.session_state.analysis_data['documents'] = [result.get('data', {})]
                        st.success("✅ Dosya başarıyla işlendi!")
                        
                        if st.button("➡️ Aşama 3'e Geç", key="next_stage_3"):
                            st.session_state.analysis_stage = 3
                            st.rerun()
                    else:
                        st.error(f"❌ Hata: {result.get('error', 'Bilinmeyen hata')}")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        if 'documents' in st.session_state.analysis_data:
            st.info("✅ Dokümanlar zaten işlenmiş.")
            if st.button("➡️ Aşama 3'e Geç", key="next_stage_3_alt"):
                st.session_state.analysis_stage = 3
                st.rerun()

def render_stage_3_rag_reasoning(opportunity: Dict[str, Any]):
    """Aşama 3: RAG Muhakemesi"""
    
    st.markdown("---")
    
    with st.expander("🤖 Aşama 3: RAG Muhakemesi", expanded=True):
        if 'documents' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 2'yi tamamlayın.")
            return
        
        if st.button("🧠 RAG Analizi Başlat", key="start_rag", use_container_width=True):
            with st.spinner("RAG analizi yapılıyor..."):
                try:
                    rag_service = RAGService()
                    llm_analyzer = LLMAnalyzer()
                    
                    documents = st.session_state.analysis_data['documents']
                    combined_text = "\n\n".join([doc.get('text', '') for doc in documents])
                    
                    rag_results = rag_service.retrieve_relevant_context(combined_text)
                    analysis_result = llm_analyzer.extract_requirements(combined_text, rag_results)
                    
                    st.session_state.analysis_data['rag_analysis'] = analysis_result
                    st.success("✅ RAG analizi tamamlandı!")
                    
                    if analysis_result.get('success'):
                        requirements = analysis_result.get('data', {}).get('requirements', {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Oda Sayısı", requirements.get('room_count', 'N/A'))
                        with col2:
                            st.metric("AV Gereksinimleri", "✅ Var" if requirements.get('av_required', False) else "❌ Yok")
                        with col3:
                            st.metric("Kısıtlar", len(requirements.get('constraints', [])))
                        
                        if st.button("➡️ Aşama 4'e Geç", key="next_stage_4"):
                            st.session_state.analysis_stage = 4
                            st.rerun()
                    else:
                        st.error(f"❌ Analiz hatası: {analysis_result.get('error', 'Bilinmeyen hata')}")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        if 'rag_analysis' in st.session_state.analysis_data:
            st.info("✅ RAG analizi zaten tamamlanmış.")
            if st.button("➡️ Aşama 4'e Geç", key="next_stage_4_alt"):
                st.session_state.analysis_stage = 4
                st.rerun()

def render_stage_4_final_report(opportunity: Dict[str, Any]):
    """Aşama 4: Final Rapor"""
    
    st.markdown("---")
    
    with st.expander("📊 Aşama 4: Final Rapor", expanded=True):
        if 'rag_analysis' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 3'ü tamamlayın.")
            return
        
        # MergenLite Orchestrator ile analiz
        if st.button("🚀 MergenLite Analizi Başlat", key="start_mergenlite_analysis", use_container_width=True):
            with st.spinner("MergenLite analizi yapılıyor..."):
                try:
                    if MERGENLITE_DB_AVAILABLE:
                        orchestrator = MergenLiteOrchestrator()
                        
                        # Doküman yollarını hazırla
                        documents = st.session_state.analysis_data.get('documents', [])
                        document_paths = [doc.get('file_path', '') for doc in documents if doc.get('file_path')]
                        
                        if not document_paths:
                            st.warning("⚠️ İşlenmiş doküman bulunamadı.")
                            document_paths = []
                        
                        # Tam analiz çalıştır
                        analysis_result = orchestrator.run_full_analysis(
                            opportunity_id=opportunity.get('opportunityId', 'N/A'),
                            document_paths=document_paths
                        )
                        
                        # Veritabanına kaydet
                        db_session = get_db_session()
                        if db_session:
                            try:
                                # Opportunity kaydet
                                opp = Opportunity(
                                    opportunity_id=opportunity.get('opportunityId', 'N/A'),
                                    title=opportunity.get('title', 'N/A'),
                                    notice_type=opportunity.get('noticeType', 'N/A'),
                                    naics_code=opportunity.get('naicsCode', 'N/A'),
                                    response_deadline=datetime.fromisoformat(opportunity.get('responseDeadLine', '2024-01-01')) if opportunity.get('responseDeadLine') else None,
                                    raw_data=opportunity
                                )
                                db_session.merge(opp)
                                
                                # Analysis result kaydet
                                ai_result = AIAnalysisResult(
                                    opportunity_id=opp.opportunity_id,
                                    analysis_status=analysis_result.get('analysis_status', 'COMPLETED'),
                                    consolidated_output=analysis_result.get('consolidated_output', {}),
                                    end_time=datetime.now()
                                )
                                db_session.add(ai_result)
                                db_session.commit()
                                
                                st.success("✅ Analiz tamamlandı ve veritabanına kaydedildi!")
                            except Exception as e:
                                st.error(f"❌ Veritabanı kayıt hatası: {e}")
                                db_session.rollback()
                        
                        st.session_state.analysis_data['mergenlite_analysis'] = analysis_result
                    else:
                        st.warning("⚠️ MergenLite veritabanı kullanılamıyor.")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        # Raporu göster
        if 'mergenlite_analysis' in st.session_state.analysis_data:
            analysis = st.session_state.analysis_data['mergenlite_analysis']
            
            st.markdown("## 📊 MergenLite Analiz Raporu")
            
            consolidated = analysis.get('consolidated_output', {})
            
            st.json(consolidated)
            
            # İndirme butonu
            report_json = json.dumps(analysis, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Raporu İndir (JSON)",
                data=report_json,
                file_name=f"mergenlite_analysis_{opportunity.get('opportunityId', 'report')}.json",
                mime="application/json"
            )

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Ana uygulama fonksiyonu"""
    
    # Sidebar Navigation (menüler için)
    with st.sidebar:
        st.markdown("## 🚀 MergenLite")
        st.markdown("---")
        
        # Sayfa seçimi
        page_options = {
            "🏠 Dashboard": "DASHBOARD",
            "📋 İlan Merkezi": "OPPORTUNITY_CENTER",
            "🧭 Rehberli Analiz": "GUIDED_ANALYSIS"
        }

        labels = list(page_options.keys())
        values = list(page_options.values())
        current_val = st.session_state.current_page
        try:
            current_index = values.index(current_val)
        except ValueError:
            current_index = 0

        selected_page = st.radio(
            "Sayfa Seçin",
            options=labels,
            index=current_index,
            key="sidebar_page_select"
        )
        
        # Sayfa değişikliğini uygula
        if page_options[selected_page] != st.session_state.current_page:
            st.session_state.current_page = page_options[selected_page]
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ⚙️ Sistem Durumu")
        
        # API Key durumu
        try:
            sam = SAMIntegration()
            if sam.api_key:
                st.success(f"✅ API Key: {sam.api_key[:20]}...")
            else:
                st.error("❌ API Key bulunamadı")
                st.info("💡 `.env` dosyasında `SAM_API_KEY` tanımlı olmalı")
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
    
    # Sayfa yönlendirmesi
    if st.session_state.current_page == 'DASHBOARD':
        render_dashboard()
    elif st.session_state.current_page == 'OPPORTUNITY_CENTER':
        render_opportunity_center()
    elif st.session_state.current_page == 'GUIDED_ANALYSIS':
        if st.session_state.selected_opportunity:
            render_guided_analysis_page(st.session_state.selected_opportunity)
        else:
            st.warning("⚠️ Lütfen önce bir ilan seçin.")
            if st.button("← İlan Merkezine Dön", use_container_width=True):
                st.session_state.current_page = 'OPPORTUNITY_CENTER'
                st.rerun()
    else:
        render_dashboard()
    
    # Global Debug Panel (opportunity results present)
    try:
        if 'opportunities' in st.session_state and st.session_state.opportunities:
            st.markdown("---")
            show_dbg_footer = st.checkbox("🔎 Debug: Parametreleri ve sayıları göster", value=False, key="debug_toggle_footer")
            if show_dbg_footer:
                gs = (st.session_state.get('general_search') or '').strip()
                ns = (st.session_state.get('naics_search') or '721110').strip()
                db_val = st.session_state.get('days_back') or 7
                eff_naics = ns or '721110'
                eff_keyword = gs or eff_naics
                eff_limit = 100
                eff_is_active = True
                eff_dates = None
                if isinstance(db_val, int) and db_val >= 60:
                    from datetime import datetime, timedelta
                    eff_dates = {
                        "postedFrom": (datetime.now() - timedelta(days=db_val)).strftime('%m/%d/%Y'),
                        "postedTo": datetime.now().strftime('%m/%d/%Y')
                    }

                src_counts = {}
                for opp in st.session_state.opportunities:
                    src = opp.get('source') or 'sam_live'
                    src_counts[src] = src_counts.get(src, 0) + 1

                dbg = {
                    "effective_params": {
                        "naicsCodes": eff_naics,
                        "keyword": eff_keyword,
                        "keywordRadio": "ALL",
                        "limit": eff_limit,
                        "is_active": eff_is_active,
                        **({} if not eff_dates else eff_dates)
                    },
                    "result_stats": {
                        "total_returned": len(st.session_state.opportunities),
                        "by_source": src_counts
                    }
                }
                st.markdown("#### Debug Bilgisi")
                st.json(dbg)
    except Exception:
        pass

    # Geri dön butonu
    if st.session_state.current_page == 'GUIDED_ANALYSIS':
        st.markdown("---")
        if st.button("← İlan Merkezine Dön", use_container_width=True):
            st.session_state.current_page = 'OPPORTUNITY_CENTER'
            st.session_state.selected_opportunity = None
            st.session_state.analysis_stage = 1
            st.session_state.analysis_data = {}
            st.rerun()

if __name__ == "__main__":
    main()
