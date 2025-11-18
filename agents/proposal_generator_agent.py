#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proposal Generator Agent
Analiz sonuçlarından otomatik teklif taslağı üretir
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# AutoGen import
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, proposal generation will be limited")

def make_proposal_generator_agent(llm_config: Optional[Dict] = None):
    """
    Proposal Generator Agent oluştur
    
    Bu ajan:
    - RFQ/SOW içindeki government iletişim bilgilerini KULLANMAZ
    - Sadece opportunity_info, requirements, compliance bilgilerini kullanır
    - Vendor profile bilgilerini kullanır
    - Profesyonel teklif taslağı üretir
    """
    
    system_message = """
Sen bir "Federal Proposal Writer" ajansın ve MergenLite tarafından üretilen
Opportunity_Requirements_Report verisini kullanarak profesyonel bir teklif taslağı hazırlıyorsun.

ÖNEMLİ KURALLAR:
1. RFQ veya SOW içindeki hükümet iletişim bilgilerini (isim, e-posta, telefon, adres)
   ASLA yazma veya kopyalama. Bu bilgileri kullanma.

2. Sadece şu bilgileri kullan:
   - Opportunity_Requirements_Report içeriği (opportunity_info, event_requirements, commercial_terms, compliance)
   - Kullanıcı tarafından verilen vendor_profile (şirket adı, adresi, SAM kaydı, past performance)
   - Analizden gelen teknik gereksinimler, tarih, kapasite, lojistik, compliance maddeleri

3. Çıktı formatın tek bir teklif dokümanı olsun (Markdown).

4. Aşağıdaki şablonu kullan ve doldur:

# Cover Letter / Transmittal

- Hitap: "To the Contracting Officer,"
- Kısa giriş: solicitation number, başlık, kimin adına teklif verildiği (vendor_profile'dan)
- Teklif verme amacı

# Executive Summary

- Fırsatın özeti (opportunity_info'dan)
- Bizim çözümümüzün kısa özeti
- Uygunluk ve güçlü yanlar (fit_assessment'dan)

# Understanding of Requirements

- Tarihler (date_range)
- Lokasyon (location)
- Katılımcı sayısı (participants_min, participants_target)
- Oda blokları (room_block_plan)
- Toplantı odaları (meeting_spaces)
- AV gereksinimleri (av_requirements)
- F&B gereksinimleri (fnb_requirements)
- Özel lojistik (special_logistics)

# Technical Approach & Event Delivery Plan

- Check-in ve registration planı
- Meeting management yaklaşımı
- Support ekibi yapısı
- AV yönetimi
- Risk yönetimi
- Quality assurance

# Lodging & Meeting Space Plan

- Oda tipleri ve blok planı
- Per diem uyumu (commercial_terms'den)
- ADA uyumu (compliance'den)
- Konum avantajları

# AV & F&B Plan

- RFQ/SOW isterlerine referansla teknik çözüm
- AV ekipman listesi (genel)
- F&B menü planı (genel)

# Compliance Statement

- İlgili FAR/EDAR maddelerine uyum beyanı (sadece isimlerini kullan; tam metin yazma)
- Örn: "We acknowledge and will comply with FAR 52.212-4, FAR 52.212-5, FAR 52.204-24/25/26, and applicable EDAR clauses."
- Security/Telecom restrictions uyumu
- Bytedance restriction uyumu (eğer varsa)

# Past Performance Summary

- vendor_profile içindeki geçmiş işler
- İlgili benzer projeler
- Başarı metrikleri

# Pricing Summary

- Yüksek seviyede kalemler (tablo formatında):
  - Lodging (if applicable)
  - Meeting Space
  - AV package
  - F&B
  - Support services
  - Other services
- Net rakamları vendor_profile/fiyat girişi varsa kullan,
  yoksa "To be finalized based on final room pickup and AV configuration." yaz.

# Assumptions & Exclusions

- Net ve okunaklı maddeler
- Örnek: "Pricing assumes standard room types and standard AV package."
- Örnek: "Final pricing subject to room pickup confirmation."

# Signature Block

- Sadece yüklenici firma bilgileri (vendor_profile'dan):
  - İsim, unvan, şirket adı, adres
  - Genel iletişim e-posta & telefon (sizin)
  - SAM.gov kayıt bilgileri (UEI, DUNS)

ÇIKTI FORMATI:
- Sadece teklif metnini döndür (geçerli Markdown).
- JSON veya debug metni ekleme.
- Government contact bilgileri KULLANMA.
- Sadece "To the Contracting Officer," generic hitabı kullan.
"""
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        return None
    
    return ConversableAgent(
        name="proposal_generator",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
    )

