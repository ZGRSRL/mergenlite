#!/usr/bin/env python3
"""
MergenAI Lite - Sadeleştirilmiş İlan Analiz Platformu
Ana Streamlit uygulaması - İlan Merkezi ve Rehberli Analiz
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import os

# .env dosyasını yükle (mergen klasöründen öncelikli) - Cache bypass
try:
    from dotenv import load_dotenv
    
    # Önce mergen klasöründeki .env dosyasını yükle (force reload)
    mergen_env = 'mergen/.env'
    if os.path.exists(mergen_env):
        load_dotenv(mergen_env, override=True, verbose=False)
    else:
        load_dotenv(override=True, verbose=False)
except ImportError:
    pass

# Local imports
from guided_analysis import render_guided_analysis_page
from sam_integration import SAMIntegration

# Configure page
st.set_page_config(
    page_title="MergenAI Lite",
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
    st.session_state.current_page = 'OPPORTUNITY_CENTER'  # OPPORTUNITY_CENTER veya GUIDED_ANALYSIS

if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None

if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}

def render_opportunity_center():
    """İlan Merkezi - Fırsatları listele ve analiz için seç"""
    
    st.markdown('<h1 class="main-header">🚀 MergenAI Lite - İlan Merkezi</h1>', unsafe_allow_html=True)
    
    # SAM API entegrasyonu - Cache bypass için her seferinde fresh instance
    # Streamlit cache'i bypass etmek için @st.cache_data kullanmıyoruz
    try:
        # Environment'ı force reload et
        from dotenv import load_dotenv
        if os.path.exists('mergen/.env'):
            load_dotenv('mergen/.env', override=True)
        else:
            load_dotenv(override=True)
    except:
        pass
    
    # Fresh SAMIntegration instance (cache yok)
    sam = SAMIntegration()
    
    # API key durumu kontrolü - Her sayfa yüklemesinde göster
    api_key_status = "✅ Yüklendi" if sam.api_key else "❌ Bulunamadı"
    env_api_key = os.getenv('SAM_API_KEY', '')
    
    if not sam.api_key:
        st.error(f"""
        ⚠️ **API Key Yüklenemedi!**
        
        **Durum:**
        - Environment'ta: {"✅ Var" if env_api_key else "❌ Yok"}
        - SAMIntegration'da: {api_key_status}
        
        **Çözüm:**
        1. Streamlit'i tamamen kapatın (Ctrl+C)
        2. Cache'i temizleyin: `streamlit cache clear`
        3. Streamlit'i yeniden başlatın: `streamlit run app.py`
        4. Terminal loglarında API key yükleme mesajını kontrol edin
        
        **Debug:** Environment API key: {env_api_key[:20] if env_api_key else 'YOK'}...
        """)
    else:
        # Başarılı yükleme - sadece ilk seferinde göster
        if 'api_key_success_shown' not in st.session_state:
            st.success(f"✅ API Key başarıyla yüklendi: {sam.api_key[:20]}...")
            st.session_state.api_key_success_shown = True
    
    # Akıllı ID arama (Notice ID veya Opportunity ID)
    st.markdown("### 🔎 İlan ID ile Direkt Arama")
    st.markdown("""
    <div style="background-color: #e7f3ff; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <small>💡 <strong>Notice ID</strong> (örn: W50S7526QA010) veya <strong>Opportunity ID</strong> (örn: a81c7ad026c74b7799b0e28e735aeeb7) girin.<br>
        • Notice ID: SAM.gov sayfasında "Notice ID" veya "Solicitation Number" olarak görünür<br>
        • Opportunity ID: SAM.gov URL'sindeki 32 karakterlik hex kod (örn: /opp/a81c7ad026c74b7799b0e28e735aeeb7/view)</small>
    </div>
    """, unsafe_allow_html=True)
    
    id_search = st.text_input(
        "Notice ID veya Opportunity ID",
        placeholder="W50S7526QA010 veya a81c7ad026c74b7799b0e28e735aeeb7",
        key="id_search",
        help="SAM.gov sayfasındaki Notice ID'yi veya URL'deki Opportunity ID'yi buraya girin"
    )
    
    if st.button("🔍 İlan ID ile Ara", key="search_by_id", use_container_width=True, type="primary"):
        if id_search:
            with st.spinner(f"ID {id_search} aranıyor..."):
                try:
                    # Akıllı arama kullan - otomatik ID tipi algılama
                    opportunities = sam.search_by_any_id(id_search.strip())
                    
                    if opportunities:
                        # Demo olmayan gerçek sonuçları kontrol et
                        real_opportunities = [opp for opp in opportunities if not opp.get('opportunityId', '').startswith('DEMO-')]
                        
                        if real_opportunities:
                            st.session_state.opportunities = real_opportunities
                            id_type = "Opportunity ID" if sam._is_opportunity_id(id_search.strip()) else "Notice ID"
                            st.success(f"✅ {id_type} {id_search} bulundu! {len(real_opportunities)} gerçek sonuç.")
                        else:
                            # Sadece demo sonuçlar varsa, gerçek arama başarısız demektir
                            st.session_state.opportunities = opportunities
                            id_type = "Opportunity ID" if sam._is_opportunity_id(id_search.strip()) else "Notice ID"
                            st.warning(f"⚠️ {id_type} {id_search} SAM.gov'da bulunamadı. Demo sonuçlar gösteriliyor.")
                    else:
                        id_type = "Opportunity ID" if sam._is_opportunity_id(id_search.strip()) else "Notice ID"
                        
                        # Hata detaylarını göster
                        st.error(f"❌ {id_type} {id_search} bulunamadı.")
                        
                        # API quota kontrolü
                        st.warning("""
                        ⚠️ **Olası Nedenler:**
                        
                        1. **API Quota Limit**: API key'iniz günlük limitini aşmış olabilir
                           - Yarın tekrar deneyin (quota reset: 00:00 UTC)
                           - SAM.gov hesabınızda limit kontrolü yapın
                        
                        2. **İlan Süresi Dolmuş**: İlan 730 günden eski olabilir
                           - SAM.gov'da ilanın durumunu kontrol edin
                        
                        3. **Yanlış ID**: ID formatı hatalı olabilir
                           - Notice ID formatı kontrol edin
                           - SAM.gov sayfasından ID'yi kopyalayın
                        """)
                        
                        # Özel mesaj Opportunity ID için
                        if sam._is_opportunity_id(id_search.strip()):
                            st.info("""
                            💡 **Opportunity ID Notu:**
                            
                            URL'deki 32 karakterlik hex kod (örn: `086008536ec84226ad9de043dc738d06`) 
                            SAM.gov workspace'inin internal ID'sidir ve search API'de görünmeyebilir.
                            
                            **Çözüm:**
                            - SAM.gov sayfasından **Notice ID**'yi kopyalayın (örn: `W50S7526QA010`)
                            - Notice ID ile arama yapın
                            - Veya ilanı SAM.gov'da açıp "Notice ID" bölümünden ID'yi alın
                            """)
                        
                        # Debug bilgisi
                        with st.expander("🔍 Debug Bilgileri"):
                            st.code(f"""
