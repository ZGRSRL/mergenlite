#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite - NiceGUI Version
Modern web framework ile Streamlit'in yerine geçen arayüz
Backend fonksiyonları app.py'den import edilir
"""

from nicegui import ui, app
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
import platform
import subprocess
import time
import asyncio
import threading

# Backend fonksiyonlarını import et - streamlit bağımlılığı olmadan
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
    import logging
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Backend import hatası: {e}")
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Backend import hatası: {e}")
    # Fallback: DB_AVAILABLE = False
    DB_AVAILABLE = False
    SAMIntegration = None
    download_from_sam = None
    prepare_opportunity_folder = None
    analyze_opportunity = None

# Search cache - 5 dakika TTL
SEARCH_CACHE: dict[str, tuple[float, list]] = {}
CACHE_TTL_SECONDS = 300.0  # 5 minutes

def _cache_key(notice_id: str | None, naics: list[str] | None, keywords: str | None) -> str:
    """Cache key oluştur"""
    naics_s = ','.join(naics) if naics else ''
    return f"notice={notice_id or ''}|naics={naics_s}|kw={keywords or ''}"

# Global state (Streamlit session_state yerine)
app_state = {
    'current_page': 'DASHBOARD',
    'opportunities': [],
    'search_params': {}
}

# Helper fonksiyonlar
def sanitize_code(code: str) -> str:
    """Kod temizleme - güvenli dosya adı için"""
    return ''.join(c for c in str(code).strip() if c.isalnum() or c in ('_', '-')) or 'unknown'

def days_left_from(deadline) -> int:
    """Deadline'dan kalan gün sayısını hesapla"""
    try:
        if isinstance(deadline, str) and len(deadline) >= 10:
            d = datetime.strptime(deadline[:10], '%Y-%m-%d')
        else:
            d = deadline
        return (d - datetime.now()).days if d else 0
    except Exception:
        return 0

def open_folder_for(code: str) -> str | None:
    """Klasörü aç (Windows/Mac/Linux)"""
    try:
        if prepare_opportunity_folder is not None:
            folder = prepare_opportunity_folder('.', sanitize_code(code))
        else:
            base = Path('.') / 'opportunities' / sanitize_code(code)
            base.mkdir(parents=True, exist_ok=True)
            folder = base
        system = platform.system()
        if system == 'Windows':
            subprocess.Popen(f'explorer "{folder.absolute()}"')
        elif system == 'Darwin':
            subprocess.Popen(['open', str(folder.absolute())])
        else:
            subprocess.Popen(['xdg-open', str(folder.absolute())])
        return str(folder.absolute())
    except Exception as e:
        logger.error(f'Open folder error: {e}', exc_info=True)
        return None

# UI fonksiyonları - Sayfa fonksiyonları içinde çağrılacak
# Not: NiceGUI'de UI kodları global scope'ta olamaz, sadece sayfa fonksiyonları içinde
def render_navigation(current_page='DASHBOARD'):
    # Deprecated: UI moved inside page functions
    return
    """Üst navigasyon menüsü - Sticky"""
    with ui.row().classes('w-full bg-gray-900/95 border-b border-gray-700 p-4 sticky top-0 z-50 backdrop-blur-sm'):
        with ui.row().classes('w-full max-w-7xl mx-auto items-center gap-2'):
            ui.label('🚀 MergenLite').classes('text-xl font-bold text-white mr-4')
            
            # Navigasyon butonları
            pages = [
                ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                ('📋', 'SAM OPPORTUNITIES', '/opportunities', 'OPPORTUNITY_CENTER'),
                ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                ('📄', 'Sonuçlar', '/results', 'RESULTS')
            ]
            
            for icon, label, url, page_key in pages:
                is_active = current_page == page_key
                if is_active:
                    ui.link(f'{icon} {label}', url).classes('px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition')
                else:
                    ui.link(f'{icon} {label}', url).classes('px-4 py-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-gray-800 transition')
            
            ui.element('div').classes('flex-1')
            
            # API durumu
            try:
                sam = SAMIntegration()
                api_key_ok = bool(sam.api_key)
                if api_key_ok:
                    ui.badge('✅ API Aktif', color='positive')
                else:
                    ui.badge('⚠️ API Key Yok', color='warning')
            except:
                ui.badge('❌ API Hatası', color='negative')

def opportunity_card(opp: dict):
    # Deprecated: UI moved inside page functions
    return
    """Her bir fırsat için modern kartı oluşturur (NiceGUI)"""
    
    # Risk seviyesi renkleri
    risk_color_map = {
        'low': 'bg-green-700',
        'medium': 'bg-amber-700',
        'high': 'bg-red-700'
    }
    risk_label_map = {
        'low': 'Düşük Risk',
        'medium': 'Orta Risk',
        'high': 'Yüksek Risk'
    }
    
    risk = opp.get('risk', 'medium')
    risk_color = risk_color_map.get(risk, 'bg-gray-700')
    risk_label = risk_label_map.get(risk, 'N/A')
    
    # Gün sayısı badge
    days_left = opp.get('daysLeft', 0)
    if days_left <= 5:
        days_class = 'bg-red-800 text-red-300'
    elif days_left <= 15:
        days_class = 'bg-amber-800 text-amber-300'
    else:
        days_class = 'bg-teal-800 text-teal-300'
    
    days_left_text = f"⏱️ {max(0, days_left)} gün kaldı"
    
    # Opportunity ID
    opp_id = opp.get('opportunityId') or opp.get('noticeId', 'N/A')
    title = opp.get('title', 'Başlık Yok')
    title_short = title[:60] + '...' if len(title) > 60 else title
    
    # Analiz durumu
    analyzed = opp.get('analyzed', False)
    analysis_status = "✅ Analiz Edildi" if analyzed else "⏳ Analiz Bekleniyor"
    status_color = 'text-green-400' if analyzed else 'text-amber-400'
    
    # SAM.gov link
    sam_gov_link = opp.get('samGovLink') or opp.get('sam_gov_link', '')
    
    with ui.card().classes('w-full shadow-lg bg-gray-900 border border-gray-700 transition duration-300 hover:border-blue-500').tight():
        with ui.row().classes('w-full items-start p-4'):
            with ui.column().classes('w-full gap-2'):
                # Üst satır: ID, Link, Günler
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label(f"📄 {opp_id}").classes('text-blue-400 font-semibold text-sm')
                        if sam_gov_link:
                            ui.link(
                                text="🔗 SAM.gov'da Görüntüle",
                                target=sam_gov_link
                            ).classes('text-blue-500 text-xs hover:text-blue-300')
                    ui.badge(days_left_text).classes(f'{days_class} text-xs font-bold')
                
                # Başlık
                ui.label(title_short).classes('text-lg font-bold text-white leading-tight')
                
                # Risk ve Analiz Durumu
                with ui.row().classes('w-full justify-between items-center mt-2'):
                    ui.badge(risk_label).classes(f'{risk_color} text-xs font-bold')
                    ui.label(analysis_status).classes(f'{status_color} text-sm')
        
        # Aksiyon Butonları
        with ui.row().classes('w-full bg-gray-800 p-3 justify-around border-t border-gray-700 gap-2'):
            notice_id = opp.get('noticeId') or opp.get('opportunityId', '')
            opportunity_id = opp.get('opportunityId', '')
            
            ui.button(
                "▶ Analizi Başlat",
                icon='play_arrow',
                on_click=lambda nid=notice_id, oid=opportunity_id: start_analysis(nid, oid)
            ).classes('flex-1').props('color=primary')
            
            ui.button(
                "📤 Döküman Yükle",
                icon='upload',
                on_click=lambda: ui.notify("Yükleme paneli açılıyor...")
            ).classes('flex-1').props('outline color=primary')
            
            ui.button(
                "📁 Klasörü Aç",
                icon='folder_open',
                on_click=lambda nid=notice_id: open_folder(nid)
            ).classes('flex-1').props('outline color=primary')
            
            ui.button(
                "📥 Dökümanları İndir",
                icon='download',
                on_click=lambda nid=notice_id, oid=opportunity_id: download_documents(nid, oid)
            ).classes('flex-1').props('outline color=primary')

def start_analysis(notice_id: str, opportunity_id: str):
    # Deprecated: UI moved inside page functions
    return
    """Analiz başlatma fonksiyonu"""
    try:
        from opportunity_runner import download_from_sam
        from pathlib import Path
        
        ui.notify(f"📥 Dokümanlar indiriliyor ve analiz başlatılıyor...", type='info')
        
        # Klasör oluştur
        safe_notice_id = "".join(c for c in str(notice_id).strip() if c.isalnum() or c in ("_", "-"))
        folder = Path(".") / "opportunities" / safe_notice_id
        folder.mkdir(parents=True, exist_ok=True)
        
        # Dokümanları indir
        downloaded = download_from_sam(
            folder=folder,
            notice_id=notice_id,
            opportunity_id=opportunity_id
        )
        
        if downloaded:
            ui.notify(f"✅ {len(downloaded)} döküman otomatik indirildi!", type='positive')
        else:
            ui.notify("ℹ️ Döküman bulunamadı veya zaten mevcut. Analiz devam ediyor...", type='info')
        
        # TODO: Analiz sayfasına yönlendir
        ui.notify("Analiz başlatıldı!", type='positive')
    except Exception as e:
        logger.error(f"Analiz başlatma hatası: {e}", exc_info=True)
        ui.notify(f"⚠️ Hata: {str(e)}", type='negative')

def open_folder(notice_id: str):
    # Deprecated: UI moved inside page functions
    return
    """Klasörü aç"""
    try:
        safe_notice_id = "".join(c for c in str(notice_id).strip() if c.isalnum() or c in ("_", "-"))
        folder = Path(".") / "opportunities" / safe_notice_id
        if folder.exists():
            import subprocess
            import platform
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{folder}"')
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(folder)])
            else:
                subprocess.Popen(['xdg-open', str(folder)])
            ui.notify(f"📁 Klasör açıldı: {folder}", type='info')
        else:
            ui.notify("⚠️ Klasör bulunamadı", type='warning')
    except Exception as e:
        logger.error(f"Klasör açma hatası: {e}")
        ui.notify(f"⚠️ Hata: {str(e)}", type='negative')

def download_documents(notice_id: str, opportunity_id: str):
    # Deprecated: UI moved inside page functions
    return
    """Dökümanları indir"""
    try:
        from opportunity_runner import download_from_sam
        from pathlib import Path
        
        ui.notify("📥 Dökümanlar indiriliyor...", type='info')
        
        safe_notice_id = "".join(c for c in str(notice_id).strip() if c.isalnum() or c in ("_", "-"))
        folder = Path(".") / "opportunities" / safe_notice_id
        folder.mkdir(parents=True, exist_ok=True)
        
        downloaded = download_from_sam(
            folder=folder,
            notice_id=notice_id,
            opportunity_id=opportunity_id
        )
        
        if downloaded:
            ui.notify(f"✅ {len(downloaded)} döküman indirildi!", type='positive')
        else:
            ui.notify("ℹ️ Döküman bulunamadı", type='info')
    except Exception as e:
        logger.error(f"Döküman indirme hatası: {e}", exc_info=True)
        ui.notify(f"⚠️ Hata: {str(e)}", type='negative')

# render_opportunity_center() - Artık sayfa fonksiyonları içinde tanımlı
# Bu fonksiyon global scope'tan tamamen kaldırıldı
# Tüm UI kodları sayfa fonksiyonları içine taşındı

