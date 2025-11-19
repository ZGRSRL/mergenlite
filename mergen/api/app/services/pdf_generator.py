"""
PDF generation utilities for analysis results.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available, PDF generation will be disabled")


def _format_value(value: Any) -> str:
    """Format a value for display in PDF tables."""
    if value is None:
        return "N/A"
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def _add_section_header(story: List, title: str, styles: Any):
    """Add a section header with Federal Blue styling and section box design."""
    # Federal Blue: #003366
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#003366'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        leftIndent=0,
        backColor=colors.HexColor('#f9fbfd'),
        borderPadding=12,
    )
    # Create section box with left border effect using table
    box_data = [[Paragraph(f"<b>{title}</b>", header_style)]]
    box_table = Table(box_data, colWidths=[6.3*inch])
    box_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fbfd')),
        ('LEFTPADDING', (0, 0), (0, 0), 18),
        ('LINEBELOW', (0, 0), (-1, -1), 0, colors.HexColor('#003366')),
        ('LINEBEFORE', (0, 0), (0, -1), 4, colors.HexColor('#003366')),
    ]))
    story.append(box_table)
    story.append(Spacer(1, 0.1*inch))


def _add_info_table(story: List, data: List[List[str]], col_widths: List[float] = None):
    """Add an information table with standard styling."""
    if col_widths is None:
        col_widths = [1.8*inch, 4.5*inch]
    
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Label column: Federal Blue background, white text
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#003366')),  # Federal Blue
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        # Value column: Light blue background
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#eef3f8')),  # Light blue
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7dce2')),  # Gray border
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),  # Dark gray text
        ('FONTSIZE', (1, 0), (1, -1), 12),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))


def _add_data_table(story: List, headers: List[str], rows: List[List[str]], col_widths: List[float] = None):
    """Add a data table with headers and rows."""
    if not rows:
        return
    
    table_data = [headers] + rows
    
    if col_widths is None:
        # Auto-calculate column widths
        num_cols = len(headers)
        total_width = 6.3*inch
        col_widths = [total_width / num_cols] * num_cols
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header: Federal Blue background, white text
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),  # Federal Blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Body: white background, alternating rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7dce2')),  # Gray border
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef3f8')]),  # Alternating rows
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),  # Dark gray text
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))


def generate_analysis_pdf(
    output_path: Path,
    analysis_result: Dict[str, Any],
    opportunity: Dict[str, Any],
) -> bool:
    """
    Generate a detailed PDF report from analysis results, similar to the example RFQ PDF.
    
    Args:
        output_path: Path where PDF will be saved
        analysis_result: Analysis result data (from result_json)
        opportunity: Opportunity metadata
        
    Returns:
        True if PDF was generated successfully, False otherwise
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab not available, cannot generate PDF")
        return False
    
    try:
        # Custom page template with footer
        from reportlab.platypus import PageTemplate, BaseDocTemplate
        from reportlab.lib.units import inch
        
        class NumberedCanvas:
            """Custom canvas for page numbers"""
            def __init__(self, canvas, doc):
                self.canvas = canvas
                self.doc = doc
            
            def draw_page_number(self):
                page_num = self.canvas.getPageNumber()
                total_pages = self.doc.page
                self.canvas.saveState()
                self.canvas.setFont("Helvetica", 11)
                self.canvas.setFillColor(colors.HexColor('#003366'))
                self.canvas.drawCentredString(4.25*inch, 0.5*inch, 
                                            f"Page {page_num} of {total_pages}")
                self.canvas.restoreState()
        
        # Use BaseDocTemplate for custom footer
        doc = BaseDocTemplate(str(output_path), pagesize=letter, 
                             rightMargin=1*inch, leftMargin=1*inch,
                             topMargin=1*inch, bottomMargin=1*inch)
        
        def on_first_page(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor('#003366'))
            page_num = canvas.getPageNumber()
            # We'll update total pages after build
            canvas.drawCentredString(4.25*inch, 0.5*inch, f"Page {page_num}")
            canvas.restoreState()
        
        def on_later_pages(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor('#003366'))
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(4.25*inch, 0.5*inch, f"Page {page_num}")
            canvas.restoreState()
        
        # Create page templates
        from reportlab.platypus import PageTemplate, Frame
        
        frame = Frame(doc.leftMargin, doc.bottomMargin, 
                     doc.width, doc.height, 
                     id='normal')
        template = PageTemplate(id='AllPages', frames=[frame], 
                               onPage=on_first_page,
                               onPageEnd=on_later_pages)
        doc.addPageTemplates([template])
        story = []
        styles = getSampleStyleSheet()
        
        # Merge opportunity details from arguments and analysis payload
        opp_data = {}
        if opportunity:
            opp_data.update(opportunity)
        analysis_opp = analysis_result.get("opportunity") or {}
        opp_data.update(analysis_opp)
        sow_analysis = analysis_result.get("sow_analysis", {})
        
        # Header with Event Name and Solicitation Number
        from reportlab.platypus import Table, TableStyle
        header_data = [
            [
                Paragraph(f"<b>{_format_value(opp_data.get('title', 'Event Name'))}</b>", 
                         ParagraphStyle('HeaderLeft', parent=styles['Normal'], 
                                      fontSize=14, textColor=colors.HexColor('#003366'),
                                      fontName='Helvetica-Bold', alignment=TA_LEFT)),
                Paragraph(f"<b>{_format_value(opp_data.get('notice_id', 'Solicitation Number'))}</b>", 
                         ParagraphStyle('HeaderRight', parent=styles['Normal'], 
                                      fontSize=14, textColor=colors.HexColor('#003366'),
                                      fontName='Helvetica-Bold', alignment=TA_LEFT)),
            ]
        ]
        header_table = Table(header_data, colWidths=[3.15*inch, 3.15*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#d7dce2')),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#003366'),  # Federal Blue
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )
        title = Paragraph("Analysis Report", title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Get SOW analysis data (already loaded as sow_analysis)
        
        # 1. Event Details
        _add_section_header(story, "Event Details", styles)
        event_details = sow_analysis.get("event_details", {})
        event_data = [
            ["Event Name:", _format_value(event_details.get("event_name", opp_data.get("title", "N/A")))],
            ["Solicitation Number:", _format_value(event_details.get("solicitation_number", opp_data.get("notice_id", "N/A")))],
            ["Agency:", _format_value(event_details.get("agency", opp_data.get("agency", "N/A")))],
            ["Start Date:", _format_value(event_details.get("start_date"))],
            ["End Date:", _format_value(event_details.get("end_date"))],
            ["Location:", _format_value(event_details.get("location"))],
            ["Submission Due Date:", _format_value(event_details.get("submission_due_date"))],
        ]
        _add_info_table(story, event_data)
        
        # 2. Sleeping Room Requirements
        room_reqs = sow_analysis.get("room_requirements", {})
        if room_reqs:
            _add_section_header(story, "Sleeping Room Requirements", styles)
            
            # Summary info
            summary_data = [
                ["Total Room Nights:", _format_value(room_reqs.get("total_room_nights"))],
                ["Special Requirements:", _format_value(room_reqs.get("special_requirements"))],
            ]
            _add_info_table(story, summary_data)
            
            # Daily breakdown
            daily_rooms = room_reqs.get("daily_breakdown", [])
            if daily_rooms:
                headers = ["Day", "Date", "Rooms Per Night"]
                rows = []
                for day in daily_rooms:
                    rows.append([
                        _format_value(day.get("day")),
                        _format_value(day.get("date")),
                        _format_value(day.get("rooms_per_night")),
                    ])
                _add_data_table(story, headers, rows, [1.5*inch, 2*inch, 2.8*inch])
        
        # 3. Function Space Requirements
        function_space = sow_analysis.get("function_space_requirements", {})
        if function_space:
            _add_section_header(story, "Function Space Requirements", styles)
            
            daily_function = function_space.get("daily_breakdown", [])
            if daily_function:
                headers = ["Day", "Date", "Room Type", "Capacity", "Setup"]
                rows = []
                for day in daily_function:
                    rooms = day.get("rooms", [])
                    if rooms:
                        for room in rooms:
                            rows.append([
                                _format_value(day.get("day")),
                                _format_value(day.get("date")),
                                _format_value(room.get("room_type")),
                                _format_value(room.get("capacity")),
                                _format_value(room.get("setup")),
                            ])
                    else:
                        rows.append([
                            _format_value(day.get("day")),
                            _format_value(day.get("date")),
                            _format_value(day.get("room_type")),
                            _format_value(day.get("capacity")),
                            _format_value(day.get("setup")),
                        ])
                if rows:
                    _add_data_table(story, headers, rows, [1*inch, 1.2*inch, 1.5*inch, 1*inch, 1.6*inch])
        
        # 4. AV Requirements
        av_reqs = sow_analysis.get("av_requirements", {})
        if av_reqs:
            _add_section_header(story, "Daily AV Requirements", styles)
            
            daily_av = av_reqs.get("daily_breakdown", [])
            if daily_av:
                headers = ["Day", "Date", "Room", "Setup", "Capacity", "AV Needs", "Special Notes"]
                rows = []
                for day in daily_av:
                    rooms = day.get("rooms", [])
                    if rooms:
                        for room in rooms:
                            rows.append([
                                _format_value(day.get("day")),
                                _format_value(day.get("date")),
                                _format_value(room.get("room_name")),
                                _format_value(room.get("setup")),
                                _format_value(room.get("capacity")),
                                _format_value(room.get("av_needs")),
                                _format_value(room.get("special_notes")),
                            ])
                    else:
                        rows.append([
                            _format_value(day.get("day")),
                            _format_value(day.get("date")),
                            _format_value(day.get("room_name")),
                            _format_value(day.get("setup")),
                            _format_value(day.get("capacity")),
                            _format_value(day.get("av_needs")),
                            _format_value(day.get("special_notes")),
                        ])
                if rows:
                    _add_data_table(story, headers, rows)
            
            # Hybrid Meeting AV
            hybrid_av = av_reqs.get("hybrid_meeting_requirements", {})
            if hybrid_av:
                story.append(Spacer(1, 0.1*inch))
                _add_section_header(story, "Hybrid Meeting AV Requirements", styles)
                hybrid_data = [
                    ["OWLs Required:", _format_value(hybrid_av.get("owls_required"))],
                    ["Zoom Management:", _format_value(hybrid_av.get("zoom_management"))],
                    ["Other Requirements:", _format_value(hybrid_av.get("other_requirements"))],
                ]
                _add_info_table(story, hybrid_data)
            
            # Court Reporter Audio Feed
            court_reporter = av_reqs.get("court_reporter_audio_feed", {})
            if court_reporter:
                story.append(Spacer(1, 0.1*inch))
                _add_section_header(story, "Court Reporter Audio Feed", styles)
                court_data = [
                    ["Required:", _format_value(court_reporter.get("required"))],
                    ["Details:", _format_value(court_reporter.get("details"))],
                ]
                _add_info_table(story, court_data)
            
            # Breakout Room Power & Setup
            breakout = av_reqs.get("breakout_room_power_setup", {})
            if breakout:
                story.append(Spacer(1, 0.1*inch))
                _add_section_header(story, "Breakout Room Power & Setup Requirements", styles)
                breakout_data = [
                    ["Power Strips:", _format_value(breakout.get("power_strips"))],
                    ["Setup Requirements:", _format_value(breakout.get("setup_requirements"))],
                ]
                _add_info_table(story, breakout_data)
        
        # 5. Food & Beverage Requirements
        fb_reqs = sow_analysis.get("food_beverage_requirements", {})
        if fb_reqs:
            _add_section_header(story, "Food & Beverage and Refreshments", styles)
            
            daily_fb = fb_reqs.get("daily_breakdown", [])
            if daily_fb:
                headers = ["Day", "Date", "Time", "Headcount", "Menu/Items"]
                rows = []
                for day in daily_fb:
                    items = day.get("items", [])
                    if items:
                        for item in items:
                            rows.append([
                                _format_value(day.get("day")),
                                _format_value(day.get("date")),
                                _format_value(item.get("time")),
                                _format_value(item.get("headcount")),
                                _format_value(item.get("menu")),
                            ])
                    else:
                        rows.append([
                            _format_value(day.get("day")),
                            _format_value(day.get("date")),
                            _format_value(day.get("time")),
                            _format_value(day.get("headcount")),
                            _format_value(day.get("menu")),
                        ])
                if rows:
                    _add_data_table(story, headers, rows, [1*inch, 1.2*inch, 1*inch, 1*inch, 2*inch])
        
        # 6. Commercial Terms & Special Conditions
        commercial = sow_analysis.get("commercial_terms", {})
        if commercial:
            _add_section_header(story, "Commercial Terms & Special Conditions", styles)
            commercial_data = [
                ["NAICS Code:", _format_value(commercial.get("naics_code", opp_data.get("naics_code")))],
                ["PSC Code:", _format_value(commercial.get("psc_code"))],
                ["Set-Aside Type:", _format_value(commercial.get("set_aside_type"))],
                ["Size Standard:", _format_value(commercial.get("size_standard"))],
                ["ADA Compliance:", _format_value(commercial.get("ada_compliance"))],
                ["Wi-Fi/Internet:", _format_value(commercial.get("wifi_internet"))],
                ["Parking Requirements:", _format_value(commercial.get("parking_requirements"))],
                ["Cancellation Terms:", _format_value(commercial.get("cancellation_terms"))],
                ["AV Discount Required:", _format_value(commercial.get("av_discount_required"))],
                ["F&B Discount Required:", _format_value(commercial.get("fb_discount_required"))],
            ]
            _add_info_table(story, commercial_data)
        
        # 7. Cost Proposal & Budget Submission Instructions
        cost_proposal = sow_analysis.get("cost_proposal", {})
        if cost_proposal:
            _add_section_header(story, "Cost Proposal & Budget Submission Instructions", styles)
            cost_data = [
                ["Quote Due Date:", _format_value(cost_proposal.get("quote_due_date"))],
                ["Submission Method:", _format_value(cost_proposal.get("submission_method"))],
                ["Submission Email:", _format_value(cost_proposal.get("submission_email"))],
                ["Required Attachments:", _format_value(cost_proposal.get("required_attachments"))],
            ]
            _add_info_table(story, cost_data)
        
        # 8. Evaluation and Award Criteria
        evaluation = sow_analysis.get("evaluation_criteria", {})
        if evaluation:
            _add_section_header(story, "Evaluation and Award Criteria", styles)
            eval_data = [
                ["Payment Terms:", _format_value(evaluation.get("payment_terms"))],
                ["Tax Exemption Status:", _format_value(evaluation.get("tax_exemption_status"))],
                ["Billing Method:", _format_value(evaluation.get("billing_method"))],
                ["Cancellation Policy:", _format_value(evaluation.get("cancellation_policy"))],
            ]
            _add_info_table(story, eval_data)
        
        # 9. Compliance Requirements
        compliance = sow_analysis.get("compliance_requirements", {})
        if compliance:
            _add_section_header(story, "Compliance Requirements", styles)
            
            far_clauses = compliance.get("far_clauses", [])
            if far_clauses:
                story.append(Paragraph("<b>FAR Clauses:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for clause in far_clauses:
                    clause_text = f"• {_format_value(clause.get('number', ''))}: {_format_value(clause.get('title', ''))}"
                    story.append(Paragraph(clause_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            edar_clauses = compliance.get("edar_clauses", [])
            if edar_clauses:
                story.append(Paragraph("<b>EDAR Clauses:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for clause in edar_clauses:
                    clause_text = f"• {_format_value(clause.get('number', ''))}: {_format_value(clause.get('title', ''))}"
                    story.append(Paragraph(clause_text, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        
        # 10. Appendices
        appendices = sow_analysis.get("appendices", {})
        if appendices:
            _add_section_header(story, "Appendices", styles)
            app_data = [
                ["Additional Documents:", _format_value(appendices.get("additional_documents"))],
                ["Other Requirements:", _format_value(appendices.get("other_requirements"))],
            ]
            _add_info_table(story, app_data)
        
        # Hotels (if available - for hotel_match analysis)
        if analysis_result.get("hotels"):
            _add_section_header(story, "Recommended Hotels", styles)
            hotels = analysis_result.get("hotels", [])
            if hotels:
                headers = ["Name", "Score", "Price", "Currency"]
                rows = []
                for hotel in hotels[:10]:
                    rows.append([
                        _format_value(hotel.get("name")),
                        _format_value(hotel.get("score")),
                        _format_value(hotel.get("total_price")),
                        _format_value(hotel.get("currency", "USD")),
                    ])
                _add_data_table(story, headers, rows, [3*inch, 1*inch, 1*inch, 1.3*inch])
        
        # Document Analysis Summary
        doc_analysis = analysis_result.get("document_analysis", {})
        if doc_analysis:
            _add_section_header(story, "Document Analysis Summary", styles)
            doc_data = [
                ["Documents Analyzed:", _format_value(doc_analysis.get("documents_analyzed"))],
                ["Total Word Count:", _format_value(doc_analysis.get("total_word_count"))],
                ["Total Text Length:", _format_value(doc_analysis.get("total_text_length"))],
                ["Total Tables Extracted:", _format_value(doc_analysis.get("total_tables"))],
            ]
            _add_info_table(story, doc_data)
        
        # Notes
        notes = analysis_result.get("notes", "")
        if notes:
            _add_section_header(story, "Notes", styles)
            story.append(Paragraph(_format_value(notes), styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF generated successfully: {output_path}")
        return True
        
    except Exception as exc:
        logger.exception(f"Failed to generate PDF: {exc}")
        return False