API Key Durumu: {'✅ Yüklü' if sam.api_key else '❌ Bulunamadı'}
API Key: {sam.api_key[:20] + '...' if sam.api_key else 'YOK'}
Aranan ID: {id_search}
ID Tipi: {id_type}
Tarih Aralığı: Son 730 gün
                            """)
                        
                        # API key kontrolü - SAMIntegration'dan al
                        api_key_status = "✅ Yapılandırılmış" if sam.api_key else "❌ Yapılandırılmamış"
                        env_api_key = os.getenv('SAM_API_KEY', '')
                        env_status = "✅ Bulundu" if env_api_key else "❌ Bulunamadı"
                        
                        if not sam.api_key:
                            st.error(f"""
                            **❌ SAM.gov API Key Yüklenemedi!**
                            
                            **Durum:**
                            - Environment'ta: {env_status}
                            - SAMIntegration'da: {api_key_status}
                            
                            **Sorun:** API key environment'ta var ama SAMIntegration'a yüklenmemiş.
                            
                            **Çözüm:**
                            1. Streamlit'i tamamen kapatıp yeniden başlatın (Ctrl+C)
                            2. Terminal'de şunu kontrol edin:
                               ```bash
                               python -c "from dotenv import load_dotenv; import os; load_dotenv('mergen/.env'); print('API Key:', os.getenv('SAM_API_KEY', 'NOT FOUND')[:30])"
                               ```
                            3. Eğer API key görünüyorsa, Streamlit cache'ini temizleyin:
                               ```bash
                               streamlit cache clear
                               ```
                            4. Streamlit'i yeniden başlatın
                            
                            **Debug Bilgisi:**
                            - Environment SAM_API_KEY: {env_api_key[:20] if env_api_key else 'YOK'}...
                            - SAMIntegration.api_key: {sam.api_key[:20] if sam.api_key else 'YOK'}...
                            """)
                        else:
                            st.info(f"✅ API Key yüklendi: {sam.api_key[:20]}...")
                        
                        st.info("""
                        💡 **İpuçları:**
                        - **Notice ID**: SAM.gov sayfasında "Notice ID" veya "Solicitation Number" bölümünden bulabilirsiniz (örn: W50S7526QA010)
                        - **Opportunity ID**: SAM.gov URL'sinden alabilirsiniz (örn: /opp/a81c7ad026c74b7799b0e28e735aeeb7/view)
                        - Uygulama otomatik olarak ID tipini algılar ve uygun arama yapar
                        - İlanın yayın tarihi son 365 gün içinde olmalı (API limiti)
                        """)
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
                    import traceback
                    with st.expander("🔍 Detaylı Hata Bilgisi"):
                        st.code(traceback.format_exc())
        else:
            st.warning("Lütfen bir Notice ID veya Opportunity ID girin.")
    
    st.markdown("---")
    
    # Genel arama ve filtreleme
    st.markdown("### 📋 Genel Arama")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 İlan Ara",
            placeholder="Başlık veya anahtar kelime girin...",
            key="general_search"
        )
    
    with col2:
        naics_code = st.text_input(
            "NAICS Kodu",
            placeholder="721110",
            value="721110",  # Varsayılan değer (Accommodation and Food Services)
            key="naics_search",
            help="NAICS kodu (örn: 721110 - Hotels and Motels)"
        )
    
    with col3:
        days_back = st.slider("Son Günler", 1, 90, 7, key="days_back")
    
    # Fırsatları getir butonu
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
                    st.warning("Fırsat bulunamadı. Lütfen arama kriterlerinizi değiştirin.")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    
    # Fırsatları göster
    if 'opportunities' in st.session_state and st.session_state.opportunities:
        st.markdown("---")
        st.markdown("### 📋 Bulunan Fırsatlar")
        
        opportunities = st.session_state.opportunities
        
        for i, opp in enumerate(opportunities):
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
                        # Seçilen fırsatı session state'e kaydet
                        st.session_state.selected_opportunity = opp
                        st.session_state.current_page = 'GUIDED_ANALYSIS'
                        st.rerun()
    
    # Demo modu (API olmadan test için)
    with st.expander("🧪 Demo Modu - Test İlanı"):
        if st.button("Demo İlan ile Devam Et"):
            demo_opportunity = {
                'opportunityId': 'a81c7ad026c74b7799b0e28e735aeeb7',
                'noticeId': 'W50S7526QA010',
                'title': 'Demo: Konaklama ve Etkinlik Hizmetleri',
                'fullParentPathName': 'Demo Organization - Department of Defense',
                'postedDate': '2024-01-15',
                'responseDeadLine': '2024-02-15',
                'description': 'Demo açıklama metni - Konaklama ve etkinlik hizmetleri tedariki',
                'naicsCode': '721110'
            }
            st.session_state.selected_opportunity = demo_opportunity
            st.session_state.current_page = 'GUIDED_ANALYSIS'
            st.rerun()

def main():
    """Ana uygulama fonksiyonu"""
    
    # Sayfa yönlendirmesi
    if st.session_state.current_page == 'OPPORTUNITY_CENTER':
        render_opportunity_center()
    elif st.session_state.current_page == 'GUIDED_ANALYSIS':
        # Rehberli analiz sayfasına git
        if st.session_state.selected_opportunity:
            render_guided_analysis_page(st.session_state.selected_opportunity)
        else:
            st.error("Lütfen önce bir ilan seçin.")
            if st.button("← İlan Merkezine Dön"):
                st.session_state.current_page = 'OPPORTUNITY_CENTER'
                st.rerun()
    else:
        render_opportunity_center()
    
    # Alt kısım - Geri dön butonu (sadece analiz sayfasında)
    if st.session_state.current_page == 'GUIDED_ANALYSIS':
        st.markdown("---")
        if st.button("← İlan Merkezine Dön", use_container_width=True):
            st.session_state.current_page = 'OPPORTUNITY_CENTER'
            st.session_state.selected_opportunity = None
            st.rerun()

if __name__ == "__main__":
    main()

