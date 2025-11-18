"""
MergenLite için modern UI bileşenleri: aşama stepper'ı, rozetler, kartlar ve tema enjeksiyonu.
"""

from __future__ import annotations
import streamlit as st
from typing import Dict, Any, List, Optional


# =============================================================
# 1) Tema & CSS
# =============================================================

def inject_theme(dark: bool = True):
    """Sayfaya modern bir koyu/açık tema CSS'i enjekte eder.
    
    Kullanım: inject_theme(dark=True)
    """
    if dark:
        st.markdown(
            """
            <style>
            :root {
                --bg: #0b1220;
                --panel: #131a2a;
                --panel-2: #0f172a;
                --text: #e5e7eb;
                --muted: #9ca3af;
                --border: #1f2a44;
                --primary: #7c3aed; /* mor */
                --primary-600: #6d28d9;
                --ok: #10b981;
                --warn: #f59e0b;
                --err: #ef4444;
            }

            .stApp { background: var(--bg); }
            .main .block-container { color: var(--text); }

            /* Tipografi */
            h1,h2,h3,h4,h5,h6 { color: var(--text); }
            p,div,small,span,label { color: var(--text); }

            /* Genel paneller */
            .panel {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 16px;
            }

            /* Butonlar */
            .stButton>button {
                background: var(--primary);
                border: 1px solid rgba(139,92,246,.7);
                color: white; font-weight: 600;
                border-radius: 8px; padding: 10px 16px;
                transition: all .15s ease-in-out;
            }
            .stButton>button:hover { background: var(--primary-600); transform: translateY(-1px); }

            /* Rozet (badge) */
            .badge { 
                display:inline-flex; 
                align-items:center; 
                gap:6px; 
                padding:4px 8px; 
                font-size:12px; 
                font-weight:600; 
                border-radius:999px; 
                border:1px solid var(--border); 
                background: #182038; 
                color: var(--text);
            } 
            .badge.ok { background:#0b2e26; color:#86efac; border-color:#164e3f; }
            .badge.warn { background:#3d2817; color:#fbbf24; border-color:#78350f; }
            .badge.err { background:#3d1a1a; color:#f87171; border-color:#7f1d1d; }
            .badge.info { background:#0b2030; color:#7dd3fc; border-color:#1b3a57; }
            .badge.primary { background:#3b1f5f; color:#c4b5fd; border-color:#7c3aed; }

            /* Opportunity kart */
            .opp-card { 
                background: var(--panel); 
                border: 1px solid var(--border); 
                border-radius: 12px; 
                padding: 20px; 
                transition: .15s ease; 
                box-shadow: 0 2px 8px rgba(0,0,0,.15);
                border-left: 4px solid var(--primary);
                margin-bottom: 16px;
            }
            .opp-card:hover { 
                border-color: var(--primary); 
                box-shadow: 0 8px 24px rgba(124,58,237,.18); 
                transform: translateY(-2px);
                background: linear-gradient(135deg, var(--panel) 0%, #1a243b 100%);
            }
            .opp-title { margin:0 0 12px 0; font-size:18px; font-weight:700; color: var(--text); }
            .opp-meta { color: var(--muted); font-size:14px; margin:6px 0; line-height: 1.6; }
            .opp-meta strong { color: var(--text); font-weight: 600; }

            /* Stepper */
            .stepper { 
                display:flex; 
                gap:12px; 
                align-items:center; 
                justify-content:space-between; 
                background: var(--panel-2); 
                border:1px solid var(--border); 
                padding:16px; 
                border-radius: 12px;
                margin: 20px 0;
            }
            .step { display:flex; align-items:center; gap:10px; flex:1; }
            .dot { 
                width:32px; 
                height:32px; 
                border-radius:999px; 
                display:grid; 
                place-items:center; 
                font-size:14px; 
                font-weight:700; 
                border:2px solid var(--border); 
                background:#0e1628; 
                color:var(--muted);
                flex-shrink: 0;
            }
            .dot.active { background: var(--primary); border-color: rgba(255,255,255,.2); color:white; }
            .dot.done { background:#0b2e26; color:#86efac; border-color:#164e3f; }
            .label { font-weight:700; font-size:14px; color: var(--text); }
            .sublabel { font-size:12px; color: var(--muted); }
            .bar { height:3px; background: var(--border); flex:1; border-radius: 2px; }
            .bar.active { background: var(--primary); }
            .bar.done { background: #0b2e26; }

            /* NAICS Badge */
            .naics-badge {
                display: inline-block;
                padding: 4px 10px;
                background: rgba(124, 58, 237, 0.15);
                color: #c4b5fd;
                border: 1px solid rgba(124, 58, 237, 0.3);
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                margin-left: 8px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Açık tema henüz eklenmedi. dark=True kullanın.")


# =============================================================
# 2) Yardımcı Görsel Bileşenler
# =============================================================

def badge(text: str, kind: str = "info"):
    """Rozet (badge) gösterir.
    
    Args:
        text: Badge metni
        kind: "info", "ok", "warn", "err", "primary"
    """
    kind = kind if kind in {"info","ok","warn","err","primary"} else "info"
    st.markdown(f'<span class="badge {kind}">{text}</span>', unsafe_allow_html=True)


def opportunity_card(opp: Dict[str, Any], key: Optional[str] = None, actions: bool = True, show_naics_badge: bool = True) -> None:
    """Şık bir ilan kartı.
    
    Args:
        opp: İlan verisi dict'i
            Beklenen alanlar: 'title', 'opportunityId', 'noticeId', 'fullParentPathName', 
                             'postedDate', 'responseDeadLine', 'naicsCode', 'source'
        key: Unique key (butonlar için)
        actions: Butonları göster/gizle
        show_naics_badge: NAICS badge'ini göster
    """
    title = opp.get('title', 'Başlık Yok')
    oid = opp.get('opportunityId', 'N/A')
    notice_id = opp.get('noticeId', 'N/A')
    org = opp.get('fullParentPathName', 'Organizasyon Yok')
    posted = opp.get('postedDate', 'N/A')
    deadline = opp.get('responseDeadLine', 'N/A')
    naics = opp.get('naicsCode', '—')
    source = opp.get('source', 'unknown')
    
    # Source badge
    source_badge_map = {
        'gsa_live': ('GSA (canlı)', 'ok'),
        'sam_live': ('SAM.gov (canlı)', 'ok'),
        'gsa_description_api': ('GSA (canlı)', 'ok')
    }
    source_text, source_kind = source_badge_map.get(source, ('Canlı API', 'info'))
    
    naics_badge_html = f'<span class="naics-badge">NAICS: {naics}</span>' if show_naics_badge and naics != '—' else ''
    
    # SAM.gov link oluştur
    sam_link_html = ""
    if oid != 'N/A' and len(str(oid)) == 32:  # Opportunity ID (32 karakter hex)
        sam_url = f"https://sam.gov/opp/{oid}/view"
        sam_link_html = f'<a href="{sam_url}" target="_blank" style="color: #7c3aed; text-decoration: none; font-size: 12px; margin-left: 8px; font-weight: 600;">🔗 SAM.gov</a>'
    elif notice_id != 'N/A':
        # Notice ID varsa, search URL kullan
        sam_url = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
        sam_link_html = f'<a href="{sam_url}" target="_blank" style="color: #7c3aed; text-decoration: none; font-size: 12px; margin-left: 8px; font-weight: 600;">🔗 SAM.gov</a>'
    
    st.markdown(
        f"""
        <div class="opp-card">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span class="badge {source_kind}" style="font-size: 11px;">{source_text}</span>
                {naics_badge_html}
            </div>
            <div class="opp-title">{title}</div>
            <div class="opp-meta"><strong>Notice ID:</strong> {notice_id} · <strong>Organizasyon:</strong> {org} {sam_link_html}</div>
            <div class="opp-meta">🗓️ <strong>Yayın:</strong> {posted} · ⏰ <strong>Son Teslim:</strong> {deadline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if actions:
        cols = st.columns([1, 1])
        with cols[0]:
            analyze_clicked = st.button("📊 Analiz Et", key=f"analyze_{key or notice_id}", use_container_width=True)
        with cols[1]:
            detail_clicked = st.button("📄 Detay", key=f"detail_{key or notice_id}", use_container_width=True)
        
        if analyze_clicked:
            st.session_state['_card_action'] = ("analyze", opp)
            st.rerun()
        elif detail_clicked:
            st.session_state['_card_action'] = ("detail", opp)
            st.rerun()
    
    return None


def stepper(current_stage: int, labels: Optional[List[str]] = None, total: int = 4):
    """Aşama stepper'ı. 
    
    Args:
        current_stage: Aktif aşama (1..total)
        labels: Aşama etiketleri listesi
        total: Toplam aşama sayısı
    """
    labels = labels or [
        "Veri Çekme",
        "Doküman İşleme",
        "RAG Muhakemesi",
        "Final Rapor",
    ]
    current_stage = max(1, min(total, current_stage))

    # HTML çizimi
    html = ["<div class='stepper'>"]
    for i in range(1, total + 1):
        state = "active" if i == current_stage else ("done" if i < current_stage else "")
        dot_cls = f"dot {state}".strip()
        label = labels[i - 1] if i - 1 < len(labels) else f"Aşama {i}"
        
        status_text = 'Tamamlandı' if i < current_stage else ('Aktif' if i == current_stage else 'Beklemede')
        status_icon = '✅' if i < current_stage else ('🔄' if i == current_stage else '⏸️')
        
        html.append(
            f"""
            <div class='step'>
                <div class='{dot_cls}'>{i}</div>
                <div style="flex: 1;">
                    <div class='label'>{label}</div>
                    <div class='sublabel'>{status_icon} {status_text}</div>
                </div>
            </div>
            """
        )
        if i < total:
            bar_cls = "bar " + ("done" if i < current_stage else ("active" if i == current_stage else ""))
            html.append(f"<div class='{bar_cls}'></div>")
    html.append("</div>")

    st.markdown("\n".join(html), unsafe_allow_html=True)


# =============================================================
# 3) Sekmeli Aşama Görünümü
# =============================================================

def staged_tabs(current_stage: int) -> int:
    """Sekmeli görünüm. 
    
    Args:
        current_stage: Aktif aşama (1..4)
    
    Returns:
        Seçili/aktif aşama index (1..4)
    """
    tabs = st.tabs(["1. Veri", "2. Doküman", "3. RAG", "4. Rapor"])

    with tabs[0]:
        st.subheader("📥 Aşama 1: Veri Çekme")
        if current_stage > 1:
            badge("Durum: Tamamlandı", kind="ok")
        elif current_stage == 1:
            badge("Durum: Aktif", kind="info")
        else:
            badge("Durum: Beklemede", kind="warn")
        st.write("SAM'den metadata çek, kritik alanları göster, ileri butonu ile Aşama 2'ye geç.")

    with tabs[1]:
        st.subheader("📄 Aşama 2: Doküman İşleme")
        if current_stage > 2:
            badge("Durum: Tamamlandı", kind="ok")
        elif current_stage == 2:
            badge("Durum: Aktif", kind="info")
        else:
            badge("Durum: Beklemede", kind="warn")
        st.write("PDF/DOCX yükle, özet/temizlik yap, sayfa sayısı ve boyut gibi metrikleri göster.")

    with tabs[2]:
        st.subheader("🤖 Aşama 3: RAG Muhakemesi")
        if current_stage > 3:
            badge("Durum: Tamamlandı", kind="ok")
        elif current_stage == 3:
            badge("Durum: Aktif", kind="info")
        else:
            badge("Durum: Beklemede", kind="warn")
        st.write("Vektör arama sonuçları, bağlam paragrafları ve çıkarılan gereksinimler.")

    with tabs[3]:
        st.subheader("📊 Aşama 4: Final Rapor")
        if current_stage == 4:
            badge("Durum: Aktif", kind="info")
        else:
            badge("Durum: Beklemede", kind="warn")
        st.write("Konsolide sonuç kartları (tablo + madde işaretli özet) ve indirme butonları.")

    return current_stage

