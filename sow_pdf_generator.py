#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOW PDF Generator
Markdown SOW'u PDF formatına dönüştürür
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# PDF library
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available, PDF generation will be limited")

# Markdown parser
try:
    import markdown
    from markdown.extensions import codehilite, tables, fenced_code
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown not available, using simple text conversion")

def generate_gpt_style_sow_pdf(
    output_path: str,
    opportunity_code: str = "{OPPORTUNITY_CODE}",
    sow_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Sample SOW for GPT formatında PDF oluştur (Sample PDF'e birebir uyumlu)
    - Mavi başlık bandı
    - APPENDIX A bölümü
    - Haftalık tablolar (Sleeping Room, Function Space)
    - Placeholder'lar ({PLACEHOLDER} formatında)
    
    Args:
        output_path: PDF çıktı dosyası yolu
        opportunity_code: Fırsat kodu
        sow_data: SOW verileri (opsiyonel, yoksa placeholder'lar kullanılır)
    
    Returns:
        Başarılı ise True
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab not available, cannot generate PDF")
        return False
    
    try:
        # PDF oluştur
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Stil tanımlamaları
        styles = getSampleStyleSheet()
        
        # Mavi başlık bandı stili
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=20,
            spaceBefore=0
        )
        
        # Section başlık stili (APPENDIX A, etc.)
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#0033A0'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Subsection başlık stili
        subsection_style = ParagraphStyle(
            'SubsectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=8,
            spaceBefore=15
        )
        
        # Tablo başlık stili (mavi arka plan)
        table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leftIndent=3,
            rightIndent=3
        )
        
        # Tablo hücre stili
        table_cell_style = ParagraphStyle(
            'TableCellStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=3,
            rightIndent=3
        )
        
        # Field name stili (sol sütun)
        field_name_style = ParagraphStyle(
            'FieldNameStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leftIndent=5,
            rightIndent=5
        )
        
        # Placeholder stili
        placeholder_style = ParagraphStyle(
            'PlaceholderStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT,
            fontName='Helvetica-Oblique',
            leftIndent=5,
            rightIndent=5
        )
        
        # Normal metin stili
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=6,
            leading=12
        )
        
        # Story (içerik) listesi
        story = []
        
        # Mavi başlık bandı
        header_color = colors.HexColor('#0033A0')  # Mavi renk
        header_table = Table(
            [[Paragraph("STATEMENT OF WORK (SOW)<br/>FOR HOTEL ACCOMMODATIONS AND MEETING SPACE", header_style)]],
            colWidths=[7*inch],
            rowHeights=[0.6*inch]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.4*inch))
        
        # 1. BACKGROUND
        story.append(Paragraph("1. BACKGROUND", section_style))
        background_text = sow_data.get('background', 
            "This Statement of Work (SOW) outlines the requirements for hotel accommodations and meeting space services for a federal government event.") if sow_data else \
            "This Statement of Work (SOW) outlines the requirements for hotel accommodations and meeting space services for a federal government event."
        story.append(Paragraph(background_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Background bilgileri (basit tablo)
        bg_data = [
            ["Solicitation Number:", sow_data.get('solicitation_number', '{SOLICITATION_NUMBER}') if sow_data else '{SOLICITATION_NUMBER}'],
            ["Agency:", sow_data.get('agency', '{AGENCY}') if sow_data else '{AGENCY}'],
            ["Event Title:", sow_data.get('event_title', '{EVENT_TITLE}') if sow_data else '{EVENT_TITLE}'],
        ]
        bg_table = _create_simple_table(bg_data, field_name_style, placeholder_style)
        story.append(bg_table)
        story.append(Spacer(1, 0.3*inch))
        
        # APPENDIX A
        story.append(Paragraph("APPENDIX A", section_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Meeting Information
        story.append(Paragraph("Meeting Information", subsection_style))
        meeting_info_data = [
            ["MEETING NAME", "MEETING DATES"],
            [
                sow_data.get('meeting_name', '{MEETING_NAME}') if sow_data else '{MEETING_NAME}',
                sow_data.get('meeting_dates', '{MEETING_DATES}') if sow_data else '{MEETING_DATES}'
            ]
        ]
        meeting_info_table = _create_meeting_info_table(meeting_info_data, table_header_style, table_cell_style)
        story.append(meeting_info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Sleeping Room Requirements
        story.append(Paragraph("Sleeping Room Requirements", subsection_style))
        sleeping_table = _create_weekly_sleeping_room_table(sow_data, table_header_style, table_cell_style)
        story.append(sleeping_table)
        
        # Notes
        notes_text = sow_data.get('room_block_notes', 
            "Room block requested may be amended slightly. Room Block of {TOTAL_PARTICIPANTS} participants. If fewer than {TOTAL_PARTICIPANTS} rooms are reserved by the hold end date, no attrition or any other fees or penalties will be assessed.") if sow_data else \
            "Room block requested may be amended slightly. Room Block of {TOTAL_PARTICIPANTS} participants. If fewer than {TOTAL_PARTICIPANTS} rooms are reserved by the hold end date, no attrition or any other fees or penalties will be assessed."
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph(f"<b>NOTES:</b> {notes_text}", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Function Space Requirements
        story.append(Paragraph("Function Space Requirements", subsection_style))
        function_table = _create_weekly_function_space_table(sow_data, table_header_style, table_cell_style)
        story.append(function_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Function Space Requirements (cont.)
        story.append(Paragraph("Function Space Requirements (cont.)", subsection_style))
        story.append(Paragraph("MEETING ROOM SETUP/ AUDIO VISUAL REQUIREMENTS", subsection_style))
        
        # Detailed AV Requirements
        av_sections = [
            ("Registration Area (1):", sow_data.get('registration_area_details', '{REGISTRATION_AREA_DETAILS}') if sow_data else '{REGISTRATION_AREA_DETAILS}'),
            ("General Sessions Room (1):", sow_data.get('general_session_details', '{GENERAL_SESSION_DETAILS}') if sow_data else '{GENERAL_SESSION_DETAILS}'),
            ("Conference Breakout Rooms (4):", sow_data.get('breakout_rooms_details', '{BREAKOUT_ROOMS_DETAILS}') if sow_data else '{BREAKOUT_ROOMS_DETAILS}'),
            ("Logistics Room (1):", sow_data.get('logistics_room_details', '{LOGISTICS_ROOM_DETAILS}') if sow_data else '{LOGISTICS_ROOM_DETAILS}'),
        ]
        
        for section_title, section_text in av_sections:
            story.append(Paragraph(f"<b>{section_title}</b>", field_name_style))
            story.append(Paragraph(section_text, normal_style))
            story.append(Spacer(1, 0.15*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # LIGHT REFRESHMENTS
        story.append(Paragraph("LIGHT REFRESHMENTS", subsection_style))
        refreshments_text = sow_data.get('refreshments', '{REFRESHMENTS_DETAILS}') if sow_data else '{REFRESHMENTS_DETAILS}'
        story.append(Paragraph(refreshments_text, normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Pre-con Meeting and Event Logistics
        story.append(Paragraph("Pre-con Meeting and Event Logistics", subsection_style))
        logistics_text = sow_data.get('pre_con_meeting', '{PRE_CON_MEETING_DETAILS}') if sow_data else '{PRE_CON_MEETING_DETAILS}'
        story.append(Paragraph(logistics_text, normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # TERMS AND CONDITIONS
        story.append(Paragraph("TERMS AND CONDITIONS", section_style))
        terms_data = [
            ["Payment Terms:", sow_data.get('payment_terms', '{PAYMENT_TERMS}') if sow_data else '{PAYMENT_TERMS}'],
            ["Tax Exempt:", sow_data.get('tax_exempt', '{TAX_EXEMPT}') if sow_data else '{TAX_EXEMPT}'],
            ["E-Invoicing IPP:", sow_data.get('e_invoicing_ipp', '{E_INVOICING_IPP}') if sow_data else '{E_INVOICING_IPP}'],
            ["Cancellation Penalties:", sow_data.get('cancellation_penalties', '{CANCELLATION_PENALTIES}') if sow_data else '{CANCELLATION_PENALTIES}'],
        ]
        terms_table = _create_simple_table(terms_data, field_name_style, placeholder_style)
        story.append(terms_table)
        story.append(Spacer(1, 0.3*inch))
        
        # COMPLIANCE REQUIREMENTS
        story.append(Paragraph("COMPLIANCE REQUIREMENTS", section_style))
        compliance_data = [
            ["FAR 52.212-4:", sow_data.get('far_52_212_4', '{FAR_52_212_4}') if sow_data else '{FAR_52_212_4}'],
            ["FAR 52.212-5:", sow_data.get('far_52_212_5', '{FAR_52_212_5}') if sow_data else '{FAR_52_212_5}'],
            ["FAR 52.204-24/25/26:", sow_data.get('far_52_204_24_25_26', '{FAR_52_204_24_25_26}') if sow_data else '{FAR_52_204_24_25_26}'],
            ["Security/Telecom Restrictions:", sow_data.get('security_telecom_restrictions', '{SECURITY_TELECOM_RESTRICTIONS}') if sow_data else '{SECURITY_TELECOM_RESTRICTIONS}'],
            ["Bytedance Restriction:", sow_data.get('bytedance_restriction', '{BYTEDANCE_RESTRICTION}') if sow_data else '{BYTEDANCE_RESTRICTION}'],
            ["Other Mandatory Clauses:", sow_data.get('other_mandatory_clauses', '{OTHER_MANDATORY_CLAUSES}') if sow_data else '{OTHER_MANDATORY_CLAUSES}'],
        ]
        compliance_table = _create_simple_table(compliance_data, field_name_style, placeholder_style)
        story.append(compliance_table)
        
        # PDF'i oluştur
        doc.build(story)
        logger.info(f"[SOW PDF] Generated GPT-style PDF: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"[SOW PDF] Error generating GPT-style PDF: {e}", exc_info=True)
        return False


def _create_simple_table(
    data: List[List[str]],
    field_style: ParagraphStyle,
    value_style: ParagraphStyle
) -> Table:
    """
    Basit 2 sütunlu tablo oluştur (Field: Value formatında)
    """
    table_data = []
    for row in data:
        field_para = Paragraph(row[0], field_style)
        # Placeholder kontrolü
        if row[1].startswith('{') and row[1].endswith('}'):
            value_para = Paragraph(row[1], value_style)
        else:
            value_para = Paragraph(row[1], value_style)
        table_data.append([field_para, value_para])
    
    table = Table(
        table_data,
        colWidths=[2.5*inch, 4.5*inch]
    )
    
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    return table


def _create_meeting_info_table(
    data: List[List[str]],
    header_style: ParagraphStyle,
    cell_style: ParagraphStyle
) -> Table:
    """
    Meeting Information tablosu oluştur (2 sütun: MEETING NAME, MEETING DATES)
    """
    header_color = colors.HexColor('#0033A0')
    
    table_data = []
    for i, row in enumerate(data):
        if i == 0:
            # Başlık satırı
            table_data.append([
                Paragraph(row[0], header_style),
                Paragraph(row[1], header_style)
            ])
        else:
            # Veri satırı
            table_data.append([
                Paragraph(row[0], cell_style),
                Paragraph(row[1], cell_style)
            ])
    
    table = Table(
        table_data,
        colWidths=[3.5*inch, 3.5*inch]
    )
    
    table.setStyle(TableStyle([
        # Başlık satırı
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, 0), 5),
        ('RIGHTPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Veri satırı
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 5),
        ('RIGHTPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    
    return table


def _create_weekly_sleeping_room_table(
    sow_data: Optional[Dict[str, Any]],
    header_style: ParagraphStyle,
    cell_style: ParagraphStyle
) -> Table:
    """
    Haftalık Sleeping Room Requirements tablosu oluştur
    (Sunday-Saturday, Date, Rooms Booked/Night)
    """
    header_color = colors.HexColor('#0033A0')
    
    # Günler
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    # Tablo verisi
    table_data = []
    
    # Başlık satırı
    header_row = [""] + days
    table_data.append([Paragraph(cell, header_style) for cell in header_row])
    
    # Date satırı
    date_row = ["Date"]
    for day in days:
        date_row.append(sow_data.get(f'date_{day.lower()}', '{DATE}') if sow_data else '{DATE}')
    table_data.append([Paragraph(cell, cell_style) for cell in date_row])
    
    # Rooms Booked/Night satırı
    rooms_row = ["Rooms Booked/Night"]
    for day in days:
        rooms_row.append(sow_data.get(f'rooms_{day.lower()}', '{ROOMS}') if sow_data else '{ROOMS}')
    table_data.append([Paragraph(cell, cell_style) for cell in rooms_row])
    
    # Sütun genişlikleri
    col_widths = [1.2*inch] + [0.85*inch] * 7
    
    table = Table(table_data, colWidths=col_widths)
    
    table.setStyle(TableStyle([
        # Başlık satırı
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, 0), 3),
        ('RIGHTPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        
        # Veri satırları
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # İlk sütun (Date, Rooms)
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 3),
        ('RIGHTPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    
    return table


def _create_weekly_function_space_table(
    sow_data: Optional[Dict[str, Any]],
    header_style: ParagraphStyle,
    cell_style: ParagraphStyle
) -> Table:
    """
    Haftalık Function Space Requirements tablosu oluştur
    (Sunday-Friday, Registration Area, General Sessions Room, Conference Breakout Rooms, Logistics Room)
    """
    header_color = colors.HexColor('#0033A0')
    
    # Günler (Sunday-Friday)
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Tablo verisi
    table_data = []
    
    # Başlık satırı
    header_row = [""] + days
    table_data.append([Paragraph(cell, header_style) for cell in header_row])
    
    # Date satırı
    date_row = ["Date"]
    for day in days:
        date_row.append(sow_data.get(f'date_{day.lower()}', '{DATE}') if sow_data else '{DATE}')
    table_data.append([Paragraph(cell, cell_style) for cell in date_row])
    
    # Registration Area satırı
    reg_row = ["Registration Area"]
    for day in days:
        reg_row.append(sow_data.get(f'registration_{day.lower()}', '{REGISTRATION}') if sow_data else '{REGISTRATION}')
    table_data.append([Paragraph(cell, cell_style) for cell in reg_row])
    
    # General Sessions Room satırı
    gen_row = ["General Sessions Room"]
    for day in days:
        gen_row.append(sow_data.get(f'general_session_{day.lower()}', '{GENERAL_SESSION}') if sow_data else '{GENERAL_SESSION}')
    table_data.append([Paragraph(cell, cell_style) for cell in gen_row])
    
    # Conference Breakout Rooms satırı
    breakout_row = ["Conference Breakout Rooms (4)"]
    for day in days:
        breakout_row.append(sow_data.get(f'breakout_{day.lower()}', '{BREAKOUT}') if sow_data else '{BREAKOUT}')
    table_data.append([Paragraph(cell, cell_style) for cell in breakout_row])
    
    # Logistics Room satırı
    logistics_row = ["Logistics Room (1)"]
    for day in days:
        logistics_row.append(sow_data.get(f'logistics_{day.lower()}', '{LOGISTICS}') if sow_data else '{LOGISTICS}')
    table_data.append([Paragraph(cell, cell_style) for cell in logistics_row])
    
    # Sütun genişlikleri
    col_widths = [1.5*inch] + [0.9*inch] * 6
    
    table = Table(table_data, colWidths=col_widths)
    
    table.setStyle(TableStyle([
        # Başlık satırı
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, 0), 3),
        ('RIGHTPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        
        # Veri satırları
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # İlk sütun
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 3),
        ('RIGHTPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    
    return table


def _create_gpt_style_table(
    data: List[List[str]],
    header_style: ParagraphStyle,
    field_style: ParagraphStyle,
    value_style: ParagraphStyle
) -> Table:
    """
    GPT formatında tablo oluştur (mavi başlık bandı ile)
    
    Args:
        data: Tablo verisi [[field, value], ...]
        header_style: Başlık satırı stili
        field_style: Field name stili
        value_style: Value stili
    
    Returns:
        Table objesi
    """
    # Tablo verisini Paragraph'lara dönüştür
    table_data = []
    for i, row in enumerate(data):
        if i == 0:
            # Başlık satırı
            table_data.append([
                Paragraph(row[0], header_style),
                Paragraph(row[1], header_style)
            ])
        else:
            # Veri satırları
            field_para = Paragraph(row[0], field_style)
            # Placeholder kontrolü
            if row[1].startswith('{') and row[1].endswith('}'):
                value_para = Paragraph(row[1], value_style)
            else:
                value_para = Paragraph(row[1], value_style)
            table_data.append([field_para, value_para])
    
    # Tablo oluştur
    table = Table(
        table_data,
        colWidths=[2.5*inch, 4.5*inch],
        repeatRows=0
    )
    
    # Tablo stili
    header_color = colors.HexColor('#0033A0')  # Mavi renk
    table.setStyle(TableStyle([
        # Başlık satırı (mavi arka plan)
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, 0), 5),
        ('RIGHTPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Veri satırları
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 5),
        ('RIGHTPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Grid (kenarlık)
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        
        # Field sütunu (kalın)
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    
    return table


def markdown_to_pdf(markdown_text: str, output_path: str, title: str = "Statement of Work") -> bool:
    """
    Markdown metnini PDF'e dönüştür
    
    Args:
        markdown_text: Markdown formatında SOW metni
        output_path: PDF çıktı dosyası yolu
        title: PDF başlığı
    
    Returns:
        Başarılı ise True
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab not available, cannot generate PDF")
        return False
    
    try:
        # PDF oluştur
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Stil tanımlamaları
        styles = getSampleStyleSheet()
        
        # Özel stiller
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            leading=14,
            alignment=TA_LEFT
        )
        
        # Story (içerik) listesi
        story = []
        
        # Başlık
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Markdown'ı parse et ve PDF'e dönüştür
        lines = markdown_text.split('\n')
        in_list = False
        list_items = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list and list_items:
                    # Liste öğelerini ekle
                    for item in list_items:
                        story.append(Paragraph(f"• {item}", normal_style))
                    list_items = []
                    in_list = False
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # Başlıklar
            if line.startswith('# '):
                story.append(Paragraph(line[2:], heading1_style))
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], heading2_style))
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], heading2_style))
                story.append(Spacer(1, 0.1*inch))
            # Liste öğeleri
            elif line.startswith('- ') or line.startswith('* '):
                in_list = True
                list_items.append(line[2:])
            elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
                in_list = True
                # Numaralı liste
                item_text = line.split('. ', 1)[1] if '. ' in line else line
                list_items.append(item_text)
            # Markdown tabloları (| col1 | col2 |)
            elif '|' in line and line.strip().startswith('|'):
                # Tablo satırı - basit metin olarak ekle (ileride Table objesi ile geliştirilebilir)
                if in_list and list_items:
                    for item in list_items:
                        story.append(Paragraph(f"• {item}", normal_style))
                    list_items = []
                    in_list = False
                
                # Tablo satırını temizle ve ekle
                table_line = line.replace('|', ' | ').strip()
                # HTML karakterlerini temizle
                table_line = table_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(table_line, normal_style))
            # Normal metin
            else:
                if in_list and list_items:
                    # Önceki listeyi ekle
                    for item in list_items:
                        story.append(Paragraph(f"• {item}", normal_style))
                    list_items = []
                    in_list = False
                
                # HTML karakterlerini temizle
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(line, normal_style))
        
        # Kalan liste öğelerini ekle
        if in_list and list_items:
            for item in list_items:
                story.append(Paragraph(f"• {item}", normal_style))
        
        # PDF'i oluştur
        doc.build(story)
        logger.info(f"[SOW PDF] Generated PDF: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"[SOW PDF] Error generating PDF: {e}", exc_info=True)
        return False

def convert_sow_md_to_pdf(sow_md_path: str, output_pdf_path: Optional[str] = None) -> str:
    """
    SOW Markdown dosyasını PDF'e dönüştür
    
    Args:
        sow_md_path: SOW Markdown dosyası yolu
        output_pdf_path: Çıktı PDF yolu (opsiyonel)
    
    Returns:
        PDF dosyası yolu
    """
    md_path = Path(sow_md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"SOW Markdown not found: {sow_md_path}")
    
    # PDF yolu belirle
    if output_pdf_path:
        pdf_path = Path(output_pdf_path)
    else:
        pdf_path = md_path.with_suffix('.pdf')
    
    # Markdown içeriğini oku
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # PDF'e dönüştür
    success = markdown_to_pdf(markdown_text, str(pdf_path), title="Statement of Work (SOW)")
    
    if not success:
        raise RuntimeError(f"Failed to generate PDF from SOW")
    
    return str(pdf_path)
