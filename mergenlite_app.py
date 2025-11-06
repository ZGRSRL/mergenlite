#!/usr/bin/env python3
"""
MergenLite - Sadeleştirilmiş İlan Analiz Platformu
Tek birleşik Streamlit uygulaması - Tüm özellikler tek dosyada
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import os
import json
import time
from typing import Dict, Any, List, Optional
from uuid import uuid4

# .env dosyasını yükle (mergen klasöründen öncelikli) - Cache bypass
try:
    from dotenv import load_dotenv
    
    # Önce mergen klasöründeki .env dosyasını yükle (force reload)
    mergen_env = '.env'
    if os.path.exists(mergen_env):
        load_dotenv(mergen_env, override=True, verbose=False)
    else:
        load_dotenv(override=True, verbose=False)
except ImportError:
    pass

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
    initial_sidebar_state="collapsed"
)

# Custom CSS - Minimal ve odaklı tasarım
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .opportunity-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .opportunity-card:hover {
        background-color: #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .analysis-step {
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #e9ecef;
        margin-bottom: 1.5rem;
    }
    .step-complete {
        border-color: #28a745;
        background-color: #d4edda;
    }
    .step-active {
        border-color: #1f77b4;
        background-color: #e7f3ff;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'OPPORTUNITY_CENTER'

if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None

if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

if 'analysis_stage' not in st.session_state:
    st.session_state.analysis_stage = 1

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
# OPPORTUNITY CENTER - İlan Merkezi
# ============================================================================

def render_opportunity_center():
    """İlan Merkezi - Fırsatları listele ve analiz için seç"""
    
    st.markdown('<h1 class="main-header">🚀 MergenLite - İlan Merkezi</h1>', unsafe_allow_html=True)
    
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
                        real_opportunities = [opp for opp in opportunities if not opp.get('opportunityId', '').startswith('DEMO-')]
                        
                        if real_opportunities:
                            st.session_state.opportunities = real_opportunities
                            st.success(f"✅ {len(real_opportunities)} fırsat bulundu!")
                        else:
                            st.warning("⚠️ Fırsat bulunamadı. Demo modu kullanılabilir.")
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
                opportunities = sam.fetch_opportunities(
                    keywords=search_query if search_query else None,
                    naics_codes=[naics_code] if naics_code else None,
                    days_back=days_back,
                    limit=50
                )
                
                if opportunities:
                    st.session_state.opportunities = opportunities
                    st.success(f"✅ {len(opportunities)} fırsat bulundu!")
                else:
                    st.warning("Fırsat bulunamadı.")
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
                    <div class="opportunity-card">
                        <h3>{title}</h3>
                        <p><strong>Notice ID:</strong> {notice_id}</p>
                        <p><strong>Organizasyon:</strong> {org}</p>
                        <p><strong>Yayın Tarihi:</strong> {posted_date}</p>
                        <p><strong>Son Teslim:</strong> {deadline}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📊 Analiz Et", key=f"analyze_{i}", use_container_width=True):
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.rerun()
    
    # Demo modu
    with st.expander("🧪 Demo Modu"):
        if st.button("Demo İlan ile Devam Et"):
            demo_opportunity = {
                'opportunityId': 'a81c7ad026c74b7799b0e28e735aeeb7',
                'noticeId': 'W50S7526QA010',
                'title': 'Demo: Konaklama ve Etkinlik Hizmetleri',
                'fullParentPathName': 'Demo Organization',
                'postedDate': '2024-01-15',
                'responseDeadLine': '2024-02-15',
                'naicsCode': '721110'
            }
            st.session_state.selected_opportunity = demo_opportunity
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
    <div style="background-color: #e7f3ff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;">
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
                            st.warning("⚠️ İşlenmiş doküman bulunamadı. Demo analiz yapılıyor.")
                            document_paths = ["demo_document.pdf"]
                        
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
                        st.warning("⚠️ MergenLite veritabanı kullanılamıyor. Demo analiz yapılıyor.")
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
    
    # Sayfa yönlendirmesi
    if st.session_state.current_page == 'OPPORTUNITY_CENTER':
        render_opportunity_center()
    elif st.session_state.current_page == 'GUIDED_ANALYSIS':
        if st.session_state.selected_opportunity:
            render_guided_analysis_page(st.session_state.selected_opportunity)
        else:
            st.error("Lütfen önce bir ilan seçin.")
            if st.button("← İlan Merkezine Dön"):
                st.session_state.current_page = 'OPPORTUNITY_CENTER'
                st.rerun()
    else:
        render_opportunity_center()
    
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

