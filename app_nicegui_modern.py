#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite - Modern NiceGUI Application
GitHub tasarımına göre modern ve profesyonel arayüz
"""

from nicegui import ui, app
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Environment variables
load_dotenv()
load_dotenv(dotenv_path='mergen/.env')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backend imports
try:
    from sam_integration import SAMIntegration
    from backend_utils import (
        load_opportunities_from_db,
        sync_opportunities_from_sam,
        get_db_session,
        DB_AVAILABLE
    )
    from mergenlite_models import Opportunity
    from opportunity_runner import download_from_sam, prepare_opportunity_folder, analyze_opportunity
    from detailed_opportunity_analysis import DetailedOpportunityAnalyzer
except ImportError as e:
    logger.warning(f"Backend import hatası: {e}")
    DB_AVAILABLE = False
    SAMIntegration = None

# Global state
app_state = {
    'current_page': 'dashboard',
    'opportunities': [],
    'selected_opportunity': None,
    'search_params': {
        'notice_id': '',
        'naics_code': '721110',
        'keyword': ''
    }
}

# Custom CSS - GitHub tasarımına göre
CUSTOM_CSS = """
<style>
    /* Gradient Background */
    body {
        background: linear-gradient(to bottom right, #eff6ff, #ffffff, #faf5ff);
        min-height: 100vh;
    }
    
    /* Background decorations */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        right: 0;
        width: 50%;
        height: 50%;
        background: radial-gradient(ellipse at top right, rgba(59, 130, 246, 0.4), transparent);
        pointer-events: none;
        z-index: 0;
    }
    
    body::after {
        content: '';
        position: fixed;
        bottom: 0;
        left: 0;
        width: 50%;
        height: 50%;
        background: radial-gradient(ellipse at bottom left, rgba(16, 185, 129, 0.3), transparent);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Main container */
    .main-container {
        position: relative;
        z-index: 1;
        max-width: 1280px;
        margin: 0 auto;
        padding: 24px;
    }
    
    /* Gradient text */
    .gradient-text {
        background: linear-gradient(to right, #2563eb, #9333ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Card styles */
    .modern-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 1);
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* KPI Card gradients */
    .kpi-card-blue {
        background: linear-gradient(to bottom right, #2563eb, #3b82f6);
        color: white;
        border: none;
    }
    
    .kpi-card-emerald {
        background: linear-gradient(to bottom right, #059669, #10b981);
        color: white;
        border: none;
    }
    
    .kpi-card-purple {
        background: linear-gradient(to bottom right, #9333ea, #a855f7);
        color: white;
        border: none;
    }
    
    .kpi-card-orange {
        background: linear-gradient(to bottom right, #ea580c, #f97316);
        color: white;
        border: none;
    }
    
    /* Navigation tabs */
    .nav-tabs {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(226, 232, 240, 1);
        border-radius: 16px;
        padding: 6px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .nav-tab {
        padding: 12px 16px;
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 500;
        cursor: pointer;
    }
    
    .nav-tab.active {
        background: linear-gradient(to right, #2563eb, #3b82f6);
        color: white;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
    }
    
    .nav-tab:not(.active) {
        color: #475569;
    }
    
    .nav-tab:not(.active):hover {
        color: #2563eb;
        background: rgba(239, 246, 255, 1);
    }
    
    /* Badge styles */
    .badge-low {
        background: rgba(209, 250, 229, 1);
        color: #047857;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-medium {
        background: rgba(254, 243, 199, 1);
        color: #92400e;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    .badge-high {
        background: rgba(254, 226, 226, 1);
        color: #991b1b;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Input styles */
    .modern-input {
        background: rgba(248, 250, 252, 1);
        border: 1px solid rgba(203, 213, 225, 1);
        border-radius: 8px;
        padding: 10px 12px;
        color: #1e293b;
    }
    
    .modern-input:focus {
        border-color: #2563eb;
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* Button styles */
    .btn-primary {
        background: linear-gradient(to right, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
        background: linear-gradient(to right, #1d4ed8, #2563eb);
        box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.4);
        transform: translateY(-1px);
    }
    
    /* Status indicator */
    .status-indicator {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
"""


def create_navigation():
    """Navigation component"""
    with ui.card().classes('nav-tabs w-full'):
        with ui.row().classes('w-full gap-2'):
            pages = [
                ('dashboard', '🏠 Dashboard'),
                ('opportunities', '🔍 Fırsat Arama'),
                ('analysis', '🤖 AI Analiz'),
                ('results', '📄 Sonuçlar')
            ]
            
            for page_id, label in pages:
                is_active = app_state['current_page'] == page_id
                btn = ui.button(label).classes('nav-tab flex-1')
                if is_active:
                    btn.classes('active', replace=True)
                btn.on('click', lambda e, p=page_id: navigate_to_page(p))


def navigate_to_page(page: str):
    """Sayfa değiştir"""
    app_state['current_page'] = page
    ui.open(f'/{page}' if page != 'dashboard' else '/')


def create_dashboard():
    """Dashboard sayfası"""
    with ui.column().classes('w-full space-y-8'):
        # Header
        with ui.column().classes('mb-8'):
            ui.label('MergenLite').classes('text-4xl font-bold gradient-text mb-2')
            ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-slate-600')
        
        # KPI Cards
        ui.label('📊 Sistem Durumu').classes('text-xl font-semibold text-slate-800 mb-5')
        
        with ui.row().classes('w-full gap-5'):
            kpi_cards = [
                ('Toplam Fırsat Sayısı', '1,247', 'kpi-card-blue', '📈'),
                ('Bugün Yeni Eklenenler', '23', 'kpi-card-emerald', '✅'),
                ('Tamamlanan Analiz', '342', 'kpi-card-purple', '✅'),
                ('Ortalama Analiz Süresi', '28sn', 'kpi-card-orange', '⏱️')
            ]
            
            for title, value, card_class, icon in kpi_cards:
                with ui.card().classes(f'modern-card {card_class} flex-1 p-6'):
                    with ui.row().classes('items-start justify-between w-full'):
                        with ui.column().classes('flex-1'):
                            ui.label(title).classes('text-white/90 text-xs mb-2 font-medium')
                            ui.label(value).classes('text-white text-3xl font-bold')
                        ui.label(icon).classes('text-3xl')
        
        # AI Agents & Recent Activities
        with ui.row().classes('w-full gap-6'):
            # AI Agents
            with ui.column().classes('flex-1'):
                ui.label('🤖 AI Ajanlar').classes('text-xl font-semibold text-slate-800 mb-5')
                
                agents = [
                    ('📄', 'Document Processor'),
                    ('🔍', 'Requirements Extractor'),
                    ('🛡️', 'Compliance Analyst'),
                    ('✍️', 'Proposal Writer')
                ]
                
                for icon, name in agents:
                    with ui.card().classes('modern-card p-4 mb-3'):
                        with ui.row().classes('items-center gap-3 w-full'):
                            ui.label(icon).classes('text-2xl')
                            ui.label(name).classes('flex-1 text-slate-700 font-medium')
                            with ui.element('div').classes('status-indicator'):
                                pass
            
            # Recent Activities
            with ui.column().classes('flex-2'):
                ui.label('📋 Son Aktiviteler').classes('text-xl font-semibold text-slate-800 mb-5')
                
                activities = [
                    {
                        'id': 'AN-12847',
                        'notice_id': 'SAM-721110-2024-001',
                        'title': 'Hotel Conference Services - Washington DC',
                        'risk': 'low',
                        'days_left': 28
                    },
                    {
                        'id': 'AN-12846',
                        'notice_id': 'SAM-721110-2024-002',
                        'title': 'Lodging Services for Federal Training Event',
                        'risk': 'medium',
                        'days_left': 12
                    },
                    {
                        'id': 'AN-12845',
                        'notice_id': 'SAM-721110-2024-003',
                        'title': 'Executive Retreat Accommodation Services',
                        'risk': 'high',
                        'days_left': 4
                    }
                ]
                
                for activity in activities:
                    with ui.card().classes('modern-card p-5 mb-3'):
                        with ui.row().classes('items-start justify-between mb-2'):
                            ui.label(activity['notice_id']).classes('text-xs text-slate-500 font-medium')
                            
                            risk_class = f"badge-{activity['risk']}"
                            risk_label = {
                                'low': 'Düşük Risk',
                                'medium': 'Orta Risk',
                                'high': 'Yüksek Risk'
                            }[activity['risk']]
                            
                            ui.badge(risk_label).classes(f'{risk_class} px-2 py-1 text-xs')
                        
                        ui.label(activity['title']).classes('text-slate-800 font-medium mb-3')
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('schedule', size='sm').classes('text-blue-600')
                            ui.label(f"{activity['days_left']} gün kaldı").classes('text-sm text-blue-600 font-medium')


def create_opportunity_center():
    """Opportunity Center sayfası"""
    with ui.column().classes('w-full space-y-6'):
        ui.label('📋 İlan Merkezi').classes('text-2xl font-semibold text-slate-800')
        
        # Search and Filter
        with ui.card().classes('modern-card p-6'):
            with ui.row().classes('w-full gap-4'):
                notice_input = ui.input('Notice ID', placeholder='Notice ID').classes('modern-input flex-1')
                naics_input = ui.input('NAICS Kodu', placeholder='NAICS Kodu', value='721110').classes('modern-input flex-1')
                keyword_input = ui.input('Anahtar Kelime', placeholder='Anahtar Kelime').classes('modern-input flex-1')
                
                def safe_search():
                    try:
                        search_opportunities()
                    except Exception as e:
                        logger.error(f"Search error: {e}", exc_info=True)
                        ui.notify(f'Arama hatası: {str(e)}', type='negative')
                
                search_btn = ui.button('🔍 Ara', icon='search').classes('btn-primary')
                search_btn.on('click', safe_search)
        
        # API Status
        with ui.card().classes('modern-card p-4 bg-emerald-50 border-emerald-200'):
            ui.label('✅ SAM.gov API bağlantısı aktif').classes('text-emerald-800')
        
        # Opportunities List
        ui.label('📋 Toplam 0 Fırsat Bulundu').classes('text-xl font-semibold text-slate-800 mb-5')
        
        # Opportunities will be loaded here
        opportunities_container = ui.column().classes('w-full space-y-4')
        
        # Load opportunities from database - async olarak yükle
        try:
            @ui.timer(0.1, once=True)  # Sayfa yüklendikten sonra yükle
            def load_data():
                try:
                    load_opportunities_ui(opportunities_container)
                except Exception as load_error:
                    logger.error(f"Error loading opportunities in timer: {load_error}", exc_info=True)
                    with opportunities_container:
                        ui.label(f'Veri yükleme hatası: {str(load_error)}').classes('text-red-600')
        except Exception as timer_error:
            logger.error(f"Error setting up timer: {timer_error}")
            # Fallback: direkt yükle
            try:
                load_opportunities_ui(opportunities_container)
            except Exception as fallback_error:
                logger.error(f"Fallback load error: {fallback_error}", exc_info=True)


def load_opportunities_ui(container: ui.column):
    """Load opportunities and display in UI"""
    try:
        if DB_AVAILABLE:
            opportunities = load_opportunities_from_db(limit=50)
            
            # Tüm değerleri güvenli hale getir - Boolean değerleri tamamen kaldır
            safe_opportunities = []
            for opp in opportunities:
                try:
                    safe_opp = {}
                    for key, value in opp.items():
                        # Boolean değerleri None'a çevir (kullanılmayacak)
                        if isinstance(value, bool):
                            safe_opp[key] = None  # Boolean değerleri None yap
                        # None değerleri olduğu gibi bırak
                        elif value is None:
                            safe_opp[key] = None
                        # String, int, float, dict, list değerleri olduğu gibi bırak
                        elif isinstance(value, (str, int, float, dict, list)):
                            safe_opp[key] = value
                        # Diğer tipleri string'e çevir
                        else:
                            try:
                                safe_opp[key] = str(value)
                            except:
                                safe_opp[key] = None
                    safe_opportunities.append(safe_opp)
                except Exception as safe_error:
                    logger.warning(f"Error sanitizing opportunity: {safe_error}", exc_info=True)
                    continue
            
            app_state['opportunities'] = safe_opportunities
            
            # Container'ı temizle ve yeni içerik ekle
            container.clear()
            
            if not safe_opportunities:
                with container:
                    ui.label('Henüz fırsat bulunamadı').classes('text-slate-600')
            else:
                for opp in safe_opportunities:
                    try:
                        create_opportunity_card(opp, container)
                    except Exception as card_error:
                        logger.error(f"Error creating card for opportunity: {card_error}", exc_info=True)
                        continue
        else:
            container.clear()
            with container:
                ui.label('Veritabanı bağlantısı yok').classes('text-slate-600')
    except Exception as e:
        logger.error(f"Error loading opportunities: {e}", exc_info=True)
        container.clear()
        with container:
            ui.label(f'Hata: {str(e)}').classes('text-red-600')


def create_opportunity_card(opp: Dict[str, Any], container: ui.column):
    """Create opportunity card"""
    try:
        # Tüm değerleri güvenli string'e çevir
        def safe_str(value, default=''):
            """Güvenli string dönüşümü"""
            if value is None:
                return default
            if isinstance(value, bool):
                return default  # Boolean değerleri kullanma
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, str):
                return value
            return str(value) if value else default
        
        # Güvenli değer çıkarma
        notice_id = safe_str(opp.get('notice_id') or opp.get('noticeId'), 'N/A')
        title = safe_str(opp.get('title'), 'Başlık Yok')
        
        # Description güvenli işleme
        description_raw = opp.get('description') or opp.get('raw_data', {}).get('description', '')
        if description_raw and not isinstance(description_raw, bool):
            description = safe_str(description_raw)
            if len(description) > 200:
                description = description[:200] + '...'
        else:
            description = ''
        
        # SAM.gov link güvenli işleme
        sam_link = opp.get('sam_gov_link') or opp.get('samGovLink')
        if sam_link and isinstance(sam_link, str) and sam_link.startswith('http'):
            sam_link_value = sam_link
        else:
            sam_link_value = None
        
        # Response deadline güvenli işleme
        deadline = opp.get('response_deadline')
        if deadline and isinstance(deadline, bool):
            deadline = None
        
        with ui.card().classes('modern-card p-6 mb-4'):
            with ui.row().classes('items-start gap-4 mb-4'):
                ui.label('📄').classes('text-3xl')
                
                with ui.column().classes('flex-1 min-w-0'):
                    with ui.row().classes('items-center gap-3 mb-2 flex-wrap'):
                        ui.label(notice_id).classes('text-blue-600 font-medium')
                        
                        if sam_link_value:
                            ui.link('SAM.gov', sam_link_value, new_tab=True).classes('text-blue-600 hover:text-blue-700')
                    
                    ui.label(title).classes('text-slate-800 font-semibold mb-2')
                    
                    if description:
                        ui.label(description).classes('text-slate-600 text-sm mb-3')
                    
                    with ui.row().classes('items-center gap-4'):
                        days_left = calculate_days_left(deadline)
                        days_class = 'text-red-600' if days_left <= 5 else 'text-orange-600' if days_left <= 10 else 'text-teal-600'
                        
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('schedule', size='sm').classes(days_class)
                            ui.label(f'{days_left} gün kaldı').classes(f'text-sm font-medium {days_class}')
                        
                        def make_analyze_handler(opp_data):
                            return lambda: analyze_opportunity_clicked(opp_data)
                        
                        analyze_btn = ui.button('🤖 Analiz Et', icon='play_arrow').classes('btn-primary')
                        analyze_btn.on('click', make_analyze_handler(opp))
    except Exception as e:
        logger.error(f"Error creating opportunity card: {e}", exc_info=True)
        with ui.card().classes('modern-card p-6 mb-4'):
            ui.label(f'Hata: {str(e)}').classes('text-red-600')


def calculate_days_left(deadline: Optional[str]) -> int:
    """Calculate days left"""
    if not deadline:
        return 0
    try:
        if isinstance(deadline, str) and len(deadline) >= 10:
            d = datetime.strptime(deadline[:10], '%Y-%m-%d')
            return (d - datetime.now()).days
    except:
        pass
    return 0


def search_opportunities():
    """Search opportunities"""
    logger.info("Searching opportunities...")
    # TODO: Implement search


def analyze_opportunity_clicked(opp: Dict[str, Any]):
    """Handle analyze button click"""
    app_state['selected_opportunity'] = opp
    app_state['current_page'] = 'analysis'
    ui.open('/analysis')
    logger.info(f"Analyzing opportunity: {opp.get('opportunity_id')}")


def create_guided_analysis():
    """Guided Analysis sayfası"""
    opp = app_state.get('selected_opportunity')
    
    with ui.column().classes('w-full space-y-6'):
        if not opp:
            ui.label('⚠️ Lütfen önce bir ilan seçin.').classes('text-slate-600 mb-4')
            ui.button('Geri', icon='arrow_back').on('click', lambda: ui.open('/opportunities'))
            return
        
        # Header
        with ui.column():
            back_btn = ui.button('Geri', icon='arrow_back').classes('mb-4')
            back_btn.on('click', lambda: ui.open('/opportunities'))
            
            # Güvenli değer çıkarma
            def safe_get(key, default='N/A'):
                val = opp.get(key) or opp.get(key.replace('_', '').lower()) or default
                if isinstance(val, bool):
                    return default
                return str(val) if val else default
            
            ui.label('🤖 AI Analiz').classes('text-2xl font-semibold text-slate-800 mb-2')
            ui.label(safe_get('notice_id', 'N/A')).classes('text-slate-600 font-medium')
            ui.label(safe_get('title', 'N/A')).classes('text-slate-700 font-semibold')
        
        # Analysis Progress
        with ui.card().classes('modern-card p-6 bg-gradient-to-br from-blue-100 to-purple-100 border-blue-300'):
            with ui.row().classes('items-center justify-between mb-4'):
                ui.label('Analiz İlerlemesi').classes('text-slate-800 font-semibold')
                ui.label('65%').classes('text-blue-700 font-bold text-lg')
            
            ui.linear_progress(value=0.65).classes('h-2.5 mb-4')
            
            with ui.row().classes('items-center gap-2'):
                ui.icon('refresh', size='sm').classes('text-blue-700 animate-spin')
                ui.label('Compliance kontrolü yapılıyor...').classes('text-xs font-medium text-blue-700')
        
        # Analysis Steps
        ui.label('📊 Analiz Aşamaları').classes('text-xl font-semibold text-slate-800 mb-5')
        
        steps = [
            ('📄', 'Döküman İşleme', 'completed'),
            ('🔍', 'Gereksinim Analizi', 'completed'),
            ('🛡️', 'Compliance Kontrolü', 'in-progress'),
            ('✍️', 'Teklif Taslağı', 'pending')
        ]
        
        with ui.row().classes('w-full gap-4'):
            for icon, name, status in steps:
                status_class = {
                    'completed': 'badge-low',
                    'in-progress': 'bg-blue-100 text-blue-700 border-blue-300',
                    'pending': 'bg-slate-100 text-slate-500 border-slate-300'
                }[status]
                
                with ui.card().classes(f'modern-card p-6 flex-1 {status_class}'):
                    with ui.row().classes('items-center gap-4'):
                        ui.label(icon).classes('text-4xl')
                        with ui.column().classes('flex-1'):
                            ui.label(name).classes('font-semibold mb-1')
                            status_label = {
                                'completed': '✅ Tamamlandı',
                                'in-progress': '⏳ Devam ediyor...',
                                'pending': '⏸️ Bekliyor'
                            }[status]
                            ui.label(status_label).classes('text-xs font-medium')


def create_results():
    """Results sayfası"""
    with ui.column().classes('w-full space-y-6'):
        ui.label('📄 Sonuçlar').classes('text-2xl font-semibold text-slate-800')
        ui.label('Analiz sonuçları burada görüntülenecek').classes('text-slate-600')


def create_page_content():
    """Page content based on current page"""
    with ui.column().classes('mt-8 w-full'):
        current = app_state['current_page']
        if current == 'dashboard':
            create_dashboard()
        elif current == 'opportunities':
            create_opportunity_center()
        elif current == 'analysis':
            create_guided_analysis()
        elif current == 'results':
            create_results()


@ui.page('/')
def main_page():
    """Ana sayfa - Dashboard"""
    ui.add_head_html(CUSTOM_CSS)
    app_state['current_page'] = 'dashboard'
    
    with ui.column().classes('main-container w-full'):
        create_navigation()
        create_page_content()


@ui.page('/opportunities')
def opportunities_page():
    """Opportunities sayfası"""
    ui.add_head_html(CUSTOM_CSS)
    app_state['current_page'] = 'opportunities'
    
    with ui.column().classes('main-container w-full'):
        create_navigation()
        create_page_content()


@ui.page('/analysis')
def analysis_page():
    """Analysis sayfası"""
    ui.add_head_html(CUSTOM_CSS)
    app_state['current_page'] = 'analysis'
    
    with ui.column().classes('main-container w-full'):
        create_navigation()
        create_page_content()


@ui.page('/results')
def results_page():
    """Results sayfası"""
    ui.add_head_html(CUSTOM_CSS)
    app_state['current_page'] = 'results'
    
    with ui.column().classes('main-container w-full'):
        create_navigation()
        create_page_content()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='MergenLite - Modern UI',
        favicon='🚀',
        port=8082,  # Farklı port kullan
        show=True,
        reload=False,
        dark=False
    )

