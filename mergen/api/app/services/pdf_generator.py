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
    # Add extra space before section header to prevent overlap
    story.append(Spacer(1, 0.15*inch))
    
    # Federal Blue: #003366
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#003366'),
        spaceAfter=8,
        spaceBefore=0,  # Space handled by Spacer above
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
    story.append(Spacer(1, 0.15*inch))  # Increased from 0.1 to 0.15


def _add_info_table(story: List, data: List[List[str]], col_widths: List[float] = None):
    """Add an information table with standard styling."""
    if col_widths is None:
        # Ensure total width doesn't exceed available width (6.3 inch)
        col_widths = [1.8*inch, 4.5*inch]
        total = sum(col_widths)
        if total > 6.3*inch:
            scale = 6.3*inch / total
            col_widths = [w * scale for w in col_widths]
    
    # Convert cell values to Paragraphs for proper text wrapping
    from reportlab.lib.styles import getSampleStyleSheet
    base_styles = getSampleStyleSheet()
    
    label_style = ParagraphStyle(
        'InfoTableLabel',
        parent=base_styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.white,
        leading=14,
        leftIndent=6,
        rightIndent=6,
    )
    
    value_style = ParagraphStyle(
        'InfoTableValue',
        parent=base_styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        leading=14,
        leftIndent=6,
        rightIndent=6,
    )
    
    # Convert data to Paragraphs
    table_data = []
    for row in data:
        label = Paragraph(str(row[0]) if len(row) > 0 else "", label_style)
        value = Paragraph(str(row[1]) if len(row) > 1 else "", value_style)
        table_data.append([label, value])
    
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Label column: Federal Blue background, white text
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#003366')),  # Federal Blue
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        # Value column: Light blue background
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#eef3f8')),  # Light blue
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7dce2')),  # Gray border
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),  # Dark gray text
        ('FONTSIZE', (1, 0), (1, -1), 11),
        # Word wrap for long text
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*inch))  # Increased spacing after info tables