# render_dashboard() - Artık sayfa fonksiyonları içinde tanımlı
# Bu fonksiyon global scope'tan kaldırıldı, sayfa fonksiyonları içine taşındı
def _render_dashboard_OLD():
    # Deprecated: removed
    return
    """Dashboard - NiceGUI versiyonu (DEPRECATED - sayfa içinde tanımlı)"""
    pass
    # ui.label('🏠 MergenLite Dashboard').classes('text-3xl font-bold text-white mb-6')
    
    # KPI Data
    opportunities = load_opportunities_from_db()
    total_cnt = len(opportunities) if opportunities else 0
    
    # Bugün eklenenleri hesapla
    today = datetime.now().date()
    saved_cnt = 0
    if opportunities:
        for opp in opportunities:
            created_at = opp.get('created_at')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_date = datetime.strptime(created_at[:10], '%Y-%m-%d').date()
                    else:
                        created_date = created_at.date() if hasattr(created_at, 'date') else today
                    if created_date == today:
                        saved_cnt += 1
                except:
                    pass
    
    # Tamamlanan analiz sayısı (DB'den)
    completed_analyses = 0
    if DB_AVAILABLE:
        try:
            db = get_db_session()
            if db:
                from mergenlite_models import AIAnalysisResult
                completed_analyses = db.query(AIAnalysisResult).filter(
                    AIAnalysisResult.analysis_type == 'COMPLETED'
                ).count()
                db.close()
        except:
            pass
    
    # KPI Cards (4 Sütunlu)
    ui.label('📊 Sistem Durumu').classes('text-xl font-semibold text-white mb-4')
    
    with ui.row().classes('w-full gap-4 mb-6'):
        # 1. Toplam Fırsat
        with ui.card().classes('flex-1 bg-blue-600 text-white shadow-lg relative'):
            with ui.column().classes('w-full p-4'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('flex-1'):
                        ui.label('Toplam Fırsat Sayısı').classes('text-xs opacity-80 mb-2')
                        ui.label(f'{total_cnt:,}').classes('text-4xl font-bold')
                    ui.label('📊').classes('text-2xl opacity-80')
        
        # 2. Bugün Yeni Eklenenler
        with ui.card().classes('flex-1 bg-emerald-600 text-white shadow-lg relative'):
            with ui.column().classes('w-full p-4'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('flex-1'):
                        ui.label('Bugün Yeni Eklenenler').classes('text-xs opacity-80 mb-2')
                        ui.label(f'{saved_cnt:,}').classes('text-4xl font-bold')
                        ui.label('NAICS 721110').classes('text-xs opacity-70 mt-1')
                    ui.label('📈').classes('text-2xl opacity-80')
        
        # 3. Tamamlanan Analiz
        with ui.card().classes('flex-1 bg-purple-600 text-white shadow-lg relative'):
            with ui.column().classes('w-full p-4'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('flex-1'):
                        ui.label('Tamamlanan Analiz').classes('text-xs opacity-80 mb-2')
                        ui.label(f'{completed_analyses:,}').classes('text-4xl font-bold')
                    ui.label('✅').classes('text-2xl opacity-80')
        
        # 4. Ortalama Analiz Süresi
        with ui.card().classes('flex-1 bg-orange-600 text-white shadow-lg relative'):
            with ui.column().classes('w-full p-4'):
                with ui.row().classes('w-full items-start justify-between'):
                    with ui.column().classes('flex-1'):
                        ui.label('Ortalama Analiz Süresi').classes('text-xs opacity-80 mb-2')
                        ui.label('28sn').classes('text-4xl font-bold')
                    ui.label('⏱️').classes('text-2xl opacity-80')
    
    ui.separator().classes('my-6')
    
    # AI Ajanlar ve Son Aktiviteler
    with ui.row().classes('w-full gap-6'):
        # Sol Sütun: AI Ajanlar
        with ui.column().classes('w-1/3'):
            ui.label('🤖 AI Ajanlar').classes('text-lg font-semibold text-white mb-4')
            
            agents = [
                {"name": "Document Processor", "icon": "📄", "status": "Aktif"},
                {"name": "Requirements Extractor", "icon": "🔍", "status": "Aktif"},
                {"name": "Compliance Analyst", "icon": "🛡️", "status": "Aktif"},
                {"name": "Proposal Writer", "icon": "✍️", "status": "Aktif"}
            ]
            
            for agent in agents:
                with ui.card().classes('w-full bg-gray-800 border border-gray-700 mb-3'):
                    with ui.row().classes('w-full items-center p-3'):
                        ui.label(agent['icon']).classes('text-xl mr-3')
                        ui.label(agent['name']).classes('text-white flex-1')
                        ui.badge(agent['status']).classes('bg-green-600 text-white text-xs')
        
        # Sağ Sütun: Son Aktiviteler
        with ui.column().classes('w-2/3'):
            ui.label('📋 Son Aktiviteler').classes('text-lg font-semibold text-white mb-4')
            
            recent_opportunities = load_opportunities_from_db(limit=5)
            
            if recent_opportunities:
                for opp in recent_opportunities:
                    # Risk seviyesi hesapla
                    days_left = 0
                    if opp.get('response_deadline'):
                        try:
                            if isinstance(opp['response_deadline'], str):
                                deadline_date = datetime.strptime(opp['response_deadline'][:10], '%Y-%m-%d')
                            else:
                                deadline_date = opp['response_deadline']
                            days_left = (deadline_date - datetime.now()).days
                        except:
                            pass
                    
                    if days_left <= 5:
                        risk = "high"
                    elif days_left <= 15:
                        risk = "medium"
                    else:
                        risk = "low"
                    
                    risk_color_map = {
                        'low': 'bg-green-700',
                        'medium': 'bg-amber-700',
                        'high': 'bg-red-700'
                    }
                    risk_label_map = {
                        'low': 'Düşük Risk',
                        'medium': 'Orta Risk',
                        'high': 'Yüksek Risk'
                    }
                    
                    opp_id = opp.get('opportunityId') or opp.get('noticeId') or opp.get('opportunity_id', 'N/A')
                    title = opp.get('title', 'Başlık Yok')
                    title_short = title[:60] + '...' if len(title) > 60 else title
                    days_text = f"{days_left} gün kaldı" if days_left > 0 else "Geçmiş"
                    
                    # Days badge renkleri
                    if days_left <= 5:
                        days_class = 'bg-red-800 text-red-300'
                    elif days_left <= 15:
                        days_class = 'bg-amber-800 text-amber-300'
                    else:
                        days_class = 'bg-teal-800 text-teal-300'
                    
                    with ui.card().classes('w-full bg-gray-800 border border-gray-700 mb-3'):
                        with ui.column().classes('w-full p-3 gap-2'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(f"📄 {opp_id}").classes('text-blue-400 font-semibold text-sm')
                                with ui.row().classes('items-center gap-2'):
                                    ui.badge(days_text).classes(f'{days_class} text-xs font-bold')
                                    ui.badge(risk_label_map[risk]).classes(f'{risk_color_map[risk]} text-xs font-bold')
                            ui.label(title_short).classes('text-white text-sm')
            else:
                ui.label("Henüz aktivite yok.").classes('text-amber-400')
    
    ui.separator().classes('my-6')
    
    # Hızlı Başlangıç Butonları
    with ui.row().classes('w-full gap-4'):
        ui.button(
            "🔄 Yeni İlanları Senkronize Et",
            icon='sync',
            on_click=lambda: sync_and_reload_dashboard()
        ).classes('flex-1').props('color=primary')
        
        ui.button(
            "🔍 Fırsat Ara",
            icon='search',
            on_click=lambda: ui.run_javascript('window.location.href = "/opportunities"')
        ).classes('flex-1').props('outline color=primary')

def sync_and_reload_dashboard():
    # Deprecated: UI moved inside page functions
    return
    """Dashboard için senkronizasyon"""
    try:
        ui.notify("🔄 Fırsatlar SAM.gov'dan çekiliyor...", type='info')
        sync_opportunities_from_sam("721110", days_back=30, limit=100, show_progress=False)
        ui.notify("✅ Senkronizasyon tamamlandı!", type='positive')
        # Sayfayı yenile
        ui.navigate.to('/')
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {e}", exc_info=True)
        ui.notify(f"⚠️ Hata: {str(e)}", type='negative')

# render_results_page() - Artık sayfa fonksiyonları içinde tanımlı
# Bu fonksiyon global scope'tan kaldırıldı, sayfa fonksiyonları içine taşındı
def _render_results_page_OLD():
    # Deprecated: removed
    return
    """Sonuçlar sayfası - NiceGUI versiyonu (DEPRECATED - sayfa içinde tanımlı)"""
    pass
    # ui.label('📄 Analiz Sonuçları').classes('text-3xl font-bold text-white mb-6')
    
    # Analiz Geçmişi - Veritabanından çek
    analysis_history = []
    
    if DB_AVAILABLE:
        try:
            db = get_db_session()
            if db:
                from mergenlite_models import AIAnalysisResult, Opportunity
                from sqlalchemy import or_
                import json
                
                # Analizleri çek
                analyses = db.query(AIAnalysisResult, Opportunity).outerjoin(
                    Opportunity,
                    or_(
                        AIAnalysisResult.opportunity_id == Opportunity.opportunity_id,
                        AIAnalysisResult.opportunity_id == Opportunity.notice_id
                    )
                ).order_by(AIAnalysisResult.timestamp.desc()).limit(50).all()
                
                for analysis, opp in analyses:
                    # Skor hesapla
                    skor = "N/A"
                    skor_class = "bg-gray-600"
                    result_data = analysis.result
                    
                    if isinstance(result_data, str):
                        try:
                            result_data = json.loads(result_data)
                        except:
                            result_data = {}
                    
                    if result_data and isinstance(result_data, dict):
                        # Skor hesaplama mantığı
                        fit_assessment = result_data.get('data', {}).get('proposal', {}) or result_data.get('fit_assessment', {})
                        compliance = result_data.get('data', {}).get('compliance', {}) or result_data.get('compliance', {})
                        
                        score = 0
                        if fit_assessment and fit_assessment.get('overall_score'):
                            score = int(fit_assessment.get('overall_score', 0))
                        elif compliance and compliance.get('score'):
                            score = int(compliance.get('score', 0))
                        elif analysis.confidence is not None:
                            score = int(float(analysis.confidence) * 100)
                        
                        if score >= 80:
                            skor = "Mükemmel"
                            skor_class = "bg-green-600"
                        elif score >= 60:
                            skor = "İyi"
                            skor_class = "bg-blue-600"
                        elif score >= 40:
                            skor = "Orta"
                            skor_class = "bg-amber-600"
                        else:
                            skor = "Düşük"
                            skor_class = "bg-red-600"
                    
                    # Süre hesapla
                    sure = "N/A"
                    if analysis.timestamp and analysis.created_at:
                        delta = analysis.created_at - analysis.timestamp
                        if delta.total_seconds() > 0:
                            sure = f"{delta.total_seconds():.0f}sn"
                    
                    analysis_history.append({
                        "analizId": f"AN-{analysis.id}",
                        "noticeId": opp.notice_id if opp and opp.notice_id else (analysis.opportunity_id[:20] if analysis.opportunity_id else 'N/A'),
                        "title": opp.title if opp else "Başlık Yok",
                        "tarih": analysis.timestamp.strftime("%Y-%m-%d %H:%M") if analysis.timestamp else "N/A",
                        "sure": sure,
                        "skor": skor,
                        "skorClass": skor_class,
                        "analysis_id": str(analysis.id),
                        "opportunity_id": analysis.opportunity_id,
                        "status": analysis.analysis_type,
                        "consolidated_output": result_data
                    })
                
                db.close()
        except Exception as e:
            logger.error(f"Analiz geçmişi yükleme hatası: {e}", exc_info=True)
            ui.notify(f"⚠️ Veritabanı hatası: {str(e)}", type='warning')
    
    if not analysis_history:
        ui.label("Henüz analiz sonucu bulunmuyor.").classes('text-amber-400 mb-6')
        return
    
    # Analiz Geçmişi Tablosu
    ui.label('📊 Analiz Geçmişi').classes('text-xl font-semibold text-white mb-4')
    
    # NiceGUI Table
    columns = [
        {'name': 'analizId', 'label': 'Analiz ID', 'field': 'analizId', 'required': True, 'align': 'left'},
        {'name': 'noticeId', 'label': 'Notice ID', 'field': 'noticeId', 'align': 'left'},
        {'name': 'title', 'label': 'Başlık', 'field': 'title', 'align': 'left'},
        {'name': 'tarih', 'label': 'Tarih', 'field': 'tarih', 'align': 'left'},
        {'name': 'sure', 'label': 'Süre', 'field': 'sure', 'align': 'left'},
        {'name': 'skor', 'label': 'Skor', 'field': 'skor', 'align': 'center'},
        {'name': 'status', 'label': 'Durum', 'field': 'status', 'align': 'center'},
    ]
    
    rows = analysis_history
    
    # Table oluştur - Kartlar halinde göster
    with ui.column().classes('w-full gap-3'):
        for row in rows[:20]:  # İlk 20 kayıt
            skor_badge_class = row["skorClass"]
            status_badge = 'bg-green-600' if row['status'] == 'COMPLETED' else ('bg-amber-600' if row['status'] == 'IN_PROGRESS' else 'bg-red-600')
            status_text = 'Tamamlandı' if row['status'] == 'COMPLETED' else ('Devam Ediyor' if row['status'] == 'IN_PROGRESS' else 'Başarısız')
            
            with ui.card().classes('w-full bg-gray-800 border border-gray-700 hover:border-blue-500 transition'):
                with ui.row().classes('w-full items-center p-4 gap-4'):
                    # Analiz ID
                    ui.label(row['analizId']).classes('text-blue-400 font-semibold text-sm w-24')
                    
                    # Notice ID
                    ui.label(row['noticeId']).classes('text-white text-sm w-32')
                    
                    # Başlık
                    ui.label(row['title'][:60] + '...' if len(row['title']) > 60 else row['title']).classes('text-white text-sm flex-1')
                    
                    # Tarih
                    ui.label(row['tarih']).classes('text-gray-400 text-sm w-32')
                    
                    # Süre
                    ui.label(row['sure']).classes('text-gray-400 text-sm w-16')
                    
                    # Skor
                    ui.badge(row['skor']).classes(f'{skor_badge_class} text-white text-xs font-bold')
                    
                    # Durum
                    ui.badge(status_text).classes(f'{status_badge} text-white text-xs font-bold')
                    
                    # Detay butonu
                    ui.button('📄', on_click=lambda r=row: show_analysis_detail(r)).props('flat dense')
    
    ui.separator().classes('my-6')
    
    # Detaylı Görünüm (İlk kayıt)
    if analysis_history:
        selected_analysis = analysis_history[0]
        ui.label('🔍 Detaylı Görünüm').classes('text-xl font-semibold text-white mb-4')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            ui.button("⬇️ PDF İndir", icon='download').classes('bg-blue-600')
            ui.button("📄 JSON Export", icon='code').classes('bg-gray-600')
        
        # Tabs
        with ui.tabs().classes('w-full') as tabs:
            tab_docs = ui.tab('📄 İşlenen Dokümanlar')
            tab_req = ui.tab('📋 Gereksinimler')
            tab_comp = ui.tab('🛡️ Uyumluluk')
            tab_prop = ui.tab('✍️ Teklif Taslağı')
        
        with ui.tab_panels(tabs, value=tab_docs).classes('w-full mt-4'):
            with ui.tab_panel(tab_docs):
                ui.label('İşlenen Dokümanlar Listesi').classes('text-white mb-4')
                consolidated = selected_analysis.get('consolidated_output', {})
                documents = consolidated.get('data', {}).get('documents', []) or consolidated.get('documents', [])
                if documents:
                    for doc in documents:
                        ui.label(f"📄 {doc.get('filename', doc.get('name', 'Doküman'))}").classes('text-white mb-2')
                else:
                    ui.label("Doküman bilgisi bulunamadı.").classes('text-amber-400')
            
            with ui.tab_panel(tab_req):
                ui.label('Gereksinimler Özeti').classes('text-white mb-4')
                consolidated = selected_analysis.get('consolidated_output', {})
                requirements = consolidated.get('data', {}).get('requirements', []) or consolidated.get('requirements', [])
                if requirements:
                    for req in requirements[:10]:
                        ui.label(f"• {req.get('text', req.get('requirement', 'N/A'))}").classes('text-white mb-2')
                else:
                    ui.label("Gereksinim bilgisi bulunamadı.").classes('text-amber-400')
            
            with ui.tab_panel(tab_comp):
                ui.label('Uyumluluk Skoru:').classes('text-lg text-white mb-2')
                ui.label(selected_analysis['skor']).classes('text-4xl text-green-500 font-bold mb-4')
                ui.label('Compliance Matrisi Detayları').classes('text-white')
                consolidated = selected_analysis.get('consolidated_output', {})
                compliance = consolidated.get('data', {}).get('compliance', {}) or consolidated.get('compliance', {})
                if compliance:
                    ui.json(compliance).classes('mt-4')
                else:
                    ui.label("Compliance bilgisi bulunamadı.").classes('text-amber-400')
            
            with ui.tab_panel(tab_prop):
                ui.label('Teklif Taslağı').classes('text-white mb-4')
                consolidated = selected_analysis.get('consolidated_output', {})
                proposal = consolidated.get('data', {}).get('proposal', {}) or consolidated.get('proposal', {})
                if proposal:
                    ui.json(proposal).classes('mt-4')
                else:
                    ui.label("Teklif taslağı bulunamadı.").classes('text-amber-400')

def show_analysis_detail(analysis_row):
    # Deprecated: UI moved inside page functions
    return
    """Analiz detaylarını göster"""
    ui.notify(f"Detaylar: {analysis_row['analizId']}", type='info')
    # TODO: Modal veya yeni sayfa ile detay göster

# Tema ayarları - Sayfa bazlı
def setup_theme(dark=True):
    """Tema ayarlarını yap"""
    if dark:
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()
    ui.colors(
        primary='#3b82f6',      # Mavi
        secondary='#10b981',    # Yeşil
        accent='#a855f7',       # Mor
        positive='#10b981',     # Başarı
        negative='#ef4444',     # Hata
        info='#60a5fa',         # Bilgi
        warning='#f59e0b'       # Uyarı
    )

# Test sayfası - Route'ların çalıştığını doğrulamak için
@ui.page('/test')
def test_page():
    """Test sayfası"""
    setup_theme(dark=False)
    with ui.column().classes('w-full min-h-screen bg-gray-50 p-6'):
        ui.label('✅ NiceGUI Route Test').classes('text-3xl font-bold text-gray-900')
        ui.label('Sayfa route\'ları çalışıyor!').classes('text-green-600 text-xl')

# Ana sayfa - Dashboard
@ui.page('/')
def main_page():
    """Ana sayfa - Dashboard - Açık Tema"""
    setup_theme(dark=False)  # Açık tema
    
    # Navigation - sayfa içinde tanımlı - İkinci görseldeki gibi
    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            # Sol taraf: Logo ve başlık
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            
            # Sağ taraf: Navigation bar - Beyaz, yuvarlatılmış container, ortalanmış
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📋', 'SAM OPPORTUNITIES', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📄', 'Sonuçlar', '/results', 'RESULTS')
                    ]
                    for icon, label, url, page_key in pages:
                        is_active = page_key == 'DASHBOARD'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap')
                        else:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap')
    
    # Dashboard içeriği - sayfa içinde tanımlı
    def render_dashboard_content():
        # Başlık kaldırıldı - Navigation'da zaten var
        
        # KPI Data
        opportunities = load_opportunities_from_db()
        total_cnt = len(opportunities) if opportunities else 0
        
        # Bugün eklenenleri hesapla
        today = datetime.now().date()
        saved_cnt = 0
        if opportunities:
            for opp in opportunities:
                created_at = opp.get('created_at')
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            created_date = datetime.strptime(created_at[:10], '%Y-%m-%d').date()
                        else:
                            created_date = created_at.date() if hasattr(created_at, 'date') else today
                        if created_date == today:
                            saved_cnt += 1
                    except:
                        pass
        
        # Tamamlanan analiz sayısı (DB'den)
        completed_analyses = 0
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    from mergenlite_models import AIAnalysisResult
                    completed_analyses = db.query(AIAnalysisResult).filter(
                        AIAnalysisResult.analysis_type == 'COMPLETED'
                    ).count()
                    db.close()
            except:
                pass
        
        # KPI Cards (4 Sütunlu) - Açık Tema
        with ui.row().classes('w-full items-center mb-4'):
            ui.label('📊').classes('text-xl mr-2')
            ui.label('Sistem Durumu').classes('text-xl font-semibold text-gray-900')
        
        with ui.row().classes('w-full gap-4 mb-6'):
            # 1. Toplam Fırsat - Mavi
            with ui.card().classes('flex-1 bg-blue-600 text-white shadow-lg rounded-lg overflow-hidden'):
                with ui.column().classes('w-full p-6'):
                    with ui.row().classes('w-full items-start justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.label('Toplam Fırsat Sayısı').classes('text-sm opacity-90 mb-2')
                            ui.label(f'{total_cnt:,}').classes('text-4xl font-bold')
                        ui.element('div').classes('text-3xl opacity-80')  # Icon placeholder
            
            # 2. Bugün Yeni Eklenenler - Yeşil
            with ui.card().classes('flex-1 bg-emerald-600 text-white shadow-lg rounded-lg overflow-hidden'):
                with ui.column().classes('w-full p-6'):
                    with ui.row().classes('w-full items-start justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.label('Bugün Yeni Eklenenler').classes('text-sm opacity-90 mb-2')
                            ui.label(f'{saved_cnt:,}').classes('text-4xl font-bold')
                            # NAICS bilgisi kaldırıldı - diğerleri ile aynı boyutta olması için
                        ui.element('div').classes('text-3xl opacity-80')  # Icon placeholder
            
            # 3. Tamamlanan Analiz - Mor
            with ui.card().classes('flex-1 bg-purple-600 text-white shadow-lg rounded-lg overflow-hidden'):
                with ui.column().classes('w-full p-6'):
                    with ui.row().classes('w-full items-start justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.label('Tamamlanan Analiz').classes('text-sm opacity-90 mb-2')
                            ui.label(f'{completed_analyses:,}').classes('text-4xl font-bold')
                        ui.element('div').classes('text-3xl opacity-80')  # Icon placeholder
            
            # 4. Ortalama Analiz Süresi - Turuncu
            with ui.card().classes('flex-1 bg-orange-600 text-white shadow-lg rounded-lg overflow-hidden'):
                with ui.column().classes('w-full p-6'):
                    with ui.row().classes('w-full items-start justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.label('Ortalama Analiz Süresi').classes('text-sm opacity-90 mb-2')
                            ui.label('28sn').classes('text-4xl font-bold')
                        ui.element('div').classes('text-3xl opacity-80')  # Icon placeholder
        
        ui.separator().classes('my-6')
        
        # AI Ajanlar ve Son Aktiviteler
        with ui.row().classes('w-full gap-6'):
            # Sol Sütun: AI Ajanlar - Açık Tema
            with ui.column().classes('w-1/3'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('🤖').classes('text-lg mr-2')
                    ui.label('AI Ajanlar').classes('text-lg font-semibold text-gray-900')
                
                agents = [
                    {"name": "Document Processor", "icon": "📄", "status": "Aktif"},
                    {"name": "Requirements Extractor", "icon": "🔍", "status": "Aktif"},
                    {"name": "Compliance Analyst", "icon": "🛡️", "status": "Aktif"},
                    {"name": "Proposal Writer", "icon": "✍️", "status": "Aktif"}
                ]
                
                for agent in agents:
                    with ui.card().classes('w-full bg-white border border-gray-200 shadow-sm mb-3 rounded-lg'):
                        with ui.row().classes('w-full items-center p-4'):
                            ui.label(agent['icon']).classes('text-xl mr-3')
                            ui.label(agent['name']).classes('text-gray-900 flex-1 font-medium')
                            ui.button(agent['status']).classes('bg-blue-600 text-white text-xs px-3 py-1 rounded font-semibold').props('flat')
            
            # Sağ Sütun: Son Aktiviteler - Açık Tema
            with ui.column().classes('w-2/3'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('📋').classes('text-lg mr-2')
                    ui.label('Son Aktiviteler').classes('text-lg font-semibold text-gray-900')
                
                try:
                    recent_opportunities = load_opportunities_from_db(limit=5) or []
                except:
                    recent_opportunities = []
                
                if recent_opportunities:
                    for opp in recent_opportunities:
                        # Risk seviyesi hesapla
                        days_left = 0
                        if opp.get('response_deadline'):
                            try:
                                if isinstance(opp['response_deadline'], str):
                                    deadline_date = datetime.strptime(opp['response_deadline'][:10], '%Y-%m-%d')
                                else:
                                    deadline_date = opp['response_deadline']
                                days_left = (deadline_date - datetime.now()).days
                            except:
                                pass
                        
                        if days_left <= 5:
                            risk = "high"
                        elif days_left <= 15:
                            risk = "medium"
                        else:
                            risk = "low"
                        
                        risk_color_map = {
                            'low': 'bg-green-100 text-green-800',
                            'medium': 'bg-amber-100 text-amber-800',
                            'high': 'bg-red-100 text-red-800'
                        }
                        risk_label_map = {
                            'low': 'Düşük Risk',
                            'medium': 'Orta Risk',
                            'high': 'Yüksek Risk'
                        }
                        
                        opp_id = opp.get('opportunityId') or opp.get('noticeId') or opp.get('opportunity_id', 'N/A')
                        title = opp.get('title', 'Başlık Yok')
                        title_short = title[:60] + '...' if len(title) > 60 else title
                        days_text = f"{days_left} gün kaldı" if days_left > 0 else "Geçmiş"
                        
                        # Days badge renkleri - Açık tema
                        if days_left <= 5:
                            days_class = 'bg-red-100 text-red-800'
                        elif days_left <= 15:
                            days_class = 'bg-amber-100 text-amber-800'
                        else:
                            days_class = 'bg-teal-100 text-teal-800'
                        
                        with ui.card().classes('w-full bg-white border border-gray-200 shadow-sm mb-3 rounded-lg'):
                            with ui.column().classes('w-full p-4 gap-2'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    ui.label(f"{opp_id}").classes('text-blue-600 font-semibold text-sm')
                                    with ui.row().classes('items-center gap-2'):
                                        ui.badge(days_text).classes(f'{days_class} text-xs font-bold px-2 py-1 rounded-full')
                                        ui.badge(risk_label_map[risk]).classes(f'{risk_color_map[risk]} text-xs font-bold px-2 py-1 rounded-full')
                                ui.label(title_short).classes('text-gray-900 text-sm font-medium')
                else:
                    ui.label("Henüz aktivite yok.").classes('text-gray-500')
        
        ui.separator().classes('my-6')
        
        # Alt Butonlar - Görseldeki gibi
        with ui.row().classes('w-full gap-4 mt-6'):
            ui.button(
                "Fırsat Ara",
                icon='search',
                on_click=lambda: ui.navigate.to('/opportunities')
            ).classes('bg-blue-600 text-white hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold')
            
            ui.button(
                "Sonuçları Görüntüle",
                icon='bar_chart',
                on_click=lambda: ui.navigate.to('/results')
            ).classes('bg-gray-600 text-white hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold')
    
    with ui.column().classes('w-full min-h-screen bg-gray-50'):  # Açık tema arka plan
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_dashboard_content()

# SAM OPPORTUNITIES sayfası
@ui.page('/opportunities')
def opportunities_page():
    """SAM OPPORTUNITIES sayfası - Açık Tema"""
    setup_theme(dark=False)  # Açık tema
    
    # Navigation - sayfa içinde tanımlı - İkinci görseldeki gibi
    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            # Sol taraf: Logo ve başlık
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            
            # Sağ taraf: Navigation bar - Beyaz, yuvarlatılmış container, ortalanmış
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📋', 'SAM OPPORTUNITIES', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📄', 'Sonuçlar', '/results', 'RESULTS')
                    ]
                    for icon, label, url, page_key in pages:
                        is_active = page_key == 'OPPORTUNITY_CENTER'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap')
                        else:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap')
    
    # Opportunity Center içeriği - Açık Tema - Geliştirilmiş (cache + pagination + analysis)
    def render_opportunity_content():
        ui.label('📋 SAM OPPORTUNITIES').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Sonuçlar için global değişkenler (hem arama kartı hem de önceki kayıtlar için)
        results_container = ui.column().classes('w-full mt-4')
        page_size = 10
        page_index = 0
        current_results: list = []
        
        # Arama ve Filtreleme Bölümü - Açık Tema
        with ui.card().classes('w-full bg-white border border-gray-200 mb-6 shadow-sm rounded-lg'):
            with ui.row().classes('w-full items-end gap-4 p-4'):
                notice_id_input = ui.input(label="Notice ID", placeholder="Opsiyonel").classes('flex-1')
                naics_input = ui.input(label="NAICS", value="721110").classes('flex-1')
                keyword_input = ui.input(label="Anahtar Kelime", placeholder="Örn: hotel, lodging...").classes('flex-1')
                
                # Tarih aralığı seçici
                days_back_options = {
                    7: 'Son 7 gün',
                    14: 'Son 14 gün',
                    30: 'Son 30 gün',
                    60: 'Son 60 gün',
                    90: 'Son 90 gün',
                    180: 'Son 180 gün',
                    365: 'Son 365 gün'
                }
                days_back_select = ui.select(
                    options=days_back_options,
                    value=30,
                    label="Tarih Aralığı"
                ).classes('flex-1')
                
                def render_results():
                    """Pagination ile sonuçları göster"""
                    nonlocal page_index
                    results_container.clear()
                    total = len(current_results)
                    pages = max(1, (total + page_size - 1) // page_size)
                    if page_index >= pages:
                        page_index = pages - 1
                    start = page_index * page_size
                    end = min(start + page_size, total)
                    
                    with results_container:
                        ui.label(f'Toplam {total} Fırsat Bulundu').classes('text-xl font-semibold text-gray-900 mb-2')
                        
                        # Pagination kontrolleri
                        if pages > 1:
                            with ui.row().classes('w-full items-center justify-end gap-2 mb-4'):
                                def prev_page():
                                    nonlocal page_index
                                    page_index = max(0, page_index - 1)
                                    render_results()
                                
                                def next_page():
                                    nonlocal page_index
                                    page_index = min(pages - 1, page_index + 1)
                                    render_results()
                                
                                ui.button('⟨ Önceki', on_click=prev_page).props('flat').classes('text-blue-600')
                                ui.label(f'Sayfa {page_index+1}/{pages}').classes('text-sm text-gray-600')
                                ui.button('Sonraki ⟩', on_click=next_page).props('flat').classes('text-blue-600')
                        
                        # Sadece mevcut sayfadaki sonuçları göster
                        for o in current_results[start:end]:
                            oid = o.get('opportunityId') or o.get('noticeId')
                            title = o.get('title', 'Başlık Yok')
                            sam_link = o.get('samGovLink') or (
                                f'https://sam.gov/opp/{oid}/view' if oid and len(str(oid)) == 32 else ''
                            )
                            posted = o.get('postedDate') or o.get('posted_date', '')
                            resp = o.get('responseDeadLine') or o.get('response_deadline', '')
                            left = days_left_from(resp)
                            
                            # Days badge renkleri
                            if left <= 5:
                                days_class = 'bg-red-100 text-red-800'
                                risk = "high"
                            elif left <= 15:
                                days_class = 'bg-amber-100 text-amber-800'
                                risk = "medium"
                            else:
                                days_class = 'bg-teal-100 text-teal-800'
                                risk = "low"
                            
                            risk_color_map = {
                                'low': 'bg-green-100 text-green-800',
                                'medium': 'bg-amber-100 text-amber-800',
                                'high': 'bg-red-100 text-red-800'
                            }
                            risk_label_map = {
                                'low': 'Düşük Risk',
                                'medium': 'Orta Risk',
                                'high': 'Yüksek Risk'
                            }
                            
                            with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg'):
                                # Header Row
                                with ui.row().classes('w-full items-center justify-between p-3 border-b border-gray-200'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(f'{oid}').classes('text-blue-600 font-semibold text-sm')
                                        if sam_link:
                                            ui.link('SAM.gov\'da Görüntüle', sam_link).classes('text-blue-600 text-xs hover:text-blue-800')
                                    ui.badge('Geçmiş' if left <= 0 else f'{left} gün').classes(
                                        f'{days_class} text-xs font-bold px-2 py-1 rounded-full'
                                    )
                                
                                # Title
                                ui.label(title).classes('text-lg font-bold text-gray-900 leading-tight p-4')
                                
                                # Dates
                                if posted or resp:
                                    with ui.row().classes('w-full px-4 pb-2 gap-4'):
                                        if posted:
                                            ui.label(f'Yayın: {str(posted)[:10]}').classes('text-gray-600 text-xs')
                                        if resp:
                                            ui.label(f'Yanıt: {str(resp)[:10]}').classes('text-gray-600 text-xs')
                                
                                # Risk Badge
                                with ui.row().classes('w-full px-4 pb-4'):
                                    ui.badge(risk_label_map[risk]).classes(f'{risk_color_map[risk]} text-xs font-bold px-2 py-1 rounded-full')
                                
                                # Action Buttons
                                with ui.row().classes('w-full bg-gray-50 p-3 justify-around border-t border-gray-200 gap-2 rounded-b-lg'):
                                    nid = o.get('noticeId') or oid
                                    oid2 = o.get('opportunityId')
                                    
                                    def on_analyze(nid=nid, oid2=oid2):
                                        """Analiz başlat - arka plan thread'inde"""
                                        def run_analysis():
                                            try:
                                                code = sanitize_code(nid or oid2 or 'unknown')
                                                if analyze_opportunity:
                                                    result = analyze_opportunity(
                                                        base_dir='.',
                                                        opportunity_code=code,
                                                        notice_id=nid,
                                                        opportunity_id=oid2,
                                                        download_from_sam_gov=True
                                                    )
                                                    return bool(result)
                                                return False
                                            except Exception as e:
                                                logger.error(f'Analysis error: {e}', exc_info=True)
                                                return None
                                        
                                        # Client context'i sakla
                                        try:
                                            client = ui.context.client
                                        except:
                                            client = None
                                        
                                        def thread_worker():
                                            success = run_analysis()
                                            if client:
                                                try:
                                                    with client:
                                                        if success is True:
                                                            ui.notify('✅ Analiz tamamlandı! Sonuçlar sayfasına bakabilirsiniz.', type='positive')
                                                            # Sayfa yönlendirmesi için navigate kullan
                                                            try:
                                                                ui.navigate.to('/results')
                                                            except:
                                                                # Fallback: JavaScript
                                                                ui.run_javascript('window.location.href = "/results"')
                                                        elif success is False:
                                                            ui.notify('⚠️ Analiz sonuç üretmedi', type='warning')
                                                        else:
                                                            ui.notify('❌ Analiz hatası oluştu', type='negative')
                                                except:
                                                    pass
                                        
                                        ui.notify('🔄 Analiz başlatılıyor...', type='info')
                                        thread = threading.Thread(target=thread_worker, daemon=True)
                                        thread.start()
                                    
                                    def on_open(nid=nid):
                                        folder = open_folder_for(nid)
                                        ui.notify(f'Klasör açıldı: {folder}' if folder else 'Klasör açılamadı', type='info')
                                    
                                    def on_download(nid=nid, oid2=oid2):
                                        """Döküman indir - arka plan thread'inde"""
                                        def run_download():
                                            try:
                                                code = sanitize_code(nid or oid2 or 'unknown')
                                                if prepare_opportunity_folder:
                                                    folder = prepare_opportunity_folder('.', code)
                                                else:
                                                    folder = Path('.') / 'opportunities' / code
                                                    folder.mkdir(parents=True, exist_ok=True)
                                                
                                                if download_from_sam:
                                                    docs = download_from_sam(
                                                        folder=folder,
                                                        notice_id=(nid or ''),
                                                        opportunity_id=oid2
                                                    )
                                                    return len(docs) if docs else 0
                                                else:
                                                    return -1  # Modül yok
                                            except Exception as e:
                                                logger.error(f'Download error: {e}', exc_info=True)
                                                return None
                                        
                                        # Client context'i sakla
                                        try:
                                            client = ui.context.client
                                        except:
                                            client = None
                                        
                                        def thread_worker():
                                            count = run_download()
                                            if client:
                                                try:
                                                    with client:
                                                        if count is None:
                                                            ui.notify('❌ Döküman indirme hatası', type='negative')
                                                        elif count == -1:
                                                            ui.notify('⚠️ İndirme modülü yok', type='warning')
                                                        elif count > 0:
                                                            ui.notify(f'✅ {count} doküman başarıyla indirildi!', type='positive')
                                                            # Klasörü otomatik aç
                                                            try:
                                                                code = sanitize_code(nid or oid2 or 'unknown')
                                                                if prepare_opportunity_folder:
                                                                    folder = prepare_opportunity_folder('.', code)
                                                                else:
                                                                    folder = Path('.') / 'opportunities' / code
                                                                open_folder_for(str(folder))
                                                            except:
                                                                pass
                                                        else:
                                                            ui.notify('⚠️ Döküman bulunamadı', type='warning')
                                                except:
                                                    pass
                                        
                                        ui.notify('📥 Dökümanlar indiriliyor...', type='info')
                                        thread = threading.Thread(target=thread_worker, daemon=True)
                                        thread.start()
                                    
                                    ui.button('Analizi Başlat', icon='play_arrow', on_click=on_analyze).classes(
                                        'flex-1 bg-blue-600 text-white hover:bg-blue-700'
                                    )
                                    ui.button('Klasörü Aç', icon='folder_open', on_click=on_open).classes('flex-1').props('outline color=primary')
                                    ui.button('Doküman İndir', icon='download', on_click=on_download).classes('flex-1').props('outline color=primary')
                
                def do_search():
                    """Arama yap - cache ve pagination ile detaylı statü gösterimi"""
                    def search_in_background():
                        """Arama fonksiyonu - detaylı sonuç döndürür"""
                        result = {
                            'success': False,
                            'opportunities': [],
                            'count': 0,
                            'error': None,
                            'api_key_status': None,
                            'cache_used': False,
                            'api_version': None
                        }
                        
                        try:
                            # API key kontrolü
                            if not SAMIntegration:
                                result['error'] = 'SAMIntegration modülü yüklenemedi'
                                return result
                            
                            sam = SAMIntegration()
                            if not sam.api_key:
                                result['error'] = 'API key bulunamadı (SAM_API_KEY)'
                                result['api_key_status'] = 'MISSING'
                                return result
                            
                            result['api_key_status'] = 'OK'
                            result['api_version'] = sam.get_api_version() if hasattr(sam, 'get_api_version') else 'v2'
                            
                            # Quota kontrolü
                            if hasattr(sam, 'quota_exceeded') and sam.quota_exceeded:
                                # 429 hatası varsa, database'den kayıtları kullan
                                logger.warning('API quota limit aşıldı, database\'den kayıtlar yükleniyor...')
                                try:
                                    if DB_AVAILABLE:
                                        db_opps = load_opportunities_from_db(limit=50)
                                        if db_opps:
                                            # Filtreleme (NAICS, keyword, notice_id)
                                            filtered = []
                                            for db_opp in db_opps:
                                                # NAICS filtresi
                                                if naics_codes:
                                                    db_naics = db_opp.get('naics_code') or ''
                                                    if not any(nc in str(db_naics) for nc in naics_codes):
                                                        continue
                                                
                                                # Keyword filtresi
                                                if keywords:
                                                    title = db_opp.get('title', '').lower()
                                                    if keywords.lower() not in title:
                                                        continue
                                                
                                                # Notice ID filtresi
                                                if notice_id:
                                                    db_notice = db_opp.get('noticeId') or db_opp.get('opportunityId', '')
                                                    if notice_id not in str(db_notice):
                                                        continue
                                                
                                                filtered.append(db_opp)
                                            
                                            if filtered:
                                                result['success'] = True
                                                result['opportunities'] = filtered
                                                result['count'] = len(filtered)
                                                result['cache_used'] = False
                                                result['from_database'] = True  # Database'den geldi
                                                result['error'] = None
                                                logger.info(f'Database\'den {len(filtered)} kayıt bulundu (429 hatası nedeniyle)')
                                                return result
                                except Exception as db_error:
                                    logger.error(f'Database fallback hatası: {db_error}')
                                
                                result['error'] = f'API quota limit aşıldı. Reset zamanı: {getattr(sam, "quota_reset_time", "Bilinmiyor")}'
                                return result
                            
                            notice_id = (notice_id_input.value or '').strip() or None
                            naics_codes = [naics_input.value.strip()] if naics_input.value and naics_input.value.strip() else None
                            keywords = (keyword_input.value or '').strip() or None
                            
                            # Tarih aralığı - seçilen değer veya varsayılan 30
                            days_back_value = days_back_select.value
                            days_back = int(days_back_value) if days_back_value else 30
                            # Clamp: min 1, max 365 (API limiti)
                            days_back = max(1, min(365, days_back))
                            
                            # Cache kontrolü (tarih aralığını da dahil et)
                            key = _cache_key(notice_id, naics_codes, keywords)
                            key = f"{key}|days={days_back}"  # Tarih aralığını cache key'e ekle
                            now = time.time()
                            cached = SEARCH_CACHE.get(key)
                            
                            if cached and (now - cached[0] < CACHE_TTL_SECONDS):
                                logger.info(f'Cache hit: {key}')
                                result['success'] = True
                                result['opportunities'] = cached[1]
                                result['count'] = len(cached[1])
                                result['cache_used'] = True
                                return result
                            
                            # API çağrısı - arka plan thread'inde (timeout ile)
                            logger.info(f'API çağrısı başlıyor: notice_id={notice_id}, naics={naics_codes}, keywords={keywords}')
                            
                            # Timeout koruması - max 60 saniye
                            
                            opps = []
                            api_error = None
                            
                            def api_call_with_timeout():
                                nonlocal opps, api_error
                                try:
                                    opps = sam.fetch_opportunities(
                                        keywords=keywords,
                                        naics_codes=naics_codes,
                                        days_back=days_back,  # Seçilen tarih aralığı
                                        limit=50,
                                        notice_id=notice_id,
                                    ) or []
                                except Exception as e:
                                    api_error = str(e)
                                    logger.error(f'API çağrısı hatası: {e}', exc_info=True)
                            
                            # Thread ile timeout kontrolü
                            api_thread = threading.Thread(target=api_call_with_timeout, daemon=True)
                            api_thread.start()
                            api_thread.join(timeout=60)  # Max 60 saniye bekle
                            
                            if api_thread.is_alive():
                                # Timeout oldu
                                result['error'] = 'API çağrısı zaman aşımına uğradı (60 saniye). Lütfen tekrar deneyin.'
                                logger.warning('API çağrısı timeout (60s)')
                                return result
                            
                            if api_error:
                                result['error'] = f'API hatası: {api_error}'
                                return result
                            
                            # Cache'e kaydet
                            SEARCH_CACHE[key] = (now, opps)
                            logger.info(f'Cache stored: {key} ({len(opps)} results)')
                            
                            result['success'] = True
                            result['opportunities'] = opps
                            result['count'] = len(opps)
                            result['cache_used'] = False
                            
                            return result
                        except ValueError as e:
                            # Quota hatası gibi özel hatalar
                            error_msg = str(e)
                            if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                                result['error'] = f'API Quota Limit: {error_msg}'
                            else:
                                result['error'] = error_msg
                            logger.error(f'Search ValueError: {e}', exc_info=True)
                            return result
                        except Exception as e:
                            result['error'] = str(e)
                            logger.error(f'Search error: {e}', exc_info=True)
                            return result
                    
                    def update_ui(search_result):
                        """UI'yi güncelle - detaylı statü göster"""
                        # Butonu tekrar aktif et
                        search_button.enable()
                        
                        # Statü mesajı göster
                        if not search_result:
                            ui.notify('Arama sonucu alınamadı', type='negative')
                            results_container.clear()
                            with results_container:
                                ui.label('Arama hatası. Lütfen tekrar deneyin.').classes('text-red-500')
                            return
                        
                        # Hata durumu
                        if not search_result.get('success'):
                            error_msg = search_result.get('error', 'Bilinmeyen hata')
                            api_key_status = search_result.get('api_key_status', 'UNKNOWN')
                            
                            results_container.clear()
                            with results_container:
                                with ui.card().classes('w-full bg-red-50 border-2 border-red-300 p-4'):
                                    ui.label('❌ Arama Hatası').classes('text-xl font-bold text-red-700 mb-2')
                                    ui.label(f'Hata: {error_msg}').classes('text-red-600 mb-2')
                                    ui.label(f'API Key Durumu: {api_key_status}').classes('text-sm text-gray-600')
                            
                            ui.notify(f'Arama hatası: {error_msg}', type='negative')
                            return
                        
                        # Başarılı sonuç
                        opps = search_result.get('opportunities', [])
                        count = search_result.get('count', 0)
                        cache_used = search_result.get('cache_used', False)
                        api_version = search_result.get('api_version', 'v2')
                        
                        # Başarı mesajı
                        from_database = search_result.get('from_database', False)
                        if from_database:
                            ui.notify(f'📦 Database\'den {count} kayıt yüklendi (429 hatası nedeniyle)', type='warning')
                        elif cache_used:
                            ui.notify(f'✅ Cache\'den {count} kayıt yüklendi', type='info')
                        else:
                            ui.notify(f'✅ API\'den {count} kayıt bulundu (v{api_version})', type='positive')
                        
                        # Sonuçları sakla ve ilk sayfayı göster
                        nonlocal page_index, current_results
                        page_index = 0
                        current_results = opps
                        
                        # Database'e kaydet (arka plan thread'inde)
                        def save_to_db():
                            try:
                                if not DB_AVAILABLE:
                                    return {'saved': 0, 'updated': 0}
                                
                                db = get_db_session()
                                if not db:
                                    return {'saved': 0, 'updated': 0}
                                
                                count_new = 0
                                count_updated = 0
                                
                                from mergenlite_models import Opportunity
                                
                                for opp_data in opps:
                                    opportunity_id = opp_data.get('opportunityId', '').strip()
                                    notice_id = opp_data.get('noticeId', '').strip() or opp_data.get('solicitationNumber', '').strip()
                                    
                                    if not opportunity_id:
                                        raw_data = opp_data.get('raw_data', {})
                                        if isinstance(raw_data, dict):
                                            opportunity_id = raw_data.get('opportunityId', '').strip()
                                    
                                    if not opportunity_id:
                                        continue
                                    
                                    existing = db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
                                    
                                    if existing:
                                        existing.raw_data = opp_data.get('raw_data', opp_data)
                                        existing.updated_at = datetime.now()
                                        count_updated += 1
                                    else:
                                        new_opp = Opportunity(
                                            opportunity_id=opportunity_id,
                                            notice_id=notice_id,
                                            title=opp_data.get('title', 'Başlık Yok'),
                                            raw_data=opp_data.get('raw_data', opp_data)
                                        )
                                        db.add(new_opp)
                                        count_new += 1
                                
                                db.commit()
                                logger.info(f"Database'e kaydedildi: {count_new} yeni, {count_updated} güncellendi")
                                return {'saved': count_new, 'updated': count_updated}
                            except Exception as e:
                                if db:
                                    db.rollback()
                                logger.error(f"Database kayıt hatası: {e}", exc_info=True)
                                return {'saved': 0, 'updated': 0}
                            finally:
                                if db:
                                    db.close()
                        
                        # Client context'i sakla
                        try:
                            client = ui.context.client
                        except:
                            client = None
                        
                        def thread_worker():
                            db_result = save_to_db()
                            if client and (db_result.get('saved', 0) > 0 or db_result.get('updated', 0) > 0):
                                try:
                                    with client:
                                        ui.notify(f"💾 {db_result.get('saved', 0)} yeni, {db_result.get('updated', 0)} güncellendi", type='info')
                                except:
                                    pass
                        
                        # Database'e kaydet (arka plan thread'inde, UI'yi bloklamaz)
                        thread = threading.Thread(target=thread_worker, daemon=True)
                        thread.start()
                        
                        # Sonuçları göster
                        logger.info(f'UI güncelleniyor: {len(opps)} kayıt')
                        render_results()
                        logger.info(f'render_results() çağrıldı, current_results: {len(current_results)}')
                    
                    # Loading indicator ve buton durumu
                    ui.notify('🔍 Aranıyor... (Max 60 saniye)', type='info')
                    search_button.disable()
                    
                    # Loading göster - API key durumu ile
                    results_container.clear()
                    with results_container:
                        ui.spinner(size='lg', color='blue').classes('mx-auto my-8')
                        ui.label('SAM.gov API\'den fırsatlar çekiliyor...').classes('text-center text-gray-600 mb-2')
                        ui.label('⏱️ Maksimum bekleme süresi: 60 saniye').classes('text-center text-gray-500 text-xs mb-2')
                        
                        # API key durumu kontrolü
                        try:
                            if SAMIntegration:
                                sam_check = SAMIntegration()
                                if sam_check.api_key:
                                    api_ver = sam_check.get_api_version() if hasattr(sam_check, 'get_api_version') else 'v2'
                                    ui.label(f'✅ API Key: Aktif | API: {api_ver}').classes('text-center text-green-600 text-sm')
                                else:
                                    ui.label('⚠️ API Key: Bulunamadı').classes('text-center text-red-600 text-sm')
                            else:
                                ui.label('⚠️ SAMIntegration: Yüklenemedi').classes('text-center text-red-600 text-sm')
                        except Exception as e:
                            ui.label(f'⚠️ API Kontrolü: {str(e)[:50]}').classes('text-center text-yellow-600 text-sm')
                    
                    # Arka plan thread'inde çalıştır
                    def thread_worker():
                        result = search_in_background()
                        update_ui(result)
                    
                    thread = threading.Thread(target=thread_worker, daemon=True)
                    thread.start()
                
                # Butonu tanımla
                search_button = ui.button("Ara", icon='search', on_click=do_search).classes('bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold')
        
        # API Durumu Alert - Açık Tema
        with ui.row().classes('w-full mb-6'):
            try:
                sam = SAMIntegration() if SAMIntegration else None
                api_status = "✅ SAM.gov API bağlantısı aktif" if sam and sam.api_key else "⚠️ API Key yapılandırılmamış"
                status_color = "text-green-700" if sam and sam.api_key else "text-amber-700"
                status_bg = "bg-green-50" if sam and sam.api_key else "bg-amber-50"
                status_border = "border-green-500" if sam and sam.api_key else "border-amber-500"
                ui.label(api_status).classes(f'w-full text-sm {status_color} p-3 border-l-4 {status_border} {status_bg} rounded-md')
            except:
                ui.label("⚠️ API durumu kontrol edilemedi").classes('w-full text-sm text-amber-700 p-3 border-l-4 border-amber-500 bg-amber-50 rounded-md')
        
        # Arama sonuçları container'ı (üstte, arama sonuçları için)
        with results_container:
            pass  # Arama sonuçları buraya gelecek
        
        # Arşiv Bölümü (Altta, geçmiş ilanlar)
        ui.separator().classes('my-8')
        
        # Arşiv başlığı ve göster/gizle butonu
        archive_visible = True
        archive_container = ui.column().classes('w-full')
        
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.label('📦').classes('text-xl')
                ui.label('Arşiv').classes('text-2xl font-bold text-gray-900')
            
            def toggle_archive():
                nonlocal archive_visible
                archive_visible = not archive_visible
                if archive_visible:
                    archive_container.set_visibility(True)
                    toggle_btn.props('icon=expand_less')
                else:
                    archive_container.set_visibility(False)
                    toggle_btn.props('icon=expand_more')
            
            toggle_btn = ui.button(icon='expand_less', on_click=toggle_archive).props('flat').classes('text-gray-600')
        
        # Arşiv içeriği
        with archive_container:
            try:
                # Daha fazla kayıt göster (50 kayıt) ve en yeni kayıtlar önce
                initial = load_opportunities_from_db(limit=50) or []
            except Exception as e:
                logger.error(f"Arşiv yükleme hatası: {e}", exc_info=True)
                initial = []
            
            if initial:
                # Toplam kayıt sayısını göster
                db = get_db_session()
                total_in_db = 0
                if db:
                    try:
                        total_in_db = db.query(Opportunity).count()
                    except:
                        pass
                    finally:
                        db.close()
                
                ui.label(f'Geçmiş İlanlar: {len(initial)} kayıt gösteriliyor (Toplam: {total_in_db})').classes('text-sm text-gray-600 mb-4')
                
                # Arşiv için ayrı bir container
                archive_results_container = ui.column().classes('w-full')
                
                # Arşiv kayıtlarını göster
                with archive_results_container:
                    for o in initial:
                        oid = o.get('opportunityId') or o.get('noticeId')
                        title = o.get('title', 'Başlık Yok')
                        sam_link = o.get('samGovLink') or (
                            f'https://sam.gov/opp/{oid}/view' if oid and len(str(oid)) == 32 else ''
                        )
                        posted = o.get('postedDate') or o.get('posted_date', '')
                        resp = o.get('responseDeadLine') or o.get('response_deadline', '')
                        left = days_left_from(resp)
                        
                        # Days badge renkleri
                        if left <= 5:
                            days_class = 'bg-red-100 text-red-800'
                            risk = "high"
                        elif left <= 15:
                            days_class = 'bg-amber-100 text-amber-800'
                            risk = "medium"
                        else:
                            days_class = 'bg-teal-100 text-teal-800'
                            risk = "low"
                        
                        risk_color_map = {
                            'low': 'bg-green-100 text-green-800',
                            'medium': 'bg-amber-100 text-amber-800',
                            'high': 'bg-red-100 text-red-800'
                        }
                        risk_label_map = {
                            'low': 'Düşük Risk',
                            'medium': 'Orta Risk',
                            'high': 'Yüksek Risk'
                        }
                        
                        with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg'):
                            # Header Row
                            with ui.row().classes('w-full items-center justify-between p-3 border-b border-gray-200'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(f'{oid}').classes('text-blue-600 font-semibold text-sm')
                                    if sam_link:
                                        ui.link('SAM.gov\'da Görüntüle', sam_link, new_tab=True).classes('text-blue-600 text-xs hover:text-blue-800')
                                ui.badge('Geçmiş' if left <= 0 else f'{left} gün').classes(
                                    f'{days_class} text-xs font-bold px-2 py-1 rounded-full'
                                )
                            
                            # Content Row
                            with ui.column().classes('w-full p-4 gap-2'):
                                title_short = title[:80] + '...' if len(title) > 80 else title
                                ui.label(title_short).classes('text-gray-900 text-sm font-medium mb-2')
                                
                                with ui.row().classes('w-full items-center gap-2 mb-2'):
                                    ui.badge('Geçmiş' if left <= 0 else f'{left} gün').classes(f'{days_class} text-xs font-bold px-2 py-1 rounded-full')
                                    ui.badge(risk_label_map[risk]).classes(f'{risk_color_map[risk]} text-xs font-bold px-2 py-1 rounded-full')
                                
                                if posted:
                                    ui.label(f'Yayın: {posted}').classes('text-xs text-gray-500')
                                if resp:
                                    ui.label(f'Son Tarih: {resp}').classes('text-xs text-gray-500')
            else:
                ui.label('Arşivde kayıt yok.').classes('text-sm text-gray-500 mb-4')
    
    with ui.column().classes('w-full min-h-screen bg-gray-50'):  # Açık tema arka plan
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_opportunity_content()

# AI Analiz sayfası
@ui.page('/analysis')
def analysis_page():
    """AI Analiz sayfası - Açık Tema"""
    setup_theme(dark=False)  # Açık tema
    
    # Navigation - sayfa içinde tanımlı - İkinci görseldeki gibi
    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            # Sol taraf: Logo ve başlık
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            
            # Sağ taraf: Navigation bar - Beyaz, yuvarlatılmış container, ortalanmış
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📋', 'SAM OPPORTUNITIES', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📄', 'Sonuçlar', '/results', 'RESULTS')
                    ]
                    for icon, label, url, page_key in pages:
                        is_active = page_key == 'GUIDED_ANALYSIS'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap')
                        else:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap')
    
    # AI Analiz içeriği
    def render_analysis_content():
        ui.label('🤖 AI Analiz').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # Database'den analiz edilmemiş kayıtları göster
        ui.label('📋 Analiz Edilmemiş Kayıtlar').classes('text-xl font-semibold text-gray-900 mb-4')
        
        # Database'den kayıtları yükle
        unanalyzed_opportunities = []
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    # Analiz edilmemiş kayıtları çek (en yeni önce)
                    all_opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(100).all()
                    
                    for opp in all_opps:
                        # Analiz durumunu kontrol et
                        analyzed = False
                        try:
                            if hasattr(opp, 'analyses') and opp.analyses:
                                latest_analysis = sorted(opp.analyses, key=lambda x: getattr(x, 'start_time', datetime.now()), reverse=True)[0] if opp.analyses else None
                                if latest_analysis:
                                    analyzed = getattr(latest_analysis, 'analysis_status', None) == 'COMPLETED'
                        except:
                            pass
                        
                        if not analyzed:
                            # raw_data'dan bilgileri çek
                            raw_data = opp.raw_data or {}
                            opportunity_id = opp.opportunity_id or ''
                            notice_id = getattr(opp, 'notice_id', None) or raw_data.get('noticeId', '') or ''
                            
                            if not opportunity_id and raw_data:
                                opportunity_id = raw_data.get('opportunityId', '') or raw_data.get('noticeId', '')
                            
                            if not opportunity_id and notice_id:
                                opportunity_id = notice_id
                            
                            unanalyzed_opportunities.append({
                                'opportunityId': opportunity_id,
                                'noticeId': notice_id,
                                'title': getattr(opp, 'title', None) or 'Başlık Yok',
                                'created_at': getattr(opp, 'created_at', None),
                                'raw_data': raw_data
                            })
                    
                    db.close()
            except Exception as e:
                logger.error(f"Database yükleme hatası: {e}", exc_info=True)
        
        if not unanalyzed_opportunities:
            with ui.card().classes('w-full bg-white border border-gray-200 mb-6 shadow-sm rounded-lg p-6'):
                ui.label('✅ Tüm kayıtlar analiz edilmiş!').classes('text-lg font-semibold text-green-600 mb-2')
                ui.label('Yeni kayıtlar için SAM OPPORTUNITIES sayfasından arama yapabilirsiniz.').classes('text-gray-600')
        else:
            ui.label(f'Toplam {len(unanalyzed_opportunities)} analiz edilmemiş kayıt bulundu').classes('text-sm text-gray-600 mb-4')
            
            # Kayıtları listele
            for opp in unanalyzed_opportunities[:20]:  # İlk 20 kayıt
                oid = opp.get('opportunityId') or opp.get('noticeId', 'N/A')
                title = opp.get('title', 'Başlık Yok')
                created = opp.get('created_at')
                created_str = created.strftime('%Y-%m-%d %H:%M') if created else 'N/A'
                
                sam_link = f'https://sam.gov/opp/{oid}/view' if oid and len(str(oid)) == 32 else ''
                
                with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg hover:border-blue-300 transition'):
                    with ui.row().classes('w-full items-center justify-between p-4'):
                        with ui.column().classes('flex-1'):
                            ui.label(f'{oid}').classes('text-blue-600 font-semibold text-sm mb-1')
                            ui.label(title[:100] + '...' if len(title) > 100 else title).classes('text-gray-900 text-base font-medium mb-2')
                            ui.label(f'Eklenme: {created_str}').classes('text-gray-500 text-xs')
                            if sam_link:
                                ui.link('SAM.gov\'da Görüntüle', sam_link, new_tab=True).classes('text-blue-600 text-xs hover:text-blue-800')
                        
                        # Analiz Başlat butonu ve statü gösterimi
                        nid = opp.get('noticeId') or ''
                        oid2 = opp.get('opportunityId') or ''
                        
                        # Her kayıt için statü container'ı
                        status_container = ui.column().classes('w-full mt-2')
                        
                        def create_analyze_handler(nid=nid, oid2=oid2, title=title, status_cont=status_container):
                            """Analiz başlat handler'ı oluştur"""
                            def on_analyze():
                                """Analiz başlat"""
                                # Client context'i sakla (thread'den UI güncellemesi için)
                                try:
                                    client = ui.context.client
                                except:
                                    client = None
                                
                                # Statü container'ını temizle ve başlangıç mesajı göster
                                status_cont.clear()
                                with status_cont:
                                    with ui.card().classes('w-full bg-blue-50 border border-blue-200 p-4'):
                                        ui.label('🔄 Analiz başlatılıyor...').classes('text-blue-700 font-semibold mb-2')
                                        status_label = ui.label('Hazırlanıyor...').classes('text-sm text-gray-600')
                                        progress_bar = ui.linear_progress(value=0).classes('w-full mt-2')
                                
                                def run_analysis():
                                    try:
                                        code = sanitize_code(nid or oid2 or 'unknown')
                                        if analyze_opportunity:
                                            result = analyze_opportunity(
                                                base_dir='.',
                                                opportunity_code=code,
                                                notice_id=nid,
                                                opportunity_id=oid2,
                                                download_from_sam_gov=True
                                            )
                                            return bool(result)
                                        return False
                                    except Exception as e:
                                        logger.error(f'Analysis error: {e}', exc_info=True)
                                        return None
                                
                                def thread_worker():
                                    # Analiz başladı - statü güncelle (client context ile)
                                    def update_status(msg, progress=0.25):
                                        if client:
                                            try:
                                                with client:
                                                    status_cont.clear()
                                                    with status_cont:
                                                        with ui.card().classes('w-full bg-blue-50 border border-blue-200 p-4'):
                                                            ui.label(f'🔄 {msg}').classes('text-blue-700 font-semibold mb-2')
                                                            ui.linear_progress(value=progress).classes('w-full mt-2')
                                            except Exception as e:
                                                logger.error(f'Status update error: {e}')
                                    
                                    try:
                                        update_status('Dokümanlar indiriliyor...', 0.1)
                                        time.sleep(0.3)
                                        
                                        update_status('Dokümanlar işleniyor...', 0.3)
                                        time.sleep(0.3)
                                        
                                        update_status('AI analiz yapılıyor...', 0.6)
                                        time.sleep(0.3)
                                        
                                        update_status('Rapor oluşturuluyor...', 0.8)
                                        
                                        success = run_analysis()
                                        
                                        # Sonuç göster
                                        if client:
                                            try:
                                                with client:
                                                    status_cont.clear()
                                                    with status_cont:
                                                        if success is True:
                                                            with ui.card().classes('w-full bg-green-50 border border-green-200 p-4'):
                                                                ui.label('✅ Analiz tamamlandı!').classes('text-green-700 font-semibold mb-2')
                                                                ui.label(f'{title[:60]}...').classes('text-sm text-gray-700 mb-2')
                                                                # Sonuçlar sayfasına yönlendirme için link kullan
                                                                ui.link('Sonuçları Görüntüle', '/results', new_tab=False).classes('bg-green-600 text-white hover:bg-green-700 px-4 py-2 rounded-lg inline-block text-center')
                                                        elif success is False:
                                                            with ui.card().classes('w-full bg-amber-50 border border-amber-200 p-4'):
                                                                ui.label('⚠️ Analiz sonuç üretmedi').classes('text-amber-700 font-semibold')
                                                        else:
                                                            with ui.card().classes('w-full bg-red-50 border border-red-200 p-4'):
                                                                ui.label('❌ Analiz hatası oluştu').classes('text-red-700 font-semibold')
                                            except Exception as e:
                                                logger.error(f'Result display error: {e}')
                                    except Exception as e:
                                        logger.error(f'Thread worker error: {e}', exc_info=True)
                                        if client:
                                            try:
                                                with client:
                                                    status_cont.clear()
                                                    with status_cont:
                                                        with ui.card().classes('w-full bg-red-50 border border-red-200 p-4'):
                                                            ui.label(f'❌ Hata: {str(e)[:100]}').classes('text-red-700 font-semibold')
                                            except:
                                                pass
                                
                                thread = threading.Thread(target=thread_worker, daemon=True)
                                thread.start()
                            
                            return on_analyze
                        
                        with ui.column().classes('w-full'):
                            ui.button('Analizi Başlat', icon='play_arrow', on_click=create_analyze_handler(nid, oid2, title, status_container)).classes(
                                'bg-blue-600 text-white hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold'
                            )
                            # Statü container'ı butonun altına ekle
                            with status_container:
                                pass  # Başlangıçta boş
        
        ui.separator().classes('my-6')
        
        # 4 Aşamalı Workflow
        stages = [
            {"num": 1, "title": "Veri Çekme", "icon": "📥", "desc": "SAM.gov'dan ilan verileri çekiliyor"},
            {"num": 2, "title": "Doküman İşleme", "icon": "📄", "desc": "Dokümanlar analiz ediliyor"},
            {"num": 3, "title": "RAG Muhakemesi", "icon": "🤖", "desc": "AI analiz yapıyor"},
            {"num": 4, "title": "Final Rapor", "icon": "📊", "desc": "Rapor oluşturuluyor"}
        ]
        
        ui.label('📊 Analiz Aşamaları').classes('text-xl font-semibold text-gray-900 mb-4')
        
        with ui.row().classes('w-full gap-4 mb-6'):
            for stage in stages:
                with ui.card().classes('flex-1 bg-white border border-gray-200 shadow-sm rounded-lg p-4'):
                    ui.label(f"{stage['icon']} Aşama {stage['num']}").classes('text-lg font-bold text-gray-900 mb-2')
                    ui.label(stage['title']).classes('text-sm font-semibold text-blue-600 mb-1')
                    ui.label(stage['desc']).classes('text-xs text-gray-600')
        
        # Analiz Geçmişi
        ui.label('📋 Analiz Geçmişi').classes('text-xl font-semibold text-gray-900 mb-4 mt-6')
        
        analysis_history = []
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    from mergenlite_models import AIAnalysisResult
                    analyses = db.query(AIAnalysisResult).order_by(AIAnalysisResult.timestamp.desc()).limit(10).all()
                    for analysis in analyses:
                        analysis_history.append({
                            'id': analysis.id,
                            'opportunity_id': analysis.opportunity_id,
                            'status': analysis.analysis_type,
                            'timestamp': analysis.timestamp.strftime("%Y-%m-%d %H:%M") if analysis.timestamp else "N/A"
                        })
                    db.close()
            except:
                pass
        
        if analysis_history:
            for analysis in analysis_history:
                with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg p-4'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.column().classes('flex-1'):
                            ui.label(f"Analiz #{analysis['id']}").classes('text-sm font-semibold text-gray-900')
                            ui.label(f"İlan ID: {analysis['opportunity_id'][:20]}...").classes('text-xs text-gray-600')
                            ui.label(f"Tarih: {analysis['timestamp']}").classes('text-xs text-gray-500')
                        with ui.row().classes('items-center gap-2'):
                            ui.badge(analysis['status']).classes('bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full')
                            def go_to_detail(aid=analysis['id']):
                                try:
                                    ui.navigate.to(f'/results?analysis_id={aid}')
                                except:
                                    ui.run_javascript(f'window.location.href = "/results?analysis_id={aid}"')
                            ui.button('📄 Detay', on_click=lambda aid=analysis['id']: go_to_detail(aid)).classes('bg-blue-600 text-white text-xs px-3 py-1 rounded')
        else:
            ui.label("Henüz analiz yapılmamış.").classes('text-gray-500')
        
        # Hızlı Aksiyonlar
        ui.label('🚀 Hızlı Aksiyonlar').classes('text-xl font-semibold text-gray-900 mb-4 mt-6')
        
        with ui.row().classes('w-full gap-4'):
            ui.button("📋 SAM OPPORTUNITIES'e Git", icon='list', on_click=lambda: ui.navigate.to('/opportunities')).classes('flex-1 bg-blue-600 text-white hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold')
            ui.button("📊 Sonuçları Görüntüle", icon='bar_chart', on_click=lambda: ui.navigate.to('/results')).classes('flex-1 bg-gray-600 text-white hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold')
    
    with ui.column().classes('w-full min-h-screen bg-gray-50'):  # Açık tema arka plan
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_analysis_content()

# Sonuçlar sayfası
@ui.page('/results')
def results_page():
    """Sonuçlar sayfası - Açık Tema"""
    setup_theme(dark=False)  # Açık tema
    
    # Navigation - sayfa içinde tanımlı - İkinci görseldeki gibi
    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            # Sol taraf: Logo ve başlık
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            
            # Sağ taraf: Navigation bar - Beyaz, yuvarlatılmış container, ortalanmış
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📋', 'SAM OPPORTUNITIES', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📄', 'Sonuçlar', '/results', 'RESULTS')
                    ]
                    for icon, label, url, page_key in pages:
                        is_active = page_key == 'RESULTS'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap')
                        else:
                            ui.link(f'{icon} {label}', url).classes('px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap')
    
    # Results içeriği
    def render_results_content():
        ui.label('📄 Analiz Sonuçları').classes('text-3xl font-bold text-gray-900 mb-6')
        
        # URL parametresinden seçili analiz ID'sini al
        try:
            from nicegui import app
            request = app.get_request()
            selected_id_from_url = request.query_params.get('analysis_id', None)
        except:
            selected_id_from_url = None
        
        # Seçili analiz state (reactive variable)
        selected_analysis_id = {'value': selected_id_from_url}
        
        # Detaylı görünüm container'ı (dinamik güncelleme için)
        detail_container = ui.column().classes('w-full')
        
        # Analiz Geçmişi
        analysis_history = []
        
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    from mergenlite_models import AIAnalysisResult, Opportunity
                    from sqlalchemy import or_
                    import json
                    
                    analyses = db.query(AIAnalysisResult, Opportunity).outerjoin(
                        Opportunity,
                        or_(
                            AIAnalysisResult.opportunity_id == Opportunity.opportunity_id,
                            AIAnalysisResult.opportunity_id == Opportunity.notice_id
                        )
                    ).order_by(AIAnalysisResult.timestamp.desc()).limit(50).all()
                    
                    for analysis, opp in analyses:
                        # Skor hesapla
                        skor = "N/A"
                        skor_class = "bg-gray-100 text-gray-800"
                        result_data = analysis.result
                        
                        if isinstance(result_data, str):
                            try:
                                result_data = json.loads(result_data)
                            except:
                                result_data = {}
                        
                        if result_data and isinstance(result_data, dict):
                            fit_assessment = result_data.get('data', {}).get('proposal', {}) or result_data.get('fit_assessment', {})
                            compliance = result_data.get('data', {}).get('compliance', {}) or result_data.get('compliance', {})
                            
                            score = 0
                            if fit_assessment and fit_assessment.get('overall_score'):
                                score = int(fit_assessment.get('overall_score', 0))
                            elif compliance and compliance.get('score'):
                                score = int(compliance.get('score', 0))
                            elif analysis.confidence is not None:
                                score = int(float(analysis.confidence) * 100)
                            
                            if score >= 80:
                                skor = "Mükemmel"
                                skor_class = "bg-green-100 text-green-800"
                            elif score >= 60:
                                skor = "İyi"
                                skor_class = "bg-blue-100 text-blue-800"
                            elif score >= 40:
                                skor = "Orta"
                                skor_class = "bg-amber-100 text-amber-800"
                            else:
                                skor = "Düşük"
                                skor_class = "bg-red-100 text-red-800"
                        
                        # Süre hesapla
                        sure = "N/A"
                        if analysis.timestamp and analysis.created_at:
                            delta = analysis.created_at - analysis.timestamp
                            if delta.total_seconds() > 0:
                                sure = f"{delta.total_seconds():.0f}sn"
                        
                        analysis_history.append({
                            "analizId": f"AN-{analysis.id}",
                            "noticeId": opp.notice_id if opp and opp.notice_id else (analysis.opportunity_id[:20] if analysis.opportunity_id else 'N/A'),
                            "title": opp.title if opp else "Başlık Yok",
                            "tarih": analysis.timestamp.strftime("%Y-%m-%d %H:%M") if analysis.timestamp else "N/A",
                            "sure": sure,
                            "skor": skor,  # Türkçe label (İyi, Mükemmel, vb.)
                            "score": score,  # Sayısal skor (0-100)
                            "skorClass": skor_class,
                            "analysis_id": str(analysis.id),
                            "opportunity_id": analysis.opportunity_id,
                            "status": analysis.analysis_type,
                            "consolidated_output": result_data
                        })
                    
                    db.close()
            except Exception as e:
                logger.error(f"Analiz geçmişi yükleme hatası: {e}", exc_info=True)
        
        if not analysis_history:
            ui.label("Henüz analiz sonucu bulunmuyor.").classes('text-gray-500 mb-6')
            with ui.row().classes('w-full gap-4'):
                ui.button("📋 SAM OPPORTUNITIES'e Git", icon='list', on_click=lambda: ui.navigate.to('/opportunities')).classes('bg-blue-600 text-white hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold')
                ui.button("🤖 AI Analiz'e Git", icon='psychology', on_click=lambda: ui.navigate.to('/analysis')).classes('bg-gray-600 text-white hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold')
            return
        
        # Analiz Geçmişi Tablosu
        ui.label('📊 Analiz Geçmişi').classes('text-xl font-semibold text-gray-900 mb-4')
        
        for row in analysis_history[:20]:  # İlk 20 kayıt
            # Status kontrolü: FULL_ANALYSIS = tamamlandı, diğerleri kontrol et
            status_val = row['status']
            is_completed = status_val == 'COMPLETED' or status_val == 'FULL_ANALYSIS' or (isinstance(status_val, str) and 'COMPLETED' in status_val.upper())
            is_in_progress = status_val == 'IN_PROGRESS' or (isinstance(status_val, str) and 'PROGRESS' in status_val.upper())
            
            status_badge = 'bg-green-100 text-green-800' if is_completed else ('bg-amber-100 text-amber-800' if is_in_progress else 'bg-red-100 text-red-800')
            status_text = 'Completed' if is_completed else ('In Progress' if is_in_progress else 'Failed')
            
            # Kart tıklanabilir hale getir - seçili analizi değiştir
            def select_analysis(analysis_id):
                selected_analysis_id['value'] = analysis_id
                ui.notify(f"Selected analysis: {analysis_id}", type='info')
                # URL'yi güncelle (sayfa yeniden yüklemeden)
                ui.run_javascript(f'window.history.pushState({{}}, "", "/results?analysis_id={analysis_id}")')
                # Detaylı görünümü güncelle
                update_detail_view(analysis_id)
            
            # Detaylı görünümü güncelleme fonksiyonu
            def update_detail_view(analysis_id):
                # Seçili analizi bul
                selected_analysis = None
                for analysis in analysis_history:
                    if analysis['analysis_id'] == analysis_id:
                        selected_analysis = analysis
                        break
                
                if selected_analysis:
                    # Container'ı temizle ve yeni içerik ekle
                    detail_container.clear()
                    with detail_container:
                        render_detail_view(selected_analysis)
            
            # Seçili analiz için border rengi
            is_selected = row['analysis_id'] == selected_analysis_id['value']
            card_classes = 'w-full bg-white border-2 mb-3 shadow-sm rounded-lg hover:shadow-md transition-all duration-200 cursor-pointer'
            if is_selected:
                card_classes += ' border-blue-500 bg-blue-50'
            else:
                card_classes += ' border-gray-200 hover:border-blue-400'
            
            with ui.card().classes(card_classes).on('click', lambda aid=row['analysis_id']: select_analysis(aid)):
                # Daha düzenli row layout
                with ui.row().classes('w-full items-center p-4 gap-3 flex-wrap'):
                    # Analiz ID - Sabit genişlik
                    with ui.column().classes('w-20 flex-shrink-0'):
                        ui.label(row['analizId']).classes('text-blue-600 font-bold text-xs')
                    
                    # Notice ID - Sabit genişlik
                    with ui.column().classes('w-32 flex-shrink-0'):
                        notice_display = row['noticeId'][:20] + '...' if len(row['noticeId']) > 20 else row['noticeId']
                        ui.label(notice_display).classes('text-gray-700 text-xs font-mono truncate')
                    
                    # Başlık - Esnek genişlik
                    with ui.column().classes('flex-1 min-w-0'):
                        title_display = row['title'][:70] + '...' if len(row['title']) > 70 else row['title']
                        ui.label(title_display).classes('text-gray-900 text-sm font-medium truncate')
                    
                    # Tarih - Sabit genişlik
                    with ui.column().classes('w-32 flex-shrink-0'):
                        ui.label(row['tarih']).classes('text-gray-600 text-xs')
                    
                    # Süre - Sabit genişlik
                    with ui.column().classes('w-16 flex-shrink-0 text-center'):
                        ui.label(row['sure']).classes('text-gray-600 text-xs')
                    
                    # Skor - Sabit genişlik
                    with ui.column().classes('w-20 flex-shrink-0'):
                        ui.badge(row['skor']).classes(f'{row["skorClass"]} text-xs font-bold px-2 py-1 rounded-full')
                    
                    # Durum - Sabit genişlik
                    with ui.column().classes('w-24 flex-shrink-0'):
                        ui.badge(status_text).classes(f'{status_badge} text-xs font-bold px-2 py-1 rounded-full')
                    
                    # Detay butonu - Sabit genişlik
                    with ui.column().classes('w-24 flex-shrink-0'):
                        ui.button('Detail', icon='description', on_click=lambda r=row: select_analysis(r['analysis_id'])).classes('bg-blue-600 text-white text-xs px-3 py-1 rounded-lg hover:bg-blue-700 font-semibold w-full')
        
        ui.separator().classes('my-6')
        
        # Detaylı görünüm render fonksiyonu
        def render_detail_view(selected_analysis):
            ui.label('🔍 Detailed View').classes('text-xl font-semibold text-gray-900 mb-4')
            
            # PDF yolunu bul
            pdf_path = None
            opportunity_id = selected_analysis.get('opportunity_id', '')
            if opportunity_id:
                from pathlib import Path
                # opportunities/{opportunity_id}/analysis_report.pdf
                pdf_candidate = Path('opportunities') / opportunity_id / 'analysis_report.pdf'
                if pdf_candidate.exists():
                    pdf_path = str(pdf_candidate)
                else:
                    # Alternatif: metadata'dan al
                    consolidated = selected_analysis.get('consolidated_output', {})
                    metadata = consolidated.get('metadata', {})
                    if metadata and metadata.get('report_pdf_path'):
                        pdf_path = metadata.get('report_pdf_path')
            
            with ui.row().classes('w-full gap-4 mb-4'):
                if pdf_path:
                    from pathlib import Path
                    pdf_file = Path(pdf_path)
                    if pdf_file.exists():
                        # İndirme butonu - JavaScript ile indirme
                        def download_pdf():
                            try:
                                # Dosya yolunu URL'e çevir
                                pdf_url = f'/download/pdf/{opportunity_id}'
                                
                                # JavaScript ile indirme tetikle
                                ui.run_javascript(f'''
                                    const link = document.createElement('a');
                                    link.href = '{pdf_url}';
                                    link.download = '{pdf_file.name}';
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                ''')
                                ui.notify(f'Downloading PDF: {pdf_file.name}', type='positive')
                            except Exception as e:
                                logger.error(f"PDF download error: {e}", exc_info=True)
                                ui.notify(f'Download error: {str(e)}', type='negative')
                        
                        ui.button("⬇️ Download PDF", icon='download', on_click=download_pdf).classes('bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded-lg')
                    else:
                        ui.button("⬇️ Download PDF", icon='download').classes('bg-gray-400 text-white px-4 py-2 rounded-lg').props('disabled')
                else:
                    ui.button("⬇️ Download PDF", icon='download').classes('bg-gray-400 text-white px-4 py-2 rounded-lg').props('disabled')
                
                def export_json():
                    import json
                    consolidated = selected_analysis.get('consolidated_output', {})
                    json_str = json.dumps(consolidated, indent=2, ensure_ascii=False)
                    ui.notify('JSON kopyalandı (konsola bakın)', type='info')
                    print(f"\n=== JSON Export ===\n{json_str}\n")
                
                ui.button("📄 JSON Export", icon='code', on_click=export_json).classes('bg-gray-600 text-white hover:bg-gray-700 px-4 py-2 rounded-lg')
                
                # Mail gönderme butonu
                with ui.dialog() as email_dialog, ui.card().classes('w-full max-w-md p-6'):
                    ui.label('📧 Send Analysis Report via Email').classes('text-xl font-bold text-gray-900 mb-4')
                    email_input = ui.input(label='Recipient Email', placeholder='example@domain.com').classes('w-full mb-4')
                    
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Cancel', on_click=email_dialog.close).classes('flex-1 bg-gray-300 text-gray-700 hover:bg-gray-400')
                        
                        def send_email():
                            email = email_input.value.strip()
                            if not email or '@' not in email:
                                ui.notify('Please enter a valid email address', type='negative')
                                return
                            
                            try:
                                from mail_package import build_mail_package
                                from pathlib import Path
                                
                                # Mail paketi oluştur
                                opp_id = selected_analysis.get('opportunity_id', '')
                                folder_path = Path('opportunities') / opp_id
                                
                                if not folder_path.exists():
                                    ui.notify('Analysis folder not found', type='negative')
                                    return
                                
                                package = build_mail_package(
                                    opportunity_code=opp_id,
                                    folder_path=str(folder_path),
                                    to_email=email
                                )
                                
                                # SMTP ayarları (basit - kullanıcı daha sonra yapılandırabilir)
                                ui.notify(f'Email package prepared for {email}. Configure SMTP settings to send.', type='info')
                                logger.info(f"Email package created for {email}: {package.get('subject', 'N/A')}")
                                
                                email_dialog.close()
                                
                            except Exception as e:
                                logger.error(f"Email send error: {e}", exc_info=True)
                                ui.notify(f'Error preparing email: {str(e)}', type='negative')
                        
                        ui.button('Send Email', icon='send', on_click=send_email).classes('flex-1 bg-blue-600 text-white hover:bg-blue-700')
                
                ui.button("📧 Send Email", icon='email', on_click=email_dialog.open).classes('bg-green-600 text-white hover:bg-green-700 px-4 py-2 rounded-lg')
            
            # PDF Önizleme ve Sekmeler - Yan yana layout
            with ui.row().classes('w-full gap-4 items-start'):
                # Sol taraf: PDF Önizleme
                with ui.column().classes('flex-1 min-w-0'):
                    if pdf_path:
                        from pathlib import Path
                        pdf_file = Path(pdf_path)
                        if pdf_file.exists():
                            ui.label('📄 PDF Report Preview').classes('text-lg font-semibold text-gray-900 mb-2')
                            # Base64 encode ile PDF önizleme
                            try:
                                import base64
                                with open(pdf_file, 'rb') as f:
                                    pdf_bytes = f.read()
                                    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                                
                                ui.html(f'''
                                    <iframe
                                        src="data:application/pdf;base64,{pdf_b64}"
                                        width="100%"
                                        height="800"
                                        style="border:1px solid #ddd; border-radius: 8px; margin-top: 10px;"
                                    ></iframe>
                                ''', sanitize=False)
                            except Exception as e:
                                logger.error(f"PDF preview error: {e}")
                                ui.label(f'PDF preview error: {str(e)}').classes('text-red-600')
                        else:
                            ui.label('PDF file not found.').classes('text-gray-500 mb-4')
                    else:
                        ui.label('PDF report not yet generated.').classes('text-gray-500 mb-4')
                
                # Sağ taraf: Sekmeler
                with ui.column().classes('flex-1 min-w-0'):
                    # Tabs
                    with ui.tabs().classes('w-full') as tabs:
                        tab_docs = ui.tab('📄 Processed Documents')
                        tab_req = ui.tab('📋 Requirements')
                        tab_comp = ui.tab('🛡️ Compliance')
                        tab_prop = ui.tab('✍️ Proposal Draft')
                    
                    consolidated = selected_analysis.get('consolidated_output', {})
                    
                    with ui.tab_panels(tabs, value=tab_docs).classes('w-full mt-4'):
                        with ui.tab_panel(tab_docs):
                            ui.label('📄 Processed Documents Summary').classes('text-lg font-semibold text-gray-900 mb-4')
                            
                            # Farklı yapılardan doküman bilgisini bul
                            documents = []
                            if isinstance(consolidated, dict):
                                # Yapı 1: data.documents
                                documents = consolidated.get('data', {}).get('documents', [])
                                # Yapı 2: direkt documents
                                if not documents:
                                    documents = consolidated.get('documents', [])
                            
                            metadata = consolidated.get('metadata', {}) if isinstance(consolidated, dict) else {}
                            
                            with ui.card().classes('w-full bg-white border border-gray-200 p-4'):
                                if documents:
                                    ui.label(f'Total Documents: {len(documents)}').classes('text-sm font-semibold text-gray-900 mb-3')
                                    for i, doc in enumerate(documents[:20], 1):  # İlk 20 doküman
                                        doc_name = doc.get('filename') or doc.get('name') or doc.get('file_name') or f'Document {i}'
                                        doc_type = doc.get('type') or doc.get('document_type') or ''
                                        doc_pages = doc.get('pages', doc.get('page_count'))
                                        doc_size = doc.get('size', doc.get('file_size'))
                                        
                                        with ui.row().classes('w-full items-center gap-2 mb-2 pb-2 border-b border-gray-100'):
                                            ui.label(f'{i}. {doc_name}').classes('flex-1 text-gray-700 text-sm')
                                            if doc_type:
                                                ui.badge(doc_type).classes('text-xs')
                                            if doc_pages:
                                                ui.label(f'{doc_pages} pages').classes('text-xs text-gray-500')
                                else:
                                    # Metadata'dan bilgi göster
                                    if metadata and metadata.get('documents_count'):
                                        ui.label(f"📊 Total: {metadata.get('documents_count', 0)} documents processed").classes('text-gray-700 mb-2 font-semibold')
                                        if metadata.get('document_types'):
                                            ui.label('Document Types:').classes('text-sm font-semibold text-gray-900 mt-3 mb-2')
                                            for doc_type in metadata.get('document_types', []):
                                                ui.label(f"  • {doc_type}").classes('text-gray-600 text-sm mb-1')
                                        if metadata.get('total_pages'):
                                            ui.label(f"Total Pages: {metadata.get('total_pages', 0)}").classes('text-gray-600 text-sm mt-2')
                                    else:
                                        ui.label("No document information found.").classes('text-gray-500')
                        
                        with ui.tab_panel(tab_req):
                            ui.label('📋 Requirements Summary').classes('text-lg font-semibold text-gray-900 mb-4')
                            
                            requirements = consolidated.get('data', {}).get('requirements', []) or consolidated.get('requirements', [])
                            
                            with ui.card().classes('w-full bg-white border border-gray-200 p-4'):
                                if requirements:
                                    ui.label(f'Total Requirements: {len(requirements)}').classes('text-sm font-semibold text-gray-900 mb-3')
                                    for i, req in enumerate(requirements[:15], 1):  # İlk 15 gereksinim
                                        req_text = req.get('text', req.get('requirement', req.get('description', 'N/A')))
                                        req_category = req.get('category', req.get('type', ''))
                                        
                                        with ui.row().classes('w-full items-start gap-2 mb-3 pb-3 border-b border-gray-100'):
                                            ui.label(f'{i}. {req_text}').classes('flex-1 text-gray-700 text-sm')
                                            if req_category:
                                                ui.badge(req_category).classes('text-xs')
                                else:
                                    # Event requirements veya başka kaynaklardan kontrol et
                                    event_reqs = consolidated.get('event_requirements', []) or consolidated.get('data', {}).get('event_requirements', [])
                                    if event_reqs:
                                        ui.label(f'Event Requirements: {len(event_reqs)}').classes('text-sm font-semibold text-gray-900 mb-3')
                                        for i, req in enumerate(event_reqs[:15], 1):
                                            req_text = str(req) if isinstance(req, str) else req.get('text', req.get('requirement', str(req)))
                                            ui.label(f'{i}. {req_text}').classes('text-gray-700 text-sm mb-2')
                                    else:
                                        ui.label("No requirements information found.").classes('text-gray-500')
                        
                        with ui.tab_panel(tab_comp):
                            ui.label('🛡️ Compliance Analysis Summary').classes('text-lg font-semibold text-gray-900 mb-4')
                            
                            with ui.card().classes('w-full bg-white border border-gray-200 p-4'):
                                # Score göster - önce sayısal skor değerini kontrol et
                                score_num = selected_analysis.get('score')
                                # score değeri None olabilir veya 0 olabilir, bu yüzden 'score' in selected_analysis kontrolü yap
                                if 'score' not in selected_analysis:
                                    score_num = None
                                
                                skor_label = selected_analysis.get('skor', 'N/A')
                                score_color = 'text-gray-600'
                                
                                # Eğer sayısal skor yoksa, fit_assessment'ten al
                                if score_num is None:
                                    fit_assessment = consolidated.get('fit_assessment', {}) or consolidated.get('data', {}).get('fit_assessment', {})
                                    if fit_assessment and fit_assessment.get('overall_score'):
                                        try:
                                            score_num = int(fit_assessment.get('overall_score', 0))
                                        except (ValueError, TypeError):
                                            score_num = None
                                
                                # Eğer hala sayısal skor yoksa, Türkçe label'dan tahmin et
                                if score_num is None and skor_label and skor_label != 'N/A':
                                    score_map = {'mükemmel': 90, 'iyi': 70, 'orta': 50, 'düşük': 30}
                                    score_num = score_map.get(skor_label.lower(), None)
                                
                                # Skor rengini belirle
                                if score_num is not None:
                                    score_color = 'text-green-600' if score_num >= 80 else ('text-blue-600' if score_num >= 60 else ('text-amber-600' if score_num >= 40 else 'text-red-600'))
                                else:
                                    # Skor sayısal değilse, string değere göre renk belirle
                                    score_lower = str(skor_label).lower()
                                    if 'mükemmel' in score_lower or 'excellent' in score_lower:
                                        score_color = 'text-green-600'
                                    elif 'iyi' in score_lower or 'good' in score_lower:
                                        score_color = 'text-blue-600'
                                    elif 'orta' in score_lower or 'medium' in score_lower:
                                        score_color = 'text-amber-600'
                                    else:
                                        score_color = 'text-red-600'
                                
                                # Skor gösterimi
                                if score_num is not None:
                                    ui.label(f'Overall Score: {score_num}/100').classes(f'text-3xl font-bold {score_color} mb-4')
                                elif skor_label and skor_label != 'N/A':
                                    ui.label(f'Overall Score: {skor_label}').classes(f'text-3xl font-bold {score_color} mb-4')
                                else:
                                    ui.label('Overall Score: N/A').classes(f'text-3xl font-bold {score_color} mb-4')
                                
                                compliance = consolidated.get('data', {}).get('compliance', {}) or consolidated.get('compliance', {})
                                
                                # Fit assessment'ten bilgi göster
                                fit_assessment = consolidated.get('fit_assessment', {}) or consolidated.get('data', {}).get('fit_assessment', {})
                                
                                if fit_assessment:
                                    if fit_assessment.get('summary'):
                                        ui.label('Summary:').classes('text-sm font-semibold text-gray-900 mt-4 mb-2')
                                        ui.label(fit_assessment.get('summary')).classes('text-gray-700 text-sm mb-4')
                                    
                                    if fit_assessment.get('strengths'):
                                        ui.label('Strengths:').classes('text-sm font-semibold text-gray-900 mt-2 mb-2')
                                        for strength in fit_assessment.get('strengths', [])[:10]:
                                            ui.label(f"✓ {strength}").classes('text-gray-700 text-sm mb-1 ml-4')
                                    
                                    if fit_assessment.get('risks'):
                                        ui.label('Risks:').classes('text-sm font-semibold text-gray-900 mt-4 mb-2')
                                        for risk in fit_assessment.get('risks', [])[:10]:
                                            ui.label(f"⚠ {risk}").classes('text-gray-700 text-sm mb-1 ml-4')
                                    
                                    if fit_assessment.get('blocking_issues'):
                                        ui.label('Blocking Issues:').classes('text-sm font-semibold text-red-600 mt-4 mb-2')
                                        for issue in fit_assessment.get('blocking_issues', [])[:10]:
                                            ui.label(f"✗ {issue}").classes('text-red-700 text-sm mb-1 ml-4')
                                
                                elif compliance:
                                    # Compliance objesi varsa özet göster
                                    if isinstance(compliance, dict):
                                        for key, value in list(compliance.items())[:10]:
                                            if value and key not in ['score', 'risk_level']:
                                                ui.label(f"{key.replace('_', ' ').title()}: {value}").classes('text-gray-700 text-sm mb-2')
                                else:
                                    ui.label("No compliance information found.").classes('text-gray-500')
                        
                        with ui.tab_panel(tab_prop):
                            ui.label('✍️ Proposal Draft Summary').classes('text-lg font-semibold text-gray-900 mb-4')
                            
                            proposal = consolidated.get('data', {}).get('proposal', {}) or consolidated.get('proposal', {})
                            commercial = consolidated.get('commercial_terms', {}) or consolidated.get('data', {}).get('commercial_terms', {})
                            
                            with ui.card().classes('w-full bg-white border border-gray-200 p-4'):
                                if proposal:
                                    if isinstance(proposal, dict):
                                        ui.label('Proposal Details:').classes('text-sm font-semibold text-gray-900 mb-3')
                                        for key, value in list(proposal.items())[:15]:
                                            if value and not isinstance(value, (dict, list)):
                                                ui.label(f"{key.replace('_', ' ').title()}: {value}").classes('text-gray-700 text-sm mb-2')
                                            elif isinstance(value, list) and len(value) > 0:
                                                ui.label(f"{key.replace('_', ' ').title()}:").classes('text-sm font-semibold text-gray-900 mt-2 mb-1')
                                                for item in value[:5]:
                                                    item_str = str(item) if not isinstance(item, dict) else ', '.join([f"{k}: {v}" for k, v in list(item.items())[:3]])
                                                    ui.label(f"  • {item_str}").classes('text-gray-600 text-sm mb-1 ml-4')
                                elif commercial:
                                    ui.label('Commercial Terms:').classes('text-sm font-semibold text-gray-900 mb-3')
                                    for key, value in commercial.items():
                                        if value and not isinstance(value, (dict, list)):
                                            ui.label(f"{key.replace('_', ' ').title()}: {value}").classes('text-gray-700 text-sm mb-2')
                                        elif isinstance(value, list) and len(value) > 0:
                                            ui.label(f"{key.replace('_', ' ').title()}:").classes('text-sm font-semibold text-gray-900 mt-2 mb-1')
                                            for item in value[:5]:
                                                ui.label(f"  • {item}").classes('text-gray-600 text-sm mb-1 ml-4')
                                else:
                                    ui.label("No proposal draft found.").classes('text-gray-500')
        
        # İlk yüklemede detaylı görünümü göster
        if analysis_history:
            # Seçili analizi bul veya ilk kaydı kullan
            selected_analysis = None
            if selected_analysis_id['value']:
                for analysis in analysis_history:
                    if analysis['analysis_id'] == selected_analysis_id['value']:
                        selected_analysis = analysis
                        break
            
            if not selected_analysis:
                selected_analysis = analysis_history[0]
            
            if selected_analysis:
                render_detail_view(selected_analysis)
    
    with ui.column().classes('w-full min-h-screen bg-gray-50'):  # Açık tema arka plan
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_results_content()

# PDF indirme endpoint'i - NiceGUI app kullanarak
@app.get('/download/pdf/{opportunity_id}')
def download_pdf_file(opportunity_id: str):
    """PDF dosyasını indir"""
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        pdf_file = Path('opportunities') / opportunity_id / 'analysis_report.pdf'
        
        if pdf_file.exists():
            return FileResponse(
                path=str(pdf_file.absolute()),
                filename=pdf_file.name,
                media_type='application/pdf'
            )
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="PDF file not found")
    except Exception as e:
        logger.error(f"PDF download endpoint error: {e}", exc_info=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

# Uygulama başlatma
if __name__ in {"__main__", "__mp_main__"}:
    # Tüm sayfaları yükle (route'ların tanımlanması için)
    # Sayfalar zaten @ui.page() decorator'ı ile tanımlı
    
    print("=" * 60)
    print("MergenLite NiceGUI Baslatiliyor...")
    print("=" * 60)
    print("Route'lar yuklendi:")
    print("   - / (Dashboard)")
    print("   - /test (Test Sayfasi)")
    print("   - /opportunities (Ilan Merkezi)")
    print("   - /analysis (AI Analiz)")
    print("   - /results (Sonuclar)")
    print("=" * 60)
    print(f"Sunucu baslatiliyor: http://127.0.0.1:8081")
    print("=" * 60)
    print("NOT: Port 8080 kullanimda, 8081 kullaniliyor")
    print("=" * 60)
    
    ui.run(
        title="MergenLite - NiceGUI",
        port=8081,  # Port 8080 kullanımda, 8081 kullanıyoruz
        show=True,
        reload=False,  # False yap - daha stabil
        dark=False  # Açık tema (sayfalar zaten setup_theme ile ayarlı)
    )

