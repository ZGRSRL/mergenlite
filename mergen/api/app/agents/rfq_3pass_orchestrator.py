"""
3-Pass AutoGen RFQ Analyzer Orchestrator
Enterprise Pipeline v3 implementation

Pass 1: AnalyzerAgent - RFQ → Raw structured JSON
Pass 2: ReviewerAgent - Error correction + normalization
Pass 3: SOWGeneratorAgent - (Fallback) SOW generation
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Import agents
from .sow_analyzer_agent import analyze_sow_document  # Pass 1
from .reviewer_agent import run_reviewer_agent  # Pass 2
from .sow_generator_agent import run_sow_generator_agent  # Pass 3
from ..models.sow_data_model import SOWDataModel
from ..services.parsing.seating_chart_parser import parse_seating_chart_pdf
from ..services.parsing.document_analyzer import analyze_document
from ..services.sow_template_engine import render_sow_from_model
try:
    from ..services.sow_pdf_generator_weasyprint import html_to_pdf, generate_pdf_from_markdown
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not available, will use ReportLab fallback for PDF generation")

try:
    try:
        from autogen import AssistantAgent, UserProxyAgent
        AUTOGEN_AVAILABLE = True
    except ImportError:
        from pyautogen import AssistantAgent, UserProxyAgent
        AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


class RFQ3PassOrchestratorUnavailableError(RuntimeError):
    pass


# SOWDataModel - Normalized Full Schema
SOW_DATA_MODEL_SCHEMA = {
    "event_name": str,
    "agency": str,
    "solicitation_number": str,
    "dates": {
        "start": str,
        "end": str
    },
    "location": str,
    "sleeping_rooms": List[Dict],
    "function_space_calendar": List[Dict],
    "meeting_rooms": List[Dict],
    "av_requirements": List[Dict],
    "f_and_b": List[Dict],
    "commercial_terms": Dict,
    "compliance_clauses": Dict,
    # Enhanced fields
    "outreach_event": Optional[bool],
    "hybrid_meeting": Optional[Dict],
    "breakout_power": Optional[Dict],
    "av_day_requirements": List[Dict],
    "seating_layout": Optional[Dict],
    "special_requirements": Optional[Dict],
    "twenty_four_hour_hold": Optional[bool],
    "court_reporter_audio": Optional[Dict],
}


def create_analyzer_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Pass 1: AnalyzerAgent - RFQ → Raw structured JSON"""
    if not AUTOGEN_AVAILABLE:
        raise RFQ3PassOrchestratorUnavailableError("pyautogen not installed")
    
    system_message = """You are a Structured Requirements Analyzer Agent (Pass 1).

Your task: Extract ALL requirements from RFQ PDF content and output normalized JSON.

CRITICAL RULES:
1. Extract ALL Function Space data (Breakouts, General Session, Staff Office)
2. Extract hours, setup types, capacities
3. Extract AV requirements day-by-day
4. Extract F&B headcount + menu
5. Extract special requirements (WiFi, AV discount, hold requirements)
6. DO NOT make up any data - use "TBD" for missing fields
7. Extract compliance clauses element-by-element

Output format must match SOWDataModel schema exactly."""
    
    llm_config = {
        "config_list": [{
            "model": llm_model,
            "api_key": api_key,
        }],
        "temperature": 0.1,
    }
    
    return AssistantAgent(
        name="AnalyzerAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )


def create_reviewer_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Pass 2: ReviewerAgent - Error correction + normalization"""
    if not AUTOGEN_AVAILABLE:
        raise RFQ3PassOrchestratorUnavailableError("pyautogen not installed")
    
    system_message = """You are a Requirements Reviewer Agent (Pass 2).

Your task: Review and correct the raw analyzer JSON output.

CORRECT:
- Contradictory information
- Missing values (fill or mark as "TBD")
- Date format normalization
- Room number totals
- Table OCR errors
- Merge duplicate lists
- Ensure 100% schema compliance

Output: Clean normalized JSON that strictly follows SOWDataModel schema."""
    
    llm_config = {
        "config_list": [{
            "model": llm_model,
            "api_key": api_key,
        }],
        "temperature": 0.1,
    }
    
    return AssistantAgent(
        name="ReviewerAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )


def create_sow_generator_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Pass 3: SOWGeneratorAgent - (Fallback) SOW generation"""
    if not AUTOGEN_AVAILABLE:
        raise RFQ3PassOrchestratorUnavailableError("pyautogen not installed")
    
    system_message = """You are a SOW Generator Agent (Pass 3 - Fallback).

Your task: Generate SOW Markdown from normalized event specification.

IMPORTANT:
- Use the normalized event specification
- Follow federal format
- Do NOT hallucinate
- Include: event summary, sleeping rooms table, function space tables, F&B tables, AV requirements, commercial terms, compliance clauses

Output: Professional SOW in Markdown format."""
    
    llm_config = {
        "config_list": [{
            "model": llm_model,
            "api_key": api_key,
        }],
        "temperature": 0.3,
    }
    
    return AssistantAgent(
        name="SOWGeneratorAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )


def run_3pass_rfq_analysis(
    document_text: str,
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Run 3-pass RFQ analysis pipeline.
    
    Returns:
        {
            "pass1_output": {...},  # analyzer_output.json
            "pass2_output": {...},  # normalized_output.json
            "pass3_output": "...",  # sow_markdown (if needed)
            "sow_data_model": {...},  # Final normalized model
        }
    """
    if not AUTOGEN_AVAILABLE:
        raise RFQ3PassOrchestratorUnavailableError("pyautogen not installed")
    
    import os
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("No API key provided, AutoGen may not work")
    
    user = UserProxyAgent(
        name="RFQAnalysisUser",
        code_execution_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
    )
    
    results = {
        "pass1_output": None,
        "pass2_output": None,
        "pass3_output": None,
        "sow_data_model": None,
        "errors": [],
    }
    
    # PASS 1: Analyzer (use sow_analyzer_agent module)
    try:
        logger.info("Pass 1: Running AnalyzerAgent...")
        pass1_output = analyze_sow_document(
            document_text=document_text,
            llm_model=llm_model,
            api_key=api_key,
        )
        results["pass1_output"] = pass1_output
        logger.info("Pass 1 completed")
        
    except Exception as e:
        logger.error(f"Pass 1 failed: {e}", exc_info=True)
        results["errors"].append(f"Pass 1 error: {e}")
        return results
    
    # PASS 2: Reviewer (use dedicated reviewer_agent module)
    try:
        logger.info("Pass 2: Running ReviewerAgent...")
        pass2_output = run_reviewer_agent(
            raw_analyzer_json=pass1_output,
            llm_model=llm_model,
            api_key=api_key,
        )
        results["pass2_output"] = pass2_output
        results["sow_data_model"] = pass2_output  # Final normalized model
        logger.info("Pass 2 completed")
    except Exception as e:
        logger.error(f"Pass 2 failed: {e}", exc_info=True)
        results["errors"].append(f"Pass 2 error: {e}")
        # Use Pass 1 output as fallback
        results["pass2_output"] = pass1_output
        results["sow_data_model"] = pass1_output
    
    # PASS 3: SOW Generator (Fallback - only if template engine fails)
    # This is typically not needed if template engine works
    # But we keep it as fallback
    
    return results


def run_rfq_3pass_pipeline(
    rfq_pdf_path: str,
    seating_chart_pdf_path: Optional[str] = None,
    use_template_engine: bool = True,
    output_dir: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run complete 3-pass RFQ → SOW pipeline.
    
    Pipeline:
    1) RFQ PDF → text → Pass 1 AnalyzerAgent → analyzer_json
    2) Pass 2 ReviewerAgent → normalized_json
    3) Seating chart (if provided) → parse → seating_layout
    4) SOWDataModel.from_analyzer_json(...)
    5) If use_template_engine:
         - HTML = render_sow_from_model(data_model)
         - PDF = html_to_pdf(HTML, output_path)
       Else:
         - sow_markdown = run_sow_generator_agent(normalized_json)
         - PDF = generate_pdf_from_markdown(sow_markdown, output_path)
    
    Args:
        rfq_pdf_path: Path to RFQ PDF file
        seating_chart_pdf_path: Optional path to seating chart PDF
        use_template_engine: Whether to use template engine (True) or LLM fallback (False)
        output_dir: Directory for output files (default: same as RFQ PDF directory)
        llm_model: LLM model to use
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        {
            "analyzer_json": {...},  # Pass 1 output
            "normalized_json": {...},  # Pass 2 output
            "data_model": SOWDataModel,  # Final normalized model
            "sow_html": str,  # HTML (if template engine used)
            "sow_pdf_path": str,  # Path to generated PDF
            "fallback_markdown": str,  # Markdown (if fallback used)
            "seating_layout": {...},  # Seating layout (if parsed)
            "errors": [...],  # Any errors encountered
        }
    """
    if not AUTOGEN_AVAILABLE:
        raise RFQ3PassOrchestratorUnavailableError("pyautogen not installed")
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    rfq_path = Path(rfq_pdf_path)
    if not rfq_path.exists():
        raise FileNotFoundError(f"RFQ PDF not found: {rfq_pdf_path}")
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = rfq_path.parent
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        "analyzer_json": None,
        "normalized_json": None,
        "data_model": None,
        "sow_html": None,
        "sow_pdf_path": None,
        "fallback_markdown": None,
        "seating_layout": None,
        "errors": [],
    }
    
    try:
        # Step 1: Extract text from RFQ PDF
        logger.info(f"Step 1: Extracting text from RFQ PDF: {rfq_pdf_path}")
        doc_analysis = analyze_document(str(rfq_path), "application/pdf")
        document_text = doc_analysis.get("extracted_text", "")
        
        if not document_text:
            raise ValueError("No text extracted from RFQ PDF")
        
        logger.info(f"Extracted {len(document_text)} characters from RFQ PDF")
        
        # Step 2: Run 3-pass analysis
        logger.info("Step 2: Running 3-pass RFQ analysis...")
        analysis_results = run_3pass_rfq_analysis(
            document_text=document_text,
            llm_model=llm_model,
            api_key=api_key,
            max_retries=2,
        )
        
        results["analyzer_json"] = analysis_results.get("pass1_output")
        results["normalized_json"] = analysis_results.get("pass2_output")
        results["errors"].extend(analysis_results.get("errors", []))
        
        if not results["normalized_json"]:
            raise ValueError("Pass 2 failed, no normalized JSON available")
        
        # Step 3: Parse seating chart if provided
        seating_layout = None
        if seating_chart_pdf_path and Path(seating_chart_pdf_path).exists():
            logger.info(f"Step 3: Parsing seating chart: {seating_chart_pdf_path}")
            seating_layout = parse_seating_chart_pdf(seating_chart_pdf_path)
            results["seating_layout"] = seating_layout
        
        # Step 4: Create SOWDataModel
        logger.info("Step 4: Creating SOWDataModel...")
        data_model = SOWDataModel.from_analyzer_json(
            normalized_json=results["normalized_json"],
            seating_layout=seating_layout,
        )
        results["data_model"] = data_model
        
        # Step 5: Generate SOW (template engine or fallback)
        sow_pdf_filename = f"{rfq_path.stem}_sow.pdf"
        sow_pdf_path = output_path / sow_pdf_filename
        
        if use_template_engine and WEASYPRINT_AVAILABLE:
            try:
                logger.info("Step 5: Generating SOW using template engine...")
                sow_html = render_sow_from_model(data_model)
                results["sow_html"] = sow_html
                
                html_to_pdf(sow_html, str(sow_pdf_path))
                results["sow_pdf_path"] = str(sow_pdf_path)
                logger.info(f"SOW PDF generated: {sow_pdf_path}")
                
            except Exception as e:
                logger.warning(f"Template engine failed: {e}, falling back to LLM generator")
                use_template_engine = False
        elif use_template_engine and not WEASYPRINT_AVAILABLE:
            logger.warning("WeasyPrint not available, using LLM fallback for PDF generation")
            use_template_engine = False
        
        if not use_template_engine:
            logger.info("Step 5: Generating SOW using LLM fallback...")
            sow_markdown = run_sow_generator_agent(
                normalized_json=results["normalized_json"],
                llm_model=llm_model,
                api_key=api_key,
            )
            results["fallback_markdown"] = sow_markdown
            
            generate_pdf_from_markdown(sow_markdown, str(sow_pdf_path))
            results["sow_pdf_path"] = str(sow_pdf_path)
            logger.info(f"SOW PDF generated (fallback): {sow_pdf_path}")
        
        logger.info("3-pass RFQ pipeline completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error in 3-pass RFQ pipeline: {e}", exc_info=True)
        results["errors"].append(f"Pipeline error: {e}")
        return results

