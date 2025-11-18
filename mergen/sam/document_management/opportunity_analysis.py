"""
SAM Opportunity Analysis Page
Tek sayfada fırsat seçimi ve kapsamlı analiz
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List, Any

# Import functions
from sam_document_access_v2 import (
    fetch_opportunities,
    get_opportunity_details,
    get_opportunity_description_v2,
    get_opportunity_resource_links_v2,
    get_opportunity_documents_complete_v2
)

from autogen_analysis_center import (
    analyze_opportunity_comprehensive,
    generate_analysis_report
)

from autogen_document_manager import (
    get_manual_documents,
    get_document_analysis_results
)

def opportunity_analysis_page():
    """Fırsat analiz sayfası"""
    
    st.markdown("""
    <div class="main-header">
        🎯 SAM Fırsat Analizi
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📋 Fırsat Seçimi ve Kapsamlı Analiz</h3>
        <p>Bir fırsat seçin ve tüm detaylarını, dokümanlarını ve analizlerini tek sayfada görün.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Fırsat Arama
    with st.sidebar:
        st.header("🔍 Fırsat Arama")
        
        # Arama kriterleri
        keywords = st.text_input("Anahtar Kelimeler", placeholder="hotel, lodging, conference")
        naics_codes = st.text_input("NAICS Kodları", placeholder="721110, 721310")
        days_back = st.slider("Kaç Gün Geriye", 1, 30, 7)
        limit = st.slider("Maksimum Fırsat Sayısı", 10, 100, 50)
        
        # Arama butonu
        if st.button("🔍 Fırsatları Ara", type="primary"):
            with st.spinner("Fırsatlar aranıyor..."):
                # Keywords'ü listeye çevir
                keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
                naics_list = [n.strip() for n in naics_codes.split(",") if n.strip()] if naics_codes else None
                
                # Fırsatları getir
                result = fetch_opportunities(
                    keywords=keyword_list,
                    naics_codes=naics_list,
                    days_back=days_back,
                    limit=limit
                )
                
                if result['success']:
                    st.session_state['opportunities'] = result['opportunities']
                    st.success(f"✅ {result['count']} fırsat bulundu!")
                else:
                    st.error(f"❌ Hata: {result['error']}")
    
    # Ana içerik
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📋 Fırsat Listesi")
        
        if 'opportunities' in st.session_state and st.session_state['opportunities']:
            opportunities = st.session_state['opportunities']
            
            # Fırsat seçimi
            opportunity_options = {}
            for opp in opportunities:
                title = opp.get('title', 'Başlık Yok')[:50] + "..." if len(opp.get('title', '')) > 50 else opp.get('title', 'Başlık Yok')
                notice_id = opp.get('noticeId', 'ID Yok')
                department = opp.get('department', 'Departman Yok')
                
                option_text = f"{title} | {department} | {notice_id}"
                opportunity_options[option_text] = opp
            
            selected_opportunity_text = st.selectbox(
                "Fırsat Seçin:",
                options=list(opportunity_options.keys()),
                key="opportunity_selector"
            )
            
            if selected_opportunity_text:
                selected_opportunity = opportunity_options[selected_opportunity_text]
                st.session_state['selected_opportunity'] = selected_opportunity
                
                # Fırsat özeti
                st.markdown("### 📄 Seçilen Fırsat Özeti")
                st.write(f"**Başlık:** {selected_opportunity.get('title', 'N/A')}")
                st.write(f"**Departman:** {selected_opportunity.get('department', 'N/A')}")
                st.write(f"**Notice ID:** {selected_opportunity.get('noticeId', 'N/A')}")
                st.write(f"**Yayın Tarihi:** {selected_opportunity.get('postedDate', 'N/A')}")
                st.write(f"**Son Tarih:** {selected_opportunity.get('responseDeadLine', 'N/A')}")
                
                # Analiz butonu
                if st.button("🔬 Kapsamlı Analiz Başlat", type="primary"):
                    st.session_state['analysis_started'] = True
        else:
            st.info("👆 Sol panelden fırsat araması yapın")
    
    with col2:
        st.header("📊 Analiz Sonuçları")
        
        if 'selected_opportunity' in st.session_state:
            selected_opportunity = st.session_state['selected_opportunity']
            notice_id = selected_opportunity.get('noticeId')
            
            # Analiz başlatıldı mı?
            if st.session_state.get('analysis_started', False):
                with st.spinner("Kapsamlı analiz yapılıyor..."):
                    # 1. Fırsat Detayları
                    st.subheader("📋 Fırsat Detayları")
                    
                    details_result = get_opportunity_details(notice_id)
                    if details_result['success']:
                        opportunity = details_result['opportunity']
                        
                        col_detail1, col_detail2 = st.columns(2)
                        
                        with col_detail1:
                            st.write("**Temel Bilgiler:**")
                            st.write(f"• Başlık: {opportunity.get('title', 'N/A')}")
                            st.write(f"• Departman: {opportunity.get('department', 'N/A')}")
                            st.write(f"• Yayın Tarihi: {opportunity.get('postedDate', 'N/A')}")
                            st.write(f"• Son Tarih: {opportunity.get('responseDeadLine', 'N/A')}")
                        
                        with col_detail2:
                            st.write("**İletişim Bilgileri:**")
                            poc = opportunity.get('pointOfContact', {})
                            if poc:
                                st.write(f"• İsim: {poc.get('name', 'N/A')}")
                                st.write(f"• Email: {poc.get('email', 'N/A')}")
                                st.write(f"• Telefon: {poc.get('phone', 'N/A')}")
                    
                    # 2. Fırsat Açıklaması
                    st.subheader("📝 Fırsat Açıklaması")
                    
                    description_result = get_opportunity_description_v2(notice_id)
                    if description_result['success']:
                        st.text_area(
                            "Açıklama İçeriği:",
                            value=description_result.get('content', 'İçerik bulunamadı'),
                            height=200,
                            disabled=True
                        )
                    else:
                        st.error(f"Açıklama alınamadı: {description_result.get('error', 'Bilinmeyen hata')}")
                    
                    # 3. Resource Links
                    st.subheader("📎 Ek Dokümanlar")
                    
                    resource_links = get_opportunity_resource_links_v2(notice_id)
                    if resource_links:
                        st.write(f"**{len(resource_links)} ek doküman bulundu:**")
                        
                        for i, link in enumerate(resource_links, 1):
                            with st.expander(f"📄 {link.get('title', 'Başlık Yok')}"):
                                st.write(f"**Tür:** {link.get('type', 'N/A')}")
                                st.write(f"**Açıklama:** {link.get('description', 'N/A')}")
                                st.write(f"**URL:** {link.get('url', 'N/A')}")
                                st.write(f"**Kaynak:** {link.get('source', 'N/A')}")
                    else:
                        st.info("Ek doküman bulunamadı")
                    
                    # 4. Manuel Dokümanlar
                    st.subheader("📁 Manuel Yüklenen Dokümanlar")
                    
                    manual_docs = get_manual_documents(notice_id=notice_id)
                    if manual_docs:
                        st.write(f"**{len(manual_docs)} manuel doküman bulundu:**")
                        
                        for doc in manual_docs:
                            with st.expander(f"📄 {doc.get('title', 'Başlık Yok')}"):
                                st.write(f"**Açıklama:** {doc.get('description', 'N/A')}")
                                st.write(f"**Dosya Türü:** {doc.get('file_type', 'N/A')}")
                                st.write(f"**Yüklenme Tarihi:** {doc.get('upload_date', 'N/A')}")
                                st.write(f"**Etiketler:** {', '.join(doc.get('tags', []))}")
                                st.write(f"**Analiz Durumu:** {doc.get('analysis_status', 'N/A')}")
                    else:
                        st.info("Bu fırsat için manuel doküman bulunamadı")
                    
                    # 5. AI Analizi
                    st.subheader("🤖 AI Analizi")
                    
                    if st.button("🧠 AI Analizi Başlat", type="secondary"):
                        with st.spinner("AI analizi yapılıyor..."):
                            # Kapsamlı analiz
                            analysis_result = analyze_opportunity_comprehensive(notice_id)
                            
                            if analysis_result.get('success', False):
                                st.success("✅ AI analizi tamamlandı!")
                                
                                # Analiz sonuçlarını göster
                                analysis_data = analysis_result.get('analysis', {})
                                
                                # Go/No-Go Skoru
                                go_no_go_score = analysis_data.get('go_no_go_score', 0)
                                st.metric("🎯 Go/No-Go Skoru", f"{go_no_go_score:.1f}/10")
                                
                                # Riskler
                                risks = analysis_data.get('risks', [])
                                if risks:
                                    st.write("**⚠️ Riskler:**")
                                    for risk in risks:
                                        st.write(f"• {risk.get('description', 'N/A')} (Skor: {risk.get('score', 'N/A')})")
                                
                                # Eksik Öğeler
                                missing_items = analysis_data.get('missing_items', [])
                                if missing_items:
                                    st.write("**❌ Eksik Öğeler:**")
                                    for item in missing_items:
                                        st.write(f"• {item}")
                                
                                # Özet
                                summary = analysis_data.get('summary', '')
                                if summary:
                                    st.write("**📝 Analiz Özeti:**")
                                    st.write(summary)
                                
                                # Aksiyon Öğeleri
                                action_items = analysis_data.get('action_items', [])
                                if action_items:
                                    st.write("**✅ Aksiyon Öğeleri:**")
                                    for item in action_items:
                                        st.write(f"• {item}")
                            else:
                                st.error(f"AI analizi başarısız: {analysis_result.get('error', 'Bilinmeyen hata')}")
                    
                    # 6. Analiz Raporu
                    st.subheader("📊 Analiz Raporu")
                    
                    if st.button("📈 Rapor Oluştur", type="secondary"):
                        with st.spinner("Rapor oluşturuluyor..."):
                            report_result = generate_analysis_report(notice_id)
                            
                            if report_result.get('success', False):
                                st.success("✅ Rapor oluşturuldu!")
                                
                                # Rapor içeriğini göster
                                report_content = report_result.get('report', '')
                                if report_content:
                                    st.text_area(
                                        "Analiz Raporu:",
                                        value=report_content,
                                        height=300,
                                        disabled=True
                                    )
                                
                                # Raporu indirme
                                if st.button("📥 Raporu İndir"):
                                    st.download_button(
                                        label="📄 PDF Olarak İndir",
                                        data=report_content,
                                        file_name=f"analysis_report_{notice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                        mime="text/plain"
                                    )
                            else:
                                st.error(f"Rapor oluşturulamadı: {report_result.get('error', 'Bilinmeyen hata')}")
            
            else:
                st.info("👆 Sol panelden 'Kapsamlı Analiz Başlat' butonuna tıklayın")
        else:
            st.info("👆 Sol panelden bir fırsat seçin")

def main():
    """Ana fonksiyon"""
    opportunity_analysis_page()

if __name__ == "__main__":
    main()
