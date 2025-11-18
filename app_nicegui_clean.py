#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite - NiceGUI (Clean UTF-8)
Light theme UI with pill-style navigation and a fully wired
‘İlan Merkezi’ search (Notice ID, NAICS, Keyword) + actions.
No Streamlit dependency; all UI is inside page functions.
"""

from nicegui import ui
import asyncio
import time
from pathlib import Path
from datetime import datetime, timedelta
import platform
import subprocess
import logging

# Backend imports (no streamlit)
try:
    from sam_integration import SAMIntegration
    from backend_utils import (
        load_opportunities_from_db,
        get_db_session,
        DB_AVAILABLE,
    )
    from opportunity_runner import download_from_sam, prepare_opportunity_folder, analyze_opportunity
except Exception as e:
    SAMIntegration = None
    download_from_sam = None
    prepare_opportunity_folder = None
    DB_AVAILABLE = False
    load_opportunities_from_db = lambda limit=10: []  # fallback

logger = logging.getLogger(__name__)


# Simple in-memory cache for search results (key -> (timestamp, results))
SEARCH_CACHE: dict[str, tuple[float, list]] = {}
CACHE_TTL_SECONDS = 300.0  # 5 minutes

def _cache_key(notice_id: str | None, naics: list[str] | None, keywords: str | None) -> str:
    naics_s = ','.join(naics) if naics else ''
    return f"notice={notice_id or ''}|naics={naics_s}|kw={keywords or ''}"


def setup_theme(dark: bool = False) -> None:
    if dark:
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()
    ui.colors(
        primary='#3b82f6',
        secondary='#10b981',
        accent='#a855f7',
        positive='#10b981',
        negative='#ef4444',
        info='#60a5fa',
        warning='#f59e0b',
    )


def sanitize_code(code: str) -> str:
    return ''.join(c for c in str(code).strip() if c.isalnum() or c in ('_', '-')) or 'unknown'


def days_left_from(deadline) -> int:
    try:
        if isinstance(deadline, str) and len(deadline) >= 10:
            d = datetime.strptime(deadline[:10], '%Y-%m-%d')
        else:
            d = deadline
        return (d - datetime.now()).days if d else 0
    except Exception:
        return 0


def open_folder_for(code: str) -> str | None:
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


@ui.page('/test')
def test_page():
    setup_theme(dark=False)
    with ui.column().classes('w-full min-h-screen bg-gray-50 p-6'):
        ui.label('NiceGUI Route Test').classes('text-3xl font-bold text-gray-900')
        ui.label('Routes are active.').classes('text-green-600 text-lg')


@ui.page('/')
def dashboard_page():
    setup_theme(dark=False)

    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📄', 'İlan Merkezi', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📃', 'Sonuçlar', '/results', 'RESULTS'),
                    ]
                    for icon, label, url, key in pages:
                        is_active = key == 'DASHBOARD'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap'
                            )
                        else:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap'
                            )

    def render_content():
        ui.label('Dashboard').classes('text-3xl font-bold text-gray-900 mb-6')
        # Simple KPIs
        try:
            opps = load_opportunities_from_db(limit=50) or []
        except Exception:
            opps = []
        total_cnt = len(opps)
        today_cnt = 0
        for o in opps:
            created_at = o.get('created_at')
            if created_at:
                try:
                    d = datetime.strptime(str(created_at)[:10], '%Y-%m-%d')
                    if d.date() == datetime.now().date():
                        today_cnt += 1
                except Exception:
                    pass
        with ui.row().classes('w-full gap-4'):
            for title, value, color in [
                ('Toplam Fırsat', f'{total_cnt:,}', 'bg-blue-600'),
                ('Bugün Eklenen', f'{today_cnt:,}', 'bg-emerald-600'),
                ('Tamamlanan Analiz', '—', 'bg-purple-600'),
                ('Ortalama Süre', '—', 'bg-orange-600'),
            ]:
                with ui.card().classes(f'flex-1 {color} text-white shadow-lg rounded-lg overflow-hidden'):
                    with ui.column().classes('w-full p-6'):
                        ui.label(title).classes('text-sm opacity-90 mb-2')
                        ui.label(value).classes('text-4xl font-bold')

        ui.separator().classes('my-6')

        # Recent opportunities
        ui.label('Son Aktiviteler').classes('text-lg font-semibold text-gray-900 mb-3')
        if opps:
            for o in opps[:5]:
                opp_id = o.get('opportunityId') or o.get('noticeId') or o.get('opportunity_id', 'N/A')
                title = o.get('title', 'Başlık Yok')
                with ui.card().classes('w-full bg-white border border-gray-200 shadow-sm mb-2 rounded-lg'):
                    with ui.row().classes('w-full items-center justify-between p-3'):
                        ui.label(f'{opp_id}').classes('text-blue-600 font-semibold text-sm')
                        ui.label(title).classes('text-gray-900 text-sm font-medium')
        else:
            ui.label('Henüz aktivite yok.').classes('text-gray-500')

    with ui.column().classes('w-full min-h-screen bg-gray-50'):
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_content()


@ui.page('/opportunities')
def opportunities_page():
    setup_theme(dark=False)

    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📄', 'İlan Merkezi', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📃', 'Sonuçlar', '/results', 'RESULTS'),
                    ]
                    for icon, label, url, key in pages:
                        is_active = key == 'OPPORTUNITY_CENTER'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap'
                            )
                        else:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap'
                            )

    def render_content():
        ui.label('İlan Merkezi').classes('text-3xl font-bold text-gray-900 mb-6')

        # Search card
        with ui.card().classes('w-full bg-white border border-gray-200 mb-6 shadow-sm rounded-lg'):
            with ui.row().classes('w-full items-end gap-4 p-4'):
                notice_input = ui.input(label='Notice ID').classes('flex-1')
                naics_input = ui.input(label='NAICS', value='721110').classes('flex-1')
                keyword_input = ui.input(label='Anahtar Kelime', placeholder='örn: hotel, lodging...').classes('flex-1')

                results_container = ui.column().classes('w-full')

                async def do_search():
                    sam = SAMIntegration() if SAMIntegration else None
                    if not sam:
                        ui.notify('Backend hazır değil', type='negative')
                        return
                    ui.notify('Aranıyor...', type='info')
                    notice_id = (notice_input.value or '').strip() or None
                    naics_codes = [naics_input.value.strip()] if naics_input.value and naics_input.value.strip() else None
                    keywords = (keyword_input.value or '').strip() or None
                    # Run blocking request in a background thread
                    try:
                        opps = await asyncio.to_thread(
                            sam.fetch_opportunities,
                            keywords,
                            naics_codes,
                            30,
                            50,
                            notice_id,
                        )
                    except Exception as e:
                        ui.notify(f'Hata: {e}', type='negative')
                        return
                    opps = opps or []

                    results_container.clear()
                    with results_container:
                        ui.label(f'Toplam {len(opps)} Fırsat Bulundu').classes('text-xl font-semibold text-gray-900 mb-4')
                        for o in opps:
                            oid = o.get('opportunityId') or o.get('noticeId')
                            title = o.get('title', 'Başlık Yok')
                            sam_link = o.get('samGovLink') or (
                                f'https://sam.gov/opp/{oid}/view' if oid and len(str(oid)) == 32 else ''
                            )
                            posted = o.get('postedDate') or o.get('posted_date', '')
                            resp = o.get('responseDeadLine') or o.get('response_deadline', '')
                            left = days_left_from(resp)
                            if left <= 5:
                                days_class = 'bg-red-100 text-red-800'
                            elif left <= 15:
                                days_class = 'bg-amber-100 text-amber-800'
                            else:
                                days_class = 'bg-teal-100 text-teal-800'
                            with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg'):
                                with ui.row().classes('w-full items-center justify-between p-3 border-b border-gray-200'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(f'{oid}').classes('text-blue-600 font-semibold text-sm')
                                        if sam_link:
                                            ui.link('SAM.gov’da Görüntüle', sam_link).classes('text-blue-600 text-xs hover:text-blue-800')
                                    ui.badge('Geçmiş' if left <= 0 else f'{left} gün').classes(
                                        f'{days_class} text-xs font-bold px-2 py-1 rounded-full'
                                    )
                                ui.label(title).classes('text-lg font-bold text-gray-900 leading-tight p-4')
                                if posted or resp:
                                    with ui.row().classes('w-full px-4 pb-2 gap-4'):
                                        if posted:
                                            ui.label(f'Yayın: {str(posted)[:10]}').classes('text-gray-600 text-xs')
                                        if resp:
                                            ui.label(f'Yanıt: {str(resp)[:10]}').classes('text-gray-600 text-xs')
                                with ui.row().classes('w-full bg-gray-50 p-3 justify-around border-t border-gray-200 gap-2 rounded-b-lg'):
                                    def on_analyze(nid=oid):
                                        ui.notify('Analiz başlatılıyor...', type='info')
                                    def on_open(nid=oid):
                                        folder = open_folder_for(nid)
                                        ui.notify(f'Klasör açıldı: {folder}' if folder else 'Klasör açılamadı', type='info')
                                    async def on_download(nid=o.get('noticeId'), oid2=o.get('opportunityId')):
                                        try:
                                            code = sanitize_code(nid or oid2 or 'unknown')
                                            folder = prepare_opportunity_folder('.', code) if prepare_opportunity_folder else (Path('.') / 'opportunities' / code)
                                            folder.mkdir(parents=True, exist_ok=True)
                                            if download_from_sam:
                                                docs = await asyncio.to_thread(
                                                    download_from_sam,
                                                    folder,
                                                    nid or '',
                                                    oid2,
                                                )
                                                ui.notify(
                                                    f'{len(docs)} doküman indirildi' if docs else 'Doküman bulunamadı',
                                                    type='positive' if docs else 'warning',
                                                )
                                            else:
                                                ui.notify('İndirme modülü yok', type='warning')
                                        except Exception as e:
                                            ui.notify(f'Hata: {e}', type='negative')
                                    ui.button('Analizi Başlat', icon='play_arrow', on_click=on_analyze).classes(
                                        'flex-1 bg-blue-600 text-white hover:bg-blue-700'
                                    )
                                    ui.button('Klasörü Aç', icon='folder_open', on_click=on_open).classes('flex-1').props('outline color=primary')
                                    ui.button('Doküman İndir', icon='download', on_click=on_download).classes('flex-1').props('outline color=primary')

                ui.button('Ara', icon='search', on_click=do_search).classes(
                    'bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold'
                )

        # Initial DB list (optional)
        try:
            initial = load_opportunities_from_db(limit=10) or []
        except Exception:
            initial = []
        if initial:
            ui.label(f'Önceki Kayıtlar: {len(initial)}').classes('text-sm text-gray-600')
        else:
            ui.label('Önceki kayıt yok.').classes('text-sm text-gray-500')

    with ui.column().classes('w-full min-h-screen bg-gray-50'):
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_content()


@ui.page('/opportunities2')
def opportunities2_page():
    """Enhanced İlan Merkezi with caching, pagination, and analysis hook"""
    setup_theme(dark=False)

    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📄', 'İlan Merkezi', '/opportunities2', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📃', 'Sonuçlar', '/results', 'RESULTS'),
                    ]
                    for icon, label, url, key in pages:
                        is_active = key == 'OPPORTUNITY_CENTER'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap'
                            )
                        else:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap'
                            )

    def render_content():
        ui.label('İlan Merkezi').classes('text-3xl font-bold text-gray-900 mb-6')

        with ui.card().classes('w-full bg-white border border-gray-200 mb-6 shadow-sm rounded-lg'):
            with ui.row().classes('w-full items-end gap-4 p-4'):
                notice_input = ui.input(label='Notice ID').classes('flex-1')
                naics_input = ui.input(label='NAICS', value='721110').classes('flex-1')
                keyword_input = ui.input(label='Anahtar Kelime', placeholder='örn: hotel, lodging...').classes('flex-1')

                results_container = ui.column().classes('w-full')
                page_size = 10
                page_index = 0
                current_results: list = []

                def render_results():
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
                        with ui.row().classes('w-full items-center justify-end gap-2 mb-2'):
                            ui.button('⟨ Önceki', on_click=lambda: [globals().__setitem__('__noop', None), locals().update(page_index=max(0, page_index-1)), render_results()]).props('flat')
                            ui.label(f'Sayfa {page_index+1}/{pages}').classes('text-sm text-gray-600')
                            ui.button('Sonraki ⟩', on_click=lambda: [globals().__setitem__('__noop', None), locals().update(page_index=min(pages-1, page_index+1)), render_results()]).props('flat')

                        for o in current_results[start:end]:
                            oid = o.get('opportunityId') or o.get('noticeId')
                            title = o.get('title', 'Başlık Yok')
                            sam_link = o.get('samGovLink') or (f'https://sam.gov/opp/{oid}/view' if oid and len(str(oid)) == 32 else '')
                            posted = o.get('postedDate') or o.get('posted_date', '')
                            resp = o.get('responseDeadLine') or o.get('response_deadline', '')
                            left = days_left_from(resp)
                            days_class = 'bg-red-100 text-red-800' if left <= 5 else ('bg-amber-100 text-amber-800' if left <= 15 else 'bg-teal-100 text-teal-800')
                            with ui.card().classes('w-full bg-white border border-gray-200 mb-3 shadow-sm rounded-lg'):
                                with ui.row().classes('w-full items-center justify-between p-3 border-b border-gray-200'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(f'{oid}').classes('text-blue-600 font-semibold text-sm')
                                        if sam_link:
                                            ui.link('SAM.gov’da Görüntüle', sam_link).classes('text-blue-600 text-xs hover:text-blue-800')
                                    ui.badge('Geçmiş' if left <= 0 else f'{left} gün').classes(f'{days_class} text-xs font-bold px-2 py-1 rounded-full')
                                ui.label(title).classes('text-lg font-bold text-gray-900 leading-tight p-4')
                                if posted or resp:
                                    with ui.row().classes('w-full px-4 pb-2 gap-4'):
                                        if posted:
                                            ui.label(f'Yayın: {str(posted)[:10]}').classes('text-gray-600 text-xs')
                                        if resp:
                                            ui.label(f'Yanıt: {str(resp)[:10]}').classes('text-gray-600 text-xs')
                                with ui.row().classes('w-full bg-gray-50 p-3 justify-around border-t border-gray-200 gap-2 rounded-b-lg'):
                                    async def on_analyze(nid=oid):
                                        try:
                                            ui.notify('Analiz başlatılıyor...', type='info')
                                            code = sanitize_code(nid or 'unknown')
                                            result = await asyncio.to_thread(
                                                analyze_opportunity,
                                                '.',
                                                code,
                                                None,
                                                nid,
                                                o.get('opportunityId'),
                                                None,
                                                True,
                                            )
                                            ok = bool(result)
                                            ui.notify('Analiz tamamlandı' if ok else 'Analiz sonuç üretmedi', type='positive' if ok else 'warning')
                                        except Exception as e:
                                            ui.notify(f'Analiz hatası: {e}', type='negative')
                                    def on_open(nid=oid):
                                        folder = open_folder_for(nid)
                                        ui.notify(f'Klasör açıldı: {folder}' if folder else 'Klasör açılamadı', type='info')
                                    async def on_download(nid=o.get('noticeId'), oid2=o.get('opportunityId')):
                                        try:
                                            code = sanitize_code(nid or oid2 or 'unknown')
                                            folder = prepare_opportunity_folder('.', code) if prepare_opportunity_folder else (Path('.') / 'opportunities' / code)
                                            folder.mkdir(parents=True, exist_ok=True)
                                            if download_from_sam:
                                                docs = await asyncio.to_thread(download_from_sam, folder, nid or '', oid2)
                                                ui.notify(f'{len(docs)} doküman indirildi' if docs else 'Doküman bulunamadı', type='positive' if docs else 'warning')
                                            else:
                                                ui.notify('İndirme modülü yok', type='warning')
                                        except Exception as e:
                                            ui.notify(f'Hata: {e}', type='negative')
                                    ui.button('Analizi Başlat', icon='play_arrow', on_click=on_analyze).classes('flex-1 bg-blue-600 text-white hover:bg-blue-700')
                                    ui.button('Klasörü Aç', icon='folder_open', on_click=on_open).classes('flex-1').props('outline color=primary')
                                    ui.button('Doküman İndir', icon='download', on_click=on_download).classes('flex-1').props('outline color=primary')

                async def do_search():
                    sam = SAMIntegration() if SAMIntegration else None
                    if not sam:
                        ui.notify('Backend hazır değil', type='negative')
                        return
                    notice_id = (notice_input.value or '').strip() or None
                    naics_codes = [naics_input.value.strip()] if naics_input.value and naics_input.value.strip() else None
                    keywords = (keyword_input.value or '').strip() or None
                    key = _cache_key(notice_id, naics_codes, keywords)
                    now = time.time()
                    cached = SEARCH_CACHE.get(key)
                    results = None
                    if cached and (now - cached[0] < CACHE_TTL_SECONDS):
                        results = cached[1]
                    if results is None:
                        try:
                            results = await asyncio.to_thread(
                                sam.fetch_opportunities,
                                keywords,
                                naics_codes,
                                30,
                                50,
                                notice_id,
                            )
                            results = results or []
                            SEARCH_CACHE[key] = (now, results)
                        except Exception as e:
                            ui.notify(f'Hata: {e}', type='negative')
                            return
                    nonlocal page_index, current_results
                    page_index = 0
                    current_results = results
                    render_results()

                ui.button('Ara', icon='search', on_click=do_search).classes('bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold')

        # Initial hint from DB
        try:
            initial = load_opportunities_from_db(limit=5) or []
        except Exception:
            initial = []
        if initial:
            ui.label(f'Önceki Kayıtlar: {len(initial)}').classes('text-sm text-gray-600')
        else:
            ui.label('Önceki kayıt yok.').classes('text-sm text-gray-500')

    with ui.column().classes('w-full min-h-screen bg-gray-50'):
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_content()

@ui.page('/analysis')
def analysis_page():
    setup_theme(dark=False)

    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📄', 'İlan Merkezi', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📃', 'Sonuçlar', '/results', 'RESULTS'),
                    ]
                    for icon, label, url, key in pages:
                        is_active = key == 'GUIDED_ANALYSIS'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap'
                            )
                        else:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap'
                            )

    def render_content():
        ui.label('AI Analiz').classes('text-3xl font-bold text-gray-900 mb-6')
        ui.label('Bu sayfa yakında eklenecek...').classes('text-amber-500')

    with ui.column().classes('w-full min-h-screen bg-gray-50'):
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_content()


@ui.page('/results')
def results_page():
    setup_theme(dark=False)

    def render_nav():
        with ui.row().classes('w-full bg-gray-50 p-6 sticky top-0 z-50 items-start justify-between'):
            with ui.column().classes('items-start'):
                ui.label('MergenLite').classes('text-2xl font-bold text-blue-600 mb-1')
                ui.label('SAM.gov Otomatik Teklif Analiz Platformu').classes('text-sm text-gray-600')
            with ui.card().classes('bg-white rounded-lg shadow-sm border border-gray-200'):
                with ui.row().classes('items-center gap-0'):
                    pages = [
                        ('🏠', 'Dashboard', '/', 'DASHBOARD'),
                        ('📄', 'İlan Merkezi', '/opportunities', 'OPPORTUNITY_CENTER'),
                        ('🤖', 'AI Analiz', '/analysis', 'GUIDED_ANALYSIS'),
                        ('📃', 'Sonuçlar', '/results', 'RESULTS'),
                    ]
                    for icon, label, url, key in pages:
                        is_active = key == 'RESULTS'
                        if is_active:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition whitespace-nowrap'
                            )
                        else:
                            ui.link(f'{icon} {label}', url).classes(
                                'px-5 py-2.5 rounded-lg text-gray-600 hover:text-blue-600 hover:bg-gray-100 transition whitespace-nowrap'
                            )

    def render_content():
        ui.label('Analiz Sonuçları').classes('text-3xl font-bold text-gray-900 mb-6')
        # Load recent analyses from DB if available
        rows = []
        try:
            from mergenlite_models import AIAnalysisResult, Opportunity
            if DB_AVAILABLE and get_db_session:
                db = get_db_session()
                if db:
                    rows = (
                        db.query(AIAnalysisResult)
                        .order_by(AIAnalysisResult.timestamp.desc())
                        .limit(25)
                        .all()
                    )
                    db.close()
        except Exception as e:
            logger.debug(f'results_page load error: {e}')

        if not rows:
            ui.label('Henüz analiz sonucu yok.').classes('text-gray-500')
            return

        with ui.column().classes('w-full gap-2'):
            for r in rows:
                # Normalize fields
                rid = getattr(r, 'id', '—')
                opp_id = getattr(r, 'opportunity_id', '—')
                ts = getattr(r, 'timestamp', None)
                created = getattr(r, 'created_at', None)
                status = getattr(r, 'analysis_type', '') or getattr(r, 'status', '') or '—'
                score = None
                try:
                    data = r.result
                    if isinstance(data, str):
                        import json
                        data = json.loads(data)
                    fit = (data or {}).get('data', {}).get('proposal', {}) or (data or {}).get('fit_assessment', {})
                    comp = (data or {}).get('data', {}).get('compliance', {}) or (data or {}).get('compliance', {})
                    if fit and fit.get('overall_score'):
                        score = int(fit.get('overall_score', 0))
                    elif comp and comp.get('score'):
                        score = int(comp.get('score', 0))
                except Exception:
                    pass

                score_text = '—' if score is None else str(score)
                score_class = (
                    'bg-green-100 text-green-800' if (score or 0) >= 80 else
                    'bg-blue-100 text-blue-800' if (score or 0) >= 60 else
                    'bg-amber-100 text-amber-800' if (score or 0) >= 40 else
                    'bg-red-100 text-red-800'
                )
                with ui.card().classes('w-full bg-white border border-gray-200 rounded-lg shadow-sm'):
                    with ui.row().classes('w-full items-center justify-between p-3'):
                        ui.label(f'#{rid} • {opp_id}').classes('text-sm text-gray-600')
                        ui.badge(score_text).classes(f'{score_class} text-xs font-bold px-2 py-1 rounded-full')
                    with ui.row().classes('w-full items-center justify-between px-3 pb-3'):
                        ui.label(f'Durum: {status}').classes('text-xs text-gray-600')
                        ts_text = str(ts)[:19] if ts else '—'
                        cr_text = str(created)[:19] if created else '—'
                        ui.label(f'Başlangıç: {ts_text} • Bitiş: {cr_text}').classes('text-xs text-gray-600')

    with ui.column().classes('w-full min-h-screen bg-gray-50'):
        render_nav()
        with ui.column().classes('w-full max-w-7xl mx-auto p-6'):
            render_content()


if __name__ in {"__main__", "__mp_main__"}:
    # Faster startup: disable reload and run on 8081 as requested
    ui.run(title='MergenLite - NiceGUI', port=8081, show=True, reload=False, dark=False)
