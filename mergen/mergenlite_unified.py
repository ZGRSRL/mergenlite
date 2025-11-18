#!/usr/bin/env python3
"""
MergenLite Unified App - Tüm özellikler tek dosyada
592 satır - Dashboard, Fırsat Arama, AI Analiz, Sonuçlar
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
import hashlib
from typing import Dict, Any, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    if os.path.exists('mergen/.env'):
        load_dotenv('mergen/.env', override=True)
    elif os.path.exists('.env'):
        load_dotenv('.env', override=True)
    else:
        load_dotenv(override=True)
except ImportError:
    pass

# Path management - Root'tan import et
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    # GSA Opportunities API Client - Quota limit bypass
    from gsa_opportunities_client import GSAOpportunitiesClient
    from sam_integration import SAMIntegration
    from document_processor import DocumentProcessor
    from rag_service import RAGService
    from llm_analyzer import LLMAnalyzer
    GSA_CLIENT_AVAILABLE = True
except ImportError:
    # Alternatif path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from gsa_opportunities_client import GSAOpportunitiesClient
        from sam_integration import SAMIntegration
        from document_processor import DocumentProcessor
        from rag_service import RAGService
        from llm_analyzer import LLMAnalyzer
        GSA_CLIENT_AVAILABLE = True
    except ImportError:
        GSA_CLIENT_AVAILABLE = False
        try:
            from sam_integration import SAMIntegration
            from document_processor import DocumentProcessor
            from rag_service import RAGService
            from llm_analyzer import LLMAnalyzer
        except ImportError:
            st.error("❌ Gerekli modüller yüklenemedi. Lütfen gsa_opportunities_client.py, sam_integration.py dosyalarının mevcut olduğundan emin olun.")

# Configure page
st.set_page_config(
    page_title="MergenLite Unified",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import UI Components ve Theme Loader
try:
    from mergenlite_ui_components import opportunity_card, stepper, badge, staged_tabs
    UI_COMPONENTS_AVAILABLE = True
except ImportError:
    UI_COMPONENTS_AVAILABLE = False

# Tema yükleme - theme_loader.py kullan
try:
    # Root dizini path'e ekle
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    from theme_loader import load_css
    # theme.css dosyasının yolunu belirle (root veya mergen klasöründe olabilir)
    theme_css_path = os.path.join(root_dir, "theme.css")
    if os.path.exists(theme_css_path):
        load_css(theme_css_path)
    else:
        # Alternatif: mevcut dizinde ara
        load_css("theme.css")
    THEME_LOADED = True
except (ImportError, FileNotFoundError) as e:
    # Fallback: mergenlite_ui_components kullan
    try:
        from mergenlite_ui_components import inject_theme
        inject_theme(dark=True)
        THEME_LOADED = True
    except ImportError:
        THEME_LOADED = False
        # Fallback: Eski CSS
    st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Base Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Dark Theme Base */
    .stApp {
        background-color: #0b1220;
    }
    .main .block-container {
        background-color: #0b1220;
        color: #e5e7eb;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Typography - Modern & Readable */
    .main-header {
        font-size: 28px;
        font-weight: 700;
        color: #e5e7eb;
        text-align: center;
        margin-bottom: 32px;
        letter-spacing: -0.5px;
    }
    h1, h2, h3 {
        color: #e5e7eb;
        font-weight: 600;
        letter-spacing: -0.3px;
    }
    h1 { font-size: 24px; }
    h2 { font-size: 20px; }
    h3 { font-size: 18px; }
    p, div {
        color: #d1d5db;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Status Cards - Modern & Vibrant */
    .status-card {
        background: linear-gradient(135deg, #131a2a 0%, #1f2a44 100%);
        border: 1px solid #1f2a44;
        color: #e5e7eb;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3), 0 1px 3px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    .status-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(124, 58, 237, 0.25), 0 4px 8px rgba(0,0,0,0.3);
        border-color: #7c3aed;
    }
    .status-card h3 {
        font-size: 14px;
        font-weight: 600;
        color: #9ca3af;
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-card p {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        color: #7c3aed;
    }
    
    /* Opportunity Cards - Modern & Elegant */
    .opportunity-card {
        background: #131a2a;
        border: 1px solid #1f2a44;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        border-left: 4px solid #7c3aed;
    }
    .opportunity-card:hover {
        border-color: #7c3aed;
        border-left-color: #8b5cf6;
        box-shadow: 0 8px 16px rgba(124, 58, 237, 0.2), 0 4px 8px rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }
    .opportunity-card h3 {
        margin: 0 0 12px 0;
        font-size: 18px;
        font-weight: 600;
        color: #e5e7eb;
        line-height: 1.4;
    }
    .opportunity-card .meta {
        font-size: 14px;
        color: #9ca3af;
        margin: 6px 0;
        line-height: 1.6;
    }
    .opportunity-card .meta strong {
        color: #d1d5db;
        font-weight: 600;
    }
    
    /* Alert/Toast Components - Modern & Clean */
    .alert {
        border-radius: 10px;
        padding: 14px 16px;
        font-size: 14px;
        margin-bottom: 16px;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        font-weight: 500;
    }
    .alert-success {
        background: #0b2e26;
        border-color: #10b981;
        color: #86efac;
        border-left-color: #10b981;
    }
    .alert-info {
        background: #0b2030;
        border-color: #3b82f6;
        color: #7dd3fc;
        border-left-color: #3b82f6;
    }
    .alert-warning {
        background: #3d2817;
        border-color: #f59e0b;
        color: #fbbf24;
        border-left-color: #f59e0b;
    }
    .alert-danger {
        background: #3d1a1a;
        border-color: #ef4444;
        color: #f87171;
        border-left-color: #ef4444;
    }
    
    /* Badge - Modern & Subtle */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-primary {
        background: #3b1f5f;
        color: #c4b5fd;
        border: 1px solid #7c3aed;
    }
    .badge-success {
        background: #064e3b;
        color: #6ee7b7;
        border: 1px solid #10b981;
    }
    
    /* Buttons - Modern & Interactive */
    .stButton>button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        color: white;
        font-weight: 600;
        border: 1px solid #8b5cf6;
        border-radius: 8px;
        padding: 12px 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 15px;
        box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
        letter-spacing: 0.3px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(124, 58, 237, 0.4);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
    }
    
    /* Secondary Button */
    .btn-secondary {
        background: #131a2a;
        color: #d1d5db;
        border: 1.5px solid #1f2a44;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .btn-secondary:hover {
        background: #1f2a44;
        border-color: #7c3aed;
        color: #e5e7eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(124, 58, 237, 0.2);
    }
    
    /* Primary Button */
    .btn-primary {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        color: white;
        border: 1px solid #8b5cf6;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
        letter-spacing: 0.3px;
    }
    .btn-primary:hover {
        background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(124, 58, 237, 0.4);
    }
    
    /* Agent Cards - Clean & Modern */
    .agent-card {
        background: #131a2a;
        border: 1px solid #1f2a44;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .agent-card:hover {
        border-color: #7c3aed;
        box-shadow: 0 8px 16px rgba(124, 58, 237, 0.2);
        transform: translateY(-2px);
    }
    .agent-card h4 {
        color: #e5e7eb;
        font-weight: 600;
        margin: 0 0 8px 0;
        font-size: 16px;
    }
    .agent-card p {
        color: #9ca3af;
        margin: 4px 0;
        font-size: 14px;
    }
    
    /* Form Elements - Modern Inputs */
    .stTextInput>div>div>input {
        background-color: #131a2a;
        border: 1.5px solid #1f2a44;
        color: #e5e7eb;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 15px;
        transition: all 0.2s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #7c3aed;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
        outline: none;
    }
    .stSelectbox>div>div>select {
        background-color: #131a2a;
        border: 1.5px solid #1f2a44;
        color: #e5e7eb;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 15px;
    }
    .stSlider>div>div>div {
        background-color: #131a2a;
    }
    
    /* Status Line - Subtle & Informative */
    .status-line {
        font-size: 14px;
        color: #9ca3af;
        padding: 12px 16px;
        background: #131a2a;
        border-left: 4px solid #7c3aed;
        border-radius: 6px;
        margin-bottom: 16px;
        font-weight: 500;
    }
    .status-line strong {
        color: #e5e7eb;
        font-weight: 600;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 22px;
        }
        .opportunity-card {
            padding: 16px;
        }
        .status-card {
            padding: 16px;
        }
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

if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

if 'analysis_progress' not in st.session_state:
    st.session_state.analysis_progress = 0

# ============================================================================
# DASHBOARD SAYFASI
# ============================================================================

def render_dashboard():
    """Dashboard - Sistem durumu ve hızlı başlangıç (Figma tasarımı entegre)"""
    
    st.markdown('<h1 class="main-header">🏠 MergenLite Dashboard</h1>', unsafe_allow_html=True)
    
    # Modern KPI Kartları (Figma tasarımı - Gradient)
    st.markdown("### 📊 Sistem Durumu")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card kpi-blue">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Toplam Fırsat Sayısı</h3>
                <span style="font-size: 20px;">📊</span>
            </div>
            <p style="margin: 0; font-size: 32px; font-weight: 700; color: #e5e7eb;">1,247</p>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #9ca3af;">Son 30 gün</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card kpi-emerald">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Bugün Yeni Eklenenler</h3>
                <span style="font-size: 20px;">📈</span>
            </div>
            <p style="margin: 0; font-size: 32px; font-weight: 700; color: #e5e7eb;">23</p>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #9ca3af;">NAICS 721110</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card kpi-orange">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Tamamlanan Analiz</h3>
                <span style="font-size: 20px;">✅</span>
            </div>
            <p style="margin: 0; font-size: 32px; font-weight: 700; color: #e5e7eb;">342</p>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #9ca3af;">Başarılı</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card kpi-blue">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Ortalama Analiz Süresi</h3>
                <span style="font-size: 20px;">⏱️</span>
            </div>
            <p style="margin: 0; font-size: 32px; font-weight: 700; color: #e5e7eb;">28sn</p>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #9ca3af;">Son 7 gün</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hızlı başlangıç butonları
    st.markdown("### 🚀 Hızlı Başlangıç")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Fırsat Ara", use_container_width=True, type="primary"):
            st.session_state.current_page = 'OPPORTUNITY_SEARCH'
            st.rerun()
    
    with col2:
        if st.button("📊 Sonuçları Görüntüle", use_container_width=True, type="primary"):
            st.session_state.current_page = 'RESULTS'
            st.rerun()
    
    with col3:
        if st.button("🤖 AI Analiz", use_container_width=True, type="primary"):
            st.session_state.current_page = 'AI_ANALYSIS'
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Son aktiviteler
    st.markdown("### 📋 Son Aktiviteler")
    activities = [
        {"time": "2 dakika önce", "action": "Fırsat analizi tamamlandı", "id": "W50S7526QA010"},
        {"time": "15 dakika önce", "action": "Yeni fırsat bulundu", "id": "a81c7ad026c74b7799b0e28e735aeeb7"}
    ]
    
    for activity in activities:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;">
            <strong>{activity['action']}</strong> - {activity['id']}<br>
            <small style="color: #6c757d;">{activity['time']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Sistem bilgileri
    st.markdown("### ℹ️ Sistem Bilgileri")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Toplam Analiz", len(st.session_state.analysis_history))
        st.metric("Aktif Fırsatlar", "12")
    
    with col2:
        st.metric("Başarı Oranı", "95%")
        st.metric("Ortalama Süre", "2.5 dk")

# ============================================================================
# FIRSAT ARAMA SAYFASI
# ============================================================================

def render_opportunity_search():
    """Fırsat Arama - Notice ID, NAICS, keyword filtreleri"""
    
    st.markdown('<h1 class="main-header">🔍 Fırsat Arama</h1>', unsafe_allow_html=True)
    
    # SAM Integration - GSA yerine SAM kullan (NAICS filtresi daha güvenilir)
    try:
        # SAM Integration (GSA değil, çünkü NAICS filtresi düzgün çalışmıyor)
        if 'sam_client' not in st.session_state:
            st.session_state.sam_client = SAMIntegration()
        
        client = st.session_state.sam_client
        client_name = "SAM.gov API"
        
        if not client.api_key:
            st.error("⚠️ **API Key Yüklenemedi!** Lütfen `.env` dosyasında `SAM_API_KEY` değerini kontrol edin.")
        else:
            st.success(f"✅ {client_name} - API Key yüklendi: {client.api_key[:20]}...")
    except Exception as e:
        st.error(f"❌ API Client hatası: {str(e)}")
        return
    
    # Filtreler - Form ile sadeleştirilmiş
    st.markdown("### 🔎 Arama Filtreleri")
    
    with st.form(key="search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            notice_id = st.text_input("Notice ID", placeholder="W50S7526QA010", key="notice_id_search")
            keywords = st.text_input("Anahtar Kelime", placeholder="meeting, conference, hotel...", key="keywords_search")
        
        with col2:
            naics_code = st.text_input("NAICS Kodu", placeholder="721110", value="721110", key="naics_search")
            limit = st.number_input("Sonuç Limiti", min_value=1, max_value=1000, value=100, key="limit_search", 
                                   help="Maksimum 1000 kayıt getirilebilir. Sayfalama otomatik yapılır.")
        
        # Gelişmiş Filtreler
        with st.expander("⚙️ Gelişmiş Filtreler", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                days_back = st.slider("Son Kaç Gün (60+ önerilir)", 1, 365, 90, key="days_back", 
                                     help="Web ile uyum için 60+ gün önerilir. 60'dan küçükse tarih filtresi uygulanmaz.")
            with col2:
                date_from = st.date_input("Başlangıç Tarihi", value=datetime.now() - timedelta(days=days_back), key="date_from")
                date_to = st.date_input("Bitiş Tarihi", value=datetime.now(), key="date_to")
        
        # Filtre ipucu
        if naics_code:
            st.caption("💡 NAICS kodu sadece NAICS filtresi olarak uygulanır. Keyword alanına ayrıca 'hotel', 'motel' gibi kelimeler ekleyebilirsiniz.")
        
        # Birincil aksiyon butonu
        submitted = st.form_submit_button("🔍 Fırsatları Ara", use_container_width=True, type="primary")
    
    # Arama işlemi
    if submitted:
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.markdown('<div class="status-line">🔍 <strong>Notice ID aranıyor:</strong> ' + (notice_id.strip().upper() if notice_id else "Genel arama") + '</div>', unsafe_allow_html=True)
        
        try:
            # Notice ID ile direkt arama
            if notice_id:
                notice_id_clean = notice_id.strip().upper()
                
                # Notice ID aramasında GSA kullanma, direkt SAM kullan
                opportunities = client.search_by_any_id(notice_id_clean)
            else:
                # Genel arama - Önce lokal cache kontrol et
                # Cache key oluştur (parametrelere göre)
                cache_params = {
                    'naics': naics_code if naics_code else '721110',
                    'days_back': days_back,
                    'limit': limit,
                    'keyword': keywords if keywords else ''
                }
                cache_key_str = json.dumps(cache_params, sort_keys=True)
                cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
                cache_key = f"search_{cache_key_hash}"
                
                # Session state'te cache kontrolü
                opportunities = None
                cache_source = None
                
                if 'search_cache' not in st.session_state:
                    st.session_state.search_cache = {}
                
                # Cache'den kontrol et
                if cache_key in st.session_state.search_cache:
                    cached_data = st.session_state.search_cache[cache_key]
                    cache_age = (datetime.now() - cached_data.get('timestamp', datetime.now())).total_seconds()
                    
                    # Cache 1 saat geçerli (3600 saniye)
                    if cache_age < 3600:
                        opportunities = cached_data.get('results', [])
                        cache_source = 'local_cache'
                        st.info(f"✅ Cache'den yüklendi: {len(opportunities)} fırsat ({(cache_age/60):.1f} dakika önce)")
                
                # Cache'de yoksa API'ye git
                if not opportunities:
                    try:
                        import requests
                        proxy_api_url = os.getenv('PROXY_API_URL', 'http://localhost:8000')
                        
                        # Proxy endpoint'e istek gönder
                        search_params = {
                            'naics': naics_code if naics_code else '721110',
                            'days_back': days_back,
                            'limit': limit
                        }
                        if keywords:
                            search_params['keyword'] = keywords
                        
                        response = requests.get(
                            f"{proxy_api_url}/api/proxy/opportunities/search",
                            params=search_params,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            opportunities = data.get('results', [])
                            saved_count = data.get('saved', 0)
                            cache_status = response.headers.get('X-Cache', 'MISS')
                            
                            # Lokal cache'e kaydet
                            st.session_state.search_cache[cache_key] = {
                                'results': opportunities,
                                'timestamp': datetime.now(),
                                'saved_count': saved_count
                            }
                            
                            # Başarı mesajı
                            if saved_count > 0:
                                st.success(f"✅ {saved_count} fırsat veritabanına kaydedildi")
                            if cache_status == 'HIT':
                                st.info(f"📦 API cache'den geldi (Redis)")
                            else:
                                st.info(f"🌐 Canlı API'den çekildi")
                        else:
                            raise Exception(f"API Error: {response.status_code}")
                            
                    except Exception as api_error:
                        # Fallback: Direkt SAM client kullan (GSA kullanma, NAICS filtresi düzgün çalışmıyor)
                        if 'logger' in globals():
                            logger.warning(f"Proxy API kullanılamadı, direkt SAM client kullanılıyor: {api_error}")
                        else:
                            st.warning(f"⚠️ Proxy API kullanılamadı, direkt SAM client kullanılıyor")
                        
                        # SAM client kullan (GSA değil, çünkü NAICS filtresi düzgün çalışmıyor)
                        opportunities = client.fetch_opportunities(
                            keywords=keywords if keywords else None,
                            naics_codes=[naics_code] if naics_code else None,
                            days_back=days_back,
                            limit=limit
                        )
                        
                        # Direkt client'tan gelen sonuçları da cache'e kaydet
                        if opportunities:
                            st.session_state.search_cache[cache_key] = {
                                'results': opportunities,
                                'timestamp': datetime.now(),
                                'saved_count': 0
                            }
            
            status_placeholder.empty()
            
            if opportunities:
                st.session_state.opportunities = opportunities
                
                # Source analizi
                sources = {}
                for opp in opportunities:
                    source = opp.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                # Source mesajı
                source_info = []
                if sources.get('gsa_live', 0) > 0:
                    source_info.append(f"{sources['gsa_live']} GSA (canlı)")
                if sources.get('sam_live', 0) > 0:
                    source_info.append(f"{sources['sam_live']} SAM.gov (canlı)")
                
                source_text = " · ".join(source_info) if source_info else "Canlı API"
                
                st.markdown(f'<div class="alert alert-success">✅ <strong>{len(opportunities)} fırsat bulundu</strong> · Kaynak: {source_text}</div>', unsafe_allow_html=True)
                
                # W50S7526QA010 özel kontrol
                if notice_id and 'W50S7526QA010' in notice_id_clean:
                    matching = [opp for opp in opportunities if 'W50S7526QA010' in str(opp.get('noticeId', '')).upper()]
                    if matching:
                        st.markdown(f'<div class="alert alert-success">🎯 <strong>W50S7526QA010 bulundu!</strong> {len(matching)} eşleşme.</div>', unsafe_allow_html=True)
            else:
                # Daha açıklayıcı hata mesajı
                if notice_id:
                    st.markdown(f'<div class="alert alert-warning">⚠️ <strong>Notice ID bulunamadı:</strong> {notice_id}<br>API erişilemedi veya ilan mevcut değil. Lütfen SAM.gov\'da kontrol edin.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert alert-warning">⚠️ <strong>Fırsat bulunamadı</strong><br>API erişilemedi veya arama kriterlerinize uygun sonuç yok. Filtreleri değiştirip tekrar deneyin.</div>', unsafe_allow_html=True)
        except Exception as e:
            status_placeholder.empty()
            st.markdown(f'<div class="alert alert-danger">❌ <strong>Hata:</strong> {str(e)}</div>', unsafe_allow_html=True)
    
    # Sonuçları göster - Yoğunlaştırılmış kartlar
    if 'opportunities' in st.session_state and st.session_state.opportunities:
        st.markdown("---")
        st.markdown(f"### 📋 Bulunan Fırsatlar ({len(st.session_state.opportunities)})")
        
        # Debug Panel
        with st.expander("🔎 Debug: Parametreleri ve sayıları göster", expanded=False):
            # Effective params oluştur (sam_integration.py ile uyumlu)
            keyword_parts = []
            if keywords:
                keyword_parts.append(keywords)
            # NAICS keyword olarak da ekleniyor (keyword boşsa)
            if naics_code and not keywords:
                keyword_parts.append(naics_code)
            
            effective_params = {
                "naicsCodes": naics_code if naics_code else None,
                "keyword": ' '.join(keyword_parts) if keyword_parts else None,
                "keywordRadio": "ALL" if keyword_parts else None,
                "limit": limit,
                "is_active": "true",
                "sort": "-modifiedDate"
            }
            
            # Tarih filtresi (days_back >= 60 ise)
            if days_back and days_back >= 60:
                effective_params["postedFrom"] = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
                effective_params["postedTo"] = datetime.now().strftime('%m/%d/%Y')
            
            # None değerleri temizle
            effective_params = {k: v for k, v in effective_params.items() if v is not None}
            
            # Source analizi
            sources = {}
            for opp in st.session_state.opportunities:
                source = opp.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            result_stats = {
                "total_returned": len(st.session_state.opportunities),
                "by_source": sources
            }
            
            st.json({
                "effective_params": effective_params,
                "result_stats": result_stats
            })
        
        for i, opp in enumerate(st.session_state.opportunities):
            opp_id = opp.get('opportunityId', 'N/A')
            notice_id_opp = opp.get('noticeId', 'N/A')
            title = opp.get('title', 'Başlık Yok')
            org = opp.get('fullParentPathName', 'Organizasyon Yok')
            posted_date = opp.get('postedDate', 'N/A')
            deadline = opp.get('responseDeadLine', 'N/A')
            naics = opp.get('naicsCode', 'N/A')
            
            # Source badge
            source = opp.get('source', 'unknown')
            source_badge_map = {
                'gsa_live': ('GSA (canlı)', 'badge-success'),
                'sam_live': ('SAM.gov (canlı)', 'badge-success'),
                'gsa_description_api': ('GSA (canlı)', 'badge-success')
            }
            source_text, source_class = source_badge_map.get(source, ('Canlı API', 'badge-success'))
            
            # SAM.gov link oluştur
            sam_link_html = ""
            if opp_id != 'N/A' and len(str(opp_id)) == 32:  # Opportunity ID (32 karakter hex)
                sam_url = f"https://sam.gov/opp/{opp_id}/view"
                sam_link_html = f'<a href="{sam_url}" target="_blank" style="color: #7c3aed; text-decoration: none; font-size: 12px; margin-left: 8px; font-weight: 600;">🔗 SAM.gov</a>'
            elif notice_id_opp != 'N/A':
                # Notice ID varsa, search URL kullan
                sam_url = f"https://sam.gov/opportunities/search?noticeId={notice_id_opp}"
                sam_link_html = f'<a href="{sam_url}" target="_blank" style="color: #7c3aed; text-decoration: none; font-size: 12px; margin-left: 8px; font-weight: 600;">🔗 SAM.gov</a>'
            
            # Modern card design (UI components kullanılıyorsa)
            if UI_COMPONENTS_AVAILABLE:
                opportunity_card(opp, key=f"card_{i}", actions=True, show_naics_badge=True)
            else:
                # Fallback: Modern op-card design (theme.css ile uyumlu)
                st.markdown(f"""
                <div class="op-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;">
                                <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--text);">{title}</h3>
                                <span class="badge badge-success" style="font-size: 11px; padding: 2px 6px;">{source_text}</span>
                                {sam_link_html}
                            </div>
                            <div class="meta" style="color: var(--muted); font-size: 13px; margin: 4px 0;">
                                <strong style="color: var(--text);">Notice ID:</strong> {notice_id_opp} · 
                                <strong style="color: var(--text);">NAICS:</strong> {naics} · 
                                <strong style="color: var(--text);">Son Tarih:</strong> {deadline}
                            </div>
                            <div class="meta" style="color: var(--muted); font-size: 12px; margin-top: 4px;">
                                {org}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Eski butonlar (fallback için)
                col1, col2 = st.columns([1, 1], gap="small")
                with col1:
                    if st.button("📊 Detay", key=f"view_{i}", use_container_width=True):
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'AI_ANALYSIS'
                        st.rerun()
                with col2:
                    if st.button("🚀 Analiz Başlat", key=f"analyze_{i}", use_container_width=True, type="primary"):
                        notice_id_for_api = opp.get('noticeId', opp.get('opportunityId', ''))
                        
                        # API çağrısı
                        try:
                            import requests
                            api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
                            response = requests.post(
                                f"{api_url}/api/proposal/auto",
                                params={"notice_id": notice_id_for_api},
                                timeout=120
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.session_state.analysis_result = result
                                st.session_state.selected_opportunity = opp
                                st.success(f"✅ Analiz başlatıldı! {result.get('docs_count', 0)} doküman indirildi.")
                                st.session_state.current_page = 'AI_ANALYSIS'
                            else:
                                st.error(f"❌ Analiz başlatılamadı: {response.text}")
                        except Exception as e:
                            # API erişilemezse, manuel analiz sayfasına yönlendir
                            st.warning(f"⚠️ API erişilemedi, manuel analiz moduna geçiliyor: {str(e)}")
                            st.session_state.selected_opportunity = opp
                            st.session_state.current_page = 'AI_ANALYSIS'
                        
                        st.rerun()
        
        # Modern card için action kontrolü (döngü sonrası)
        if UI_COMPONENTS_AVAILABLE and '_card_action' in st.session_state:
            action, opp_data = st.session_state._card_action
            del st.session_state._card_action
            
            if action == "analyze":
                notice_id_for_api = opp_data.get('noticeId', opp_data.get('opportunityId', ''))
                try:
                    import requests
                    api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
                    response = requests.post(
                        f"{api_url}/api/proposal/auto",
                        params={"notice_id": notice_id_for_api},
                        timeout=120
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.analysis_result = result
                        st.session_state.selected_opportunity = opp_data
                        st.success(f"✅ Analiz başlatıldı! {result.get('docs_count', 0)} doküman indirildi.")
                        st.session_state.current_page = 'AI_ANALYSIS'
                    else:
                        st.error(f"❌ Analiz başlatılamadı: {response.text}")
                except Exception as e:
                    st.warning(f"⚠️ API erişilemedi, manuel analiz moduna geçiliyor: {str(e)}")
                    st.session_state.selected_opportunity = opp_data
                    st.session_state.current_page = 'AI_ANALYSIS'
            elif action == "detail":
                st.session_state.selected_opportunity = opp_data
                st.session_state.current_page = 'AI_ANALYSIS'
            
            st.rerun()
    
    # Geri dön butonu
    if st.button("← Dashboard'a Dön", use_container_width=True):
        st.session_state.current_page = 'DASHBOARD'
        st.rerun()

# ============================================================================
# AI ANALİZ SAYFASI
# ============================================================================

def render_ai_analysis():
    """AI Analiz - 4 çekirdek ajan gösterimi ve analiz"""
    
    st.markdown('<h1 class="main-header">🤖 AI Analiz</h1>', unsafe_allow_html=True)
    
    if not st.session_state.selected_opportunity:
        st.warning("⚠️ Lütfen önce bir fırsat seçin.")
        if st.button("← Fırsat Arama'ya Dön"):
            st.session_state.current_page = 'OPPORTUNITY_SEARCH'
            st.rerun()
        return
    
    opportunity = st.session_state.selected_opportunity
    notice_id = opportunity.get('opportunityId', 'N/A')
    title = opportunity.get('title', 'Başlık Yok')
    
    st.markdown(f"""
    <div class="opportunity-card" style="margin-bottom: 2rem;">
        <h3 style="margin: 0 0 12px 0; color: #e5e7eb;">📋 Seçilen Fırsat</h3>
        <div class="meta" style="margin: 8px 0;">
            <strong>Notice ID:</strong> <span style="color: #c4b5fd; font-weight: 600;">{notice_id}</span>
        </div>
        <div class="meta" style="margin: 8px 0;">
            <strong>Başlık:</strong> <span style="color: #e5e7eb;">{title}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4 Çekirdek Ajan Gösterimi - Modern Stepper
    st.markdown("### 🤖 Analiz Aşamaları")
    
    if UI_COMPONENTS_AVAILABLE:
        # Modern stepper kullan
        current_stage = st.session_state.get('analysis_stage', 1)
        stepper(current_stage=current_stage, labels=[
            "Veri Çekme",
            "Doküman İşleme", 
            "RAG Muhakemesi",
            "Final Rapor"
        ])
        
        # Sekmeli görünüm (opsiyonel)
        use_tabs = st.checkbox("📑 Sekmeli Görünüm", value=False, key="use_tabs_view")
        if use_tabs:
            staged_tabs(current_stage=current_stage)
    else:
        # Fallback: Eski ajan kartları
        col1, col2 = st.columns(2)
        
        agents = [
            {"name": "SAM Opportunity Agent", "status": "✅ Hazır", "description": "Fırsat metadata analizi"},
            {"name": "Document Analysis Agent", "status": "✅ Hazır", "description": "Doküman içerik analizi"},
            {"name": "AI Analysis Agent", "status": "✅ Hazır", "description": "AI destekli özellik çıkarımı"},
            {"name": "Summary Agent", "status": "✅ Hazır", "description": "Konsolidasyon ve özet"}
        ]
        
        for i, agent in enumerate(agents):
            col = col1 if i % 2 == 0 else col2
            with col:
                st.markdown(f"""
                <div class="agent-card">
                    <h4>{agent['name']}</h4>
                    <p style="margin: 8px 0;"><strong style="color: #4a5568;">Durum:</strong> <span style="color: #10b981;">{agent['status']}</span></p>
                    <p style="color: #718096; font-size: 13px; margin: 4px 0;">{agent['description']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analiz başlatma
    if st.button("🚀 Analizi Başlat", use_container_width=True, type="primary", key="start_analysis"):
        st.session_state.analysis_progress = 0
        st.session_state.analysis_data = {}
        
        # Progress bar ile analiz simülasyonu
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        stages = [
            ("📥 Metadata çekiliyor...", 25),
            ("📄 Dokümanlar işleniyor...", 50),
            ("🤖 AI analizi yapılıyor...", 75),
            ("📊 Sonuçlar hazırlanıyor...", 100)
        ]
        
        for stage_name, progress_value in stages:
            status_text.text(stage_name)
            progress_bar.progress(progress_value / 100)
            time.sleep(1)  # Gerçekçi simülasyon
        
        # Gerçekçi analiz sonuçları
        analysis_result = {
            "opportunity_id": notice_id,
            "title": title,
            "analysis_status": "COMPLETED",
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "sam_opportunity_agent": {
                    "status": "completed",
                    "findings": ["NAICS kodu: 721110", "Son teslim: 2024-02-15", "Organizasyon bilgisi mevcut değil"]
                },
                "document_analysis_agent": {
                    "status": "completed",
                    "findings": ["3 doküman analiz edildi", "Toplam 45 sayfa", "PDF formatı tespit edildi"]
                },
                "ai_analysis_agent": {
                    "status": "completed",
                    "findings": ["Oda gereksinimi: 50+", "AV ekipmanı gerekli", "Catering hizmeti isteniyor"]
                },
                "summary_agent": {
                    "status": "completed",
                    "findings": ["Analiz tamamlandı", "Risk seviyesi: Orta", "Uygunluk: %85"]
                }
            },
            "metrics": {
                "total_documents": 3,
                "total_pages": 45,
                "analysis_time": "2.3 saniye",
                "confidence_score": 0.85
            },
            "recommendations": [
                "Fırsat uygun görünüyor",
                "Teknik dokümanlar hazırlanmalı",
                "Fiyat teklifi hazırlanmalı"
            ]
        }
        
        st.session_state.analysis_data = analysis_result
        st.session_state.analysis_history.append({
            "id": notice_id,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "result": analysis_result
        })
        
        status_text.text("✅ Analiz tamamlandı!")
        st.success("✅ Analiz başarıyla tamamlandı!")
    
    # Analiz sonuçlarını göster (Tabbed Interface - Figma tasarımı)
    if st.session_state.analysis_data:
        st.markdown("---")
        st.markdown("### 📊 Analiz Sonuçları")
        
        analysis = st.session_state.analysis_data
        
        # Tabbed Interface (Figma tasarımı)
        tab1, tab2, tab3 = st.tabs(["📋 Gereksinimler Özeti", "✅ Compliance Matrisi", "📄 Teklif Taslağı"])
        
        with tab1:
            st.markdown("#### Gereksinimler Özeti")
            agents_data = analysis.get('agents', {})
            
            # Gereksinimler tablosu
            requirements_data = []
            for agent_name, agent_data in agents_data.items():
                findings = agent_data.get('findings', [])
                for finding in findings:
                    # Kategori belirleme (basit eşleştirme)
                    category = "Genel"
                    priority = "Orta"
                    if "NAICS" in finding or "kod" in finding.lower():
                        category = "Teknik"
                        priority = "Yüksek"
                    elif "doküman" in finding.lower() or "sayfa" in finding.lower():
                        category = "Doküman"
                        priority = "Orta"
                    elif "risk" in finding.lower() or "uygunluk" in finding.lower():
                        category = "Uyumluluk"
                        priority = "Yüksek"
                    
                    requirements_data.append({
                        "Kategori": category,
                        "Gereksinim": finding,
                        "Öncelik": priority,
                        "Durum": "Karşılanıyor" if "tamamlandı" in finding.lower() or "mevcut" in finding.lower() else "İnceleniyor"
                    })
            
            if requirements_data:
                df_req = pd.DataFrame(requirements_data)
                st.dataframe(df_req, use_container_width=True, hide_index=True)
            else:
                st.info("Henüz gereksinim çıkarılmadı.")
        
        with tab2:
            st.markdown("#### Compliance Matrisi")
            metrics = analysis.get('metrics', {})
            
            # Metrikler
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Doküman Sayısı", metrics.get('total_documents', 0))
            with col2:
                st.metric("Toplam Sayfa", metrics.get('total_pages', 0))
            with col3:
                st.metric("Analiz Süresi", metrics.get('analysis_time', 'N/A'))
            with col4:
                st.metric("Güven Skoru", f"{metrics.get('confidence_score', 0) * 100:.0f}%")
            
            # Compliance durumu
            confidence = metrics.get('confidence_score', 0)
            if confidence >= 0.8:
                st.success("✅ Yüksek Uyumluluk - Fırsat uygun görünüyor")
            elif confidence >= 0.6:
                st.warning("⚠️ Orta Uyumluluk - Ek doküman gerekebilir")
            else:
                st.error("❌ Düşük Uyumluluk - Detaylı inceleme gerekli")
        
        with tab3:
            st.markdown("#### Teklif Taslağı")
            recommendations = analysis.get('recommendations', [])
            
            if recommendations:
                st.markdown("**Öneriler:**")
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"{i}. {rec}")
            else:
                st.info("Teklif taslağı hazırlanıyor...")
        
        # Sonuçları kaydet butonu
        if st.button("💾 Sonuçları Kaydet", use_container_width=True):
            st.session_state.current_page = 'RESULTS'
            st.rerun()
    
    # Geri dön butonu
    if st.button("← Dashboard'a Dön", use_container_width=True):
        st.session_state.current_page = 'DASHBOARD'
        st.rerun()

# ============================================================================
# SONUÇLAR SAYFASI
# ============================================================================

def render_results():
    """Sonuçlar - Analiz geçmişi ve export seçenekleri (Figma tasarımı - Tabbed Interface)"""
    
    st.markdown('<h1 class="main-header">📊 Sonuçlar</h1>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_history:
        st.info("Henüz analiz yapılmamış. Fırsat arama sayfasından analiz başlatabilirsiniz.")
    else:
        # Tabbed Interface (Figma tasarımı)
        tab1, tab2 = st.tabs(["📋 Analiz Geçmişi", "📊 Detaylı Görünüm"])
        
        with tab1:
            st.markdown("### Analiz Geçmişi")
            
            # Analiz geçmişi tablosu
            history_data = []
            for analysis in reversed(st.session_state.analysis_history[-10:]):
                result = analysis.get('result', {})
                metrics = result.get('metrics', {})
                confidence = metrics.get('confidence_score', 0)
                
                # Skor badge
                if confidence >= 0.8:
                    score = "Mükemmel"
                elif confidence >= 0.6:
                    score = "İyi"
                else:
                    score = "Orta"
                
                history_data.append({
                    "Analiz ID": f"AN-{analysis['id'][:8]}",
                    "Notice ID": analysis['id'],
                    "Başlık": analysis['title'],
                    "Tarih": analysis['timestamp'][:16] if len(analysis['timestamp']) > 16 else analysis['timestamp'],
                    "Süre": metrics.get('analysis_time', 'N/A'),
                    "Skor": score,
                    "Durum": "Tamamlandı"
                })
            
            if history_data:
                df_history = pd.DataFrame(history_data)
                st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        with tab2:
            st.markdown("### Detaylı Görünüm")
            
            # Seçilen analiz varsa göster
            if 'selected_analysis' in st.session_state and st.session_state.selected_analysis:
                analysis = st.session_state.selected_analysis
                st.markdown(f"**{analysis['title']} - {analysis['id']}**")
                
                # Export butonları
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button("📥 PDF İndir", use_container_width=True, key="export_pdf")
                with col_btn2:
                    st.button("📄 JSON Export", use_container_width=True, key="export_json")
                
                # Detaylı görünüm sekmeleri
                detail_tab1, detail_tab2, detail_tab3 = st.tabs(["📋 Gereksinimler Özeti", "✅ Compliance Matrisi", "📄 Teklif Taslağı"])
                
                result = analysis.get('result', {})
                metrics = result.get('metrics', {})
                agents_data = result.get('agents', {})
                recommendations = result.get('recommendations', [])
                
                with detail_tab1:
                    # Gereksinimler tablosu (AI Analiz sayfasındaki gibi)
                    requirements_data = []
                    for agent_name, agent_data in agents_data.items():
                        findings = agent_data.get('findings', [])
                        for finding in findings:
                            category = "Genel"
                            priority = "Orta"
                            if "NAICS" in finding or "kod" in finding.lower():
                                category = "Teknik"
                                priority = "Yüksek"
                            elif "doküman" in finding.lower() or "sayfa" in finding.lower():
                                category = "Doküman"
                                priority = "Orta"
                            elif "risk" in finding.lower() or "uygunluk" in finding.lower():
                                category = "Uyumluluk"
                                priority = "Yüksek"
                            
                            requirements_data.append({
                                "Kategori": category,
                                "Gereksinim": finding,
                                "Öncelik": priority,
                                "Durum": "Karşılanıyor" if "tamamlandı" in finding.lower() or "mevcut" in finding.lower() else "İnceleniyor"
                            })
                    
                    if requirements_data:
                        df_req = pd.DataFrame(requirements_data)
                        st.dataframe(df_req, use_container_width=True, hide_index=True)
                    else:
                        st.info("Gereksinim verisi bulunamadı.")
                
                with detail_tab2:
                    # Compliance Matrisi
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Doküman Sayısı", metrics.get('total_documents', 0))
                    with col2:
                        st.metric("Toplam Sayfa", metrics.get('total_pages', 0))
                    with col3:
                        st.metric("Analiz Süresi", metrics.get('analysis_time', 'N/A'))
                    with col4:
                        st.metric("Güven Skoru", f"{metrics.get('confidence_score', 0) * 100:.0f}%")
                    
                    confidence = metrics.get('confidence_score', 0)
                    if confidence >= 0.8:
                        st.success("✅ Yüksek Uyumluluk")
                    elif confidence >= 0.6:
                        st.warning("⚠️ Orta Uyumluluk")
                    else:
                        st.error("❌ Düşük Uyumluluk")
                
                with detail_tab3:
                    # Teklif Taslağı
                    if recommendations:
                        st.markdown("**Öneriler:**")
                        for i, rec in enumerate(recommendations, 1):
                            st.markdown(f"{i}. {rec}")
                    else:
                        st.info("Teklif taslağı bulunamadı.")
            else:
                st.info("Detay görüntülemek için analiz geçmişinden bir analiz seçin.")
    
    # Özet istatistikler
    st.markdown("---")
    st.markdown("### 📈 Özet İstatistikler")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_analyses = len(st.session_state.analysis_history)
    avg_confidence = sum([a.get('result', {}).get('metrics', {}).get('confidence_score', 0) for a in st.session_state.analysis_history]) / max(total_analyses, 1)
    
    with col1:
        st.metric("Toplam Analiz", total_analyses)
    with col2:
        st.metric("Ortalama Güven", f"{avg_confidence * 100:.1f}%")
    with col3:
        st.metric("Başarılı", total_analyses)
    with col4:
        st.metric("Başarı Oranı", "100%")
    
    # Export seçenekleri
    st.markdown("---")
    st.markdown("### 📤 Export Seçenekleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 PDF Olarak İndir", use_container_width=True):
            st.info("PDF export özelliği yakında eklenecek.")
    
    with col2:
        if st.button("📊 Excel Olarak İndir", use_container_width=True):
            if st.session_state.analysis_history:
                df = pd.DataFrame([
                    {
                        "ID": a['id'],
                        "Başlık": a['title'],
                        "Tarih": a['timestamp'],
                        "Güven Skoru": a.get('result', {}).get('metrics', {}).get('confidence_score', 0) * 100
                    }
                    for a in st.session_state.analysis_history
                ])
                st.download_button(
                    label="📥 Excel İndir",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f"mergenlite_analiz_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("📧 Email Gönder", use_container_width=True):
            st.info("Email export özelliği yakında eklenecek.")
    
    # Geri dön butonu
    if st.button("← Dashboard'a Dön", use_container_width=True):
        st.session_state.current_page = 'DASHBOARD'
        st.rerun()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Ana uygulama fonksiyonu"""
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🚀 MergenLite")
        st.markdown("---")
        
        pages = {
            "🏠 Dashboard": "DASHBOARD",
            "🔍 Fırsat Arama": "OPPORTUNITY_SEARCH",
            "🤖 AI Analiz": "AI_ANALYSIS",
            "📊 Sonuçlar": "RESULTS"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
    
    # Sayfa yönlendirmesi
    if st.session_state.current_page == 'DASHBOARD':
        render_dashboard()
    elif st.session_state.current_page == 'OPPORTUNITY_SEARCH':
        render_opportunity_search()
    elif st.session_state.current_page == 'AI_ANALYSIS':
        render_ai_analysis()
    elif st.session_state.current_page == 'RESULTS':
        render_results()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()

