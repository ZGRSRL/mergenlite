"""
AutoGen-based SOW analyzer agent that extracts detailed requirements from SOW documents.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

# Import LLM logger for database logging
try:
    from ..services.llm_logger import log_llm_call
    from ..db import SessionLocal
    LLM_LOGGER_AVAILABLE = True
except ImportError:
    LLM_LOGGER_AVAILABLE = False
    logger.warning("LLM logger not available - LLM calls will not be logged to database")

# Try to import json_repair for robust JSON parsing
try:
    import json_repair
    JSON_REPAIR_AVAILABLE = True
    logger.info("json_repair available - will use for robust JSON parsing")
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    logger.warning("json_repair not available - falling back to standard json. Install with: pip install json_repair")

# Use autogen package (standard, supports llm_config)
try:
    from autogen import AssistantAgent, UserProxyAgent
    try:
        from autogen import tool
    except ImportError:
        tool = None  # tool decorator may not be available in all versions
    AUTOGEN_AVAILABLE = True
    AUTOGEN_NEW_API = False
except ImportError:
    # Fallback to autogen_agentchat only if autogen is not available
    try:
        from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
        tool = None  # tool decorator not available in new API
        AUTOGEN_AVAILABLE = True
        AUTOGEN_NEW_API = True
    except ImportError:
        AUTOGEN_AVAILABLE = False
        AUTOGEN_NEW_API = False

class SOWAnalyzerUnavailableError(RuntimeError):
    pass

def create_sow_analyzer_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Create an AutoGen agent for analyzing SOW documents."""
    if not AUTOGEN_AVAILABLE:
        raise SOWAnalyzerUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    # Get API key from parameter or environment
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    # NOTE:
    # We intentionally keep max_tokens well below 4k to avoid
    # "max_tokens too large" errors on models with 4k completion limits.
    # However, GPT-4o-mini supports up to 16k tokens, so we can use 4000 safely.
    if not api_key:
        logger.warning("OPENAI_API_KEY or AZURE_OPENAI_API_KEY not set. AutoGen may not work without API key.")
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4000,  # Increased from 3500 for better completeness
            "response_format": {"type": "json_object"},  # Force JSON output mode
        }
    else:
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                    "api_key": api_key,
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4000,  # Increased from 3500 for better completeness
            "response_format": {"type": "json_object"},  # Force JSON output mode - CRITICAL for production
        }

    system_message = """You are a SOW (Statement of Work) Analyzer Agent. Your task is to extract detailed, structured information from SOW documents and Combined Synopsis documents.

**CRITICAL INSTRUCTIONS:**
- Extract ALL information from BOTH SOW and Combined Synopsis documents if both are provided.
- Pay special attention to TABLES (LOCATIONS, DELIVERABLES, PERFORMANCE, etc.) - convert them to structured JSON arrays.
- If a table exists but cannot be extracted, set the top-level flag "table_extraction_failed": true.
- NEVER say "None specified" or "Not specified" if the information actually exists in the document - extract it!
- For lodging requirements, cancellation policies, amenities, and special terms - extract EVERY detail mentioned.

**ADDITIONAL MANDATORY RULES:**
- NEVER output "N/A" anywhere. Use null or empty arrays instead.
- NEVER output "Not specified" if information exists in the document.
- If a table exists visually (LOCATIONS, DELIVERABLES, PERFORMANCE), extract manually even if PDF extraction fails. Treat any aligned row/column structure as a table even without borders.
- ALWAYS correct malformed dates such as "226-06-12" → "2026-06-12". NEVER output malformed dates. If OCR extraction produces malformed dates, infer or correct from surrounding context.
- ALWAYS fill EventDetails.start_date and EventDetails.end_date using Period Of Performance if present. If period of performance is specified, EventDetails.start_date and EventDetails.end_date must be the same values.
- ALWAYS compute EventDetails.duration_days from the two dates (end_date - start_date).
- NEVER copy example JSON dates. Only use real dates from document. If due date appears malformed, search context to correct-year inference.
- ALWAYS extract NAICS, set-aside type, and size standard from Combined Synopsis if available. DO NOT output "Not specified" if the data exists.
- ONLY output fields defined in the output schema. Do NOT generate fields like "Payment Terms" or "Billing Method" that are not in the schema.
- Add a top-level field "data_quality_issues": [] and populate with human-readable issues (missing ZIPs, bad dates, missing stadium names, etc.). If Locations table has missing data (zip_codes missing, stadium missing, start_date missing), add warnings to this field.
- Extract all FAR/EDAR clauses mentioned anywhere in the document into ComplianceRequirements.far_clauses[].
- If ZIP codes are missing from Locations table but exist in SOW text, extract them from the text.

Extract ALL the following information from the provided documents:

1. **Event Details:**
   - Event name
   - Solicitation number
   - Agency
   - Dates (start, end, duration)
   - Locations / cities
   - Submission due date and time (with timezone if present)

2. **Lodging Requirements (CRITICAL - Extract ALL details):**
   - Minimum and maximum rooms per city/location
   - Maximum stay days per city/location
   - Cancellation policy details:
     * Free cancellation hours before check-in (e.g., 48 hours)
     * Force majeure (no penalty) provisions
     * Name change/guest change policies (allowed until check-in, etc.)
   - Uniform terms requirement (same price, conditions, amenities across all cities)
   - Required amenities (loyalty program benefits, complimentary parking, free Wi-Fi, etc.)
   - Any special room requirements or preferences

3. **Locations Table (CRITICAL - Extract ALL cities):**
   - If document contains a LOCATIONS table or similar, extract EVERY row:
     * City name
     * Stadium/venue name
     * ZIP codes (array)
     * Start date for that city
     * Number of days for that city
   - If table extraction fails, set "table_extraction_failed": true.
   - NEVER leave this empty if a locations table exists in the document.

4. **Transportation Requirements (CRITICAL):**
   - Maximum distance in miles from hotel to venue (e.g., 3 miles radius)
   - Required transportation options (list ALL mentioned):
     * Ridesharing (Uber/Lyft)
     * Shuttle services
     * Car rentals
     * Public transit
     * Dynamic on-demand systems
     * Walking or cycling
   - Transportation plan requirement (yes/no)
   - Transportation plan due date (days post award)

5. **Sleeping Room Requirements:**
   - Daily breakdown (day, date, number of rooms per night) if available
   - Total room nights (calculate min/max if locations table provides room ranges)
   - Any special room requirements

6. **Function Space Requirements (CRITICAL - Extract EXACT Layout Types):**
   - Daily breakdown (day, date)
   - Room types needed (Registration, General Session, Breakouts, Logistics, etc.)
   - **EXACT setup/layout types (CRITICAL):**
     * "Hollow Square" (interior space for tables in square formation)
     * "U-Shape" or "U-Form" (tables arranged in U shape)
     * "Boardroom" (large table with chairs around)
     * "Theater" or "Auditorium" (rows of chairs)
     * "Classroom" (tables with chairs facing front)
     * "Chevron" (V-shaped arrangement)
   - **IMPORTANT:** Different layouts require different room sizes. "Hollow Square" or "U-Shape" requires 2-3x more space than "Theater" for the same number of people.
   - Capacity requirements (exact number of people)
   - Setup requirements (table arrangements, spacing, etc.)
   - If separate attachments mention seating charts or layout diagrams, extract layout type from those files
   - **CRITICAL FOR COMPLEX TABLES:** If you see text marked as "[COMPLEX TABLE]" or "[TABLE ... - EXTRACTED AS TEXT]", this means the table structure was too complex to parse. In these cases:
     * Look for keywords: "Room", "Setup", "Attendees", "pp" (people), "capacity", "configuration"
     * Extract room names, capacities, and setup types even if they appear in paragraph form
     * Example: "Plenary Room - 60 pp - Hollow square configuration" should be extracted as: room_type="Plenary", capacity=60, setup="Hollow Square"
     * If you see phrases like "60 people" or "60 pp", extract the number as capacity
     * If you see "Hollow square", "U-Shape", "Boardroom", etc., extract as setup_requirements

7. **AV (Audio/Visual) Requirements (CRITICAL - Extract ALL Equipment Details):**
   - Room-by-room AV needs
   - Setup requirements (Hollow Square, Theater, Classroom, etc.)
   - Capacity for each room
   - **EXACT AV equipment needed (CRITICAL):**
     * "Table microphones" or "Table mics" (one per table/seat)
     * "Push-to-talk systems" or "PTT systems"
     * "Podium microphone" or "Lavaliere mic"
     * "Power strips" or "Power outlets" (count per person or per table)
     * "Audio feeds" for court reporters
     * "Video conferencing" or "OWLs" (Overhead Wide-angle Lens)
     * "Zoom management" or "Hybrid meeting support"
   - Special notes (power strips per person, audio feeds, etc.)
   - 24-hour hold requirements
   - Hybrid meeting requirements (OWLs, Zoom management, etc.)
   - Court reporter audio feed requirements
   - Breakout room power & setup needs
   - **IMPORTANT:** If CSV/Excel files or separate attachments list AV equipment, prioritize those quantities. Standard "projector available" is NOT sufficient - extract specific equipment needs.
   - **CRITICAL FOR COMPLEX TABLES:** If you see text marked as "[COMPLEX TABLE]" or plain text paragraphs:
     * Look for AV keywords: "microphone", "mic", "PTT", "push-to-talk", "power strip", "audio feed", "video", "screen", "projector"
     * Extract equipment names and quantities even if they appear in paragraph form
     * Example: "Table mics required for each table" should be extracted as AV equipment requirement
     * If quantities are mentioned (e.g., "3 microphones", "power strip per person"), extract them

8. **Food & Beverage Requirements (CRITICAL - Extract Detailed Breakdown):**
   - Daily breakdown (day, date, time, headcount, menu) if present
   - **EXACT meal types and quantities:**
     * "Continental Breakfast" (with headcount)
     * "AM Break" or "Morning Break" (coffee, snacks, headcount)
     * "PM Break" or "Afternoon Break" (coffee, snacks, headcount)
     * "Lunch" (type: buffet, plated, box lunch - with headcount)
     * "Dinner" (if applicable)
     * "Appetizers" (if applicable)
     * "Beverages" (coffee, tea, soft drinks - quantities)
   - **IMPORTANT:** F&B costs can be 30-40% of total budget. Extract exact quantities and meal types from CSV/Excel files if provided.
   - If separate cost estimate files (CSV/Excel) are provided, extract F&B breakdown from those files
   - **CRITICAL FOR COMPLEX TABLES:** If you see text marked as "[COMPLEX TABLE]" or plain text paragraphs:
     * Look for F&B keywords: "Breakfast", "Lunch", "Dinner", "Break", "Coffee", "Beverage", "Reception", "Appetizer"
     * Extract meal types, times, and headcounts even if they appear in paragraph form
     * Example: "Working Lunch for 60 people at 12:00 PM" should be extracted as: meal_type="Lunch", headcount=60, time="12:00 PM"
     * If quantities are mentioned (e.g., "60 people", "for 60 attendees"), extract them as headcount
   - **CRITICAL FOR COMPLEX TABLES:** If you see text marked as "[COMPLEX TABLE]" or plain text paragraphs:
     * Look for F&B keywords: "Breakfast", "Lunch", "Dinner", "Break", "Coffee", "Beverage", "Reception", "Appetizer"
     * Extract meal types, times, and headcounts even if they appear in paragraph form
     * Example: "Working Lunch for 60 people at 12:00 PM" should be extracted as: meal_type="Lunch", headcount=60, time="12:00 PM"
     * If quantities are mentioned (e.g., "60 people", "for 60 attendees"), extract them as headcount

9. **Deliverables (CRITICAL - Extract ALL):**
   - For each deliverable mentioned:
     * Name (e.g., "Hotel List and Loyalty Program Details")
     * Due date (days post award or specific date)
     * Recipient (e.g., "COR")
   - Common deliverables: Hotel list, booking confirmations, transportation plan, etc.

10. **Performance Metrics (CRITICAL - Extract ALL KPIs):**
    - For each performance metric:
      * Metric name (e.g., "room_blocks_secured", "cancellation_processing")
      * Target (e.g., "100%")
      * Time limit or deadline
    - Extract ALL performance requirements mentioned.

11. **Period of Performance (CRITICAL):**
    - Start date (ISO format: YYYY-MM-DD)
    - End date (ISO format: YYYY-MM-DD)
    - Extract exact dates from the document.

12. **Invoicing Instructions (CRITICAL):**
    - Allowed invoice structures (e.g., "single_consolidated_invoice", "one_invoice_per_city")
    - Billing basis (e.g., "only_confirmed_and_not_cancelled_bookings")
    - Tax exemption status (lodging tax exempt: true/false)
    - Invoice recipient email addresses (list ALL)

13. **Submission Package (CRITICAL - Extract from Combined Synopsis):**
    - Required sections with page limits:
      * Cover page (max pages)
      * Technical Approach (max pages, per city or total)
      * Past Performance (max pages)
      * Pricing Schedule (attachment name/number)
    - Submission method (email, portal, etc.)
    - Submission email addresses (list ALL)
    - Due date and time (with timezone if specified)

14. **Evaluation Criteria (CRITICAL - Extract from Combined Synopsis):**
    - Evaluation factors with relative importance/weights:
      * Technical Approach (weight: highest/medium/lowest)
      * Past Performance (weight: highest/medium/lowest)
      * Price (weight: highest/medium/lowest)
    - Notes about evaluation (e.g., "Technical Approach is more important than Past Performance")
    - Specific criteria within each factor (e.g., 3 mile radius, transportation accessibility, 48-hour cancellation flexibility)

15. **Commercial Terms:**
    - NAICS Code
    - PSC Code
    - Set-Aside type
    - Size standard
    - ADA compliance requirements
    - Wi-Fi/Internet requirements
    - Parking requirements
    - Cancellation terms
    - AV discount requirements
    - F&B discount requirements

16. **Cost Proposal & Budget:**
    - Quote due date and time
    - Submission method
    - Submission email
    - Required attachments (e.g., pricing schedule)

17. **Compliance Requirements:**
    - FAR clauses (list all clause numbers and titles)
    - EDAR or agency-specific clauses (list all clause numbers and titles)

18. **Appendices:**
    - Any additional documents or requirements referenced.

**OUTPUT FORMAT:**
Respond with a comprehensive JSON structure containing ALL extracted information. Use this structure (field names are important; fill with null or empty arrays if the document does not specify):

{
  "table_extraction_failed": false,
  "data_quality_issues": [],
  "EventDetails": {
    "event_name": null,
    "solicitation_number": null,
    "agency": null,
    "start_date": null,
    "end_date": null,
    "duration_days": null,
    "locations": [],
    "submission_due": null
  },
  "LodgingRequirements": {
    "rooms_per_city_min": null,
    "rooms_per_city_max": null,
    "max_stay_days_per_city": null,
    "cancellation_policy": {
      "free_cancellation_hours_before_checkin": null,
      "force_majeure_no_penalty": null,
      "name_change_allowed_until_checkin": null
    },
    "uniform_terms_required": null,
    "amenities_required": []
  },
  "Locations": [
    {
      "city": null,
      "stadium": null,
      "zip_codes": [],
      "start_date": null,
      "num_days": null
    }
  ],
  "TransportationRequirements": {
    "max_distance_miles_hotel_to_venue": null,
    "required_transportation_options": [],
    "transportation_plan_required": null,
    "transportation_plan_due_days_post_award": null
  },
  "SleepingRoomRequirements": {
    "daily_breakdown": [],
    "total_room_nights_min": null,
    "total_room_nights_max": null,
    "special_requirements": []
  },
  "FunctionSpaceRequirements": {
    "daily_breakdown": [],
    "room_types": [],
    "capacity_requirements": [],
    "setup_requirements": []
  },
  "AVRequirements": {
    "room_requirements": [],
    "special_notes": [],
    "hybrid_meeting_needs": [],
    "court_reporter_needs": []
  },
  "FoodAndBeverageRequirements": {
    "daily_breakdown": []
  },
  "Deliverables": [
    {
      "name": null,
      "due_days_post_award": null,
      "due_date": null,
      "recipient": null
    }
  ],
  "PerformanceMetrics": [
    {
      "metric": null,
      "target": null,
      "time_limit": null
    }
  ],
  "PeriodOfPerformance": {
    "start_date": null,
    "end_date": null
  },
  "InvoicingInstructions": {
    "allowed_invoice_structure": [],
    "billing_basis": null,
    "tax_exempt_lodging": null,
    "invoice_recipients": []
  },
  "SubmissionPackage": {
    "required_sections": [
      {"name": "cover_page", "max_pages": null},
      {"name": "technical_approach", "max_pages": null},
      {"name": "past_performance", "max_pages": null},
      {"name": "pricing_schedule_attachment", "attachment_name": null}
    ],
    "submission_method": null,
    "submission_emails": [],
    "due_datetime_local": "YYYY-MM-DDTHH:MM:SS±HH:MM"
  },
  "EvaluationCriteria": {
    "factors": [
      {"name": "technical_approach", "weight": null},
      {"name": "past_performance", "weight": null},
      {"name": "price", "weight": null}
    ],
    "notes": [],
    "detailed_criteria": []
  },
  "CommercialTerms": {
    "naics_code": null,
    "psc_code": null,
    "set_aside_type": null,
    "size_standard": null,
    "ada_compliance": null,
    "wifi_requirements": null,
    "parking_requirements": null,
    "cancellation_terms": null,
    "av_discount_requirements": null,
    "fb_discount_requirements": null
  },
  "CostProposal": {
    "quote_due_datetime_local": null,
    "submission_method": null,
    "submission_email": null,
    "required_attachments": []
  },
  "ComplianceRequirements": {
    "far_clauses": [],
    "other_clauses": []
  },
  "Appendices": [],
  "data_quality_issues": []
}

Be thorough and extract every detail mentioned in the document. If information is missing, use null or empty arrays, but NEVER say "None specified" if the information actually exists."""

    # Use appropriate API based on what's available
    if AUTOGEN_NEW_API:
        # New API requires model_client
        try:
            from autogen_agentchat.models import OpenAIChatCompletionClient
            model_client = OpenAIChatCompletionClient(
                model=llm_model,
                api_key=api_key,
            )
            assistant = AssistantAgent(
                name="SOWAnalyzerAgent",
                system_message=system_message,
                model_client=model_client,
            )
        except ImportError:
            raise SOWAnalyzerUnavailableError(
                "autogen_agentchat.models module not found. "
                "Please install the correct AutoGen version or use the old API."
            )
    else:
        # Old API uses llm_config
        try:
            assistant = AssistantAgent(
                name="SOWAnalyzerAgent",
                system_message=system_message,
                llm_config=llm_config,
                tools=[],
            )
        except TypeError:
            assistant = AssistantAgent(
                name="SOWAnalyzerAgent",
                system_message=system_message,
                llm_config=llm_config,
            )
    return assistant

