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
from typing import Dict, Any, List, Optional

# Local imports
from sam_integration import SAMIntegration
from document_processor import DocumentProcessor
from rag_service import RAGService
from llm_analyzer import LLMAnalyzer

def render_guided_analysis_page(opportunity: Dict[str, Any]):
    """Rehberli analiz sayfasını render et"""
    
    st.markdown('<h1 class="main-header">📊 Rehberli Analiz - İlan Analizi</h1>', unsafe_allow_html=True)
    
    # Seçilen ilan bilgisi
    notice_id = opportunity.get('opportunityId', 'N/A')
    title = opportunity.get('title', 'Başlık Yok')
    
    st.markdown(f"""
    <div style="background-color: #e7f3ff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;">
        <h3>📋 Seçilen İlan</h3>
        <p><strong>Notice ID:</strong> {notice_id}</p>
        <p><strong>Başlık:</strong> {title}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Analiz durumunu kontrol et
    if 'analysis_stage' not in st.session_state:
        st.session_state.analysis_stage = 1  # 1-4 arası aşama
    
    # 4 Aşamalı Workflow
    stages = {
        1: "📥 Aşama 1: Veri Çekme",
        2: "📄 Aşama 2: Doküman İşleme",
        3: "🤖 Aşama 3: RAG Muhakemesi",
        4: "📊 Aşama 4: Final Rapor"
    }
    
    # Progress bar
    progress = st.session_state.analysis_stage / 4
    st.progress(progress, text=f"{stages[st.session_state.analysis_stage]}")
    
    # Aşama 1: Metadata ve Doküman İndirme
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
        st.markdown("""
        **Görev:** Son Teslim Tarihi, Notice ID ve Ek Dosya URL'lerinin API'den çekilmesi.
        **Doğrulama:** İlanın canlı olduğu teyit edilir.
        """)
        
        notice_id = opportunity.get('opportunityId', 'N/A')
        
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

