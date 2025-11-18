#!/usr/bin/env python3
"""
MergenAI Lite - Rehberli Analiz Modülü
4 Aşamalı İlan Analiz Workflow'u:
1. Metadata ve Doküman İndirme
2. Doküman İşleme (PDF/DOCX Metin Çıkarımı)
3. RAG Muhakemesi (LLM ile Özellik Çıkarımı)
4. Final Rapor
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
import time
import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Local imports
from sam_integration import SAMIntegration
from document_processor import DocumentProcessor
from rag_service import RAGService
from llm_analyzer import LLMAnalyzer

# Proposal generator (opsiyonel)
try:
    from proposal_pipeline import generate_proposal_from_analysis, get_llm_config
    PROPOSAL_GENERATOR_AVAILABLE = True
except ImportError:
    PROPOSAL_GENERATOR_AVAILABLE = False
    logger.warning("Proposal generator not available")

# Orchestrator kullanılmıyor - direkt analiz yapılıyor
# Autogen çağrıları kaldırıldı - basit ve hızlı analiz pipeline kullanılıyor

def render_guided_analysis_page(opportunity: Dict[str, Any]):
    """
    Modern AI Analysis Interface - MergenLite Core
    Real-time agent workflow with live progress tracking
    """
    
    # Header with modern gradient
    st.markdown('<h1 class="main-header">🤖 AI Analiz - Canlı Ajan Çalışması</h1>', unsafe_allow_html=True)
    
    # Seçilen ilan bilgisi - Modern card design
    # Label clarity: Show both IDs explicitly
    notice_id = opportunity.get('noticeId') or opportunity.get('solicitationNumber') or 'N/A'
    opportunity_id = opportunity.get('opportunityId') or opportunity.get('opportunity_id', '')
    title = opportunity.get('title', 'Başlık Yok')
    
    # SAM.gov view link oluştur
    sam_gov_link = opportunity.get('samGovLink') or opportunity.get('sam_gov_link')
    if not sam_gov_link:
        if opportunity_id and len(str(opportunity_id)) == 32:  # Opportunity ID (32 karakter hex)
            sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
        elif notice_id and notice_id != 'N/A':
            sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
    
    sam_link_html = ""
    if sam_gov_link:
        sam_link_html = f'<a href="{sam_gov_link}" target="_blank" style="color: var(--blue-400); text-decoration: none; font-size: 12px; margin-left: 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">🔗 SAM.gov\'da Görüntüle</a>'
    
    st.markdown(f"""
    <div class="op-card" style="margin-bottom: 24px; background: linear-gradient(135deg, rgba(124,58,237,.15), rgba(59,130,246,.1)); border: 1px solid rgba(124,58,237,.3);">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px; flex-wrap: wrap;">
            <span style="font-size: 24px;">📄</span>
            <div style="flex: 1;">
                <h3 style="color: var(--text); font-size: 18px; font-weight: 600; margin: 0;">{title}</h3>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px; flex-wrap: wrap;">
                    {f'<p style="color: var(--blue-400); font-size: 12px; margin: 0; font-weight: 500;">Opportunity ID: {opportunity_id[:20]}...</p>' if opportunity_id and opportunity_id != 'N/A' else ''}
                    {f'<p style="color: var(--text-400); font-size: 12px; margin: 0;">Notice ID: {notice_id}</p>' if notice_id and notice_id != 'N/A' else ''}
                    {sam_link_html}
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 24px; color: var(--text-400); font-size: 14px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>📅</span>
                <span>Yanıt: {opportunity.get('responseDeadline', 'Belirtilmemiş')}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>⏱️</span>
                <span>{opportunity.get('daysLeft', 'N/A')} gün kaldı</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fırsat Açıklaması - Sadeleştirilmiş (collapsed)
    description = opportunity.get('description') or opportunity.get('descriptionText') or opportunity.get('summary') or ''
    if description:
        with st.expander("📝 Fırsat Açıklaması", expanded=False):
            import re
            clean_description = re.sub(r'<[^>]+>', '', str(description))
            if len(clean_description) > 2000:
                clean_description = clean_description[:2000] + "..."
            st.markdown(f"<div style='color: var(--text-300); font-size: 14px; line-height: 1.6;'>{clean_description}</div>", unsafe_allow_html=True)
    
    # Analiz Geçmişi Bölümü - Bu fırsat için yapılan analizler
    st.markdown("---")
    st.markdown("### 📊 Analiz Geçmişi")
    
    # DB'den bu fırsat için analiz geçmişini yükle
    analysis_history = []
    try:
        # DB kontrolü
        try:
            from mergenlite_models import AIAnalysisResult, Opportunity
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            DB_AVAILABLE = True
        except ImportError:
            DB_AVAILABLE = False
        
        if DB_AVAILABLE:
            from app import get_db_session
            import json
            
            db = get_db_session()
            if db:
                try:
                    # Opportunity'yi bul
                    opp_db = None
                    if opportunity_id and len(str(opportunity_id)) == 32:
                        opp_db = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
                    elif notice_id and notice_id != 'N/A':
                        opp_db = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
                    
                    if opp_db:
                        # Bu opportunity için analizleri bul
                        analyses = db.query(AIAnalysisResult).filter(
                            AIAnalysisResult.opportunity_id == opp_db.opportunity_id
                        ).order_by(AIAnalysisResult.timestamp.desc()).limit(10).all()
                        
                        for analysis in analyses:
                            result_data = analysis.result or {}
                            if isinstance(result_data, str):
                                try:
                                    result_data = json.loads(result_data)
                                except:
                                    result_data = {}
                            
                            # Skor hesapla
                            skor = "N/A"
                            skor_class = "badge-info"
                            if result_data:
                                score = result_data.get('data', {}).get('proposal', {}).get('overall_score') or \
                                        result_data.get('compliance', {}).get('score') or \
                                        (float(analysis.confidence) * 100 if analysis.confidence else None)
                                if score:
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
                            
                            # Durum
                            status_map = {
                                'COMPLETED': 'Tamamlandı',
                                'IN_PROGRESS': 'Devam Ediyor',
                                'FAILED': 'Başarısız',
                                'PENDING': 'Beklemede'
                            }
                            status = status_map.get(analysis.analysis_type, analysis.analysis_type)
                            
                            analysis_history.append({
                                'id': analysis.id,
                                'opportunity_id': analysis.opportunity_id,
                                'status': status,
                                'skor': skor,
                                'skor_class': skor_class,
                                'timestamp': analysis.timestamp.strftime("%Y-%m-%d %H:%M") if analysis.timestamp else "N/A",
                                'result_data': result_data
                            })
                finally:
                    db.close()
    except Exception as e:
        logger.error(f"Analiz geçmişi yükleme hatası: {e}", exc_info=True)
    
    # Analiz geçmişi listesi
    if analysis_history:
        for analysis in analysis_history:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"""
                <div class="modern-card" style="margin-bottom: 10px; padding: 14px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="color: var(--text-300); font-size: 14px; font-weight: 500;">Analiz #{analysis['id']}</span>
                        <span class="badge badge-info" style="font-size: 11px;">{analysis['status']}</span>
                        <span class="badge {analysis['skor_class']}" style="font-size: 11px;">{analysis['skor']}</span>
                    </div>
                    <div style="color: var(--text-400); font-size: 12px; margin-top: 4px;">{analysis['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                if st.button("📄 Detay", key=f"detail_{analysis['id']}", use_container_width=True):
                    st.session_state.selected_analysis_data = analysis
                    st.session_state.current_page = 'RESULTS'
                    st.rerun()
    else:
        st.info("Henüz analiz yapılmamış. Aşağıdaki 'Analiz Et' butonuna tıklayarak analiz başlatabilirsiniz.")
    
    # Hızlı Aksiyonlar Bölümü - Fonksiyon Odaklı
    st.markdown("---")
    st.markdown("### 🚀 Hızlı Aksiyonlar")
    
    # Fırsat kodu
    opportunity_code = opportunity.get('solicitationNumber') or notice_id or opportunity_id or 'UNKNOWN'
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Klasör Oluştur ve Aç", use_container_width=True, key="create_folder"):
            try:
                import subprocess
                import platform
                
                folder = Path(".") / "opportunities" / opportunity_code
                folder.mkdir(parents=True, exist_ok=True)
                folder_path = str(folder.absolute())
                
                if platform.system() == "Windows":
                    subprocess.Popen(f'explorer "{folder_path}"')
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", folder_path])
                else:
                    subprocess.Popen(["xdg-open", folder_path])
                
                st.success(f"✅ Klasör oluşturuldu: `{folder_path}`")
                st.info("💡 Dökümanları bu klasöre kaydedin, sonra 'Analiz Et' butonuna tıklayın.")
            except Exception as e:
                st.error(f"❌ Klasör oluşturma hatası: {str(e)}")
    
    with col2:
        if st.button("📤 Döküman Yükle", use_container_width=True, key="upload_docs"):
            st.session_state['show_upload'] = True
            st.rerun()
    
    with col3:
        if st.button("▶ Analiz Et", use_container_width=True, type="primary", key="analyze_btn"):
            if not st.session_state.ai_analysis_state.get('analysis_running', False):
                start_ai_analysis(opportunity)
            else:
                st.warning("⚠️ Analiz zaten devam ediyor...")
    
    # Döküman Yükleme Bölümü
    if st.session_state.get('show_upload', False):
        st.markdown("---")
        st.markdown("#### 📤 Döküman Yükleme")
        
        folder = Path(".") / "opportunities" / opportunity_code
        folder.mkdir(parents=True, exist_ok=True)
        
        # Mevcut dosyalar
        existing_files = []
        if folder.exists():
            existing_files = (
                list(folder.glob("*.pdf")) + 
                list(folder.glob("*.docx")) + 
                list(folder.glob("*.txt")) +
                list(folder.glob("*.zip")) +
                list(folder.glob("*.xls")) +
                list(folder.glob("*.xlsx"))
            )
            existing_files = [f for f in existing_files if f.name != 'analysis_report.pdf']
        
        if existing_files:
            st.markdown("**📁 Klasördeki Mevcut Dökümanlar:**")
            for f in existing_files[:5]:
                st.markdown(f"  - `{f.name}` ({f.stat().st_size / 1024:.1f} KB)")
            if len(existing_files) > 5:
                st.markdown(f"  - ... ve {len(existing_files) - 5} dosya daha")
        
        uploaded_files = st.file_uploader(
            "Yeni dökümanları seçin (PDF, DOCX, TXT, ZIP, XLS, XLSX)",
            type=['pdf', 'docx', 'doc', 'txt', 'zip', 'xls', 'xlsx'],
            accept_multiple_files=True,
            key="file_uploader_main"
        )
        
        if uploaded_files:
            uploaded_count = 0
            for uploaded_file in uploaded_files:
                try:
                    file_path = folder / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    if uploaded_file.name.lower().endswith('.zip'):
                        from opportunity_runner import extract_zip_to_folder
                        extract_zip_to_folder(file_path, folder)
                    
                    st.success(f"✅ {uploaded_file.name} yüklendi")
                    uploaded_count += 1
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} yüklenirken hata: {str(e)}")
            
            if uploaded_count > 0:
                st.success(f"🎉 {uploaded_count} döküman başarıyla yüklendi!")
                st.session_state['show_upload'] = False
                st.rerun()
    
    # Form-Based Analysis Configuration - Collapsed
    with st.expander("⚙️ Analiz Konfigürasyonu (Form Tabanlı)", expanded=False):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            company_name = st.text_input("🏢 Firma Adı", value="", key="form_company_name", help="Analiz edilecek firma adı")
            project_type = st.text_input("📋 Proje Tipi", value="", key="form_project_type", help="Örn: Conference and Lodging Support")
            location = st.text_input("📍 Konum", value="", key="form_location", help="Etkinlik yeri (şehir/ülke)")
            dates = st.text_input("📅 Tarih Aralığı", value="", key="form_dates", help="Örn: April 14-18, 2024")
            participants = st.number_input("👥 Katılımcı Sayısı", min_value=1, value=1, key="form_participants", help="Tahmini katılımcı sayısı")
        
        with col_form2:
            budget = st.number_input("💰 Tahmini Bütçe ($)", min_value=0, value=0, key="form_budget", help="Tahmini bütçe miktarı")
            naics_code = st.text_input("🔢 NAICS Kodu", value=opportunity.get('naicsCode', '721110'), key="form_naics", help="NAICS kodu")
            contract_type = st.selectbox("📄 Sözleşme Türü", ["Fixed Price", "Time & Materials", "Cost Plus", "IDIQ", "Diğer"], key="form_contract_type")
            evaluation_focus = st.multiselect(
                "🎯 Analiz Kriterleri (Öncelikli)",
                [
                    "Room capacity and ADA compliance",
                    "Conference space AV requirements",
                    "FAR/DFAR compliance clauses",
                    "Electronic invoicing (IPP)",
                    "Small business eligibility",
                    "Lojistik",
                    "Uyumluluk (Compliance)",
                    "Maliyet",
                    "AV Gereksinimleri",
                    "Performans Referansları"
                ],
                key="form_evaluation_focus",
                help="PDF analizinde öncelik verilecek kriterler"
            )
    
    # Form verilerini session state'e kaydet
    form_data = {
        "company_name": company_name,
        "project_type": project_type,
        "location": location,
        "dates": dates,
        "participants": participants,
        "budget": budget,
        "naics": naics_code,
        "contract_type": contract_type,
        "evaluation_focus": evaluation_focus
    }
    st.session_state.form_data = form_data
    
    # Initialize analysis state
    if 'ai_analysis_state' not in st.session_state:
        st.session_state.ai_analysis_state = {
            'current_stage': 0,
            'completed_stages': [],
            'analysis_running': False,
            'results': None,
            'start_time': None
        }
    
    # Initialize legacy analysis data
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {}
    
    if 'analysis_stage' not in st.session_state:
        st.session_state.analysis_stage = 1
    
    # Otomatik vendor profile yükleme - Sayfa yüklendiğinde (widget'lardan ÖNCE)
    # Eğer vendor bilgileri yoksa ve PDF mevcutsa otomatik yükle
    if 'vendor_profile_auto_loaded' not in st.session_state:
        try:
            samples_pdf = Path("samples") / "CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE_copy[1].pdf"
            if samples_pdf.exists():
                # Vendor bilgileri yoksa veya boşsa otomatik yükle
                if not st.session_state.get('vendor_company_name') or not st.session_state.get('vendor_uei'):
                    with st.spinner("📄 Şirket bilgileri PDF'den otomatik yükleniyor..."):
                        from vendor_profile_extractor import extract_vendor_profile_from_pdf
                        
                        vendor_profile = extract_vendor_profile_from_pdf(str(samples_pdf))
                        
                        # Session state'e kaydet (widget'lardan önce)
                        st.session_state['vendor_company_name'] = vendor_profile.get('company_name', '')
                        st.session_state['vendor_address'] = vendor_profile.get('address', '')
                        st.session_state['vendor_uei'] = vendor_profile.get('uei', '')
                        st.session_state['vendor_duns'] = vendor_profile.get('duns', '')
                        st.session_state['vendor_sam_registered'] = vendor_profile.get('sam_registered', True)
                        st.session_state['vendor_contact_name'] = vendor_profile.get('contact', {}).get('name', '')
                        st.session_state['vendor_contact_email'] = vendor_profile.get('contact', {}).get('email', '')
                        st.session_state['vendor_contact_phone'] = vendor_profile.get('contact', {}).get('phone', '')
                        st.session_state['vendor_past_performance'] = '\n'.join(vendor_profile.get('past_performance', []))
                        
                        # Flag set et - bir daha yükleme
                        st.session_state['vendor_profile_auto_loaded'] = True
                        
                        logger.info(f"[Vendor Profile] Auto-loaded from PDF: {vendor_profile.get('company_name', 'N/A')}")
        except Exception as e:
            logger.warning(f"[Vendor Profile] Auto-load failed: {e}", exc_info=True)
            # Hata olsa bile flag set et, sürekli deneme yapmasın
            st.session_state['vendor_profile_auto_loaded'] = True
    
    # Analiz Durumu - Sadece çalışıyorsa göster
    if st.session_state.ai_analysis_state.get('analysis_running', False):
        st.markdown("---")
        st.markdown("### 📊 Analiz Durumu")
        
        # Progress bar
        total_stages = 4
        completed_stages = len(st.session_state.ai_analysis_state.get('completed_stages', []))
        progress = completed_stages / total_stages if total_stages > 0 else 0
        
        st.progress(progress)
        st.caption(f"İlerleme: {completed_stages}/{total_stages} aşama tamamlandı")
        
        # Stage indicator - Kompakt
        stages = [
            ("📄", "Döküman İşleme"),
            ("🛡️", "Uyumluluk"),
            ("🔍", "Gereksinimler"),
            ("✍️", "Rapor")
        ]
        
        current_stage = st.session_state.ai_analysis_state.get('current_stage', 0)
        completed = st.session_state.ai_analysis_state.get('completed_stages', [])
        
        cols = st.columns(4)
        for i, (icon, name) in enumerate(stages):
            with cols[i]:
                if i in completed:
                    st.markdown(f"<div style='text-align: center; padding: 12px; background: rgba(16,185,129,.1); border-radius: 8px; border: 1px solid rgba(16,185,129,.3);'><div style='font-size: 24px;'>{icon}</div><div style='font-size: 11px; color: var(--text-300); margin-top: 4px;'>✅ {name}</div></div>", unsafe_allow_html=True)
                elif i == current_stage:
                    st.markdown(f"<div style='text-align: center; padding: 12px; background: rgba(245,158,11,.1); border-radius: 8px; border: 1px solid rgba(245,158,11,.3);'><div style='font-size: 24px;'>🔄</div><div style='font-size: 11px; color: var(--text-300); margin-top: 4px;'>{name}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center; padding: 12px; background: rgba(17,24,39,.3); border-radius: 8px; border: 1px solid var(--border); opacity: 0.6;'><div style='font-size: 24px;'>{icon}</div><div style='font-size: 11px; color: var(--text-400); margin-top: 4px;'>{name}</div></div>", unsafe_allow_html=True)
        
        # Stop button
        if st.button("⏹️ Analizi Durdur", use_container_width=True, key="stop_analysis_main"):
            stop_ai_analysis()
    
    # Sonuçlar - Tamamlandıysa göster
    if st.session_state.ai_analysis_state.get('results') and not st.session_state.ai_analysis_state.get('analysis_running', False):
        st.markdown("---")
        st.markdown("### ✅ Analiz Tamamlandı")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Detaylı Sonuçları Gör", use_container_width=True, key="view_detailed_results"):
                st.session_state.current_page = 'RESULTS'
                st.session_state.selected_opportunity = opportunity
                st.rerun()
        
        with col2:
            # PDF indirme
            results = st.session_state.ai_analysis_state.get('results', {})
            pdf_path = results.get('metadata', {}).get('report_pdf_path')
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 PDF Raporu İndir",
                        data=pdf_file,
                        file_name=f"analysis_report_{opportunity_code}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_pdf"
                    )
        
        with col3:
            # Proposal ve SOW oluşturma
            col_prop, col_sow = st.columns(2)
            with col_prop:
                if st.button("📝 Teklif Taslağı", use_container_width=True, type="primary", key="generate_proposal"):
                    st.session_state['show_proposal_generator'] = True
                    st.rerun()
            with col_sow:
                if st.button("🏨 SOW Oluştur", use_container_width=True, type="secondary", key="generate_sow"):
                    st.session_state['show_sow_generator'] = True
                    st.rerun()
        
        # Proposal Generator Bölümü
        if st.session_state.get('show_proposal_generator', False):
            st.markdown("---")
            st.markdown("### 📝 Teklif Taslağı Oluştur")
            
            # PDF extraction işlemlerini widget'lardan ÖNCE yap (session state güncellemesi için)
            # PDF'den otomatik yükleme - Session state güncellemesi
            if 'extract_from_pdf_clicked' in st.session_state and st.session_state['extract_from_pdf_clicked']:
                try:
                    with st.spinner("PDF'den bilgiler çıkarılıyor..."):
                        from vendor_profile_extractor import extract_vendor_profile_from_pdf
                        
                        past_perf_pdf = st.session_state.get('past_perf_pdf_data')
                        if past_perf_pdf:
                            # PDF'i geçici olarak kaydet
                            temp_pdf = Path(".") / "temp_past_perf.pdf"
                            with open(temp_pdf, "wb") as f:
                                f.write(past_perf_pdf.getbuffer())
                            
                            # Bilgileri çıkar
                            vendor_profile = extract_vendor_profile_from_pdf(str(temp_pdf))
                            
                            # Session state'e kaydet (widget'lardan önce)
                            st.session_state['vendor_company_name'] = vendor_profile.get('company_name', '')
                            st.session_state['vendor_address'] = vendor_profile.get('address', '')
                            st.session_state['vendor_uei'] = vendor_profile.get('uei', '')
                            st.session_state['vendor_duns'] = vendor_profile.get('duns', '')
                            st.session_state['vendor_sam_registered'] = vendor_profile.get('sam_registered', True)
                            st.session_state['vendor_contact_name'] = vendor_profile.get('contact', {}).get('name', '')
                            st.session_state['vendor_contact_email'] = vendor_profile.get('contact', {}).get('email', '')
                            st.session_state['vendor_contact_phone'] = vendor_profile.get('contact', {}).get('phone', '')
                            st.session_state['vendor_past_performance'] = '\n'.join(vendor_profile.get('past_performance', []))
                            
                            # Geçici dosyayı sil
                            temp_pdf.unlink()
                            
                            # Flag'i temizle
                            st.session_state['extract_from_pdf_clicked'] = False
                            st.session_state['past_perf_pdf_data'] = None
                            
                            st.success("✅ Bilgiler PDF'den başarıyla çıkarıldı!")
                            st.rerun()
                except Exception as e:
                    logger.error(f"PDF extraction error: {e}", exc_info=True)
                    st.error(f"❌ PDF'den bilgi çıkarma hatası: {str(e)}")
                    st.session_state['extract_from_pdf_clicked'] = False
            
            # Samples klasöründen otomatik yükle - Session state güncellemesi
            if 'load_from_samples_clicked' in st.session_state and st.session_state['load_from_samples_clicked']:
                try:
                    with st.spinner("PDF'den bilgiler çıkarılıyor..."):
                        from vendor_profile_extractor import extract_vendor_profile_from_pdf
                        
                        samples_pdf = Path("samples") / "CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE_copy[1].pdf"
                        if samples_pdf.exists():
                            vendor_profile = extract_vendor_profile_from_pdf(str(samples_pdf))
                            
                            # Session state'e kaydet (widget'lardan önce)
                            st.session_state['vendor_company_name'] = vendor_profile.get('company_name', '')
                            st.session_state['vendor_address'] = vendor_profile.get('address', '')
                            st.session_state['vendor_uei'] = vendor_profile.get('uei', '')
                            st.session_state['vendor_duns'] = vendor_profile.get('duns', '')
                            st.session_state['vendor_sam_registered'] = vendor_profile.get('sam_registered', True)
                            st.session_state['vendor_contact_name'] = vendor_profile.get('contact', {}).get('name', '')
                            st.session_state['vendor_contact_email'] = vendor_profile.get('contact', {}).get('email', '')
                            st.session_state['vendor_contact_phone'] = vendor_profile.get('contact', {}).get('phone', '')
                            st.session_state['vendor_past_performance'] = '\n'.join(vendor_profile.get('past_performance', []))
                            
                            # Flag'i temizle
                            st.session_state['load_from_samples_clicked'] = False
                            
                            st.success("✅ Bilgiler PDF'den başarıyla çıkarıldı!")
                            st.rerun()
                except Exception as e:
                    logger.error(f"PDF extraction error: {e}", exc_info=True)
                    st.error(f"❌ PDF'den bilgi çıkarma hatası: {str(e)}")
                    st.session_state['load_from_samples_clicked'] = False
            
            # PDF'den otomatik yükleme UI
            col_auto, col_manual = st.columns([1, 1])
            
            with col_auto:
                st.markdown("#### 📄 PDF'den Otomatik Yükle")
                past_perf_pdf = st.file_uploader(
                    "Past Performance PDF'i seçin",
                    type=['pdf'],
                    key="past_perf_pdf_upload",
                    help="CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE_copy[1].pdf gibi"
                )
                
                if past_perf_pdf:
                    if st.button("📥 PDF'den Bilgileri Çıkar", use_container_width=True, key="extract_from_pdf"):
                        # Flag set et ve PDF'i kaydet
                        st.session_state['extract_from_pdf_clicked'] = True
                        st.session_state['past_perf_pdf_data'] = past_perf_pdf
                        st.rerun()
                
                # Samples klasöründen otomatik yükle
                samples_pdf = Path("samples") / "CREATA_GLOBAL_MEETING_AND_EVENTS_PAST_PERFORMANCE_copy[1].pdf"
                if samples_pdf.exists():
                    if st.button("📄 Samples Klasöründen Yükle", use_container_width=True, key="load_from_samples"):
                        # Flag set et
                        st.session_state['load_from_samples_clicked'] = True
                        st.rerun()
            
            with col_manual:
                st.markdown("#### ✏️ Manuel Giriş")
                st.info("💡 PDF'den otomatik yükleme yapabilir veya manuel olarak girebilirsiniz.")
            
            # Vendor Profile Input
            with st.expander("🏢 Şirket Bilgileri (Vendor Profile)", expanded=True):
                # Otomatik yüklendi bilgisi göster
                if st.session_state.get('vendor_profile_auto_loaded'):
                    st.info("✅ Şirket bilgileri CREATA GLOBAL MEETING AND EVENTS PDF'inden otomatik yüklendi. Gerekirse düzenleyebilirsiniz.")
                
                col_v1, col_v2 = st.columns(2)
                
                with col_v1:
                    vendor_company_name = st.text_input("Şirket Adı", value=st.session_state.get('vendor_company_name', ''), key="vendor_company_name")
                    vendor_address = st.text_area("Adres", value=st.session_state.get('vendor_address', ''), key="vendor_address")
                    vendor_uei = st.text_input("UEI", value=st.session_state.get('vendor_uei', ''), key="vendor_uei")
                    vendor_duns = st.text_input("DUNS", value=st.session_state.get('vendor_duns', ''), key="vendor_duns")
                
                with col_v2:
                    vendor_contact_name = st.text_input("İletişim Kişisi", value=st.session_state.get('vendor_contact_name', ''), key="vendor_contact_name")
                    vendor_contact_email = st.text_input("E-posta", value=st.session_state.get('vendor_contact_email', ''), key="vendor_contact_email")
                    vendor_contact_phone = st.text_input("Telefon", value=st.session_state.get('vendor_contact_phone', ''), key="vendor_contact_phone")
                    vendor_sam_registered = st.checkbox("SAM.gov'da Kayıtlı", value=st.session_state.get('vendor_sam_registered', True), key="vendor_sam_registered")
                
                # Past Performance
                st.markdown("**Geçmiş Performans (Past Performance):**")
                past_performance_text = st.text_area(
                    "Geçmiş projeleri listeleyin (her satır bir proje)",
                    value=st.session_state.get('vendor_past_performance', ''),
                    key="vendor_past_performance",
                    help="Örn: Event X - 300 participants - Department of Interior"
                )
                past_performance = [line.strip() for line in past_performance_text.split('\n') if line.strip()]
            
            # Vendor profile oluştur
            vendor_profile = {
                "company_name": vendor_company_name,
                "address": vendor_address,
                "uei": vendor_uei,
                "duns": vendor_duns,
                "sam_registered": vendor_sam_registered,
                "contact": {
                    "name": vendor_contact_name,
                    "email": vendor_contact_email,
                    "phone": vendor_contact_phone
                },
                "past_performance": past_performance
            }
            
            # Session state'e kaydet
            for key, value in vendor_profile.items():
                if key != 'contact' and key != 'past_performance':
                    st.session_state[f'vendor_{key}'] = value
                elif key == 'contact':
                    for ckey, cvalue in value.items():
                        st.session_state[f'vendor_contact_{ckey}'] = cvalue
                elif key == 'past_performance':
                    st.session_state['vendor_past_performance'] = past_performance_text
            
            # Proposal oluştur butonu
            if st.button("🚀 Teklif Taslağını Oluştur", use_container_width=True, type="primary", key="create_proposal"):
                if not vendor_company_name:
                    st.error("❌ Lütfen şirket adını girin.")
                else:
                    try:
                        folder_path = Path(".") / "opportunities" / opportunity_code
                        
                        with st.spinner("📝 Teklif taslağı oluşturuluyor..."):
                            from proposal_pipeline import generate_proposal_from_analysis, get_llm_config
                            
                            llm_config = get_llm_config()
                            proposal_path = generate_proposal_from_analysis(
                                folder_path=str(folder_path),
                                vendor_profile=vendor_profile,
                                llm_config=llm_config
                            )
                            
                            st.success(f"✅ Teklif taslağı oluşturuldu: `{proposal_path}`")
                            st.session_state['proposal_path'] = proposal_path
                            st.session_state['proposal_generated'] = True
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Proposal generation error: {e}", exc_info=True)
                        st.error(f"❌ Teklif oluşturma hatası: {str(e)}")
            
            # Oluşturulan proposal'ı göster
            proposal_path = st.session_state.get('proposal_path')
            if proposal_path and Path(proposal_path).exists():
                st.markdown("---")
                st.markdown("### 📄 Oluşturulan Teklif Taslağı")
                
                with open(proposal_path, 'r', encoding='utf-8') as f:
                    proposal_content = f.read()
                
                # Proposal önizleme
                st.markdown(proposal_content)
                
                # İndirme butonları
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button(
                        label="📥 Markdown İndir",
                        data=proposal_content,
                        file_name=f"proposal_{opportunity_code}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="download_proposal_md"
                    )
                
                with col_d2:
                    # PDF'e çevir (opsiyonel)
                    if st.button("📄 PDF'e Çevir", use_container_width=True, key="convert_to_pdf"):
                        st.info("💡 PDF dönüşümü yakında eklenecek. Şimdilik Markdown formatını kullanabilirsiniz.")
        
        # SOW Generator Bölümü
        if st.session_state.get('show_sow_generator', False):
            st.markdown("---")
            st.markdown("### 🏨 Statement of Work (SOW) Oluştur")
            st.info("💡 RFQ analizinden otellere gönderilecek profesyonel SOW oluşturulacak. Sample SOW formatı kullanılacak.")
            
            # Vendor profile bilgileri (varsa)
            vendor_company_name = st.session_state.get('vendor_company_name', '')
            vendor_address = st.session_state.get('vendor_address', '')
            vendor_uei = st.session_state.get('vendor_uei', '')
            vendor_duns = st.session_state.get('vendor_duns', '')
            vendor_sam_registered = st.session_state.get('vendor_sam_registered', True)
            vendor_contact_name = st.session_state.get('vendor_contact_name', '')
            vendor_contact_email = st.session_state.get('vendor_contact_email', '')
            vendor_contact_phone = st.session_state.get('vendor_contact_phone', '')
            
            # SOW oluştur butonu
            if st.button("🚀 SOW Oluştur", use_container_width=True, type="primary", key="create_sow"):
                try:
                    folder_path = Path(".") / "opportunities" / opportunity_code
                    
                    with st.spinner("🏨 SOW oluşturuluyor (Sample SOW formatına göre)..."):
                        from sow_generator import generate_sow_from_rfq_analysis
                        
                        # RFQ analiz sonuçlarını yükle
                        report_path = folder_path / "report.json"
                        if not report_path.exists():
                            st.error("❌ Önce AI analizi yapmalısınız!")
                        else:
                            with open(report_path, 'r', encoding='utf-8') as f:
                                rfq_analysis = json.load(f)
                            
                            # Vendor profile (varsa)
                            vendor_profile = None
                            if vendor_company_name:
                                vendor_profile = {
                                    "company_name": vendor_company_name,
                                    "address": vendor_address,
                                    "uei": vendor_uei,
                                    "duns": vendor_duns,
                                    "sam_registered": vendor_sam_registered,
                                    "contact": {
                                        "name": vendor_contact_name,
                                        "email": vendor_contact_email,
                                        "phone": vendor_contact_phone
                                    }
                                }
                            
                            # Opportunity info
                            opportunity_info = {
                                "solicitation_number": opportunity_code,
                                "title": rfq_analysis.get('opportunity_info', {}).get('title', ''),
                                "agency": rfq_analysis.get('opportunity_info', {}).get('agency', '')
                            }
                            
                            # SOW oluştur
                            sow_result = generate_sow_from_rfq_analysis(
                                rfq_analysis=rfq_analysis,
                                opportunity_info=opportunity_info,
                                vendor_profile=vendor_profile,
                                output_folder=str(folder_path)
                            )
                            
                            sow_text = sow_result.get('markdown', '')
                            sow_md_path = sow_result.get('markdown_path')
                            sow_pdf_path = sow_result.get('pdf_path')
                            
                            if sow_md_path:
                                st.success(f"✅ SOW oluşturuldu: `{sow_md_path}`")
                                if sow_pdf_path:
                                    st.success(f"✅ PDF oluşturuldu: `{sow_pdf_path}`")
                                
                                st.session_state['sow_path'] = sow_md_path
                                st.session_state['sow_pdf_path'] = sow_pdf_path
                                st.session_state['sow_generated'] = True
                                st.rerun()
                            else:
                                st.error("❌ SOW oluşturulamadı!")
                except Exception as e:
                    logger.error(f"SOW generation error: {e}", exc_info=True)
                    st.error(f"❌ SOW oluşturma hatası: {str(e)}")
            
            # Oluşturulan SOW'u göster
            sow_path = st.session_state.get('sow_path')
            if sow_path and Path(sow_path).exists():
                st.markdown("---")
                st.markdown("### 📄 Oluşturulan SOW")
                
                with open(sow_path, 'r', encoding='utf-8') as f:
                    sow_content = f.read()
                
                # SOW önizleme
                st.markdown(sow_content)
                
                # İndirme butonları
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.download_button(
                        label="📥 Markdown İndir",
                        data=sow_content,
                        file_name=f"sow_{opportunity_code}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="download_sow_md"
                    )
                with col_s2:
                    # PDF dosyası varsa indir
                    sow_pdf_path = st.session_state.get('sow_pdf_path')
                    if sow_pdf_path and Path(sow_pdf_path).exists():
                        with open(sow_pdf_path, 'rb') as f:
                            pdf_data = f.read()
                        st.download_button(
                            label="📥 PDF İndir",
                            data=pdf_data,
                            file_name=f"sow_{opportunity_code}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_sow_pdf"
                        )
                    else:
                        st.info("💡 PDF oluşturuluyor...")
    
    # Live Progress Section
    # Results Preview
    if st.session_state.ai_analysis_state['results']:
        render_results_preview(st.session_state.ai_analysis_state['results'])
        
        # Mail gönderme bölümü (PDF varsa)
        results_data = st.session_state.ai_analysis_state['results'].get('data', {})
        pdf_path = results_data.get('pdf_path')
        
        if pdf_path and Path(pdf_path).exists():
            st.markdown('<div class="mail-section">', unsafe_allow_html=True)
            st.markdown("### 📨 Mail Gönderimi")
            
            col_email, col_send = st.columns([3, 1])
            
            with col_email:
                target_email = st.text_input(
                    "Alıcı E-posta",
                    value=form_data.get('target_email', '') if form_data else '',
                    key="mail_target_email",
                    help="Raporun gönderileceği e-posta adresi"
                )
            
            with col_send:
                st.markdown("<br>", unsafe_allow_html=True)  # Vertical alignment
                send_mail = st.checkbox(
                    "Bu raporu mail ile göndermeye hazırım",
                    key="mail_ready_checkbox"
                )
            
            if send_mail and target_email:
                if st.button("📨 Mail Paketi Oluştur", use_container_width=True, key="create_mail_package"):
                    try:
                        from mail_package import build_mail_package
                        
                        opportunity_code = results_data.get('opportunity_id', 'UNKNOWN')
                        folder_path = Path(pdf_path).parent
                        
                        package = build_mail_package(
                            opportunity_code=opportunity_code,
                            folder_path=str(folder_path),
                            to_email=target_email
                        )
                        
                        st.success("✅ Mail paketi hazırlandı!")
                        
                        # Mail önizleme
                        with st.expander("📧 Mail Önizleme", expanded=True):
                            st.markdown("**Konu:**")
                            st.code(package['subject'])
                            
                            st.markdown("**Alıcı:**")
                            st.code(package['to'])
                            
                            st.markdown("**Ekler:**")
                            for att in package['attachments']:
                                st.code(f"{att['filename']} ({Path(att['path']).stat().st_size / 1024:.1f} KB)")
                            
                            st.markdown("**Mail İçeriği (HTML):**")
                            st.components.v1.html(package['html_body'], height=400, scrolling=True)
                        
                        # SMTP ayarları (opsiyonel)
                        with st.expander("⚙️ SMTP Ayarları (Gönderim için)", expanded=False):
                            smtp_host = st.text_input("SMTP Host", value="smtp.office365.com", key="smtp_host")
                            smtp_port = st.number_input("SMTP Port", value=587, key="smtp_port")
                            smtp_username = st.text_input("SMTP Username", key="smtp_username")
                            smtp_password = st.text_input("SMTP Password", type="password", key="smtp_password")
                            use_tls = st.checkbox("Use TLS", value=True, key="smtp_tls")
                            
                            if st.button("📤 Mail Gönder", key="send_email_button"):
                                try:
                                    from mail_package import send_email_via_smtp
                                    
                                    smtp_config = {
                                        'host': smtp_host,
                                        'port': int(smtp_port),
                                        'username': smtp_username,
                                        'password': smtp_password,
                                        'use_tls': use_tls
                                    }
                                    
                                    if send_email_via_smtp(package, smtp_config):
                                        st.success(f"✅ Mail başarıyla gönderildi: {target_email}")
                                    else:
                                        st.error("❌ Mail gönderilemedi. Lütfen SMTP ayarlarını kontrol edin.")
                                except Exception as e:
                                    st.error(f"❌ Mail gönderme hatası: {str(e)}")
                        
                        # Package JSON (debug için)
                        st.json({
                            "to": package['to'],
                            "subject": package['subject'],
                            "attachments_count": len(package['attachments']),
                            "opportunity_code": package['opportunity_code']
                        })
                        
                    except ImportError:
                        st.warning("⚠️ mail_package modülü bulunamadı")
                    except Exception as e:
                        st.error(f"❌ Mail paketi oluşturma hatası: {str(e)}")
                        logger.error(f"Mail package error: {e}", exc_info=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close mail-section

def start_ai_analysis(opportunity: Dict[str, Any]):
    """AI analizini başlat - Opportunity Runner ile otomatik klasör oluşturma ve analiz"""
    try:
        # Opportunity Runner'ı import et
        try:
            from opportunity_runner import analyze_opportunity
            USE_OPPORTUNITY_RUNNER = True
        except ImportError:
            USE_OPPORTUNITY_RUNNER = False
            logger.warning("opportunity_runner not available, using legacy method")
        
        # Analiz durumunu güncelle
        st.session_state.ai_analysis_state['analysis_running'] = True
        st.session_state.ai_analysis_state['current_stage'] = 0
        st.session_state.ai_analysis_state['completed_stages'] = []
        st.session_state.ai_analysis_state['start_time'] = datetime.now()
        st.session_state.ai_analysis_state['results'] = None
        
        notice_id = opportunity.get('noticeId') or opportunity.get('solicitationNumber') or opportunity.get('opportunityId', 'N/A')
        opportunity_id = opportunity.get('opportunityId') or opportunity.get('opportunity_id', '')
        
        # Fırsat kodu oluştur (Notice ID veya Opportunity ID'den)
        opportunity_code = opportunity.get('solicitationNumber') or notice_id or opportunity_id or 'UNKNOWN'
        
        # Form verilerini al
        form_data = st.session_state.get('form_data', {})
        
        # Opportunity Runner kullan (yeni yöntem)
        if USE_OPPORTUNITY_RUNNER:
            try:
                logger.info(f"[Opportunity Runner] Starting analysis for: {opportunity_code}")
                
                # Progress container
                progress_container = st.empty()
                status_container = st.empty()
                
                with progress_container.container():
                    st.info("🚀 Fırsat analizi başlatılıyor...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                status_text.text("📁 Klasör oluşturuluyor ve dökümanlar indiriliyor...")
                progress_bar.progress(20)
                
                # Opportunity Runner ile analiz
                # download_from_sam_gov=False: Sadece mevcut klasördeki dökümanları kullan (manuel indirme için)
                # Kullanıcı dökümanları manuel olarak klasöre ekledi, bu yüzden SAM.gov API'yi kullanmıyoruz
                result = analyze_opportunity(
                    base_dir=".",
                    opportunity_code=opportunity_code,
                    notice_id=notice_id if notice_id != 'N/A' else None,
                    opportunity_id=opportunity_id if opportunity_id and len(opportunity_id) == 32 else None,
                    form_data=form_data,
                    download_from_sam_gov=False  # Sadece mevcut klasördeki dökümanları kullan
                )
                
                # Criteria results'ı topla (PDF için)
                # Bu bilgiyi legacy method'dan alacağız, şimdilik boş
                criteria_results_for_pdf = {}
                
                progress_bar.progress(100)
                status_text.text("✅ Analiz tamamlandı!")
                
                # Sonuçları session state'e kaydet
                report_path = Path(result['metadata']['folder']) / 'report.json'
                summary_path = Path(result['metadata']['folder']) / 'summary.md'
                
                # Report ve summary'yi oku
                if report_path.exists():
                    import json
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                else:
                    report_data = result.get('report', {})
                
                if summary_path.exists():
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_md = f.read()
                else:
                    summary_md = result.get('summary_md', '')
                
                # PDF path'i al
                pdf_path = result['metadata'].get('report_pdf_path')
                
                # Sonuçları formatla (mevcut format ile uyumlu)
                st.session_state.ai_analysis_state['results'] = {
                    'success': True,
                    'documents_processed': result['metadata'].get('documents_count', 0),
                    'requirements_count': len(report_data.get('event_requirements', {})),
                    'risk_level': report_data.get('fit_assessment', {}).get('overall_score', 0) < 50 and 'high' or 'medium',
                    'duration': result['metadata'].get('analysis_duration_seconds', 0),
                    'data': {
                        'opportunity_id': opportunity_code,
                        'analysis_completed_at': result['metadata'].get('analysis_timestamp', datetime.now().isoformat()),
                        'documents': [],  # Detaylar report'ta
                        'compliance': report_data.get('compliance', {}),
                        'requirements': report_data.get('event_requirements', {}),
                        'proposal': report_data.get('fit_assessment', {}),
                        'form_data': form_data,
                        'report_path': str(report_path),
                        'summary_path': str(summary_path),
                        'summary_md': summary_md,
                        'pdf_path': pdf_path
                    }
                }
                
                st.session_state.ai_analysis_state['analysis_running'] = False
                st.session_state.ai_analysis_state['completed_stages'] = [0, 1, 2, 3]
                
                # Veritabanına kaydet (Opportunity Runner sonuçları için)
                try:
                    from app import get_db_session
                    from mergenlite_models import AIAnalysisResult
                    
                    db = get_db_session()
                    if db:
                        try:
                            # Overall score hesapla
                            overall_score = report_data.get('fit_assessment', {}).get('overall_score', 0)
                            if isinstance(overall_score, str):
                                try:
                                    overall_score = float(overall_score)
                                except (ValueError, TypeError):
                                    overall_score = 0
                            else:
                                overall_score = float(overall_score or 0)
                            
                            # Confidence hesapla (0-1 arası)
                            confidence = overall_score / 100.0 if overall_score > 0 else 0.5
                            
                            # AIAnalysisResult kaydet
                            ai_result = AIAnalysisResult(
                                opportunity_id=notice_id if notice_id != 'N/A' else opportunity_code,
                                analysis_type='FULL_ANALYSIS',
                                result=st.session_state.ai_analysis_state['results'],  # Full results
                                confidence=confidence,
                                timestamp=datetime.now(),
                                agent_name='MergenLite Opportunity Runner'
                            )
                            
                            db.add(ai_result)
                            db.commit()
                            
                            logger.info(f"✅ Analiz sonucu veritabanına kaydedildi: {ai_result.id}")
                        except Exception as db_error:
                            logger.error(f"❌ Veritabanı kayıt hatası: {db_error}", exc_info=True)
                            db.rollback()
                        finally:
                            db.close()
                except Exception as save_error:
                    logger.error(f"❌ Analiz sonucu kaydetme hatası: {save_error}", exc_info=True)
                
                with status_container.container():
                    st.success(f"✅ Analiz tamamlandı! {result['metadata']['documents_count']} döküman analiz edildi.")
                    
                    # PDF önizleme ve indirme
                    if pdf_path and Path(pdf_path).exists():
                        st.markdown("#### 📄 Analiz Raporu (PDF)")
                        
                        # İndirme butonu
                        with open(pdf_path, 'rb') as f:
                            pdf_bytes = f.read()
                            st.download_button(
                                label="📥 PDF Raporunu İndir",
                                data=pdf_bytes,
                                file_name=f"analysis_report_{opportunity_code}.pdf",
                                mime="application/pdf",
                                key="download_pdf_report"
                            )
                        
                        # Inline önizleme (Base64 embed)
                        try:
                            import base64
                            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                            st.markdown(
                                f"""
                                <iframe
                                    src="data:application/pdf;base64,{b64}"
                                    width="100%"
                                    height="600"
                                    style="border:1px solid #ddd; margin-top: 10px;"
                                ></iframe>
                                """,
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            logger.warning(f"PDF preview failed: {e}")
                            st.info("📄 PDF raporu oluşturuldu. Yukarıdaki butonla indirebilirsiniz.")
                    else:
                        st.warning("⚠️ PDF raporu oluşturulamadı. JSON ve Markdown raporlar mevcut.")
                    
                    st.info(f"📄 JSON Rapor: {report_path}")
                    st.info(f"📝 Markdown Özet: {summary_path}")
                
                return
                
            except Exception as e:
                logger.error(f"[ERROR] Opportunity Runner failed: {e}", exc_info=True)
                st.warning(f"⚠️ Opportunity Runner hatası, eski yöntem kullanılıyor: {str(e)}")
                # Fallback to legacy method
                USE_OPPORTUNITY_RUNNER = False
        
        # Legacy method (eski kod devam ediyor)
        if not USE_OPPORTUNITY_RUNNER:
            # Progress container oluştur
            progress_container = st.empty()
            status_container = st.empty()
        
        with progress_container.container():
            st.info("🚀 Analiz başlatılıyor...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        start_time = datetime.now()
        processed_documents = []
        requirements_list = []
        compliance_result = {}
        proposal_result = {}
        
        # Stage 1: Document Processor - Gerçek döküman indirme ve işleme
        status_text.text("📄 Document Processor: PDF/DOCX indirme ve metin çıkarımı...")
        progress_bar.progress(10)
        st.session_state.ai_analysis_state['current_stage'] = 0
        
        try:
            sam = SAMIntegration()
            processor = DocumentProcessor()
            
            # Dökümanları indir - Geliştirilmiş: Hem Opportunity ID hem Notice ID ile dene
            status_text.text(f"📥 Dökümanlar indiriliyor: {notice_id}...")
            
            # Önce Notice ID ile dene
            downloaded = sam.download_documents(notice_id, dest_dir="downloads")
            
            # Eğer döküman bulunamazsa ve Opportunity ID formatındaysa, Opportunity ID ile de dene
            if not downloaded:
                opportunity_id = opportunity.get('opportunityId') or opportunity.get('opportunity_id', '')
                if opportunity_id and opportunity_id != notice_id and len(opportunity_id) == 32:
                    logger.info(f"🔄 Notice ID ile döküman bulunamadı, Opportunity ID ile deniyorum: {opportunity_id}")
                    status_text.text(f"📥 Alternatif yöntem deneniyor: {opportunity_id}...")
                    downloaded = sam.download_documents(opportunity_id, dest_dir="downloads")
            
            # Hala yoksa, opportunity details'den attachments al ve direkt işle
            if not downloaded:
                logger.info(f"🔄 Detay API'den attachments alınıyor...")
                status_text.text(f"📥 Detay API'den attachments alınıyor...")
                details = sam.get_opportunity_details(notice_id)
                if details.get('success'):
                    attachments = details.get('data', {}).get('attachments', [])
                    logger.info(f"📎 {len(attachments)} attachment bulundu (get_opportunity_details'den)")
                    
                    if attachments:
                        for att in attachments:
                            if att.get('url'):
                                try:
                                    # İndir ve işle
                                    result = sam.download_and_process_attachment(att.get('url'), att.get('title', 'document'))
                                    if result.get('success'):
                                        downloaded.append({
                                            'filename': result['data'].get('filename', 'document'),
                                            'path': result['data'].get('file_path', ''),
                                            'text': result['data'].get('text', ''),
                                            'page_count': result['data'].get('page_count', 0),
                                            'url': att.get('url'),
                                            'title': att.get('title', 'document')
                                        })
                                        logger.info(f"✅ İşlendi: {result['data'].get('filename', 'document')}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Attachment işleme hatası: {e}")
                                    continue
                    else:
                        # Attachments yoksa, description'ı döküman olarak kullan
                        description = details.get('data', {}).get('description', '')
                        title_text = details.get('data', {}).get('title', '')
                        
                        if description or title_text:
                            logger.info(f"📄 Attachments yok, description'ı döküman olarak kullanıyorum ({len(description)} karakter)")
                            combined_text = f"{title_text}\n\n{description}".strip()
                            if combined_text:
                                downloaded.append({
                                    'filename': 'opportunity_description.txt',
                                    'path': '',
                                    'text': combined_text,
                                    'page_count': 1,
                                    'url': '',
                                    'title': 'Opportunity Description'
                                })
                                logger.info(f"✅ Description döküman olarak eklendi ({len(combined_text)} karakter)")
            
            # Son çare: Opportunity'nin raw_data'sından resourceLinks ve description çıkar
            if not downloaded and opportunity.get('raw_data'):
                logger.info(f"🔄 Raw data'dan resourceLinks ve description çıkarılıyor...")
                raw_data = opportunity.get('raw_data', {})
                if isinstance(raw_data, dict):
                    # Önce nested raw_data'yı kontrol et
                    nested_raw_data = raw_data.get('raw_data', {})
                    if nested_raw_data and isinstance(nested_raw_data, dict):
                        raw_data = nested_raw_data
                    
                    # 1. resourceLinks'ten attachments indir
                    resource_links = raw_data.get('resourceLinks', [])
                    if resource_links:
                        logger.info(f"📎 {len(resource_links)} resourceLink bulundu (raw_data'dan)")
                        for i, link in enumerate(resource_links, 1):
                            url = link if isinstance(link, str) else (link.get('url') or link.get('link') or link.get('downloadUrl') or link.get('href'))
                            if url:
                                try:
                                    title = f'Attachment {i}' if isinstance(link, str) else (link.get('title') or link.get('name') or f'Attachment {i}')
                                    result = sam.download_and_process_attachment(url, title)
                                    if result.get('success'):
                                        downloaded.append({
                                            'filename': result['data'].get('filename', title),
                                            'path': result['data'].get('file_path', ''),
                                            'text': result['data'].get('text', ''),
                                            'page_count': result['data'].get('page_count', 0),
                                            'url': url,
                                            'title': title
                                        })
                                        logger.info(f"✅ İndirildi (raw_data'dan): {title}")
                                except Exception as e:
                                    logger.warning(f"⚠️ ResourceLink indirme hatası: {e}")
                    
                    # 2. Description'ı döküman olarak kullan (eğer hala döküman yoksa)
                    if not downloaded:
                        description = raw_data.get('description', '') or raw_data.get('additionalInfoText', '') or raw_data.get('summary', '') or raw_data.get('descriptionText', '')
                        title_text = raw_data.get('title', '') or opportunity.get('title', '')
                        
                        # Description URL değilse (string ve http ile başlamıyorsa)
                        if description and isinstance(description, str) and not description.startswith('http'):
                            # Tüm olası alanları kontrol et
                            all_text_parts = []
                            if title_text:
                                all_text_parts.append(title_text)
                            if description:
                                all_text_parts.append(description)
                            for key in ['additionalInfoText', 'summary', 'descriptionText', 'fullDescription', 'opportunityDescription']:
                                if raw_data.get(key) and isinstance(raw_data[key], str) and not raw_data[key].startswith('http'):
                                    all_text_parts.append(raw_data[key])
                            
                            combined_text = "\n\n".join(all_text_parts).strip()
                            
                            if combined_text:
                                downloaded.append({
                                    'filename': 'opportunity_raw_data.txt',
                                    'path': '',
                                    'text': combined_text,
                                    'page_count': max(1, len(combined_text) // 2000),
                                    'url': '',
                                    'title': 'Opportunity Raw Data'
                                })
                                logger.info(f"✅ Raw data'dan döküman oluşturuldu ({len(combined_text)} karakter)")
            
            # En son çare: Opportunity title'ı bile döküman olarak kullan
            if not downloaded:
                logger.warning(f"⚠️ Hiç döküman bulunamadı, title'ı döküman olarak kullanıyorum")
                title_text = opportunity.get('title', '')
                if title_text:
                    downloaded.append({
                        'filename': 'opportunity_title_only.txt',
                        'path': '',
                        'text': title_text,
                        'page_count': 1,
                        'url': '',
                        'title': 'Opportunity Title'
                    })
                    logger.info(f"✅ Title döküman olarak eklendi: {title_text[:50]}...")
            
            # Dökümanları işle
            if downloaded:
                status_text.text(f"📄 {len(downloaded)} döküman işleniyor...")
                logger.info(f"📄 {len(downloaded)} döküman işleniyor...")
                for doc_info in downloaded:
                    try:
                        # Eğer text zaten varsa (download_and_process_attachment'dan)
                        if 'text' in doc_info and doc_info.get('text'):
                            processed_doc = {
                                'filename': doc_info.get('filename', 'document'),
                                'text': doc_info.get('text', ''),
                                'page_count': doc_info.get('page_count', 0),
                                'file_path': doc_info.get('path', '')
                            }
                            logger.info(f"✅ Döküman zaten işlenmiş: {processed_doc['filename']} ({len(processed_doc['text'])} karakter)")
                        else:
                            # Dosya yolundan işle
                            file_path = doc_info.get('path', '')
                            if file_path and os.path.exists(file_path):
                                logger.info(f"📄 Dosya işleniyor: {file_path}")
                                result = processor.process_file_from_path(file_path)
                                if result.get('success'):
                                    processed_doc = result['data']
                                    processed_doc['file_path'] = file_path
                                    logger.info(f"✅ İşlendi: {processed_doc.get('filename', 'document')} ({processed_doc.get('page_count', 0)} sayfa)")
                                else:
                                    logger.warning(f"⚠️ İşleme başarısız: {file_path} - {result.get('error', 'Unknown error')}")
                                    continue
                            else:
                                logger.warning(f"⚠️ Dosya bulunamadı: {file_path}")
                                continue
                        
                        processed_documents.append(processed_doc)
                    except Exception as e:
                        logger.warning(f"⚠️ Döküman işleme hatası: {e}", exc_info=True)
                        continue
            else:
                logger.warning(f"⚠️ Hiç döküman indirilemedi: {notice_id}")
                status_text.text(f"⚠️ Döküman bulunamadı. Bu fırsat için ek döküman olmayabilir.")
        except Exception as e:
            logger.error(f"❌ Document Processor hatası: {e}", exc_info=True)
            st.warning(f"⚠️ Döküman işleme hatası: {str(e)}")
        
        # İşlenen dökümanları göster + Belge tipine göre özelleştirilmiş analiz
        if processed_documents:
            with status_container.container():
                st.markdown("#### 📄 İşlenen Dokümanlar")
                
                # Form verilerini al
                form_data = st.session_state.get('form_data', {})
                llm_analyzer = LLMAnalyzer()
                
                for doc in processed_documents:
                    doc_name = doc.get('filename', 'Dosya')
                    page_count = doc.get('page_count', 0)
                    text_length = len(doc.get('text', ''))
                    
                    # Belge tipini tespit et
                    doc_type = "general"
                    doc_name_lower = doc_name.lower()
                    if "rfq" in doc_name_lower or "request" in doc_name_lower or "quote" in doc_name_lower:
                        doc_type = "rfq"
                    elif "sow" in doc_name_lower or "statement" in doc_name_lower or "work" in doc_name_lower:
                        doc_type = "sow"
                    elif "contract" in doc_name_lower or "signed" in doc_name_lower:
                        doc_type = "contract"
                    elif "far" in doc_name_lower or "52.204" in doc_name_lower:
                        doc_type = "far"
                    elif "performance" in doc_name_lower or "past" in doc_name_lower:
                        doc_type = "performance"
                    
                    # Form kriterlerine göre özelleştirilmiş analiz (Her kriter için ayrı tarama)
                    doc_criteria_analyses = {}
                    if form_data and form_data.get('evaluation_focus') and doc.get('text') and len(doc.get('text', '')) > 100:
                        evaluation_focus = form_data.get('evaluation_focus', [])
                        logger.info(f"📋 {doc_name} için {len(evaluation_focus)} kriter bazlı analiz yapılıyor...")
                        
                        for criteria in evaluation_focus:
                            try:
                                # Her kriter için özelleştirilmiş analiz
                                criteria_analysis = llm_analyzer.analyze_document_by_criteria(
                                    doc.get('text', ''), 
                                    criteria, 
                                    form_data
                                )
                                
                                if criteria_analysis and criteria_analysis.get('success'):
                                    doc_criteria_analyses[criteria] = criteria_analysis.get('data', {})
                                    logger.info(f"✅ {doc_name} - '{criteria}' kriteri analizi tamamlandı")
                            except Exception as e:
                                logger.warning(f"⚠️ {doc_name} - '{criteria}' kriteri analiz hatası: {e}")
                        
                        # Belge tipine göre genel analiz de yap (fallback)
                        try:
                            doc_analysis = llm_analyzer.analyze_document_by_type(doc.get('text', ''), doc_type, form_data)
                            if doc_analysis and doc_analysis.get('success'):
                                doc['document_analysis'] = doc_analysis.get('data', {})
                        except Exception as e:
                            logger.warning(f"⚠️ {doc_name} genel analiz hatası: {e}")
                        
                        # Kriter bazlı analizleri dokümana ekle
                        if doc_criteria_analyses:
                            doc['criteria_analyses'] = doc_criteria_analyses
                            logger.info(f"✅ {doc_name} için {len(doc_criteria_analyses)} kriter bazlı analiz eklendi")
                    
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border-800); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <span style="font-size: 16px;">📄</span>
                            <span style="color: var(--text-300); font-size: 14px; font-weight: 500;">{doc_name}</span>
                            <span style="color: var(--text-400); font-size: 12px; margin-left: auto;">{page_count} sayfa, {text_length} karakter</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Kriter bazlı analiz sonuçlarını göster (Form başlıkları özelinde)
                    criteria_analyses = doc.get('criteria_analyses', {})
                    if criteria_analyses:
                        st.markdown(f"""
                        <div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid var(--blue-400); border-radius: 4px; padding: 12px; margin-top: 8px;">
                            <div style="color: var(--blue-400); font-size: 12px; font-weight: 600; margin-bottom: 8px;">📊 Form Kriterleri Bazlı Analiz Sonuçları</div>
                        """, unsafe_allow_html=True)
                        
                        for criteria, criteria_data in criteria_analyses.items():
                            analysis = criteria_data.get('analysis', {})
                            compliance_score = analysis.get('compliance_score', 0)
                            matched_info = analysis.get('matched_info', [])
                            missing = analysis.get('missing_or_conflicting', [])
                            
                            # Kriter skoruna göre renk
                            score_color = "var(--emerald-400)" if compliance_score >= 80 else ("var(--amber-400)" if compliance_score >= 60 else "var(--red-400)")
                            
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.3); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                <div style="color: var(--text-300); font-size: 11px; font-weight: 600; margin-bottom: 4px;">🎯 {criteria}</div>
                                <div style="display: flex; gap: 12px; color: var(--text-400); font-size: 10px;">
                                    <span style="color: {score_color};">Uygunluk: {compliance_score}%</span>
                                    <span>Bulunan: {len(matched_info)}</span>
                                    <span>Eksik: {len(missing)}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    elif doc.get('document_analysis'):
                        # Fallback: Genel analiz sonucu
                        analysis_data = doc.get('document_analysis', {}).get('analysis', {})
                        compliance_score = analysis_data.get('compliance_score', 0)
                        matched = analysis_data.get('matched_criteria', [])
                        missing = analysis_data.get('missing_or_conflicting', [])
                        
                        st.markdown(f"""
                        <div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid var(--blue-400); border-radius: 4px; padding: 8px; margin-top: 8px;">
                            <div style="color: var(--blue-400); font-size: 12px; font-weight: 600; margin-bottom: 4px;">📊 Genel Analiz Sonucu</div>
                            <div style="color: var(--text-300); font-size: 11px;">Uygunluk: {compliance_score}% | Eşleşen: {len(matched)} | Eksik: {len(missing)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.session_state.ai_analysis_state['completed_stages'].append(0)
        progress_bar.progress(30)
        
        # Stage 2: Compliance Analyst - Detaylı uyumluluk analizi (Form verileri ile özelleştirilmiş)
        status_text.text("🛡️ Compliance Analyst: Uyumluluk ve risk değerlendirmesi (Form kriterlerine göre)...")
        progress_bar.progress(40)
        st.session_state.ai_analysis_state['current_stage'] = 1
        
        # Form verilerini al
        form_data = st.session_state.get('form_data', {})
        
        try:
            # Tüm döküman metinlerini birleştir
            combined_text = "\n\n".join([doc.get('text', '') for doc in processed_documents])
            
            if combined_text:
                compliance_score = 75  # Varsayılan
                risk_level = 'medium'
                issues = []
                
                # Detaylı risk analizi
                risk_keywords = {
                    'critical': ['urgent', 'immediate', 'critical', 'emergency', 'asap'],
                    'high': ['must', 'required', 'mandatory', 'shall', 'obligatory'],
                    'medium': ['should', 'recommended', 'preferred', 'desirable'],
                    'compliance': ['compliance', 'certification', 'accreditation', 'standard', 'regulation'],
                    'financial': ['bond', 'insurance', 'guarantee', 'warranty', 'penalty'],
                    'legal': ['liability', 'indemnification', 'contract', 'agreement', 'terms']
                }
                
                # Her kategori için skor hesapla
                category_scores = {}
                for category, keywords in risk_keywords.items():
                    count = sum(1 for keyword in keywords if keyword.lower() in combined_text.lower())
                    category_scores[category] = count
                
                # Toplam risk skoru
                critical_count = category_scores.get('critical', 0)
                high_count = category_scores.get('high', 0)
                medium_count = category_scores.get('medium', 0)
                compliance_count = category_scores.get('compliance', 0)
                financial_count = category_scores.get('financial', 0)
                legal_count = category_scores.get('legal', 0)
                
                total_risk_score = (critical_count * 10) + (high_count * 5) + (medium_count * 2) + (compliance_count * 3) + (financial_count * 4) + (legal_count * 4)
                
                # Risk seviyesi belirleme
                if total_risk_score > 50 or critical_count > 5:
                    risk_level = 'high'
                    compliance_score = max(30, 100 - total_risk_score)
                    issues.append({
                        'type': 'Yüksek Risk',
                        'description': f'{critical_count} kritik, {high_count} yüksek öncelikli gereksinim tespit edildi',
                        'severity': 'high'
                    })
                elif total_risk_score > 25 or high_count > 10:
                    risk_level = 'medium'
                    compliance_score = max(50, 100 - total_risk_score)
                    issues.append({
                        'type': 'Orta Risk',
                        'description': f'{high_count} zorunlu gereksinim tespit edildi',
                        'severity': 'medium'
                    })
                else:
                    risk_level = 'low'
                    compliance_score = max(70, 100 - total_risk_score)
                
                # Compliance gereksinimleri
                if compliance_count > 0:
                    issues.append({
                        'type': 'Uyumluluk',
                        'description': f'{compliance_count} uyumluluk/certification gereksinimi tespit edildi',
                        'severity': 'medium'
                    })
                
                # Finansal riskler
                if financial_count > 0:
                    issues.append({
                        'type': 'Finansal',
                        'description': f'{financial_count} finansal gereksinim (bond, insurance, vb.) tespit edildi',
                        'severity': 'high'
                    })
                
                # Yasal riskler
                if legal_count > 0:
                    issues.append({
                        'type': 'Yasal',
                        'description': f'{legal_count} yasal gereksinim (liability, indemnification, vb.) tespit edildi',
                        'severity': 'high'
                    })
                
                # Form verilerine göre compliance skorunu ayarla
                if form_data and form_data.get('evaluation_focus'):
                    # Form kriterlerine göre ek compliance kontrolü
                    focus_items = form_data.get('evaluation_focus', [])
                    form_based_score_adjustment = 0
                    
                    # Her kriter için kontrol
                    for focus in focus_items:
                        focus_lower = focus.lower()
                        if any(keyword in combined_text.lower() for keyword in focus_lower.split()):
                            form_based_score_adjustment += 5  # Her eşleşen kriter için +5
                    
                    # Form kriterlerine göre compliance skorunu güncelle
                    compliance_score = min(100, compliance_score + form_based_score_adjustment)
                    logger.info(f"📋 Form kriterlerine göre compliance skoru ayarlandı: {compliance_score}%")
                
                compliance_result = {
                    'score': int(compliance_score),
                    'risk_level': risk_level,
                    'issues': issues,
                    'analysis_date': datetime.now().isoformat(),
                    'documents_analyzed': len(processed_documents),
                    'category_scores': category_scores,
                    'total_risk_score': total_risk_score,
                    'form_based_analysis': bool(form_data),
                    'form_criteria_matched': len(form_data.get('evaluation_focus', [])) if form_data else 0
                }
            else:
                compliance_result = {
                    'score': 0,
                    'risk_level': 'unknown',
                    'issues': [{'type': 'Uyarı', 'description': 'Döküman metni bulunamadı', 'severity': 'low'}],
                    'analysis_date': datetime.now().isoformat(),
                    'documents_analyzed': len(processed_documents)
                }
        except Exception as e:
            logger.error(f"Compliance Analyst hatası: {e}", exc_info=True)
            compliance_result = {'score': 0, 'risk_level': 'unknown', 'issues': []}
        
        st.session_state.ai_analysis_state['completed_stages'].append(1)
        progress_bar.progress(60)
        
        # Stage 3: Requirements Extractor - Detaylı gereksinim çıkarımı (LLM/RAG ile)
        status_text.text("🔍 Requirements Extractor: Gereksinimler ve kriterler analizi...")
        progress_bar.progress(70)
        st.session_state.ai_analysis_state['current_stage'] = 2
        
        try:
            if processed_documents:
                # Tüm doküman metinlerini birleştir (tam metin kullan)
                combined_text = "\n\n".join([doc.get('text', '') for doc in processed_documents if doc.get('text')])
                logger.info(f"📄 Toplam {len(combined_text)} karakter metin birleştirildi ({len(processed_documents)} dokümandan)")
                
                # LLM/RAG ile detaylı gereksinim çıkarımı
                requirements_list = []
                
                # RAG servisi ile ilgili bölümleri bul - TÜM dokümanları kullan
                try:
                    rag_service = RAGService()
                    # Tüm doküman metinlerini RAG'e ver
                    all_doc_texts = [doc.get('text', '') for doc in processed_documents if doc.get('text')]
                    logger.info(f"🔍 RAG servisi {len(all_doc_texts)} doküman ile çalışıyor...")
                    
                    rag_context = rag_service.retrieve_relevant_context(
                        "requirements specifications criteria standards mandatory must shall need required",
                        all_doc_texts
                    )
                    logger.info(f"✅ RAG servisi {len(rag_context)} ilgili bağlam buldu")
                except Exception as e:
                    logger.warning(f"RAG servisi hatası, basit analiz kullanılıyor: {e}", exc_info=True)
                    rag_context = None
                
                # LLM Analyzer ile gereksinim çıkarımı - TÜM metni kullan (5000 karakter limit kaldırıldı)
                try:
                    llm_analyzer = LLMAnalyzer()
                    # Metin çok uzunsa, chunk'lara böl ve her chunk'ı analiz et
                    max_text_length = 15000  # OpenAI için makul limit
                    text_to_analyze = combined_text[:max_text_length] if len(combined_text) > max_text_length else combined_text
                    
                    if len(combined_text) > max_text_length:
                        logger.info(f"⚠️ Metin çok uzun ({len(combined_text)} karakter), ilk {max_text_length} karakter analiz ediliyor")
                    
                    logger.info(f"🤖 LLM Analyzer çalışıyor ({len(text_to_analyze)} karakter)...")
                    llm_result = llm_analyzer.extract_requirements(text_to_analyze, rag_context)
                    
                    if llm_result.get('success') and llm_result.get('data'):
                        req_data = llm_result['data'].get('requirements', {})
                        
                        # LLM'den gelen yapılandırılmış gereksinimleri dönüştür
                        if isinstance(req_data, dict):
                            # Oda sayısı
                            if req_data.get('room_count') and req_data.get('room_count') != 'belirtilmemiş':
                                requirements_list.append({
                                    'category': 'Kapasite',
                                    'requirement': f"Oda sayısı: {req_data.get('room_count')}",
                                    'priority': 'Yüksek',
                                    'status': 'Karşılanıyor',
                                    'source': 'LLM Analizi'
                                })
                            
                            # AV gereksinimi
                            if req_data.get('av_required'):
                                requirements_list.append({
                                    'category': 'Teknik',
                                    'requirement': 'Audio-Visual (AV) ekipman gereksinimi',
                                    'priority': 'Orta',
                                    'status': 'İnceleniyor',
                                    'source': 'LLM Analizi'
                                })
                            
                            # Tarih aralığı
                            if req_data.get('date_range') and req_data.get('date_range') != 'belirtilmemiş':
                                requirements_list.append({
                                    'category': 'Zaman',
                                    'requirement': f"Tarih aralığı: {req_data.get('date_range')}",
                                    'priority': 'Yüksek',
                                    'status': 'Karşılanıyor',
                                    'source': 'LLM Analizi'
                                })
                            
                            # Konum
                            if req_data.get('location') and req_data.get('location') != 'belirtilmemiş':
                                requirements_list.append({
                                    'category': 'Lokasyon',
                                    'requirement': f"Konum: {req_data.get('location')}",
                                    'priority': 'Yüksek',
                                    'status': 'Karşılanıyor',
                                    'source': 'LLM Analizi'
                                })
                            
                            # Kısıtlar
                            if req_data.get('constraints'):
                                for constraint in req_data.get('constraints', []):
                                    requirements_list.append({
                                        'category': 'Kısıt',
                                        'requirement': constraint,
                                        'priority': 'Yüksek',
                                        'status': 'İnceleniyor',
                                        'source': 'LLM Analizi'
                                    })
                            
                            # Diğer gereksinimler
                            if req_data.get('other_requirements'):
                                for other_req in req_data.get('other_requirements', []):
                                    requirements_list.append({
                                        'category': 'Genel',
                                        'requirement': other_req,
                                        'priority': 'Orta',
                                        'status': 'İnceleniyor',
                                        'source': 'LLM Analizi'
                                    })
                except Exception as e:
                    logger.warning(f"LLM Analyzer hatası, pattern matching kullanılıyor: {e}")
                
                # Fallback: Pattern matching (LLM yoksa veya hata verirse)
                if not requirements_list:
                    requirement_patterns = [
                        r'(?:must|shall|required|mandatory|need to|should)\s+([^\.]+)',
                        r'(?:requirement|specification|criteria|standard)\s*:?\s*([^\.]+)',
                        r'(?:minimum|maximum|at least|no more than)\s+([^\.]+)'
                    ]
                    
                    for pattern in requirement_patterns:
                        matches = re.finditer(pattern, combined_text, re.IGNORECASE)
                        for match in matches:
                            req_text = match.group(1).strip()[:200]
                            if len(req_text) > 20:
                                requirements_list.append({
                                    'category': 'Genel',
                                    'requirement': req_text,
                                    'priority': 'Yüksek' if 'must' in match.group(0).lower() or 'required' in match.group(0).lower() else 'Orta',
                                    'status': 'İnceleniyor',
                                    'source': 'Pattern Matching'
                                })
                    
                    # Tekrarları kaldır
                    seen = set()
                    unique_requirements = []
                    for req in requirements_list:
                        req_key = req['requirement'][:50]
                        if req_key not in seen:
                            seen.add(req_key)
                            unique_requirements.append(req)
                    requirements_list = unique_requirements[:20]
        except Exception as e:
            logger.error(f"Requirements Extractor hatası: {e}", exc_info=True)
            requirements_list = []
        
        st.session_state.ai_analysis_state['completed_stages'].append(2)
        progress_bar.progress(85)
        
        # Stage 4: Proposal Writer - Teklif taslağı
        status_text.text("✍️ Proposal Writer: Teklif taslağı ve öneriler...")
        progress_bar.progress(90)
        st.session_state.ai_analysis_state['current_stage'] = 3
        
        try:
            # Teklif önerileri oluştur
            recommendations = []
            if requirements_list:
                recommendations.append(f"{len(requirements_list)} adet gereksinim tespit edildi. Her birini detaylı inceleyin.")
            if compliance_result.get('risk_level') == 'high':
                recommendations.append("Yüksek risk tespit edildi. Uyumluluk gereksinimlerini önceliklendirin.")
            if processed_documents:
                recommendations.append(f"{len(processed_documents)} döküman analiz edildi. Tüm gereksinimlerin karşılandığından emin olun.")
            
            proposal_result = {
                'status': 'Taslak',
                'recommendations': recommendations if recommendations else ['Analiz tamamlandı. Teklif hazırlığına başlayabilirsiniz.'],
                'summary': f"{len(processed_documents)} döküman analiz edildi, {len(requirements_list)} gereksinim tespit edildi.",
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Proposal Writer hatası: {e}", exc_info=True)
            proposal_result = {'status': 'Hata', 'recommendations': []}
        
        # Tamamlandı
        progress_bar.progress(100)
        status_text.text("✅ Analiz tamamlandı!")
        st.session_state.ai_analysis_state['completed_stages'].append(3)
        st.session_state.ai_analysis_state['current_stage'] = 4
        st.session_state.ai_analysis_state['analysis_running'] = False
        
        # Süre hesapla
        duration = (datetime.now() - start_time).total_seconds()
        
        # Form verilerini sonuçlara ekle
        form_data_final = st.session_state.get('form_data', {})
        
        # Criteria results'ı topla (PDF için)
        criteria_results_for_pdf = {}
        for doc in processed_documents:
            doc_name = doc.get('filename', 'document')
            if doc.get('criteria_analyses'):
                criteria_results_for_pdf[doc_name] = doc.get('criteria_analyses', {})
        
        # Sonuçları oluştur - Schema: top-level metrics + detailed data
        results_data = {
            'success': True,
            'documents_processed': len(processed_documents),  # Top-level quick metric
            'requirements_count': len(requirements_list),   # Top-level quick metric
            'risk_level': compliance_result.get('risk_level', 'medium'),    # Top-level quick metric
            'duration': duration,          # Top-level quick metric
            'data': {
                'opportunity_id': notice_id,
                'analysis_completed_at': datetime.now().isoformat(),
                # Detailed data structures
                'documents': processed_documents,  # İşlenen dökümanlar
                'compliance': compliance_result,  # Compliance analysis results
                'requirements': requirements_list,  # Çıkarılan gereksinimler
                'proposal': proposal_result,  # Proposal draft
                'form_data': form_data_final,  # Form verileri (analiz kriterleri)
                'criteria_results': criteria_results_for_pdf  # PDF için
            }
        }
        
        st.session_state.ai_analysis_state['results'] = results_data
        
        # PDF raporu oluştur (legacy method için)
        try:
            from pdf_report_builder import build_pdf_report
            from opportunity_runner import prepare_opportunity_folder
            
            # Fırsat klasörünü oluştur
            opportunity_code = opportunity.get('solicitationNumber') or notice_id or 'UNKNOWN'
            folder = prepare_opportunity_folder(".", opportunity_code)
            pdf_path = folder / "analysis_report.pdf"
            
            # Report JSON formatına çevir (opportunity_requirements schema)
            report_json = {
                'opportunity_info': {
                    'solicitation_number': opportunity.get('solicitationNumber', ''),
                    'notice_id': notice_id,
                    'title': opportunity.get('title', ''),
                    'naics': opportunity.get('naicsCode', ''),
                    'response_deadline': opportunity.get('responseDeadline', '')
                },
                'event_requirements': {
                    'location': 'unknown',
                    'date_range': 'unknown',
                    'participants_min': None,
                    'participants_target': None
                },
                'commercial_terms': {},
                'compliance': compliance_result,
                'fit_assessment': {
                    'overall_score': compliance_result.get('score', 0),
                    'strengths': [],
                    'risks': [issue.get('description', '') for issue in compliance_result.get('issues', [])],
                    'blocking_issues': [],
                    'summary': f"Analysis completed. {len(processed_documents)} documents processed."
                }
            }
            
            pdf_success = build_pdf_report(
                report_json=report_json,
                output_path=str(pdf_path),
                opportunity_code=opportunity_code,
                criteria_results=criteria_results_for_pdf
            )
            
            if pdf_success:
                results_data['data']['pdf_path'] = str(pdf_path)
                logger.info(f"[OK] PDF report created: {pdf_path}")
        except Exception as e:
            logger.warning(f"[WARNING] PDF generation failed in legacy method: {e}")
        
        # Veritabanına kaydet
        try:
            from app import get_db_session
            from mergenlite_models import AIAnalysisResult
            
            db = get_db_session()
            if db:
                try:
                    # Compliance skorunu hesapla
                    compliance_score = compliance_result.get('score', 0)
                    if isinstance(compliance_score, str):
                        try:
                            compliance_score = float(compliance_score)
                        except (ValueError, TypeError):
                            compliance_score = 0
                    else:
                        compliance_score = float(compliance_score or 0)
                    
                    # Confidence hesapla (0-1 arası)
                    confidence = compliance_score / 100.0 if compliance_score > 0 else 0.5
                    
                    # AIAnalysisResult kaydet
                    ai_result = AIAnalysisResult(
                        opportunity_id=notice_id,
                        analysis_type='FULL_ANALYSIS',  # veya 'COMPLETED'
                        result=results_data,  # JSONB olarak kaydet
                        confidence=confidence,
                        timestamp=datetime.now(),
                        agent_name='MergenLite Pipeline'
                    )
                    
                    db.add(ai_result)
                    db.commit()
                    
                    logger.info(f"✅ Analiz sonucu veritabanına kaydedildi: {ai_result.id}")
                except Exception as db_error:
                    logger.error(f"❌ Veritabanı kayıt hatası: {db_error}", exc_info=True)
                    db.rollback()
                finally:
                    db.close()
        except Exception as save_error:
            logger.error(f"❌ Analiz sonucu kaydetme hatası: {save_error}", exc_info=True)
        
        progress_container.empty()
        status_container.empty()
        st.success(f"✅ Analiz başarıyla tamamlandı! {len(processed_documents)} döküman işlendi, {len(requirements_list)} gereksinim tespit edildi.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Analiz başlatılamadı: {str(e)}")
        st.session_state.ai_analysis_state['analysis_running'] = False
        import traceback
        st.exception(e)

def stop_ai_analysis():
    """AI analizini durdur"""
    st.session_state.ai_analysis_state['analysis_running'] = False
    st.info("⏹️ Analiz durduruldu.")
    st.rerun()

def render_agent_results(agent: Dict[str, Any], results: Dict[str, Any]):
    """Ajan sonuçlarını göster"""
    agent_id = agent['id']
    
    # Ajan tipine göre sonuçları göster
    if agent_id == "document_processor":
        st.markdown("#### 📄 İşlenen Dokümanlar")
        docs = results.get('data', {}).get('documents', [])  # Fixed: use 'documents' not 'documents_processed'
        if docs:
            for doc in docs:
                st.write(f"- **{doc.get('filename', 'Dosya')}**: {doc.get('page_count', 0)} sayfa, {len(doc.get('text', ''))} karakter")
        else:
            st.info("İşlenen doküman bilgisi bulunamadı.")
    
    elif agent_id == "compliance_analyst":
        st.markdown("#### 🛡️ Uyumluluk Değerlendirmesi")
        compliance = results.get('data', {}).get('compliance', {})
        if compliance:
            score = compliance.get('score', 0)
            # Safe cast: handle None or string
            if isinstance(score, str):
                try:
                    score = int(float(score))
                except (ValueError, TypeError):
                    score = 0
            else:
                score = int(score or 0)
            st.metric("Uyumluluk Skoru", f"{score}%")
            st.write(f"**Risk Seviyesi:** {compliance.get('risk_level', 'N/A')}")
            issues = compliance.get('issues', [])
            st.write(f"**Tespit Edilen Sorunlar:** {len(issues)}")
        else:
            st.info("Uyumluluk analizi henüz tamamlanmadı.")
    
    elif agent_id == "requirements_extractor":
        st.markdown("#### 🔍 Çıkarılan Gereksinimler")
        requirements = results.get('data', {}).get('requirements', [])
        if requirements:
            for req in requirements[:5]:  # İlk 5 gereksinim
                st.write(f"- **{req.get('category', 'Genel')}**: {req.get('requirement', 'N/A')}")
            if len(requirements) > 5:
                st.caption(f"... ve {len(requirements) - 5} gereksinim daha")
        else:
            st.info("Gereksinim bilgisi bulunamadı.")
    
    elif agent_id == "proposal_writer":
        st.markdown("#### ✍️ Teklif Özeti")
        proposal = results.get('data', {}).get('proposal', {})
        if proposal:
            st.write(f"**Durum:** {proposal.get('status', 'N/A')}")
            st.write(f"**Öneriler:** {len(proposal.get('recommendations', []))} adet")
        else:
            st.info("Teklif taslağı henüz oluşturulmadı.")
    
    # Genel bilgiler - Expander yerine küçük bir gösterim
    if results.get('data'):
        st.markdown("---")
        st.caption("📋 Ham Veri (JSON)")
        st.json(results.get('data'))

def render_results_preview(results: Dict[str, Any]):
    """Analiz sonuçlarının önizlemesini göster"""
    st.markdown("---")
    st.markdown("### 📊 Analiz Sonuçları Önizleme")
    
    if results.get('success'):
        st.success("✅ Analiz başarıyla tamamlandı!")
        
        # Özet metrikler
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("İşlenen Doküman", results.get('documents_processed', 0))
        with col2:
            st.metric("Çıkarılan Gereksinim", results.get('requirements_count', 0))
        with col3:
            st.metric("Tespit Edilen Risk", results.get('risk_level', 'N/A'))
        with col4:
            st.metric("Analiz Süresi", f"{results.get('duration', 0):.1f}s")
        
        # Detaylı sonuçlar
        if results.get('data'):
            with st.expander("📋 Detaylı Sonuçlar"):
                st.json(results.get('data'))
    else:
        st.error(f"❌ Analiz hatası: {results.get('error', 'Bilinmeyen hata')}")

def render_stage_1_metadata(opportunity: Dict[str, Any]):
    """Aşama 1: Metadata ve Doküman İndirme"""
    
    st.markdown("---")
    
    with st.expander("📥 Aşama 1: Veri Çekme - Metadata ve Doküman İndirme", expanded=True):
        st.markdown("""
        **Görev:** Son Teslim Tarihi, Notice ID ve Ek Dosya URL'lerinin API'den çekilmesi.
        **Doğrulama:** İlanın canlı olduğu teyit edilir.
        """)
        
        # Use Notice ID first (SAM/GSA API expects Notice ID for details endpoint)
        notice_id = opportunity.get('noticeId') or opportunity.get('solicitationNumber') or opportunity.get('opportunityId', 'N/A')
        
        if st.button("🚀 Verileri Çek", key="fetch_metadata", use_container_width=True):
            with st.spinner("Metadata ve dokümanlar çekiliyor..."):
                try:
                    sam = SAMIntegration()
                    
                    # Metadata çekme
                    metadata_result = sam.get_opportunity_details(notice_id)
                    
                    if metadata_result.get('success'):
                        # Session state'e kaydet
                        st.session_state.analysis_data['metadata'] = metadata_result.get('data', {})
                        st.session_state.analysis_data['notice_id'] = notice_id
                        
                        # Metadata göster
                        metadata = metadata_result.get('data', {})
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Notice ID", metadata.get('noticeId', notice_id))
                            st.metric("Son Teslim Tarihi", metadata.get('responseDeadLine', 'N/A'))
                            st.metric("Yayın Tarihi", metadata.get('postedDate', 'N/A'))
                        
                        with col2:
                            st.metric("Organizasyon", metadata.get('organization', 'N/A'))
                            st.metric("NAICS Kodu", metadata.get('naicsCode', 'N/A'))
                            st.metric("Durum", "✅ Canlı" if metadata.get('active', True) else "❌ Pasif")
                        
                        # Doküman URL'lerini göster
                        attachments = metadata.get('attachments', [])
                        if attachments:
                            st.markdown("### 📎 Ek Dosyalar")
                            for i, att in enumerate(attachments):
                                st.write(f"**{i+1}. {att.get('title', 'Dosya')}**")
                                st.write(f"   - URL: {att.get('url', 'N/A')}")
                                st.write(f"   - Tip: {att.get('type', 'N/A')}")
                        
                        st.success("✅ Metadata başarıyla çekildi!")
                        
                        # Bir sonraki aşamaya geç
                        if st.button("➡️ Aşama 2'ye Geç", key="next_stage_2"):
                            st.session_state.analysis_stage = 2
                            st.rerun()
                    else:
                        st.error(f"❌ Hata: {metadata_result.get('error', 'Bilinmeyen hata')}")
                
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        # Eğer metadata zaten çekilmişse göster
        if 'metadata' in st.session_state.analysis_data:
            metadata = st.session_state.analysis_data['metadata']
            st.info("✅ Metadata zaten çekilmiş. Bir sonraki aşamaya geçebilirsiniz.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Notice ID", metadata.get('noticeId', notice_id))
                st.metric("Son Teslim", metadata.get('responseDeadLine', 'N/A'))
            with col2:
                st.metric("Organizasyon", metadata.get('organization', 'N/A'))
                st.metric("Durum", "✅ Canlı")
            
            if st.button("➡️ Aşama 2'ye Geç", key="next_stage_2_alt"):
                st.session_state.analysis_stage = 2
                st.rerun()

def render_stage_2_document_processing(opportunity: Dict[str, Any]):
    """Aşama 2: Doküman İşleme - PDF/DOCX Metin Çıkarımı"""
    
    st.markdown("---")
    
    with st.expander("📄 Aşama 2: Doküman İşleme - PDF/DOCX Metin Çıkarımı", expanded=True):
        st.markdown("""
        **Görev:** Unstructured ile metin çıkarma, dosya bütünlüğü kontrolü.
        **Veri Zenginleştirme:** SOW içeriği yapılandırılmaya başlanır.
        """)
        
        if 'metadata' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 1'i tamamlayın.")
            return
        
        metadata = st.session_state.analysis_data['metadata']
        attachments = metadata.get('attachments', [])
        
        if not attachments:
            st.info("ℹ️ Bu ilan için ek dosya bulunamadı. Manuel dosya yükleme kullanabilirsiniz.")
            
            uploaded_file = st.file_uploader(
                "📁 Dosya Yükle (PDF, DOCX, DOC)",
                type=['pdf', 'docx', 'doc'],
                help="İlan dokümanını buraya yükleyin"
            )
            
            if uploaded_file and st.button("📊 Dosyayı İşle", key="process_uploaded"):
                with st.spinner("Dosya işleniyor..."):
                    try:
                        processor = DocumentProcessor()
                        result = processor.process_uploaded_file(uploaded_file)
                        
                        if result.get('success'):
                            st.session_state.analysis_data['documents'] = [result.get('data', {})]
                            st.success("✅ Dosya başarıyla işlendi!")
                            
                            # Çıkarılan metni göster
                            extracted_text = result.get('data', {}).get('text', '')
                            st.text_area("📝 Çıkarılan Metin (İlk 500 karakter)", extracted_text[:500] + "...", height=150)
                            
                            if st.button("➡️ Aşama 3'e Geç", key="next_stage_3"):
                                st.session_state.analysis_stage = 3
                                st.rerun()
                        else:
                            st.error(f"❌ Hata: {result.get('error', 'Bilinmeyen hata')}")
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
        else:
            # Dokümanları indir ve işle
            if st.button("📥 Dokümanları İndir ve İşle", key="download_process", use_container_width=True):
                with st.spinner("Dokümanlar indiriliyor ve işleniyor..."):
                    try:
                        sam = SAMIntegration()
                        processor = DocumentProcessor()
                        
                        processed_docs = []
                        progress_bar = st.progress(0)
                        
                        for i, att in enumerate(attachments):
                            progress_bar.progress((i + 1) / len(attachments))
                            
                            url = att.get('url')
                            if url:
                                # İndir ve işle
                                result = sam.download_and_process_attachment(url, att.get('title', 'document'))
                                
                                if result.get('success'):
                                    doc_data = result.get('data', {})
                                    processed_docs.append(doc_data)
                        
                        st.session_state.analysis_data['documents'] = processed_docs
                        
                        st.success(f"✅ {len(processed_docs)} doküman başarıyla işlendi!")
                        
                        # Özet göster
                        for doc in processed_docs:
                            with st.expander(f"📄 {doc.get('filename', 'Dosya')}"):
                                st.write(f"**Sayfa Sayısı:** {doc.get('page_count', 'N/A')}")
                                st.write(f"**Metin Uzunluğu:** {len(doc.get('text', ''))} karakter")
                                st.text_area("📝 Metin Önizleme", doc.get('text', '')[:500] + "...", height=150, key=f"preview_{doc.get('filename')}")
                        
                        if st.button("➡️ Aşama 3'e Geç", key="next_stage_3_download"):
                            st.session_state.analysis_stage = 3
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
        
        # Eğer dokümanlar zaten işlenmişse göster
        if 'documents' in st.session_state.analysis_data:
            st.info("✅ Dokümanlar zaten işlenmiş. Bir sonraki aşamaya geçebilirsiniz.")
            
            documents = st.session_state.analysis_data['documents']
            st.write(f"**İşlenen Doküman Sayısı:** {len(documents)}")
            
            if st.button("➡️ Aşama 3'e Geç", key="next_stage_3_alt"):
                st.session_state.analysis_stage = 3
                st.rerun()

def render_stage_3_rag_reasoning(opportunity: Dict[str, Any]):
    """Aşama 3: RAG Muhakemesi - LLM ile Özellik Çıkarımı"""
    
    st.markdown("---")
    
    with st.expander("🤖 Aşama 3: RAG Muhakemesi - LLM ile Özellik Çıkarımı", expanded=True):
        st.markdown("""
        **Görev:** LLM/Agent'ın tüm metni okuyarak Oda Sayısı, AV ve Kısıtlar'ı (örn. Alkol yasağı) JSON formatında çıkarması.
        **Kritik Bilgiler:** İhtiyaçlar
        """)
        
        if 'documents' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 2'yi tamamlayın.")
            return
        
        documents = st.session_state.analysis_data['documents']
        
        if st.button("🧠 RAG Analizi Başlat", key="start_rag", use_container_width=True):
            with st.spinner("RAG analizi yapılıyor... Bu biraz zaman alabilir."):
                try:
                    # RAG servisi ile analiz
                    rag_service = RAGService()
                    llm_analyzer = LLMAnalyzer()
                    
                    # Tüm doküman metinlerini birleştir
                    combined_text = "\n\n".join([doc.get('text', '') for doc in documents])
                    
                    # RAG ile ilgili bölümleri bul
                    rag_results = rag_service.retrieve_relevant_context(combined_text)
                    
                    # LLM ile analiz
                    analysis_result = llm_analyzer.extract_requirements(combined_text, rag_results)
                    
                    # Session state'e kaydet
                    st.session_state.analysis_data['rag_analysis'] = analysis_result
                    
                    st.success("✅ RAG analizi tamamlandı!")
                    
                    # Sonuçları göster
                    if analysis_result.get('success'):
                        requirements = analysis_result.get('data', {}).get('requirements', {})
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Oda Sayısı", requirements.get('room_count', 'N/A'))
                            st.metric("AV Gereksinimleri", "✅ Var" if requirements.get('av_required', False) else "❌ Yok")
                        
                        with col2:
                            st.metric("Tarih Aralığı", requirements.get('date_range', 'N/A'))
                            st.metric("Konum", requirements.get('location', 'N/A'))
                        
                        with col3:
                            constraints = requirements.get('constraints', [])
                            st.metric("Kısıtlar", len(constraints))
                            if constraints:
                                st.write("**Kısıtlar:**")
                                for constraint in constraints:
                                    st.write(f"- {constraint}")
                        
                        # Detaylı JSON göster
                        with st.expander("📋 Detaylı Analiz Sonuçları (JSON)"):
                            st.json(requirements)
                        
                        if st.button("➡️ Aşama 4'e Geç", key="next_stage_4"):
                            st.session_state.analysis_stage = 4
                            st.rerun()
                    else:
                        st.error(f"❌ Analiz hatası: {analysis_result.get('error', 'Bilinmeyen hata')}")
                
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
                    st.exception(e)
        
        # Eğer analiz zaten yapılmışsa göster
        if 'rag_analysis' in st.session_state.analysis_data:
            st.info("✅ RAG analizi zaten tamamlanmış. Bir sonraki aşamaya geçebilirsiniz.")
            
            analysis = st.session_state.analysis_data['rag_analysis']
            if analysis.get('success'):
                requirements = analysis.get('data', {}).get('requirements', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Oda Sayısı", requirements.get('room_count', 'N/A'))
                    st.metric("AV Gereksinimleri", "✅ Var" if requirements.get('av_required', False) else "❌ Yok")
                with col2:
                    st.metric("Tarih Aralığı", requirements.get('date_range', 'N/A'))
                    st.metric("Kısıt Sayısı", len(requirements.get('constraints', [])))
            
            if st.button("➡️ Aşama 4'e Geç", key="next_stage_4_alt"):
                st.session_state.analysis_stage = 4
                st.rerun()

def render_stage_4_final_report(opportunity: Dict[str, Any]):
    """Aşama 4: Final Rapor"""
    
    st.markdown("---")
    
    with st.expander("📊 Aşama 4: Final Rapor", expanded=True):
        st.markdown("""
        **Görev:** Tüm analiz sonuçlarının özetlenmesi ve kullanıcıya sunulması.
        """)
        
        if 'rag_analysis' not in st.session_state.analysis_data:
            st.warning("⚠️ Önce Aşama 3'ü tamamlayın.")
            return
        
        # Rapor oluştur
        if st.button("📄 Final Raporu Oluştur", key="generate_report", use_container_width=True):
            with st.spinner("Rapor oluşturuluyor..."):
                try:
                    report = generate_final_report(opportunity, st.session_state.analysis_data)
                    st.session_state.analysis_data['final_report'] = report
                    
                    st.success("✅ Final rapor oluşturuldu!")
                
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        # Raporu göster
        if 'final_report' in st.session_state.analysis_data:
            report = st.session_state.analysis_data['final_report']
            
            st.markdown("## 📊 Final Analiz Raporu")
            
            # Özet
            st.markdown("### 📋 Özet")
            st.markdown(report.get('summary', 'Özet bulunamadı.'))
            
            # Ana Bulgular
            st.markdown("### 🔍 Ana Bulgular")
            findings = report.get('findings', [])
            for i, finding in enumerate(findings, 1):
                st.write(f"{i}. {finding}")
            
            # Öneriler
            st.markdown("### 💡 Öneriler")
            recommendations = report.get('recommendations', [])
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
            
            # Detaylı Veriler
            st.markdown("### 📈 Detaylı Veriler")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Metadata")
                metadata = st.session_state.analysis_data.get('metadata', {})
                st.json(metadata)
            
            with col2:
                st.markdown("#### Gereksinimler")
                requirements = st.session_state.analysis_data.get('rag_analysis', {}).get('data', {}).get('requirements', {})
                st.json(requirements)
            
            # İndirme butonu
            st.markdown("---")
            report_json = json.dumps(report, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Raporu İndir (JSON)",
                data=report_json,
                file_name=f"mergen_analysis_{opportunity.get('opportunityId', 'report')}.json",
                mime="application/json"
            )
        else:
            st.info("ℹ️ Final raporu oluşturmak için butona tıklayın.")

def generate_final_report(opportunity: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Final raporu oluştur"""
    
    metadata = analysis_data.get('metadata', {})
    requirements = analysis_data.get('rag_analysis', {}).get('data', {}).get('requirements', {})
    documents = analysis_data.get('documents', [])
    
    report = {
        'opportunity_id': opportunity.get('opportunityId', 'N/A'),
        'title': opportunity.get('title', 'N/A'),
        'generated_at': datetime.now().isoformat(),
        'summary': f"""
        Bu analiz, {opportunity.get('opportunityId', 'N/A')} numaralı ilan için gerçekleştirilmiştir.
        {len(documents)} doküman işlenmiş ve RAG analizi ile gereksinimler çıkarılmıştır.
        """,
        'findings': [
            f"Oda gereksinimi: {requirements.get('room_count', 'Belirtilmemiş')}",
            f"AV gereksinimleri: {'Var' if requirements.get('av_required', False) else 'Yok'}",
            f"Tarih aralığı: {requirements.get('date_range', 'Belirtilmemiş')}",
            f"Tespit edilen kısıt sayısı: {len(requirements.get('constraints', []))}"
        ],
        'recommendations': [
            "Gereksinimlerin tam karşılandığından emin olun",
            "Kısıtların dikkate alındığından emin olun",
            "Tarih aralığının uygunluğunu kontrol edin"
        ],
        'metadata': metadata,
        'requirements': requirements,
        'document_count': len(documents)
    }
    
    return report