def analyze_sow_document(
    document_text: str,
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    agent_run_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Analyze a SOW document using AutoGen agent to extract detailed requirements.
    
    Args:
        document_text: Full text content of the SOW document (and Combined Synopsis if available).
        llm_model: LLM model to use for analysis.
        api_key: OpenAI API key (if None, uses environment variable).
        
    Returns:
        Dict containing extracted SOW requirements.
    """
    if not AUTOGEN_AVAILABLE:
        raise SOWAnalyzerUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")

    assistant = create_sow_analyzer_agent(llm_model=llm_model, api_key=api_key)
    try:
        user = UserProxyAgent(
            name="SOWAnalysisUser",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
        )
    except TypeError:
        user = UserProxyAgent(name="SOWAnalysisUser")
    
    # Truncate document text if too long (to fit within token limits).
    # GPT-4o-mini has 128k context, so we can send more text
    # Increase to 120000 chars to ensure full document analysis including all tables
    max_doc_length = 120000
    if len(document_text) > max_doc_length:
        logger.warning(
            f"Document text is very long ({len(document_text)} chars), truncating to {max_doc_length} chars for analysis"
        )
        document_text = document_text[:max_doc_length] + "\n\n[... document truncated for analysis ...]"
    
    user_message = f"""Please analyze the following SOW document, RFQ (Request for Quotations), Combined Synopsis, and ALL other provided documents. Extract EVERY piece of information in detail.

**IMPORTANT:** The documents may include:
- SOW (Statement of Work) with detailed requirements
- RFQ (Request for Quotations) with submission instructions, evaluation criteria, pricing requirements
- Combined Synopsis with solicitation details, evaluation factors, submission package requirements
- Pricing schedules, attachments, amendments, clarifications

You MUST extract information from ALL of these document types, not just the SOW.

Document Text:
{document_text}

**CRITICAL EXTRACTION REQUIREMENTS:**

**IMPORTANT:** If multiple documents are provided (SOW, RFQ, Clarifications, CSV/Excel files, Seating Charts), extract information from ALL of them. Later documents (like Clarifications) may override earlier information (e.g., date changes, room count increases). Always prioritize the most recent information when conflicts exist.

1. LODGING REQUIREMENTS: Extract ALL details about room counts per city (min/max), cancellation policies (48-hour free cancellation, force majeure, name changes), uniform terms requirement, and required amenities (loyalty benefits, parking, Wi-Fi).

2. LOCATIONS TABLE (HIGHEST PRIORITY): The document contains a LOCATIONS table with multiple cities. You MUST extract EVERY row from this table into the Locations array. Look for:
   - Table headers like "LOCATIONS", "Location", "City", "Stadium", "ZIP Codes", "Start Dates", "# of Days"
   - Rows containing city names (e.g., "Philadelphia, PA", "Atlanta, GA"), stadium names, ZIP codes, start dates, and number of days
   - The table may appear as pipe-separated text (|) or in [TABLE X] format
   - Extract ALL cities mentioned - there should be 11 cities total
   - Each location entry must have: city, stadium, zip_codes (array), start_date (YYYY-MM-DD format), num_days
   - If you see "Philadelphia, PA" with "Lincoln Financial Field", "19148, 19130", "11 JUN 2026", "44" - this is ONE location entry
   - Convert dates from "11 JUN 2026" format to "2026-06-11" ISO format
   - If table extraction fails, set "table_extraction_failed": true.

3. TRANSPORTATION REQUIREMENTS: Extract maximum distance (e.g., 3 miles), ALL transportation options mentioned (ridesharing, shuttle, car rental, public transit, dynamic, walking/cycling), and transportation plan requirements.

4. DELIVERABLES: Extract ALL deliverables with names, due dates (days post award), and recipients.

5. PERFORMANCE METRICS: Extract ALL KPIs with targets (e.g., "100% room blocks secured within 10 days") and time limits.

6. PERIOD OF PERFORMANCE: Extract exact start and end dates in ISO format (YYYY-MM-DD).

7. INVOICING INSTRUCTIONS: Extract invoice structures, billing basis ("only confirmed bookings not cancelled"), tax exemption, and ALL invoice recipient emails.

8. SUBMISSION PACKAGE: Extract required sections with page limits, submission method, ALL submission emails, and due date/time.

9. EVALUATION CRITERIA: Extract evaluation factors with weights (Technical Approach > Past Performance > Price) and specific criteria notes. This information is often in RFQ/Combined Synopsis documents, NOT in the SOW itself.

10. RFQ/COMBINED SYNOPSIS DATA (CRITICAL - Often in separate documents):
   - Submission instructions (method, emails, due dates/times with timezone)
   - Evaluation criteria and factor weights
   - Required submission package sections with page limits
   - Pricing proposal requirements and formats
   - Quote due dates and submission methods
   - All email addresses mentioned (submission, invoicing, contact)
   - Commercial terms (NAICS, PSC, set-aside, size standard) - often in Combined Synopsis
   - FAR/EDAR clauses and compliance requirements

11. **CSV/EXCEL FILE DATA (CRITICAL - Prioritize Structured Data):**
   - If CSV or Excel files are provided (e.g., "Cost Estimate", "AV Template", "Meeting Schedule"), extract ALL data from them
   - CSV/Excel files often contain the most accurate and detailed information (quantities, dates, costs)
   - Extract AV equipment lists, F&B breakdowns, room setup requirements from these files
   - If CSV/Excel data conflicts with PDF text, prioritize CSV/Excel data as it's usually more accurate
   - Note in data_quality_issues if CSV/Excel files were referenced but not fully processed

12. **DETAILED LAYOUT & F&B (CRITICAL - From Excel/CSV Tables):**
   - Check extracted EXCEL/CSV tables for specific quantities and details
   - Look for meal types: "Continental Breakfast", "Working Lunch", "AM Break", "PM Break", "Box Lunch" (with exact headcounts)
   - Look for layout types: "Hollow Square", "U-Shape", "U-Form", "Boardroom", "Chevron"
   - Look for AV equipment: "Table Mics", "Table microphones", "Push-to-talk", "PTT systems", "Power strips" (with quantities)
   - If found in Excel/CSV files, list these under:
     * FunctionSpaceRequirements.setup_requirements (for layout types)
     * AVRequirements.room_requirements (for AV equipment with quantities)
     * FoodAndBeverageRequirements.daily_breakdown (for meal types with headcounts)
   - **IMPORTANT:** Excel/CSV files contain the most accurate quantities - use these numbers, not estimates from PDF text

**CRITICAL:** If you see "RFQ", "Request for Quotations", "Combined Synopsis", "Solicitation", or similar document types, extract ALL information from them. These documents contain critical submission requirements, evaluation criteria, and commercial terms that are NOT in the SOW itself.

Respond with a comprehensive JSON structure containing ALL extracted information from ALL document types. Use the exact field names from the system prompt (EventDetails, LodgingRequirements, Locations, TransportationRequirements, SleepingRoomRequirements, FunctionSpaceRequirements, AVRequirements, FoodAndBeverageRequirements, Deliverables, PerformanceMetrics, PeriodOfPerformance, InvoicingInstructions, SubmissionPackage, EvaluationCriteria, CommercialTerms, CostProposal, ComplianceRequirements, Appendices, table_extraction_failed, data_quality_issues).

**IMPORTANT REMINDERS:**
- NEVER output "N/A" or "Not specified" strings. Use null or empty arrays.
- NEVER copy example dates from JSON schema. Only use real dates from document.
- ONLY output fields defined in the schema. Do NOT invent new fields.
- Correct all OCR errors in dates (e.g., "226-06-12" → "2026-06-12").
- EventDetails.start_date and EventDetails.end_date MUST match PeriodOfPerformance dates.
- Calculate EventDetails.duration_days = (end_date - start_date) in days.
- Extract ALL FAR/EDAR clauses into ComplianceRequirements.far_clauses[].
- If Locations table has missing data, add warnings to data_quality_issues array.

Respond ONLY with valid JSON. Do not include any explanatory text outside the JSON structure."""

    # Retry mechanism for robust JSON parsing
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Track start time for latency
            start_time = time.time()
            
            user.initiate_chat(assistant, message=user_message)
            last_message = assistant.last_message()
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log LLM call to database if agent_run_id is provided
            if LLM_LOGGER_AVAILABLE and agent_run_id:
                try:
                    db = SessionLocal()
                    try:
                        # Extract prompt (first 50000 chars)
                        prompt_text = user_message[:50000] if len(user_message) > 50000 else user_message
                        
                        # Extract response
                        content = last_message.get("content", "") if last_message else ""
                        if isinstance(content, list):
                            content = content[0].get("text", "") if content else ""
                        response_text = str(content)[:100000] if content else ""  # Limit response size
                        
                        # Try to extract token usage from message metadata if available
                        prompt_tokens = None
                        completion_tokens = None
                        total_tokens = None
                        if last_message and isinstance(last_message, dict):
                            # Check for token usage in metadata
                            metadata = last_message.get("metadata", {})
                            if isinstance(metadata, dict):
                                usage = metadata.get("usage", {})
                                if isinstance(usage, dict):
                                    prompt_tokens = usage.get("prompt_tokens")
                                    completion_tokens = usage.get("completion_tokens")
                                    total_tokens = usage.get("total_tokens")
                        
                        # Log the LLM call
                        log_llm_call(
                            db=db,
                            provider="openai",
                            model=llm_model,
                            prompt=prompt_text,
                            response_text=response_text,
                            agent_run_id=agent_run_id,
                            agent_name="SOWAnalyzerAgent",
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            latency_ms=latency_ms,
                        )
                        logger.info(f"Logged LLM call to database for agent_run_id={agent_run_id}")
                    finally:
                        db.close()
                except Exception as log_exc:
                    logger.warning(f"Failed to log LLM call to database: {log_exc}", exc_info=True)
            
            if not last_message:
                raise RuntimeError("SOW analyzer produced no output.")
            
            content = last_message.get("content", "")
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
            if isinstance(content, dict):
                # If content is already a dict, validate and return
                return _validate_and_fix_sow_output(content)
            
            # Strip markdown fences if present
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Try to isolate JSON object
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                content = content[json_start:json_end]
            
            # Use json_repair if available, fallback to standard json
            if JSON_REPAIR_AVAILABLE:
                try:
                    decoded_json = json_repair.loads(content)
                except Exception as repair_error:
                    logger.warning(f"json_repair failed, trying standard json: {repair_error}")
                    decoded_json = json.loads(content)
            else:
                decoded_json = json.loads(content)
            
            # Validate and fix output
            validated_json = _validate_and_fix_sow_output(decoded_json)
            return validated_json
            
        except (json.JSONDecodeError, ValueError) as e:
            retry_count += 1
            if retry_count <= max_retries:
                logger.warning(f"JSON parse error (attempt {retry_count}/{max_retries}): {e}")
                logger.warning(f"Raw content preview: {content[:500] if 'content' in locals() else 'N/A'}")
                # Retry with error message to LLM
                error_message = f"The previous JSON output had a parsing error: {str(e)}. Please fix the JSON and respond with valid JSON only."
                user_message = f"{user_message}\n\n**ERROR FROM PREVIOUS ATTEMPT:**\n{error_message}\n\nPlease correct the JSON and respond again."
            else:
                logger.error(f"Failed to parse SOW analyzer JSON output after {max_retries} retries: {e}")
                logger.error(f"Raw content: {content[:1000] if 'content' in locals() else 'N/A'}")
                return {
                    "error": "Failed to parse LLM response as JSON after retries",
                    "raw_content_preview": content[:1000] if 'content' in locals() else "",
                    "extraction_error": str(e),
                    "table_extraction_failed": True,
                }
        except Exception as exc:
            logger.error(f"Error in SOW analysis: {exc}", exc_info=True)
            # Return error structure instead of raising to prevent pipeline crash
            return {
                "error": str(exc),
                "table_extraction_failed": True,
            }
    
    # Should not reach here, but safety fallback
    return {
        "error": "SOW analysis failed after retries",
        "table_extraction_failed": True,
    }


def _validate_and_fix_sow_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and fix common issues in SOW analysis output.
    - Fix date formats to YYYY-MM-DD
    - Remove "N/A" strings, replace with null
    - Ensure required fields exist
    """
    if not isinstance(data, dict):
        return data
    
    # Fix date formats in PeriodOfPerformance
    if "PeriodOfPerformance" in data and isinstance(data["PeriodOfPerformance"], dict):
        pop = data["PeriodOfPerformance"]
        for date_key in ["start_date", "end_date"]:
            if date_key in pop and pop[date_key]:
                date_str = str(pop[date_key])
                # Try to fix common date format issues
                fixed_date = _normalize_date_format(date_str)
                if fixed_date:
                    pop[date_key] = fixed_date
    
    # Fix EventDetails dates (should match PeriodOfPerformance)
    if "EventDetails" in data and isinstance(data["EventDetails"], dict):
        ed = data["EventDetails"]
        for date_key in ["start_date", "end_date"]:
            if date_key in ed and ed[date_key]:
                date_str = str(ed[date_key])
                fixed_date = _normalize_date_format(date_str)
                if fixed_date:
                    ed[date_key] = fixed_date
        
        # Calculate duration_days if both dates exist
        if ed.get("start_date") and ed.get("end_date"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(ed["start_date"].replace('Z', '+00:00').split('T')[0])
                end = datetime.fromisoformat(ed["end_date"].replace('Z', '+00:00').split('T')[0])
                duration = (end - start).days
                if duration >= 0:
                    ed["duration_days"] = duration
            except Exception:
                pass  # If calculation fails, leave duration_days as is
    
    # Fix Locations dates
    if "Locations" in data and isinstance(data["Locations"], list):
        for loc in data["Locations"]:
            if isinstance(loc, dict) and "start_date" in loc and loc["start_date"]:
                fixed_date = _normalize_date_format(str(loc["start_date"]))
                if fixed_date:
                    loc["start_date"] = fixed_date
    
    # Remove "N/A" and "Not specified" strings, replace with null
    def clean_value(value):
        if isinstance(value, str):
            if value.upper() in ["N/A", "NOT SPECIFIED", "NONE", "NONE SPECIFIED"]:
                return None
        elif isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_value(item) for item in value]
        return value
    
    cleaned_data = clean_value(data)
    
    return cleaned_data


def _normalize_date_format(date_str: str) -> Optional[str]:
    """
    Normalize date string to YYYY-MM-DD format.
    Handles OCR errors like "226-06-12" → "2026-06-12"
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Remove timezone and time parts if present
    date_str = date_str.split('T')[0].split(' ')[0].strip()
    
    # Fix common OCR errors: "226-06-12" → "2026-06-12"
    # Pattern: 2-digit year at start (likely OCR error for 4-digit year)
    ocr_fix_pattern = r'^(\d{1,2})-(\d{2})-(\d{2})$'
    match = re.match(ocr_fix_pattern, date_str)
    if match:
        year_part, month, day = match.groups()
        # If year is 1-2 digits, assume it's missing leading digits
        if len(year_part) <= 2:
            # Try to infer: if year < 50, assume 20XX, else 19XX
            year_int = int(year_part)
            if year_int < 50:
                year_part = f"20{year_part:02d}"
            else:
                year_part = f"19{year_part:02d}"
            date_str = f"{year_part}-{month}-{day}"
    
    # Validate YYYY-MM-DD format
    iso_date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(iso_date_pattern, date_str):
        try:
            # Validate it's a real date
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass
    
    return None