def _add_data_table(story: List, headers: List[str], rows: List[List[str]], col_widths: List[float] = None):
    """Add a data table with headers and rows."""
    if not rows:
        return
    
    # Get styles for Paragraph creation
    from reportlab.lib.styles import getSampleStyleSheet
    base_styles = getSampleStyleSheet()
    
    # Convert all cell values to Paragraphs for proper text wrapping
    # This prevents text overflow and ensures proper spacing
    cell_style = ParagraphStyle(
        'TableCell',
        parent=base_styles['Normal'],
        fontSize=10,  # Slightly smaller font for tables
        textColor=colors.HexColor('#333333'),
        leading=12,  # Line spacing
        leftIndent=4,
        rightIndent=4,
    )
    
    # Convert headers to Paragraphs
    header_style = ParagraphStyle(
        'TableHeader',
        parent=cell_style,
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.white,
    )
    
    table_data = [[Paragraph(str(h), header_style) for h in headers]]
    
    # Convert rows to Paragraphs
    for row in rows:
        table_data.append([Paragraph(str(cell) if cell else "", cell_style) for cell in row])
    
    # Available width: 8.5 inch page - 2 inch margins = 6.5 inch
    # Use 6.3 inch to leave some buffer
    available_width = 6.3*inch
    
    if col_widths is None:
        # Auto-calculate column widths
        num_cols = len(headers)
        col_widths = [available_width / num_cols] * num_cols
    else:
        # Ensure total width doesn't exceed available width
        total_width = sum(col_widths)
        if total_width > available_width:
            # Scale down proportionally
            scale_factor = available_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header: Federal Blue background, white text
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),  # Federal Blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        # Body: white background, alternating rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7dce2')),  # Gray border
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef3f8')]),  # Alternating rows
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),  # Dark gray text
        # Word wrap for long text
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*inch))  # Increased spacing after data tables


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
        sow_analysis = analysis_result.get("sow_analysis")
        
        # If sow_analysis is None, create empty dict to avoid errors
        if sow_analysis is None:
            sow_analysis = {}
            logger.warning(f"SOW analysis is None in analysis_result, using empty dict")
        
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
        # Use actual SOW analysis structure: EventDetails, SleepingRoomRequirements, etc.
        
        # 1. Event Details
        _add_section_header(story, "Event Details", styles)
        event_details = sow_analysis.get("EventDetails", {}) if sow_analysis else {}
        
        # Use EventDetails if available, otherwise fall back to opportunity data
        # SOW Analyzer outputs: event_name, solicitation_number, agency, start_date, end_date, duration_days, locations (array), submission_due
        if event_details:
            event_name = event_details.get("event_name") or event_details.get("EventName") or opp_data.get("title", "N/A")
            solicitation_number = event_details.get("solicitation_number") or event_details.get("SolicitationNumber") or opp_data.get("notice_id", "N/A")
            agency = event_details.get("agency") or event_details.get("Agency") or opp_data.get("agency", "N/A")
            
            # Try direct fields first (SOW analyzer format), then nested Dates object (legacy)
            start_date = event_details.get("start_date")
            if not start_date:
                dates = event_details.get("Dates", {})
                start_date = dates.get("Start") if isinstance(dates, dict) else None
            start_date = _format_value(start_date) if start_date else "N/A"
            
            end_date = event_details.get("end_date")
            if not end_date:
                dates = event_details.get("Dates", {})
                end_date = dates.get("End") if isinstance(dates, dict) else None
            end_date = _format_value(end_date) if end_date else "N/A"
            
            duration = event_details.get("duration_days")
            if not duration:
                dates = event_details.get("Dates", {})
                duration = dates.get("Duration") if isinstance(dates, dict) else None
            duration = _format_value(duration) if duration else "N/A"
            
            # Locations: SOW analyzer outputs as array, extract first location for display
            locations = event_details.get("locations", [])
            location_str = "N/A"
            if locations and isinstance(locations, list) and len(locations) > 0:
                # Use first location's city
                first_loc = locations[0]
                if isinstance(first_loc, dict):
                    city = first_loc.get("city", "")
                    location_str = city if city else "N/A"
                elif isinstance(first_loc, str):
                    location_str = first_loc
            elif not locations:
                # Try legacy Location object format
                location = event_details.get("Location", {})
                if isinstance(location, dict):
                    city = location.get("City", "")
                    state = location.get("State", "")
                    country = location.get("Country", "")
                    location_str = f"{city}, {state}, {country}".strip(", ") if city else "N/A"
            
            submission_due = event_details.get("submission_due") or event_details.get("SubmissionDueDate") or "N/A"
        else:
            # Fallback to opportunity data
            event_name = opp_data.get("title", "N/A")
            solicitation_number = opp_data.get("notice_id", "N/A")
            agency = opp_data.get("agency", "N/A")
            start_date = "N/A"
            end_date = "N/A"
            duration = "N/A"
            location_str = "N/A"
            submission_due = "N/A"
        
        event_data = [
            ["Event Name:", _format_value(event_name)],
            ["Solicitation Number:", _format_value(solicitation_number)],
            ["Agency:", _format_value(agency)],
            ["Start Date:", _format_value(start_date)],
            ["End Date:", _format_value(end_date)],
            ["Duration:", _format_value(duration)],
            ["Location:", _format_value(location_str)],
            ["Submission Due Date:", _format_value(submission_due)],
        ]
        _add_info_table(story, event_data)
        
        # 2. Lodging Requirements (Detailed)
        _add_section_header(story, "Lodging Requirements", styles)
        lodging_reqs = sow_analysis.get("LodgingRequirements", {}) if sow_analysis else {}
        if lodging_reqs:
            rooms_min = lodging_reqs.get("rooms_per_city_min")
            rooms_max = lodging_reqs.get("rooms_per_city_max")
            max_stay_days = lodging_reqs.get("max_stay_days_per_city")
            uniform_terms = lodging_reqs.get("uniform_terms_required")
            amenities = lodging_reqs.get("amenities_required", [])
            
            cancellation_policy = lodging_reqs.get("cancellation_policy", {})
            free_cancellation_hours = cancellation_policy.get("free_cancellation_hours_before_checkin")
            force_majeure = cancellation_policy.get("force_majeure_no_penalty")
            name_change = cancellation_policy.get("name_change_allowed_until_checkin")
            
            lodging_data = [
                ["Rooms per City (Min):", _format_value(rooms_min)],
                ["Rooms per City (Max):", _format_value(rooms_max)],
                ["Max Stay Days per City:", _format_value(max_stay_days)],
                ["Uniform Terms Required:", _format_value("Yes" if uniform_terms else "No")],
                ["Free Cancellation (Hours Before Check-in):", _format_value(free_cancellation_hours)],
                ["Force Majeure (No Penalty):", _format_value("Yes" if force_majeure else "No")],
                ["Name Change Allowed:", _format_value("Yes" if name_change else "No")],
                ["Required Amenities:", _format_value(", ".join(amenities) if isinstance(amenities, list) else amenities)],
            ]
            _add_info_table(story, lodging_data)
        else:
            story.append(Paragraph("No lodging requirements specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 2b. Locations Table
        _add_section_header(story, "Locations", styles)
        locations = sow_analysis.get("Locations", []) if sow_analysis else []
        if locations and isinstance(locations, list) and len(locations) > 0:
            headers = ["City", "Stadium", "ZIP Codes", "Start Date", "Days"]
            rows = []
            for loc in locations:
                if isinstance(loc, dict):
                    zip_codes = loc.get("zip_codes", [])
                    zip_str = ", ".join(zip_codes) if isinstance(zip_codes, list) else str(zip_codes)
                    rows.append([
                        _format_value(loc.get("city")),
                        _format_value(loc.get("stadium")),
                        _format_value(zip_str),
                        _format_value(loc.get("start_date")),
                        _format_value(loc.get("num_days")),
                    ])
            if rows:
                _add_data_table(story, headers, rows, [1.5*inch, 1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch])
        else:
            story.append(Paragraph("No locations table specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 2c. Transportation Requirements
        _add_section_header(story, "Transportation Requirements", styles)
        transport_reqs = sow_analysis.get("TransportationRequirements", {}) if sow_analysis else {}
        if transport_reqs:
            max_distance = transport_reqs.get("max_distance_miles_hotel_to_venue")
            transport_options = transport_reqs.get("required_transportation_options", [])
            plan_required = transport_reqs.get("transportation_plan_required")
            plan_due_days = transport_reqs.get("transportation_plan_due_days_post_award")
            
            transport_data = [
                ["Max Distance (Miles) to Venue:", _format_value(max_distance)],
                ["Required Transportation Options:", _format_value(", ".join(transport_options) if isinstance(transport_options, list) else transport_options)],
                ["Transportation Plan Required:", _format_value("Yes" if plan_required else "No")],
                ["Transportation Plan Due (Days Post Award):", _format_value(plan_due_days)],
            ]
            _add_info_table(story, transport_data)
        else:
            story.append(Paragraph("No transportation requirements specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 2d. Sleeping Room Requirements (Daily Breakdown)
        _add_section_header(story, "Sleeping Room Requirements (Daily Breakdown)", styles)
        room_reqs = sow_analysis.get("SleepingRoomRequirements", {}) if sow_analysis else {}
        if room_reqs:
            # Summary info
            # SOW analyzer outputs: total_room_nights_min, total_room_nights_max, special_requirements (array)
            total_room_nights_min = room_reqs.get("total_room_nights_min")
            total_room_nights_max = room_reqs.get("total_room_nights_max")
            special_reqs_list = room_reqs.get("special_requirements", [])
            
            # Format total room nights
            if total_room_nights_min and total_room_nights_max:
                total_room_nights = f"{total_room_nights_min} - {total_room_nights_max}"
            elif total_room_nights_min:
                total_room_nights = f"{total_room_nights_min}+"
            elif total_room_nights_max:
                total_room_nights = f"Up to {total_room_nights_max}"
            else:
                total_room_nights = None
            
            # Format special requirements
            special_reqs = ", ".join(special_reqs_list) if isinstance(special_reqs_list, list) and special_reqs_list else None
            
            summary_data = [
                ["Total Room Nights:", _format_value(total_room_nights)],
                ["Special Requirements:", _format_value(special_reqs)],
            ]
            _add_info_table(story, summary_data)
            
            # Daily breakdown - SOW analyzer outputs: daily_breakdown (array)
            daily_rooms = room_reqs.get("daily_breakdown", [])
            if daily_rooms:
                headers = ["Day", "Date", "Number of Rooms"]
                rows = []
                for day in daily_rooms:
                    if isinstance(day, dict):
                        # SOW analyzer outputs: day, date, number_of_rooms (or rooms)
                        rows.append([
                            _format_value(day.get("day") or day.get("Day")),
                            _format_value(day.get("date") or day.get("Date")),
                            _format_value(day.get("number_of_rooms") or day.get("NumberOfRooms") or day.get("rooms")),
                        ])
                if rows:
                    _add_data_table(story, headers, rows, [1.5*inch, 2*inch, 2.8*inch])
            else:
                # If total_room_nights exists but no daily breakdown, show summary
                if total_room_nights:
                    story.append(Paragraph(f"Total Room Nights: {total_room_nights}", styles['Normal']))
                else:
                    story.append(Paragraph("No daily breakdown available. Total room nights information not extracted from document.", styles['Normal']))
                story.append(Spacer(1, 0.3*inch))
        else:
            story.append(Paragraph("No sleeping room requirements specified in the document.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 3. Function Space Requirements
        _add_section_header(story, "Function Space Requirements", styles)
        function_space = sow_analysis.get("FunctionSpaceRequirements", {}) if sow_analysis else {}
        if function_space:
            room_types = function_space.get("room_types", []) or function_space.get("RoomTypesNeeded", [])
            capacity_reqs = function_space.get("capacity_requirements", []) or function_space.get("CapacityRequirements", [])
            setup_reqs = function_space.get("setup_requirements", []) or function_space.get("SetupRequirements", [])
            
            # Format room types
            room_types_str = ", ".join(room_types) if isinstance(room_types, list) and room_types else "N/A"
            
            # Format capacity requirements (array of dicts)
            capacity_str = "N/A"
            if capacity_reqs and isinstance(capacity_reqs, list):
                capacity_parts = []
                for cap in capacity_reqs:
                    if isinstance(cap, dict):
                        room_type = cap.get("room_type", "Unknown")
                        capacity = cap.get("capacity", "N/A")
                        capacity_parts.append(f"{room_type}: {capacity} people")
                if capacity_parts:
                    capacity_str = "; ".join(capacity_parts)
            
            # Format setup requirements (array of dicts)
            setup_str = "N/A"
            if setup_reqs and isinstance(setup_reqs, list):
                setup_parts = []
                for setup in setup_reqs:
                    if isinstance(setup, dict):
                        room_type = setup.get("room_type", "Unknown")
                        setup_type = setup.get("setup", "N/A")
                        setup_parts.append(f"{room_type}: {setup_type}")
                if setup_parts:
                    setup_str = "; ".join(setup_parts)
            
            summary_data = [
                ["Room Types Needed:", _format_value(room_types_str)],
                ["Capacity Requirements:", _format_value(capacity_str)],
                ["Setup Requirements:", _format_value(setup_str)],
            ]
            _add_info_table(story, summary_data)
            
            daily_function = function_space.get("daily_breakdown", []) or function_space.get("DailyBreakdown", [])
            if daily_function:
                headers = ["Day", "Date"]
                rows = []
                for day in daily_function:
                    if isinstance(day, dict):
                        rows.append([
                            _format_value(day.get("day") or day.get("Day")),
                            _format_value(day.get("date") or day.get("Date")),
                        ])
                if rows:
                    _add_data_table(story, headers, rows, [3*inch, 3.3*inch])
            else:
                # If function_space exists but empty, show message
                if not room_types and not capacity_reqs and not setup_reqs:
                    story.append(Paragraph("Function space requirements not extracted from document. This information may be in tables or attachments that require manual review.", styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
        else:
            story.append(Paragraph("No function space requirements specified in the document.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 4. AV Requirements
        _add_section_header(story, "AV Requirements", styles)
        av_reqs = sow_analysis.get("AVRequirements", {}) if sow_analysis else {}
        if av_reqs:
            # Extract room requirements (array of dicts)
            room_reqs = av_reqs.get("room_requirements", []) or av_reqs.get("RoomByRoomAVNeeds", [])
            room_av_str = "N/A"
            if room_reqs and isinstance(room_reqs, list):
                room_parts = []
                for req in room_reqs:
                    if isinstance(req, dict):
                        room_type = req.get("room_type", "Unknown")
                        equipment = req.get("equipment", [])
                        if equipment:
                            equip_parts = []
                            for eq in equipment:
                                if isinstance(eq, dict):
                                    eq_type = eq.get("type") or eq.get("name", "Unknown")
                                    qty = eq.get("quantity", 1)
                                    equip_parts.append(f"{eq_type} (x{qty})")
                            if equip_parts:
                                room_parts.append(f"{room_type}: {', '.join(equip_parts)}")
                if room_parts:
                    room_av_str = "; ".join(room_parts)
            
            # Extract special notes (array)
            special_notes = av_reqs.get("special_notes", []) or av_reqs.get("SpecialNotes", [])
            special_notes_str = "N/A"
            if special_notes and isinstance(special_notes, list):
                special_notes_str = "; ".join(str(note) for note in special_notes if note)
            
            # Extract hybrid meeting needs
            hybrid_needs = av_reqs.get("hybrid_meeting_needs", []) or av_reqs.get("HybridMeetingRequirements", [])
            hybrid_str = "N/A"
            if hybrid_needs and isinstance(hybrid_needs, list):
                hybrid_str = "; ".join(str(need) for need in hybrid_needs if need)
            
            # Extract court reporter needs
            court_reporter = av_reqs.get("court_reporter_needs", []) or av_reqs.get("CourtReporterAudioFeedRequirements", [])
            court_str = "N/A"
            if court_reporter and isinstance(court_reporter, list):
                court_str = "; ".join(str(need) for need in court_reporter if need)
            
            av_data = [
                ["Room-by-Room AV Needs:", _format_value(room_av_str)],
                ["Special Notes:", _format_value(special_notes_str)],
                ["Hybrid Meeting Requirements:", _format_value(hybrid_str)],
                ["Court Reporter Audio Feed:", _format_value(court_str)],
            ]
            _add_info_table(story, av_data)
            
            # If all AV fields are N/A, add note
            if room_av_str == "N/A" and special_notes_str == "N/A" and hybrid_str == "N/A" and court_str == "N/A":
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<i>AV requirements not extracted from document. This information may be in tables or attachments that require manual review.</i>", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        else:
            story.append(Paragraph("No AV requirements specified in the document.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 5. Food & Beverage Requirements
        _add_section_header(story, "Food & Beverage Requirements", styles)
        fb_reqs = sow_analysis.get("FoodAndBeverageRequirements", {}) if sow_analysis else {}
        if fb_reqs:
            daily_fb = fb_reqs.get("daily_breakdown", []) or fb_reqs.get("DailyBreakdown", [])
            if daily_fb:
                headers = ["Day", "Date", "Time", "Headcount", "Menu"]
                rows = []
                for day in daily_fb:
                    if isinstance(day, dict):
                        rows.append([
                            _format_value(day.get("day") or day.get("Day")),
                            _format_value(day.get("date") or day.get("Date")),
                            _format_value(day.get("time") or day.get("Time") or "N/A"),
                            _format_value(day.get("headcount") or day.get("Headcount") or "N/A"),
                            _format_value(day.get("menu") or day.get("Menu") or "N/A"),
                        ])
                if rows:
                    _add_data_table(story, headers, rows, [1*inch, 1.2*inch, 1*inch, 1*inch, 2*inch])
            else:
                story.append(Paragraph("No daily breakdown available.", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        else:
            story.append(Paragraph("No food & beverage requirements specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 6. Commercial Terms & Special Conditions
        _add_section_header(story, "Commercial Terms & Special Conditions", styles)
        commercial = sow_analysis.get("CommercialTerms", {}) if sow_analysis else {}
        if commercial:
            # SOW analyzer outputs: naics_code, psc_code, set_aside_type (snake_case)
            commercial_data = [
                ["NAICS Code:", _format_value(commercial.get("naics_code") or commercial.get("NAICSCode") or opp_data.get("naics_code"))],
                ["PSC Code:", _format_value(commercial.get("psc_code") or commercial.get("PSCCode"))],
                ["Set-Aside Type:", _format_value(commercial.get("set_aside_type") or commercial.get("SetAsideType"))],
                ["Size Standard:", _format_value(commercial.get("SizeStandard", "Not specified"))],
                ["ADA Compliance:", _format_value(commercial.get("ADAComplianceRequirements", "Not specified"))],
                ["Wi-Fi/Internet:", _format_value(commercial.get("WiFiInternetRequirements", "Not specified"))],
                ["Parking Requirements:", _format_value(commercial.get("ParkingRequirements", "Not specified"))],
                ["Cancellation Terms:", _format_value(commercial.get("CancellationTerms", "Not specified"))],
                ["AV Discount Required:", _format_value(commercial.get("AVDiscountRequirements", "Not specified"))],
                ["F&B Discount Required:", _format_value(commercial.get("FBDiscountRequirements", "Not specified"))],
            ]
            _add_info_table(story, commercial_data)
        else:
            # Show basic info from opportunity
            commercial_data = [
                ["NAICS Code:", _format_value(opp_data.get("naics_code", "N/A"))],
                ["PSC Code:", "Not specified"],
                ["Set-Aside Type:", "Not specified"],
            ]
            _add_info_table(story, commercial_data)
        
        # 7. Cost Proposal & Budget Submission Instructions
        _add_section_header(story, "Cost Proposal & Budget Submission Instructions", styles)
        cost_proposal = sow_analysis.get("CostProposalRequirements", {}) if sow_analysis else {}
        if cost_proposal:
            quote_due = cost_proposal.get("QuoteDueDate", "N/A")
            submission_method = cost_proposal.get("SubmissionMethod", "N/A")
            submission_email = cost_proposal.get("SubmissionEmail", "N/A")
            required_attachments = cost_proposal.get("RequiredAttachments", [])
            
            cost_data = [
                ["Quote Due Date:", _format_value(quote_due)],
                ["Submission Method:", _format_value(submission_method)],
                ["Submission Email:", _format_value(submission_email)],
                ["Required Attachments:", _format_value(", ".join(required_attachments) if isinstance(required_attachments, list) else required_attachments)],
            ]
            _add_info_table(story, cost_data)
        else:
            story.append(Paragraph("No cost proposal requirements specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 7b. Deliverables
        _add_section_header(story, "Deliverables", styles)
        deliverables = sow_analysis.get("Deliverables", []) if sow_analysis else []
        if deliverables and isinstance(deliverables, list) and len(deliverables) > 0:
            headers = ["Deliverable", "Due (Days Post Award)", "Recipient"]
            rows = []
            for deliv in deliverables:
                if isinstance(deliv, dict):
                    rows.append([
                        _format_value(deliv.get("name")),
                        _format_value(deliv.get("due_days_post_award")),
                        _format_value(deliv.get("recipient")),
                    ])
            if rows:
                _add_data_table(story, headers, rows, [3*inch, 1.5*inch, 1.8*inch])
        else:
            story.append(Paragraph("No deliverables specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 7c. Performance Metrics
        _add_section_header(story, "Performance Metrics", styles)
        perf_metrics = sow_analysis.get("PerformanceMetrics", []) if sow_analysis else []
        if perf_metrics and isinstance(perf_metrics, list) and len(perf_metrics) > 0:
            headers = ["Metric", "Target", "Time Limit"]
            rows = []
            for metric in perf_metrics:
                if isinstance(metric, dict):
                    rows.append([
                        _format_value(metric.get("metric")),
                        _format_value(metric.get("target")),
                        _format_value(metric.get("time_limit")),
                    ])
            if rows:
                _add_data_table(story, headers, rows, [2.5*inch, 1.5*inch, 2.3*inch])
        else:
            story.append(Paragraph("No performance metrics specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 7d. Period of Performance
        _add_section_header(story, "Period of Performance", styles)
        pop = sow_analysis.get("PeriodOfPerformance", {}) if sow_analysis else {}
        if pop:
            pop_data = [
                ["Start Date:", _format_value(pop.get("start_date"))],
                ["End Date:", _format_value(pop.get("end_date"))],
            ]
            _add_info_table(story, pop_data)
        else:
            story.append(Paragraph("No period of performance specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 7e. Submission Package
        _add_section_header(story, "Submission Package", styles)
        submission_pkg = sow_analysis.get("SubmissionPackage", {}) if sow_analysis else {}
        if submission_pkg:
            required_sections = submission_pkg.get("required_sections", [])
            submission_method = submission_pkg.get("submission_method")
            submission_emails = submission_pkg.get("submission_emails", [])
            due_datetime = submission_pkg.get("due_datetime_local")
            
            sub_data = [
                ["Submission Method:", _format_value(submission_method)],
                ["Due Date/Time:", _format_value(due_datetime)],
                ["Submission Emails:", _format_value(", ".join(submission_emails) if isinstance(submission_emails, list) else submission_emails)],
            ]
            _add_info_table(story, sub_data)
            
            if required_sections and isinstance(required_sections, list):
                story.append(Paragraph("<b>Required Sections:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for section in required_sections:
                    if isinstance(section, dict):
                        section_name = section.get("name", "")
                        max_pages = section.get("max_pages")
                        section_text = f"• {section_name}"
                        if max_pages:
                            section_text += f" (Max {max_pages} pages)"
                        story.append(Paragraph(section_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No submission package specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 7f. Invoicing Instructions
        _add_section_header(story, "Invoicing Instructions", styles)
        invoicing = sow_analysis.get("InvoicingInstructions", {}) if sow_analysis else {}
        if invoicing:
            invoice_structure = invoicing.get("allowed_invoice_structure", [])
            billing_basis = invoicing.get("billing_basis")
            tax_exempt = invoicing.get("tax_exempt_lodging")
            invoice_recipients = invoicing.get("invoice_recipients", [])
            
            invoice_data = [
                ["Allowed Invoice Structure:", _format_value(", ".join(invoice_structure) if isinstance(invoice_structure, list) else invoice_structure)],
                ["Billing Basis:", _format_value(billing_basis)],
                ["Tax Exempt Lodging:", _format_value("Yes" if tax_exempt else "No")],
                ["Invoice Recipients:", _format_value(", ".join(invoice_recipients) if isinstance(invoice_recipients, list) else invoice_recipients)],
            ]
            _add_info_table(story, invoice_data)
        else:
            story.append(Paragraph("No invoicing instructions specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 8. Evaluation and Award Criteria
        _add_section_header(story, "Evaluation and Award Criteria", styles)
        evaluation = sow_analysis.get("EvaluationCriteria", {}) if sow_analysis else {}
        if evaluation:
            # Legacy fields
            eval_data = [
                ["Payment Terms:", _format_value(evaluation.get("PaymentTerms", "N/A"))],
                ["Tax Exemption Status:", _format_value(evaluation.get("TaxExemptionStatus", "N/A"))],
                ["Billing Method:", _format_value(evaluation.get("BillingMethod", "N/A"))],
                ["Cancellation Policy:", _format_value(evaluation.get("CancellationPolicy", "N/A"))],
            ]
            _add_info_table(story, eval_data)
            
            # New structured evaluation factors
            factors = evaluation.get("factors", [])
            notes = evaluation.get("notes", [])
            
            if factors and isinstance(factors, list):
                story.append(Paragraph("<b>Evaluation Factors:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for factor in factors:
                    if isinstance(factor, dict):
                        factor_name = factor.get("name", "")
                        factor_weight = factor.get("weight", "")
                        factor_text = f"• {factor_name}: {factor_weight}"
                        story.append(Paragraph(factor_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            if notes and isinstance(notes, list):
                story.append(Paragraph("<b>Evaluation Notes:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for note in notes:
                    story.append(Paragraph(f"• {_format_value(note)}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No evaluation criteria specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 9. Compliance Requirements
        _add_section_header(story, "Compliance Requirements", styles)
        compliance = sow_analysis.get("ComplianceRequirements", {}) if sow_analysis else {}
        if compliance:
            far_clauses = compliance.get("FARClauses", [])
            if far_clauses:
                story.append(Paragraph("<b>FAR Clauses:</b>", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
                for clause in far_clauses:
                    if isinstance(clause, dict):
                        clause_text = f"• {_format_value(clause.get('ClauseNumber', ''))}: {_format_value(clause.get('Title', ''))}"
                        story.append(Paragraph(clause_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No compliance requirements specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # 10. Appendices
        _add_section_header(story, "Appendices", styles)
        appendices = sow_analysis.get("Appendices", {}) if sow_analysis else {}
        if appendices:
            additional_docs = appendices.get("AdditionalDocuments", "N/A")
            app_data = [
                ["Additional Documents:", _format_value(additional_docs)],
            ]
            _add_info_table(story, app_data)
        else:
            story.append(Paragraph("No appendices specified.", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Hotels (if available - check both analysis_result and opportunity-level hotel match results)
        hotels = analysis_result.get("hotels", [])
        if not hotels:
            # Try to get hotels from related hotel_match analysis
            # This will be populated by pipeline_service when generating PDF
            hotels = analysis_result.get("related_hotels", [])
        
        if hotels:
            story.append(PageBreak())
            _add_section_header(story, "Hotel Recommendations", styles)
            
            # Search criteria if available
            search_criteria = analysis_result.get("hotel_search_criteria", {})
            if search_criteria:
                criteria_data = [
                    ["City Code:", _format_value(search_criteria.get("city_code"))],
                    ["Check-In Date:", _format_value(search_criteria.get("check_in"))],
                    ["Check-Out Date:", _format_value(search_criteria.get("check_out"))],
                    ["Adults:", _format_value(search_criteria.get("adults"))],
                    ["Rooms:", _format_value(search_criteria.get("rooms", 1))],
                ]
                _add_info_table(story, criteria_data)
            
            # Hotel summary table
            headers = ["Hotel Name", "Score", "Price/Night", "Total Price", "Distance", "Rating"]
            rows = []
            for hotel in hotels[:20]:  # Show up to 20 hotels
                # Robust hotel name extraction with multiple fallbacks
                name = hotel.get("name") or hotel.get("hotel_name") or hotel.get("hotelName")
                # Try nested structures
                if not name or "Unknown" in str(name):
                    if isinstance(hotel.get("offer"), dict):
                        name = hotel.get("offer", {}).get("name") or hotel.get("offer", {}).get("hotel", {}).get("name")
                    if not name or "Unknown" in str(name):
                        if isinstance(hotel.get("hotel"), dict):
                            name = hotel.get("hotel", {}).get("name")
                # Final fallback
                if not name or "Unknown" in str(name):
                    name = "N/A"
                else:
                    name = str(name)
                
                score = hotel.get("score", 0)
                price_per_night = hotel.get("price_per_night", hotel.get("price", "N/A"))
                total_price = hotel.get("total_price", "N/A")
                currency = hotel.get("currency", "USD")
                distance = hotel.get("distance", "N/A")
                rating = hotel.get("rating", "N/A")
                
                # Format price
                if isinstance(price_per_night, (int, float)):
                    price_str = f"{currency} {price_per_night:,.2f}"
                else:
                    price_str = str(price_per_night)
                
                if isinstance(total_price, (int, float)):
                    total_str = f"{currency} {total_price:,.2f}"
                else:
                    total_str = str(total_price)
                
                # Format distance
                if isinstance(distance, (int, float)):
                    distance_str = f"{distance:.2f} km"
                else:
                    distance_str = str(distance)
                
                rows.append([
                    name[:40],  # Truncate long names
                    f"{score:.1f}" if isinstance(score, (int, float)) else str(score),
                    price_str,
                    total_str,
                    distance_str,
                    str(rating),
                ])
            
            if rows:
                _add_data_table(story, headers, rows, [2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1*inch, 0.8*inch])
            
            # Detailed hotel information for top 5 hotels
            story.append(Spacer(1, 0.2*inch))
            _add_section_header(story, "Top Hotel Recommendations - Detailed Information", styles)
            
            for idx, hotel in enumerate(hotels[:5], 1):  # Top 5 hotels
                # Robust hotel name extraction with multiple fallbacks
                hotel_name = hotel.get("name") or hotel.get("hotel_name") or hotel.get("hotelName")
                # Try nested structures
                if not hotel_name or "Unknown" in str(hotel_name):
                    if isinstance(hotel.get("offer"), dict):
                        hotel_name = hotel.get("offer", {}).get("name") or hotel.get("offer", {}).get("hotel", {}).get("name")
                    if not hotel_name or "Unknown" in str(hotel_name):
                        if isinstance(hotel.get("hotel"), dict):
                            hotel_name = hotel.get("hotel", {}).get("name")
                # Final fallback
                if not hotel_name or "Unknown" in str(hotel_name):
                    hotel_name = "N/A"
                else:
                    hotel_name = str(hotel_name)
                
                story.append(Paragraph(f"<b>{idx}. {hotel_name}</b>", styles['Heading3']))
                story.append(Spacer(1, 0.1*inch))
                
                hotel_details = [
                    ["Hotel ID:", _format_value(hotel.get("hotel_id"))],
                    ["Address:", _format_value(hotel.get("address"))],
                    ["City:", _format_value(hotel.get("city"))],
                    ["Score:", _format_value(hotel.get("score"))],
                    ["Price per Night:", _format_value(f"{hotel.get('currency', 'USD')} {hotel.get('price_per_night', hotel.get('price', 'N/A'))}")],
                    ["Total Price:", _format_value(f"{hotel.get('currency', 'USD')} {hotel.get('total_price', 'N/A')}")],
                    ["Distance:", _format_value(f"{hotel.get('distance', 'N/A')} km" if isinstance(hotel.get('distance'), (int, float)) else str(hotel.get('distance', 'N/A')))],
                    ["Rating:", _format_value(hotel.get("rating"))],
                    ["Amadeus Link:", _format_value(hotel.get("amadeus_link", "N/A"))],
                ]
                _add_info_table(story, hotel_details)
                story.append(Spacer(1, 0.2*inch))
        
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
        
        # Hotel Suggestions section removed - hotels will be in separate PDF attachment
        
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


def generate_hotel_match_pdf(
    output_path: Path,
    hotel_match_result: Dict[str, Any],
    opportunity: Dict[str, Any],
) -> bool:
    """
    Generate a detailed PDF report for hotel match results.
    
    Args:
        output_path: Path where PDF will be saved
        hotel_match_result: Hotel match result data (from result_json)
        opportunity: Opportunity metadata
        
    Returns:
        True if PDF was generated successfully, False otherwise
    """
    if not REPORTLAB_AVAILABLE:
        logger.error("reportlab not available, cannot generate PDF")
        return False
    
    try:
        from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame
        
        # Use BaseDocTemplate for custom footer
        doc = BaseDocTemplate(str(output_path), pagesize=letter, 
                             rightMargin=1*inch, leftMargin=1*inch,
                             topMargin=1*inch, bottomMargin=1*inch)
        
        def on_first_page(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor('#003366'))
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(4.25*inch, 0.5*inch, f"Page {page_num}")
            canvas.restoreState()
        
        def on_later_pages(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor('#003366'))
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(4.25*inch, 0.5*inch, f"Page {page_num}")
            canvas.restoreState()
        
        frame = Frame(doc.leftMargin, doc.bottomMargin, 
                     doc.width, doc.height, 
                     id='normal')
        template = PageTemplate(id='AllPages', frames=[frame], 
                               onPage=on_first_page,
                               onPageEnd=on_later_pages)
        doc.addPageTemplates([template])
        story = []
        styles = getSampleStyleSheet()
        
        # Header
        opp_data = {}
        if opportunity:
            opp_data.update(opportunity)
        analysis_opp = hotel_match_result.get("opportunity", {}) or {}
        opp_data.update(analysis_opp)
        
        header_data = [[
            Paragraph(f"<b>{_format_value(opp_data.get('title', 'Hotel Match Results'))}</b>", 
                     ParagraphStyle('HeaderLeft', parent=styles['Normal'], 
                                  fontSize=14, textColor=colors.HexColor('#003366'),
                                  fontName='Helvetica-Bold', alignment=TA_LEFT)),
            Paragraph(f"<b>{_format_value(opp_data.get('notice_id', 'N/A'))}</b>", 
                     ParagraphStyle('HeaderRight', parent=styles['Normal'], 
                                  fontSize=14, textColor=colors.HexColor('#003366'),
                                  fontName='Helvetica-Bold', alignment=TA_LEFT)),
        ]]
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
            textColor=colors.HexColor('#003366'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )
        title = Paragraph("Hotel Match Recommendations", title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Search Criteria
        options = hotel_match_result.get("options", {})
        if options:
            _add_section_header(story, "Hotel Search Criteria", styles)
            criteria_data = [
                ["City Code:", _format_value(options.get("city_code"))],
                ["Check-In Date:", _format_value(options.get("check_in"))],
                ["Check-Out Date:", _format_value(options.get("check_out"))],
                ["Adults:", _format_value(options.get("adults"))],
                ["Rooms:", _format_value(options.get("rooms", 1))],
            ]
            _add_info_table(story, criteria_data)
        
        # Hotel Recommendations
        hotels = hotel_match_result.get("hotels", [])
        if hotels:
            _add_section_header(story, f"Hotel Recommendations ({len(hotels)} found)", styles)
            
            headers = ["Hotel Name", "Score", "Price/Night", "Total Price", "Distance", "Rating"]
            rows = []
            for hotel in hotels:
                # Robust hotel name extraction with multiple fallbacks
                name = hotel.get("name") or hotel.get("hotel_name") or hotel.get("hotelName")
                # Try nested structures
                if not name or "Unknown" in str(name):
                    if isinstance(hotel.get("offer"), dict):
                        name = hotel.get("offer", {}).get("name") or hotel.get("offer", {}).get("hotel", {}).get("name")
                    if not name or "Unknown" in str(name):
                        if isinstance(hotel.get("hotel"), dict):
                            name = hotel.get("hotel", {}).get("name")
                # Final fallback
                if not name or "Unknown" in str(name):
                    name = "N/A"
                else:
                    name = str(name)
                
                score = hotel.get("score", 0)
                price_per_night = hotel.get("price_per_night", "N/A")
                total_price = hotel.get("total_price", "N/A")
                currency = hotel.get("currency", "USD")
                distance = hotel.get("distance", "N/A")
                rating = hotel.get("rating", "N/A")
                
                # Format price
                if isinstance(price_per_night, (int, float)):
                    price_str = f"{currency} {price_per_night:,.2f}"
                else:
                    price_str = str(price_per_night)
                
                if isinstance(total_price, (int, float)):
                    total_str = f"{currency} {total_price:,.2f}"
                else:
                    total_str = str(total_price)
                
                # Format distance
                if isinstance(distance, (int, float)):
                    distance_str = f"{distance:.2f} km"
                else:
                    distance_str = str(distance)
                
                rows.append([
                    name[:40],  # Truncate long names
                    f"{score:.1f}" if isinstance(score, (int, float)) else str(score),
                    price_str,
                    total_str,
                    distance_str,
                    str(rating),
                ])
            
            if rows:
                _add_data_table(story, headers, rows, [2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1*inch, 0.8*inch])
            
            # Detailed hotel information
            story.append(PageBreak())
            _add_section_header(story, "Detailed Hotel Information", styles)
            
            for idx, hotel in enumerate(hotels[:10], 1):  # Limit to first 10 hotels
                # Robust hotel name extraction with multiple fallbacks
                hotel_name = hotel.get("name") or hotel.get("hotel_name") or hotel.get("hotelName")
                # Try nested structures
                if not hotel_name or "Unknown" in str(hotel_name):
                    if isinstance(hotel.get("offer"), dict):
                        hotel_name = hotel.get("offer", {}).get("name") or hotel.get("offer", {}).get("hotel", {}).get("name")
                    if not hotel_name or "Unknown" in str(hotel_name):
                        if isinstance(hotel.get("hotel"), dict):
                            hotel_name = hotel.get("hotel", {}).get("name")
                # Final fallback
                if not hotel_name or "Unknown" in str(hotel_name):
                    hotel_name = "N/A"
                else:
                    hotel_name = str(hotel_name)
                
                story.append(Paragraph(f"<b>{idx}. {hotel_name}</b>", styles['Heading3']))
                story.append(Spacer(1, 0.1*inch))
                
                hotel_details = [
                    ["Hotel ID:", _format_value(hotel.get("hotel_id"))],
                    ["Address:", _format_value(hotel.get("address"))],
                    ["City:", _format_value(hotel.get("city"))],
                    ["Score:", _format_value(hotel.get("score"))],
                    ["Price per Night:", _format_value(f"{hotel.get('currency', 'USD')} {hotel.get('price_per_night', 'N/A')}")],
                    ["Total Price:", _format_value(f"{hotel.get('currency', 'USD')} {hotel.get('total_price', 'N/A')}")],
                    ["Distance:", _format_value(f"{hotel.get('distance', 'N/A')} km")],
                    ["Rating:", _format_value(hotel.get("rating"))],
                    ["Amadeus Link:", _format_value(hotel.get("amadeus_link", "N/A"))],
                ]
                _add_info_table(story, hotel_details)
                story.append(Spacer(1, 0.2*inch))
        else:
            _add_section_header(story, "No Hotels Found", styles)
            story.append(Paragraph("No hotel recommendations were found for the specified criteria.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Hotel match PDF generated successfully: {output_path}")
        return True
        
    except Exception as exc:
        logger.exception(f"Failed to generate hotel match PDF: {exc}")
        return False
