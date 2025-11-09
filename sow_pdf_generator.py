#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOW PDF Generator
Markdown SOW'u PDF formatına dönüştürür
"""

import logging
from pathlib import Path
from typing import Optional

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

