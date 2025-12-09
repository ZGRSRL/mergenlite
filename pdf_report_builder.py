#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Report Builder
Analiz sonuçlarını profesyonel PDF raporuna dönüştürür
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# PDF library
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available, PDF generation will be limited")

def build_pdf_report(
    report_json: Dict[str, Any],
    output_path: str,
    opportunity_code: str = "UNKNOWN",
    criteria_results: Optional[Dict[str, Dict[str, Any]]] = None
) -> bool:
    """
    Analiz sonuçlarını PDF raporuna dönüştür
    
    Args:
        report_json: Opportunity requirements report JSON
        criteria_results: Belge bazlı kriter analiz sonuçları {doc_name: {criteria: analysis}}
        output_path: PDF çıktı yolu
        opportunity_code: Fırsat kodu
    
    Returns:
        True if successful
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
        
        # Özel stiller - Geliştirilmiş
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            spaceBefore=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=32
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=14,
            spaceBefore=16,
            fontName='Helvetica-Bold',
            leading=22,
            borderWidth=0,
            borderPadding=5,
            backColor=colors.HexColor('#eff6ff')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            leading=18
        )
        
        # Normal text style improvement
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Story (içerik) listesi
        story = []
        
        # Başlık
        story.append(Paragraph("Opportunity Requirements Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata - Geliştirilmiş görünüm
        opp_info = report_json.get('opportunity_info', {})
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=normal_style,
            fontSize=10,
            leading=14,
            leftIndent=10,
            spaceAfter=4
        )
        story.append(Paragraph(f"<b>Opportunity Code:</b> {opportunity_code}", metadata_style))
        story.append(Paragraph(f"<b>Solicitation Number:</b> {opp_info.get('solicitation_number', 'N/A')}", metadata_style))
        story.append(Paragraph(f"<b>Title:</b> {opp_info.get('title', 'N/A')}", metadata_style))
        story.append(Paragraph(f"<b>NAICS:</b> {opp_info.get('naics', 'N/A')}", metadata_style))
        story.append(Paragraph(f"<b>Response Deadline:</b> {opp_info.get('response_deadline', 'N/A')}", metadata_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        fit_assessment = report_json.get('fit_assessment', {})
        overall_score = fit_assessment.get('overall_score', 0)
        
        story.append(Paragraph("Executive Summary", heading_style))
        
        # Score with color coding
        score_color = colors.HexColor('#059669') if overall_score >= 70 else colors.HexColor('#f59e0b') if overall_score >= 40 else colors.HexColor('#dc2626')
        score_style = ParagraphStyle(
            'Score',
            parent=normal_style,
            fontSize=14,
            textColor=score_color,
            fontName='Helvetica-Bold',
            spaceAfter=10
        )
        story.append(Paragraph(f"<b>Overall Fit Score:</b> {overall_score}/100", score_style))
        
        summary = fit_assessment.get('summary', 'No summary available')
        # Ensure text is properly encoded for PDF (UTF-8)
        if isinstance(summary, str):
            # Remove any problematic characters and ensure ASCII-safe encoding
            summary = summary.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        story.append(Paragraph(summary, normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Strengths
        strengths = fit_assessment.get('strengths', [])
        if strengths:
            story.append(Paragraph("Strengths", subheading_style))
            for strength in strengths:
                # Ensure UTF-8 encoding
                strength_text = str(strength).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                story.append(Paragraph(f"✓ {strength_text}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Risks
        risks = fit_assessment.get('risks', [])
        if risks:
            story.append(Paragraph("Risks", subheading_style))
            for risk in risks:
                # Ensure UTF-8 encoding
                risk_text = str(risk).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                story.append(Paragraph(f"⚠ {risk_text}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Blocking Issues
        blocking = fit_assessment.get('blocking_issues', [])
        if blocking:
            story.append(Paragraph("Blocking Issues", subheading_style))
            for issue in blocking:
                # Ensure UTF-8 encoding
                issue_text = str(issue).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                story.append(Paragraph(f"✗ {issue_text}", normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        # Event Requirements
        event_req = report_json.get('event_requirements', {})
        if event_req:
            story.append(Paragraph("Event Requirements", heading_style))
            
            req_data = [
                ["Field", "Value"],
                ["Location", event_req.get('location', 'N/A')],
                ["Date Range", event_req.get('date_range', 'N/A')],
                ["Participants (Min)", str(event_req.get('participants_min', 'N/A'))],
                ["Participants (Target)", str(event_req.get('participants_target', 'N/A'))],
                ["Room Block Plan", event_req.get('room_block_plan', 'N/A')],
                ["Meeting Spaces", event_req.get('meeting_spaces', 'N/A')],
                ["AV Requirements", event_req.get('av_requirements', 'N/A')],
                ["F&B Requirements", event_req.get('fnb_requirements', 'N/A')],
                ["Special Logistics", event_req.get('special_logistics', 'N/A')]
            ]
            
            req_table = Table(req_data, colWidths=[2.2*inch, 3.8*inch])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(req_table)
            story.append(Spacer(1, 0.3*inch))
        
        # DETAILED REQUIREMENTS ANALYSIS (NEW SECTION)
        # report_json['requirements'] contains the full list from agents
        all_requirements = report_json.get('requirements', [])
        
        if all_requirements:
            story.append(PageBreak())
            story.append(Paragraph("Detailed Requirements Analysis", heading_style))
            story.append(Paragraph("The following requirements were extracted by AI agents from the solicitation documents.", normal_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Group by category
            grouped_reqs = {}
            for req in all_requirements:
                cat = req.get('category', 'General')
                # Clean up category name (e.g. "lodging_requirements" -> "Lodging")
                if '_' in cat:
                    cat = cat.replace('_requirements', '').replace('_', ' ').title()
                else:
                    cat = cat.title()
                
                if cat not in grouped_reqs:
                    grouped_reqs[cat] = []
                grouped_reqs[cat].append(req)
            
            # Create a table for each category
            for category, reqs in grouped_reqs.items():
                story.append(Paragraph(f"{category} Requirements", subheading_style))
                
                # Table Header
                req_table_data = [
                    ["Requirement Details", "Priority", "Source"]
                ]
                
                # Table Rows
                for req in reqs:
                    text = req.get('text', 'N/A')
                    priority = req.get('priority', 'Medium').capitalize()
                    source = req.get('source', 'Unknown')
                    
                    # Ensure properly encoded text
                    if isinstance(text, str):
                         text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                    
                    # Wrap long text
                    text_para = Paragraph(text, normal_style)
                    
                    req_table_data.append([text_para, priority, source])
                
                # Build Table
                # Columns: Details (wide), Priority (narrow), Source (narrow)
                t = Table(req_table_data, colWidths=[4.2*inch, 0.8*inch, 1.2*inch], repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    # Content Rows
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ]))
                
                story.append(t)
                story.append(Spacer(1, 0.2*inch))
            
            story.append(PageBreak())
        
        # Commercial Terms
        commercial = report_json.get('commercial_terms', {})
        if commercial:
            story.append(Paragraph("Commercial Terms", heading_style))
            
            comm_data = [
                ["Field", "Value"],
                ["Estimated Value", commercial.get('estimated_value', 'N/A')],
                ["Per Diem Limited", "Yes" if commercial.get('per_diem_limited') else "No"],
                ["Payment Terms", commercial.get('payment_terms', 'N/A')],
                ["E-Invoicing (IPP)", "Yes" if commercial.get('e_invoicing_ipp') else "No"],
                ["Tax Exempt", "Yes" if commercial.get('tax_exempt') else "No"],
                ["Cancellation Penalties", commercial.get('cancellation_penalties', 'N/A')],
                ["Other Key Terms", commercial.get('other_key_terms', 'N/A')]
            ]
            
            comm_table = Table(comm_data, colWidths=[2.2*inch, 3.8*inch])
            comm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(comm_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Recommended Hotels
        recommended_hotels = report_json.get('recommended_hotels', [])
        if recommended_hotels:
            story.append(Paragraph("Recommended Hotels", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            for idx, hotel in enumerate(recommended_hotels[:5], 1):  # En fazla 5 otel
                hotel_name = hotel.get('name', 'Unknown Hotel')
                city = hotel.get('city', '')
                state = hotel.get('state', '')
                phone = hotel.get('phone', '')
                email = hotel.get('email', '')
                contact_person = hotel.get('contact_person', '')
                
                story.append(Paragraph(f"<b>{idx}. {hotel_name}</b>", subheading_style))
                
                location_parts = []
                if city:
                    location_parts.append(city)
                if state:
                    location_parts.append(state)
                if location_parts:
                    story.append(Paragraph(f"Location: {', '.join(location_parts)}", normal_style))
                
                if phone:
                    story.append(Paragraph(f"Phone: {phone}", normal_style))
                if email:
                    story.append(Paragraph(f"Email: {email}", normal_style))
                if contact_person:
                    story.append(Paragraph(f"Contact: {contact_person}", normal_style))
                
                match_score = hotel.get('match_score', 0)
                if match_score:
                    story.append(Paragraph(f"Match Score: {match_score}/10", normal_style))
                
                # Mesafe bilgisi (yeni ajan ile hesaplanan)
                distance_miles = hotel.get('distance_miles')
                if distance_miles is not None:
                    story.append(Paragraph(f"Distance from event location: {distance_miles} miles", normal_style))
                
                story.append(Spacer(1, 0.15*inch))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Compliance Requirements with detailed explanations
        compliance = report_json.get('compliance', {})
        if compliance:
            story.append(Paragraph("Compliance Requirements", heading_style))
            
            # Compliance clause definitions
            compliance_definitions = {
                "FAR 52.212-4": {
                    "meaning": "Contract Terms and Conditions—Commercial Items",
                    "content": "Ticari kalemler için temel sözleşme koşulları (teslimat, garanti, fesih, ödeme)",
                    "purpose": "Tüm ticari tekliflerde zorunlu"
                },
                "FAR 52.212-5": {
                    "meaning": "Contract Terms and Conditions Required to Implement Statutes or Executive Orders",
                    "content": "Federal yasa ve Başkanlık emirlerini uygulayan hükümler",
                    "purpose": "Ödeme, işyeri ayrımcılığı, vergi vs."
                },
                "FAR 52.204-24/25/26": {
                    "meaning": "Covered Telecommunications Equipment or Services",
                    "content": "Huawei, ZTE vb. yasaklı telekom ekipmanlarını kullanmama beyanı",
                    "purpose": "Güvenlik ve tedarik zinciri kontrolü"
                },
                "Security/Telecom Restrictions": {
                    "meaning": "—",
                    "content": "Ek güvenlik veya telekom kısıtlamaları (ör. bulut/şifreleme)",
                    "purpose": "Bu örnekte yok"
                },
                "Bytedance Restriction": {
                    "meaning": "—",
                    "content": "TikTok/Bytedance yazılımlarına ilişkin yasak",
                    "purpose": "Yok olarak işaretlenmiş"
                },
                "EDAR 3452.201-70": {
                    "meaning": "Contracting Officer's Representative (COR) Designation",
                    "content": "Eğitim Bakanlığı'nın temsilcisinin tanımlanması",
                    "purpose": "Sözleşme sürecinde yetkili kişi belirlenir"
                },
                "EDAR 3452.224-70": {
                    "meaning": "Privacy Act (Education)",
                    "content": "Katılımcı verilerinin gizliliği ve korunması",
                    "purpose": "Veri gizliliği"
                },
                "EDAR 3452.233-70": {
                    "meaning": "Agency Protests",
                    "content": "Eğitim Bakanlığı'na yönelik ihale itirazlarının prosedürü",
                    "purpose": "Şikayet yönetimi"
                },
                "EDAR 3452.237-71": {
                    "meaning": "Evaluation of Contractor Performance",
                    "content": "Yüklenici performans değerlendirmesi",
                    "purpose": "Hizmet kalitesi raporlaması"
                },
                "EDAR 3452.239-71": {
                    "meaning": "Information Technology Security",
                    "content": "IT güvenlik gereklilikleri",
                    "purpose": "Sistem/altyapı güvenliği"
                },
                "EDAR 3452.242-73": {
                    "meaning": "Accessibility of Meetings, Conferences, and Seminars",
                    "content": "Toplantı/konferans erişilebilirliği (ADA uyumu)",
                    "purpose": "Engelli erişimine uygunluk"
                },
                "FAR 32.202-1(b)": {
                    "meaning": "Advance Payments",
                    "content": "Peşin ödeme koşullarına ilişkin hükümler",
                    "purpose": "Finansal düzenleme"
                },
                "FAR 13.106-2(b)(3)": {
                    "meaning": "Evaluation of Quotations or Offers",
                    "content": "Teklif değerlendirme kriterleri",
                    "purpose": "Alım yöntemi (Simplified Acquisition)"
                },
                "FAR 52.252-2": {
                    "meaning": "Clauses Incorporated by Reference",
                    "content": "FAR/DFAR maddelerinin referansla dahil edilmesi",
                    "purpose": "Sözleşmede diğer hükümleri geçerli kılar"
                }
            }
            
            # Build compliance table with detailed columns
            comp_data = [
                ["Kısaltma", "Anlamı", "İçerik / Yükümlülük", "Ne İşe Yarar", "Gerekli"]
            ]
            
            # Standard clauses
            standard_clauses = [
                ("FAR 52.212-4", compliance.get('far_52_212_4', False)),
                ("FAR 52.212-5", compliance.get('far_52_212_5', False)),
                ("FAR 52.204-24/25/26", compliance.get('far_52_204_24_25_26', False)),
                ("Security/Telecom Restrictions", compliance.get('security_telecom_restrictions', False)),
                ("Bytedance Restriction", compliance.get('bytedance_restriction', False))
            ]
            
            for clause, required in standard_clauses:
                defn = compliance_definitions.get(clause, {
                    "meaning": "—",
                    "content": "—",
                    "purpose": "—"
                })
                comp_data.append([
                    clause,
                    defn["meaning"],
                    defn["content"],
                    defn["purpose"],
                    "Evet" if required else "Hayır"
                ])
            
            # Other mandatory clauses
            other_clauses = compliance.get('other_mandatory_clauses', [])
            for clause in other_clauses:
                defn = compliance_definitions.get(clause, {
                    "meaning": "—",
                    "content": "—",
                    "purpose": "—"
                })
                comp_data.append([
                    clause,
                    defn["meaning"],
                    defn["content"],
                    defn["purpose"],
                    "Evet"
                ])
            
            # Create table with appropriate column widths
            comp_table = Table(comp_data, colWidths=[1.2*inch, 1.5*inch, 2*inch, 1.8*inch, 0.8*inch])
            comp_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                # Data rows
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.whitesmoke),
                # Column alignment
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Required column centered
            ]))
            story.append(comp_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Criteria-Based Analysis Results
        if criteria_results:
            story.append(PageBreak())
            story.append(Paragraph("Document-Specific Analysis (Form Criteria)", heading_style))
            
            for doc_name, criteria_analyses in criteria_results.items():
                if not criteria_analyses:
                    continue
                
                story.append(Paragraph(f"<b>Document:</b> {doc_name}", subheading_style))
                
                for criteria, analysis_data in criteria_analyses.items():
                    analysis = analysis_data.get('analysis', {})
                    compliance_score = analysis.get('compliance_score', 0)
                    matched = analysis.get('matched_info', [])
                    missing = analysis.get('missing_or_conflicting', [])
                    
                    story.append(Paragraph(f"<b>Criteria:</b> {criteria}", styles['Normal']))
                    story.append(Paragraph(f"Compliance Score: {compliance_score}%", styles['Normal']))
                    
                    if matched:
                        story.append(Paragraph("<b>Matched Information:</b>", styles['Normal']))
                        for item in matched[:5]:  # İlk 5
                            story.append(Paragraph(f"• {item}", styles['Normal']))
                    
                    if missing:
                        story.append(Paragraph("<b>Missing/Conflicting:</b>", styles['Normal']))
                        for item in missing[:5]:  # İlk 5
                            story.append(Paragraph(f"⚠ {item}", styles['Normal']))
                    
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.2*inch))
        
        # Footer - Geliştirilmiş
        story.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=normal_style,
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceBefore=20
        )
        story.append(Paragraph(
            f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by MergenLite AI Analysis System</i>",
            footer_style
        ))
        
        # UTF-8 encoding için font desteği ekle (karakter sorunlarını önlemek için)
        # ReportLab varsayılan olarak UTF-8 destekler, ancak özel karakterler için font kontrolü yapılmalı
        
        # PDF'i oluştur
        doc.build(story)
        logger.info(f"[OK] PDF report created: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] PDF generation failed: {e}", exc_info=True)
        return False

