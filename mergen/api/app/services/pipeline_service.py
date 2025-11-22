"""
Pipeline service utilities.
Simulates AutoGen workflow, writes logs/results, and stores output artifacts.
"""
import json
import os
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import (
    Opportunity,
    OpportunityAttachment,
    AIAnalysisResult,
    AnalysisLog,
    AgentRun,
    AgentMessage,
)
from ..services.history_service import (
    record_opportunity_history,
    add_training_example,
)
from ..services.llm_logger import log_llm_call
from ..services.opportunity_context import (
    build_hotel_match_requirements,
    build_decision_cache_context,
)
from ..services.decision_cache_service import (
    lookup_decision_cache,
    persist_decision_cache,
)
from ..agents.hotel_matcher_agent import run_hotel_match_for_opportunity, HotelMatcherUnavailableError
from ..agents.sow_analyzer_agent import analyze_sow_document, SOWAnalyzerUnavailableError
from ..services.pdf_generator import generate_analysis_pdf
from ..services.parsing.document_analyzer import analyze_document

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR))).resolve()


def _resolve_attachment_path(path_str: Optional[str]) -> Optional[Path]:
    """Return a usable Path for stored attachment entries."""
    if not path_str:
        return None

    candidate = Path(path_str)
    search_paths = [candidate]

    # If the stored path is absolute, check it directly
    if candidate.is_absolute():
        if candidate.exists():
            return candidate
        # Also try if it's under /data but DATA_DIR is different
        if str(candidate).startswith("/data/"):
            # Try with actual DATA_DIR
            relative_part = candidate.relative_to(Path("/data"))
            search_paths.append(DATA_DIR / relative_part)
    else:
        # If relative, try multiple locations
        search_paths.append(DATA_DIR / candidate)
        search_paths.append(DATA_DIR.parent / candidate)
        search_paths.append(Path.cwd() / candidate)
        search_paths.append(PROJECT_ROOT / candidate)
        # Also try as absolute path under /data (common in Docker)
        if not str(candidate).startswith("/"):
            search_paths.append(Path("/data") / candidate)

    for path in search_paths:
        if path.exists():
            logger.debug(f"Resolved attachment path: {path_str} -> {path}")
            return path

    # None of the candidates exist; log for debugging
    logger.warning(f"Could not resolve attachment path: {path_str}. Tried: {search_paths}")
    # Return the original path anyway (might work if file gets created)
    return candidate


def _auto_download_attachments(
    db: Session,
    opportunity: Opportunity,
    analysis_result_id: int,
    agent_run_id: Optional[int],
    attachment_ids: Optional[List[int]] = None,
) -> List[OpportunityAttachment]:
    """
    Ensure all attachments for the opportunity are downloaded locally.
    Reuses the attachment_service async downloader and refreshes Attachment records.
    """
    query = db.query(OpportunityAttachment).filter(
        OpportunityAttachment.opportunity_id == opportunity.id
    )
    if attachment_ids:
        query = query.filter(OpportunityAttachment.id.in_(attachment_ids))
    attachments = query.all()

    # Filter attachments that need downloading (have source_url but not downloaded)
    missing: List[OpportunityAttachment] = []
    for att in attachments:
        if not att.source_url:
            continue
        if not att.downloaded or not att.local_path:
            missing.append(att)
            continue

        resolved = _resolve_attachment_path(att.local_path)
        if not resolved or not resolved.exists():
            missing.append(att)
    
    # Only download if we have attachments with source_url that are missing
    if missing:
        from ..services.attachment_service import download_attachments_for_opportunity
        import uuid

        _log_analysis(
            db,
            analysis_result_id,
            "INFO",
            f"Auto-downloading {len(missing)} missing attachment(s) before pipeline execution",
            step="prepare",
            agent_run_id=agent_run_id,
        )
        
        try:
            # Let download_attachments_for_opportunity create its own job_id
            # This ensures the job is properly registered in the database
            logger.info(f"[Pipeline {analysis_result_id}] Starting auto-download for {len(missing)} attachments")
            
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to use a different approach
                logger.warning(f"[Pipeline {analysis_result_id}] Already in async context, creating task for download")
                # Create a new event loop in a thread
                import threading
                import queue
                result_queue = queue.Queue()
                
                def run_download():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        # Pass None to let download_attachments_for_opportunity create its own job
                        result = new_loop.run_until_complete(
                            download_attachments_for_opportunity(db, opportunity.id, job_id=None)
                        )
                        result_queue.put(('success', result))
                        new_loop.close()
                    except Exception as e:
                        logger.exception(f"[Pipeline {analysis_result_id}] Download thread error: {e}")
                        result_queue.put(('error', e))
                
                thread = threading.Thread(target=run_download, daemon=False)
                thread.start()
                thread.join(timeout=300)  # 5 minute timeout
                
                if thread.is_alive():
                    logger.error(f"[Pipeline {analysis_result_id}] Download timeout after 5 minutes")
                    raise TimeoutError("Download timeout after 5 minutes")
                
                if not result_queue.empty():
                    status, result = result_queue.get()
                    if status == 'error':
                        logger.error(f"[Pipeline {analysis_result_id}] Download failed: {result}")
                        raise result
                else:
                    logger.error(f"[Pipeline {analysis_result_id}] Download thread completed but no result in queue")
                    raise RuntimeError("Download thread completed but no result available")
            except RuntimeError as e:
                if "no running event loop" in str(e).lower() or "no current event loop" in str(e).lower():
                    # No running loop, we can use asyncio.run
                    logger.info(f"[Pipeline {analysis_result_id}] No running loop, using asyncio.run")
                    try:
                        # Pass None to let download_attachments_for_opportunity create its own job
                        asyncio.run(download_attachments_for_opportunity(db, opportunity.id, job_id=None))
                    except Exception as run_error:
                        logger.exception(f"[Pipeline {analysis_result_id}] asyncio.run failed: {run_error}")
                        raise
                else:
                    raise
            
            # Refresh attachment records from DB
            db.expire_all()
            query = db.query(OpportunityAttachment).filter(
                OpportunityAttachment.opportunity_id == opportunity.id
            )
            if attachment_ids:
                query = query.filter(OpportunityAttachment.id.in_(attachment_ids))
            attachments = query.all()
            
            # Check results
            downloaded_count = len([att for att in attachments if att.downloaded and att.local_path])
            _log_analysis(
                db,
                analysis_result_id,
                "INFO",
                f"Auto-download completed: {downloaded_count}/{len(attachments)} attachments now available",
                step="prepare",
                agent_run_id=agent_run_id,
            )
            logger.info(f"[Pipeline {analysis_result_id}] Auto-download completed: {downloaded_count}/{len(attachments)} attachments available")
            
        except Exception as exc:
            logger.exception(f"Automatic attachment download failed for opportunity {opportunity.id}: {exc}")
            _log_analysis(
                db,
                analysis_result_id,
                "ERROR",
                f"Attachment auto-download failed: {exc}. Pipeline will continue with available attachments.",
                step="prepare",
                agent_run_id=agent_run_id,
            )
            # Continue with whatever attachments we have
    elif attachments and not any(att.source_url for att in attachments):
        # No source URLs available
        _log_analysis(
            db,
            analysis_result_id,
            "WARNING",
            f"Found {len(attachments)} attachment(s) but none have source_url. Cannot auto-download.",
            step="prepare",
            agent_run_id=agent_run_id,
        )
    
    return attachments


def _log_analysis(
    db: Session,
    analysis_result_id: int,
    level: str,
    message: str,
    step: Optional[str] = None,
    agent_run_id: Optional[int] = None,
) -> None:
    log = AnalysisLog(
        analysis_result_id=analysis_result_id,
        level=level,
        message=message,
        step=step,
    )
    db.add(log)
    db.commit()

    if agent_run_id:
        msg = AgentMessage(
            agent_run_id=agent_run_id,
            agent_name="pipeline",
            role="system",
            message_type="log",
            content=message,
        )
        db.add(msg)
        db.commit()


def create_pipeline_job(
    db: Session,
    opportunity_id: int,
    analysis_type: str,
    pipeline_version: Optional[str],
    agent_name: Optional[str],
    initial_options: Optional[Dict[str, Any]] = None,
) -> (AIAnalysisResult, int):
    """Create an AIAnalysisResult entry with pending status."""
    result = AIAnalysisResult(
        opportunity_id=opportunity_id,
        analysis_type=analysis_type or "sow_draft",
        status="pending",
        pipeline_version=pipeline_version or "v1",
        agent_name=agent_name or "autogen",
        result_json={"options": initial_options} if initial_options else None,
        confidence=0.0,  # Default confidence score
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    agent_run = AgentRun(
        opportunity_id=opportunity_id,
        run_type=analysis_type,
        status="started",
        extra_metadata={"options": initial_options} if initial_options else None,
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    _log_analysis(db, result.id, "INFO", "Pipeline job created", step="init", agent_run_id=agent_run.id)

    return result, agent_run.id


def run_pipeline_job(analysis_result_id: int, payload: Dict[str, Any]) -> None:
    """
    Background worker that simulates the AutoGen pipeline.
    Reads attachments, creates a summary JSON file, and updates AIAnalysisResult.
    """
    logger.info(f"[Pipeline {analysis_result_id}] Background task started")
    session = SessionLocal()
    try:
        result = session.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
        if not result:
            logger.error(f"[Pipeline {analysis_result_id}] Analysis result not found")
            return

        logger.info(f"[Pipeline {analysis_result_id}] Found analysis result, status: {result.status}")

        opportunity = session.query(Opportunity).filter(Opportunity.id == result.opportunity_id).first()
        if not opportunity:
            logger.error(f"[Pipeline {analysis_result_id}] Opportunity not found")
            _log_analysis(session, analysis_result_id, "ERROR", "Opportunity not found", step="init")
            result.status = "failed"
            result.result_json = {"error": "Opportunity not found"}
            session.commit()
            return

        attachment_ids: Optional[List[int]] = payload.get("attachment_ids")
        options: Dict[str, Any] = payload.get("options") or {}
        agent_run_id = payload.get("agent_run_id")

        logger.info(f"[Pipeline {analysis_result_id}] Processing {result.analysis_type} analysis")

        if result.analysis_type == "hotel_match":
            _execute_hotel_match(session, result, opportunity, options, agent_run_id)
            return

        result.status = "running"
        result.updated_at = datetime.utcnow()
        session.commit()
        logger.info(f"[Pipeline {analysis_result_id}] Status set to 'running'")

        _log_analysis(session, analysis_result_id, "INFO", "Pipeline job started", step="init", agent_run_id=agent_run_id)

        # Fetch attachments
        query = session.query(OpportunityAttachment).filter(
            OpportunityAttachment.opportunity_id == opportunity.id
        )
        if attachment_ids:
            query = query.filter(OpportunityAttachment.id.in_(attachment_ids))
        attachments = query.all()

        # If no attachments found, try to extract from raw_data
        if not attachments and opportunity.raw_data:
            _log_analysis(session, analysis_result_id, "INFO", "No attachments in DB; attempting to extract from raw_data", step="prepare")
            try:
                from .sam_mapper import extract_attachments_from_sam_record
                
                # Parse raw_data if it's a string
                raw_data = opportunity.raw_data
                if isinstance(raw_data, str):
                    try:
                        raw_data = json.loads(raw_data)
                    except:
                        raw_data = {}
                
                if isinstance(raw_data, dict):
                    # Extract attachments from raw_data
                    extracted_attachments = extract_attachments_from_sam_record(raw_data, opportunity.id)
                    
                    if extracted_attachments:
                        from ..crud.opportunities import create_attachment
                        for att_data in extracted_attachments:
                            try:
                                create_attachment(session, att_data)
                                attachments.append(session.query(OpportunityAttachment).filter(
                                    OpportunityAttachment.opportunity_id == opportunity.id,
                                    OpportunityAttachment.source_url == att_data.get("source_url")
                                ).first())
                            except Exception as att_error:
                                logger.warning(f"Error creating attachment from raw_data: {att_error}")
                                continue
                        
                        if attachments:
                            _log_analysis(session, analysis_result_id, "INFO", f"Extracted {len(attachments)} attachments from raw_data", step="prepare")
            except Exception as e:
                logger.warning(f"Error extracting attachments from raw_data: {e}", exc_info=True)
                _log_analysis(session, analysis_result_id, "WARNING", f"Failed to extract attachments from raw_data: {e}", step="prepare")

        # Remove any None placeholders from extraction step
        attachments = [att for att in attachments if att is not None]

        attachments = _auto_download_attachments(
            session,
            opportunity,
            analysis_result_id,
            agent_run_id,
            attachment_ids=attachment_ids,
        )

        if not attachments:
            warning_msg = (
                "No attachments found for this opportunity. "
                "AutoGen agents cannot analyze documents without attachments. "
                "Pipeline will continue with metadata only, but analysis results will be limited. "
                "Please sync attachments from SAM.gov or upload documents manually."
            )
            _log_analysis(session, analysis_result_id, "WARNING", warning_msg, step="prepare")
            logger.warning(f"[Pipeline {analysis_result_id}] {warning_msg}")

        attachment_details = []
        analyzed_documents = []
        
        # Attachments are already downloaded by _auto_download_attachments
        # Just refresh the list to get latest status
        session.expire_all()
        
        for att in attachments:
            details = {
                "id": att.id,
                "name": att.name,
                "downloaded": att.downloaded,
                "local_path": att.local_path,
                "source_url": att.source_url,
                "size_bytes": att.size_bytes,
            }
            attachment_details.append(details)
            
            # Check if attachment is downloaded and has local path
            if not att.downloaded or not att.local_path:
                error_msg = (
                    f"Attachment '{att.name}' (ID: {att.id}) is not downloaded locally. "
                    f"AutoGen cannot analyze this document without a local file. "
                    f"Please run download-attachments endpoint first. "
                    f"Source URL: {att.source_url or 'N/A'}"
                )
                _log_analysis(
                    session,
                    analysis_result_id,
                    "ERROR",
                    error_msg,
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                logger.warning(f"[Pipeline {analysis_result_id}] {error_msg}")
                continue
            
            # Check if file exists on disk
            local_path_obj = _resolve_attachment_path(att.local_path)
            if not local_path_obj.exists():
                error_msg = (
                    f"Document file not found at path: {att.local_path}. "
                    f"File may have been deleted or path is incorrect. "
                    f"Attachment ID: {att.id}, Name: {att.name}"
                )
                _log_analysis(
                    session,
                    analysis_result_id,
                    "ERROR",
                    error_msg,
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                logger.error(f"[Pipeline {analysis_result_id}] {error_msg}")
                continue
            
            # Analyze downloaded document
            try:
                logger.info(f"[Pipeline {analysis_result_id}] Analyzing document: {att.name}")
                logger.info(f"[Pipeline {analysis_result_id}] File path: {local_path_obj}")
                logger.info(f"[Pipeline {analysis_result_id}] File exists: {local_path_obj.exists()}")
                logger.info(f"[Pipeline {analysis_result_id}] File size: {local_path_obj.stat().st_size if local_path_obj.exists() else 0} bytes")
                logger.info(f"[Pipeline {analysis_result_id}] MIME type: {att.mime_type}")
                
                _log_analysis(
                    session,
                    analysis_result_id,
                    "INFO",
                    f"Analyzing document: {att.name}",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                
                analysis_result = analyze_document(str(local_path_obj), att.mime_type)
                analysis_result["attachment_id"] = att.id
                analysis_result["attachment_name"] = att.name
                analyzed_documents.append(analysis_result)
                
                # Log analysis results
                text_len = analysis_result.get("text_length", 0)
                word_count = analysis_result.get("word_count", 0)
                error = analysis_result.get("error")
                
                logger.info(f"[Pipeline {analysis_result_id}] Analysis result for {att.name}: {text_len} chars, {word_count} words, error: {error}")
                
                if error:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "WARNING",
                        f"Document analysis error for {att.name}: {error}",
                        step="analyze",
                        agent_run_id=agent_run_id,
                    )
                else:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "INFO",
                        f"Document analyzed: {att.name} ({text_len} chars, {word_count} words)",
                        step="analyze",
                        agent_run_id=agent_run_id,
                    )
            except Exception as doc_exc:
                logger.error(f"Error analyzing document {att.name}: {doc_exc}", exc_info=True)
                _log_analysis(
                    session,
                    analysis_result_id,
                    "ERROR",
                    f"Failed to analyze {att.name}: {doc_exc}",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )

        # Combine extracted text from all documents
        # CRITICAL: Combine ALL documents (SOW + Combined Synopsis) for complete analysis
        # This ensures the analyzer gets both SOW requirements and evaluation criteria
        all_extracted_text_parts = []
        for doc in analyzed_documents:
            extracted = doc.get("extracted_text", "")
            if extracted and len(extracted.strip()) > 10:  # Only add if substantial text
                doc_name = doc.get("attachment_name", "Unknown")
                all_extracted_text_parts.append(f"\n\n--- START OF DOCUMENT: {doc_name} ---\n\n")
                all_extracted_text_parts.append(extracted)
                all_extracted_text_parts.append(f"\n\n--- END OF DOCUMENT: {doc_name} ---\n\n")
        
        all_extracted_text = "".join(all_extracted_text_parts)
        
        # DEBUG: Log extracted text content to diagnose why only 16 chars
        logger.info(f"[Pipeline {analysis_result_id}] DEBUG - Combined text length: {len(all_extracted_text)} chars")
        if all_extracted_text:
            logger.info(f"[Pipeline {analysis_result_id}] DEBUG - First 500 chars of extracted text: {all_extracted_text[:500]}")
            logger.info(f"[Pipeline {analysis_result_id}] DEBUG - Last 200 chars of extracted text: {all_extracted_text[-200:]}")
        else:
            logger.warning(f"[Pipeline {analysis_result_id}] DEBUG - No text extracted from any document!")
            # Log each document's extracted text
            for i, doc in enumerate(analyzed_documents):
                doc_text = doc.get("extracted_text", "")
                logger.warning(f"[Pipeline {analysis_result_id}] DEBUG - Doc {i+1} ({doc.get('attachment_name', 'N/A')}): {len(doc_text)} chars - Content: {repr(doc_text[:200])}")
        
        # Log combined text info
        if all_extracted_text:
            _log_analysis(
                session,
                analysis_result_id,
                "INFO",
                f"Combined text from {len(analyzed_documents)} documents: {len(all_extracted_text)} chars, {len(all_extracted_text.split())} words",
                step="analyze",
                agent_run_id=agent_run_id,
            )
        
        # Extract key information from documents
        total_text_length = sum(doc.get("text_length", 0) for doc in analyzed_documents)
        total_word_count = sum(doc.get("word_count", 0) for doc in analyzed_documents)
        total_tables = sum(len(doc.get("tables", [])) for doc in analyzed_documents)
        
        # Use AutoGen SOW Analyzer if we have document text and analysis_type is sow_draft or sow
        # CRITICAL: Only use AutoGen if we have substantial text (at least 100 chars)
        # This prevents using placeholder/mock data
        sow_analysis = None
        if result.analysis_type in ["sow_draft", "sow"] and all_extracted_text and len(all_extracted_text.strip()) >= 100:
            try:
                _log_analysis(
                    session,
                    analysis_result_id,
                    "INFO",
                    "Running AutoGen SOW analyzer on extracted document text",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                llm_model = options.get("llm_model", "gpt-4o-mini")
                # Increase text limit for better analysis (up to ~120000 chars for full documents)
                # GPT-4o-mini has 128k context, so we can send more text
                # This ensures we capture pricing schedules at the end of documents
                max_text_length = options.get("max_text_length", 120000)  # Full document analysis
                text_to_analyze = all_extracted_text[:max_text_length] if len(all_extracted_text) > max_text_length else all_extracted_text
                
                if len(all_extracted_text) > max_text_length:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "INFO",
                        f"Text is long ({len(all_extracted_text)} chars), analyzing first {max_text_length} chars (~12000 tokens)",
                        step="analyze",
                        agent_run_id=agent_run_id,
                    )
                
                sow_analysis = analyze_sow_document(text_to_analyze, llm_model=llm_model, agent_run_id=agent_run_id)
                _log_analysis(
                    session,
                    analysis_result_id,
                    "INFO",
                    f"SOW analysis completed. Extracted {len(sow_analysis)} sections.",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
            except SOWAnalyzerUnavailableError as e:
                _log_analysis(
                    session,
                    analysis_result_id,
                    "WARNING",
                    f"AutoGen SOW analyzer not available: {e}. Using basic extraction.",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
            except Exception as e:
                logger.error(f"Error in SOW analysis: {e}", exc_info=True)
                _log_analysis(
                    session,
                    analysis_result_id,
                    "ERROR",
                    f"SOW analysis failed: {e}",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
        
        summary = {
            "opportunity": {
                "id": opportunity.id,
                "notice_id": opportunity.notice_id,
                "title": opportunity.title,
                "agency": opportunity.agency,
                "naics_code": opportunity.naics_code,
            },
            "analysis_type": result.analysis_type,
            "pipeline_version": result.pipeline_version,
            "options": options,
            "attachment_count": len(attachment_details),
            "attachments": attachment_details,
            "analyzed_documents": analyzed_documents,
            "document_analysis": {
                "total_text_length": total_text_length,
                "total_word_count": total_word_count,
                "total_tables": total_tables,
                "documents_analyzed": len(analyzed_documents),
                "combined_text_preview": all_extracted_text[:1000] if all_extracted_text else "",  # First 1000 chars
            },
            "sow_analysis": sow_analysis,  # AutoGen-extracted detailed SOW requirements
            "generated_at": datetime.utcnow().isoformat(),
            "notes": f"Analyzed {len(analyzed_documents)} documents. Total: {total_word_count} words, {total_tables} tables extracted." + (f" AutoGen SOW analysis completed." if sow_analysis else " Basic extraction only.") if analyzed_documents else f"No documents analyzed. Text extracted: {len(all_extracted_text)} chars. Please ensure attachments are downloaded and files exist on disk.",
        }

        # Persist summary to disk
        notice_slug = opportunity.notice_id or f"opp-{opportunity.id}"
        output_dir = DATA_DIR / "opportunities" / notice_slug / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f"analysis_{analysis_result_id}.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        # Get related hotel match results for this opportunity
        hotel_match_results = session.query(AIAnalysisResult).filter(
            AIAnalysisResult.opportunity_id == opportunity.id,
            AIAnalysisResult.analysis_type == "hotel_match",
            AIAnalysisResult.status == "completed"
        ).order_by(AIAnalysisResult.created_at.desc()).limit(1).all()
        
        # Add hotel match data to summary for PDF
        if hotel_match_results:
            hotel_result = hotel_match_results[0]
            hotel_data = hotel_result.result_json
            if isinstance(hotel_data, str):
                hotel_data = json.loads(hotel_data)
            
            # Add hotels to summary
            summary["hotels"] = hotel_data.get("hotels", [])
            summary["hotel_search_criteria"] = hotel_data.get("requirements", {})
            summary["related_hotels"] = hotel_data.get("hotels", [])
            logger.info(f"[Pipeline {analysis_result_id}] Added {len(summary.get('hotels', []))} hotels from hotel match result {hotel_result.id}")
        
        # Generate PDF
        pdf_path = output_dir / f"analysis_{analysis_result_id}.pdf"
        opp_dict = {
            "id": opportunity.id,
            "notice_id": opportunity.notice_id,
            "title": opportunity.title,
            "agency": opportunity.agency,
        }
        pdf_generated = generate_analysis_pdf(pdf_path, summary, opp_dict)
        if pdf_generated:
            result.pdf_path = str(pdf_path)
            _log_analysis(session, analysis_result_id, "INFO", f"PDF generated: {pdf_path}", step="generate", agent_run_id=agent_run_id)

        # log synthetic LLM call (replace with real call later)
        try:
            log_llm_call(
                db=session,
                provider="autogen-mock",
                model="pipeline-summarizer",
                prompt=f"Generate summary for opportunity {opportunity.notice_id}",
                response_text=json.dumps(summary),
                agent_run_id=agent_run_id,
                agent_name="pipeline",
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                latency_ms=None,
            )
        except Exception as log_exc:
            logger.warning("Failed to log LLM call: %s", log_exc)

        result.result_json = summary
        result.json_path = str(json_path)
        result.status = "completed"
        result.completed_at = datetime.utcnow()
        session.commit()

        _log_analysis(session, analysis_result_id, "INFO", "Pipeline job completed", step="complete", agent_run_id=agent_run_id)

        # Send email notification for both sow_draft and hotel_match analyses
        # For sow_draft: Send email with SOW PDF/JSON + hotel match JSON (if available)
        # For hotel_match: Send email with both SOW and hotel match PDFs/JSONs
        send_email_now = result.analysis_type in ["sow_draft", "sow", "hotel_match"]
        
        if send_email_now:
            try:
                from ..config import settings
                from ..services.mail_service import build_mail_package, send_email_via_smtp
                
                if not (settings.pipeline_notification_email and settings.smtp_host and settings.smtp_username):
                    logger.info(f"[Pipeline {analysis_result_id}] Email notification not configured (missing SMTP settings or notification email)")
                else:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "INFO",
                        f"Sending email notification to {settings.pipeline_notification_email}",
                        step="email",
                        agent_run_id=agent_run_id,
                    )
                
                # Build mail package with PDF and JSON attachments
                notice_id = opportunity.notice_id or str(opportunity.id)
                output_dir = DATA_DIR / "opportunities" / notice_id / "outputs"
                
                # Create mail package with analysis result JSON
                analysis_json = summary if isinstance(summary, dict) else (json.loads(summary) if isinstance(summary, str) else {})
                
                # Add hotel match data to analysis_json if available
                hotel_match_results = session.query(AIAnalysisResult).filter(
                    AIAnalysisResult.opportunity_id == opportunity.id,
                    AIAnalysisResult.analysis_type == "hotel_match",
                    AIAnalysisResult.status == "completed"
                ).order_by(AIAnalysisResult.created_at.desc()).limit(1).all()
                
                if hotel_match_results:
                    hotel_result = hotel_match_results[0]
                    if hotel_result.result_json:
                        hotel_data = hotel_result.result_json if isinstance(hotel_result.result_json, dict) else json.loads(hotel_result.result_json) if isinstance(hotel_result.result_json, str) else {}
                        # Add hotels array to analysis_json for email body
                        if 'hotels' in hotel_data:
                            analysis_json['hotels'] = hotel_data['hotels']
                        elif 'hotel_match' in hotel_data:
                            analysis_json['hotel_match'] = hotel_data['hotel_match']
                
                mail_package = build_mail_package(
                    opportunity_code=notice_id,
                    folder_path=str(output_dir),
                    to_email=settings.pipeline_notification_email,
                    from_email=settings.smtp_from_email,
                    analysis_result_json=analysis_json,
                )
                
                # Add generated PDF and JSON to attachments if they exist
                attachments = mail_package.get('attachments', [])
                
                # Add SOW PDF and JSON for sow_draft/sow analyses
                if result.analysis_type in ["sow_draft", "sow"]:
                    if result.pdf_path and Path(result.pdf_path).exists():
                        attachments.append({
                            'path': result.pdf_path,
                            'filename': f"sow_analysis_{analysis_result_id}.pdf",
                            'mime_type': 'application/pdf'
                        })
                    if result.json_path and Path(result.json_path).exists():
                        attachments.append({
                            'path': result.json_path,
                            'filename': f"sow_analysis_{analysis_result_id}.json",
                            'mime_type': 'application/json'
                        })
                
                # Add hotel match PDF and JSON for hotel_match analyses
                if result.analysis_type == "hotel_match":
                    if result.pdf_path and Path(result.pdf_path).exists():
                        attachments.append({
                            'path': result.pdf_path,
                            'filename': f"hotel_suggestions_{analysis_result_id}.pdf",
                            'mime_type': 'application/pdf'
                        })
                    if result.json_path and Path(result.json_path).exists():
                        attachments.append({
                            'path': result.json_path,
                            'filename': f"hotel_match_{analysis_result_id}.json",
                            'mime_type': 'application/json'
                        })
                
                # For sow_draft/sow: Also add hotel match JSON if available (Amadeus hotel suggestions)
                # For hotel_match: Also add SOW PDF/JSON if available
                if result.analysis_type in ["sow_draft", "sow"]:
                    # Add hotel match JSON if available (Amadeus'tan gelen hotel öneri JSON'u)
                    if not hotel_match_results:
                        hotel_match_results = session.query(AIAnalysisResult).filter(
                            AIAnalysisResult.opportunity_id == opportunity.id,
                            AIAnalysisResult.analysis_type == "hotel_match",
                            AIAnalysisResult.status == "completed"
                        ).order_by(AIAnalysisResult.created_at.desc()).limit(1).all()
                    
                    for hotel_result in hotel_match_results:
                        # Add hotel match JSON (Amadeus'tan gelen hotel öneri JSON'u)
                        if hotel_result.json_path:
                            hotel_json_path = Path(hotel_result.json_path)
                            # Try alternative paths if not found
                            if not hotel_json_path.exists():
                                alt_paths = [
                                    Path('/data') / hotel_result.json_path.lstrip('/'),
                                    DATA_DIR / hotel_result.json_path.lstrip('/'),
                                ]
                                for alt_path in alt_paths:
                                    if alt_path.exists():
                                        hotel_json_path = alt_path
                                        break
                            
                            if hotel_json_path.exists():
                                attachments.append({
                                    'path': str(hotel_json_path),
                                    'filename': f"hotel_match_{hotel_result.id}.json",
                                    'mime_type': 'application/json'
                                })
                                logger.info(f"[Pipeline {analysis_result_id}] Added hotel match JSON (Amadeus) to SOW email: {hotel_json_path}")
                
                elif result.analysis_type == "hotel_match":
                    # Add SOW PDF and JSON if available
                    sow_results = session.query(AIAnalysisResult).filter(
                        AIAnalysisResult.opportunity_id == opportunity.id,
                        AIAnalysisResult.analysis_type.in_(["sow_draft", "sow"]),
                        AIAnalysisResult.status == "completed"
                    ).order_by(AIAnalysisResult.created_at.desc()).limit(1).all()
                    
                    for sow_result in sow_results:
                        if sow_result.pdf_path:
                            sow_pdf_path = Path(sow_result.pdf_path)
                            # Try alternative paths if not found
                            if not sow_pdf_path.exists():
                                alt_paths = [
                                    Path('/data') / sow_result.pdf_path.lstrip('/'),
                                    DATA_DIR / sow_result.pdf_path.lstrip('/'),
                                ]
                                for alt_path in alt_paths:
                                    if alt_path.exists():
                                        sow_pdf_path = alt_path
                                        break
                            
                            if sow_pdf_path.exists():
                                attachments.append({
                                    'path': str(sow_pdf_path),
                                    'filename': f"sow_analysis_{sow_result.id}.pdf",
                                    'mime_type': 'application/pdf'
                                })
                                logger.info(f"[Pipeline {analysis_result_id}] Added SOW PDF to hotel match email: {sow_pdf_path}")
                        
                        if sow_result.json_path:
                            sow_json_path = Path(sow_result.json_path)
                            # Try alternative paths if not found
                            if not sow_json_path.exists():
                                alt_paths = [
                                    Path('/data') / sow_result.json_path.lstrip('/'),
                                    DATA_DIR / sow_result.json_path.lstrip('/'),
                                ]
                                for alt_path in alt_paths:
                                    if alt_path.exists():
                                        sow_json_path = alt_path
                                        break
                            
                            if sow_json_path.exists():
                                attachments.append({
                                    'path': str(sow_json_path),
                                    'filename': f"sow_analysis_{sow_result.id}.json",
                                    'mime_type': 'application/json'
                                })
                                logger.info(f"[Pipeline {analysis_result_id}] Added SOW JSON to hotel match email: {sow_json_path}")
                
                mail_package['attachments'] = attachments
                
                # Log attachment info
                logger.info(f"[Pipeline {analysis_result_id}] Email will include {len(attachments)} attachments:")
                for att in attachments:
                    att_path = Path(att['path'])
                    if att_path.exists():
                        logger.info(f"[Pipeline {analysis_result_id}]   - {att['filename']} ({att_path.stat().st_size} bytes) [OK]")
                    else:
                        logger.warning(f"[Pipeline {analysis_result_id}]   - {att['filename']} [MISSING: {att_path}]")
                
                # SMTP config
                smtp_config = {
                    'host': settings.smtp_host,
                    'port': settings.smtp_port,
                    'username': settings.smtp_username,
                    'password': settings.smtp_password,
                    'use_tls': settings.smtp_use_tls,
                }
                
                # Send email
                if send_email_via_smtp(mail_package, smtp_config):
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "INFO",
                        f"Email notification sent successfully to {settings.pipeline_notification_email}",
                        step="email",
                        agent_run_id=agent_run_id,
                    )
                    logger.info(f"[Pipeline {analysis_result_id}] Email notification sent successfully")
                else:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "WARNING",
                        f"Failed to send email notification to {settings.pipeline_notification_email}",
                        step="email",
                        agent_run_id=agent_run_id,
                    )
                    logger.warning(f"[Pipeline {analysis_result_id}] Failed to send email notification")
            except Exception as email_exc:
                logger.warning(f"[Pipeline {analysis_result_id}] Email notification failed: {email_exc}", exc_info=True)
                _log_analysis(
                    session,
                    analysis_result_id,
                    "WARNING",
                    f"Email notification failed: {email_exc}",
                    step="email",
                    agent_run_id=agent_run_id,
                )

        # Auto-trigger hotel match if sow_draft analysis completed successfully
        if result.analysis_type == "sow_draft" and sow_analysis:
            try:
                _log_analysis(
                    session,
                    analysis_result_id,
                    "INFO",
                    "Auto-triggering hotel match based on SOW analysis results",
                    step="auto-hotel-match",
                    agent_run_id=agent_run_id,
                )
                
                # Extract hotel match requirements from SOW analysis
                event_details = sow_analysis.get("EventDetails", {})
                if not event_details:
                    event_details = sow_analysis.get("event_details", {})
                
                location_info = event_details.get("Location", {})
                if not location_info:
                    location_info = event_details.get("location", {})
                
                dates_info = event_details.get("Dates", {})
                if not dates_info:
                    dates_info = event_details.get("dates", {})
                
                sleeping_rooms = sow_analysis.get("SleepingRoomRequirements", {})
                if not sleeping_rooms:
                    sleeping_rooms = sow_analysis.get("sleeping_room_requirements", {})
                
                # Extract city and dates - PRIORITY: Locations array > EventDetails
                city_name = None
                start_date = None
                end_date = None
                
                # FIRST: Try to extract from Locations array (most reliable)
                locations_array = sow_analysis.get("Locations", [])
                if locations_array and isinstance(locations_array, list) and len(locations_array) > 0:
                    first_location = locations_array[0]
                    if isinstance(first_location, dict):
                        # Extract city from first location
                        city_name = first_location.get("city") or first_location.get("City")
                        # Extract dates from first location
                        loc_start = first_location.get("start_date")
                        loc_days = first_location.get("num_days")
                        if loc_start:
                            try:
                                start_date = datetime.fromisoformat(loc_start.replace('Z', '+00:00')).date().isoformat()
                                if loc_days:
                                    from datetime import timedelta
                                    end_date = (datetime.fromisoformat(loc_start.replace('Z', '+00:00')) + timedelta(days=int(loc_days))).date().isoformat()
                            except:
                                pass
                
                # FALLBACK: Extract from EventDetails if Locations didn't provide data
                if not city_name and isinstance(location_info, dict):
                    city_name = location_info.get("City") or location_info.get("city")
                
                if (not start_date or not end_date) and isinstance(dates_info, dict):
                    if not start_date:
                        start_date = dates_info.get("Start") or dates_info.get("start")
                    if not end_date:
                        end_date = dates_info.get("End") or dates_info.get("end")
                    # Convert to ISO format if needed
                    if start_date and isinstance(start_date, str):
                        try:
                            dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            start_date = dt.date().isoformat()
                        except:
                            pass
                    if end_date and isinstance(end_date, str):
                        try:
                            dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            end_date = dt.date().isoformat()
                        except:
                            pass
                
                # Extract attendees from sleeping rooms
                attendees = None
                if isinstance(sleeping_rooms, dict):
                    daily_breakdown = sleeping_rooms.get("DailyBreakdown", sleeping_rooms.get("daily_breakdown", []))
                    if daily_breakdown and isinstance(daily_breakdown, list):
                        max_rooms = 0
                        for day in daily_breakdown:
                            if isinstance(day, dict):
                                rooms = day.get("NumberOfRooms") or day.get("number_of_rooms", 0)
                                if isinstance(rooms, (int, float)):
                                    max_rooms = max(max_rooms, int(rooms))
                        if max_rooms > 0:
                            attendees = max_rooms * 2  # Estimate 2 people per room
                
                # Build hotel match options from SOW analysis
                hotel_options = {
                    "use_sow_analysis": True,  # Flag to use SOW analysis in requirements
                }
                if city_name:
                    hotel_options["city_name"] = city_name
                if start_date:
                    hotel_options["check_in"] = start_date
                if end_date:
                    hotel_options["check_out"] = end_date
                if attendees:
                    hotel_options["adults"] = attendees
                
                # Only trigger if we have minimum required info (city and dates)
                if city_name and start_date and end_date:
                    # Create hotel match analysis job
                    hotel_result, hotel_agent_run_id = create_pipeline_job(
                        db=session,
                        opportunity_id=opportunity.id,
                        analysis_type="hotel_match",
                        pipeline_version=result.pipeline_version,
                        agent_name=result.agent_name,
                        initial_options=hotel_options,
                    )
                    
                    hotel_payload = {
                        "opportunity_id": opportunity.id,
                        "analysis_type": "hotel_match",
                        "pipeline_version": result.pipeline_version,
                        "agent_name": result.agent_name,
                        "options": hotel_options,
                        "agent_run_id": hotel_agent_run_id,
                    }
                    
                    # Run hotel match in background thread (non-blocking)
                    import threading
                    def run_hotel_match():
                        try:
                            run_pipeline_job(hotel_result.id, hotel_payload)
                        except Exception as e:
                            logger.error(f"Auto-triggered hotel match failed: {e}", exc_info=True)
                    
                    thread = threading.Thread(target=run_hotel_match, daemon=True)
                    thread.start()
                    
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "INFO",
                        f"Hotel match job created: {hotel_result.id}",
                        step="auto-hotel-match",
                        agent_run_id=agent_run_id,
                    )
                else:
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "WARNING",
                        f"Insufficient data for auto hotel match (city: {city_name}, dates: {start_date} to {end_date})",
                        step="auto-hotel-match",
                        agent_run_id=agent_run_id,
                    )
            except Exception as hotel_exc:
                logger.warning(f"Failed to auto-trigger hotel match: {hotel_exc}", exc_info=True)
                _log_analysis(
                    session,
                    analysis_result_id,
                    "WARNING",
                    f"Auto hotel match failed: {hotel_exc}",
                    step="auto-hotel-match",
                    agent_run_id=agent_run_id,
                )

        # update opportunity status / history
        old_status = opportunity.status
        new_status = f"{result.analysis_type}_completed"
        opportunity.status = new_status
        session.commit()

        try:
            record_opportunity_history(
                db=session,
                opportunity_id=opportunity.id,
                old_status=old_status,
                new_status=new_status,
                changed_by="agent:pipeline",
                change_source="pipeline_job",
                meta={"analysis_result_id": analysis_result_id},
            )
        except Exception as hist_exc:
            logger.warning("Failed to record opportunity history: %s", hist_exc)

        try:
            add_training_example(
                db=session,
                opportunity_id=opportunity.id,
                example_type=result.analysis_type,
                input_data={"attachments": attachment_details, "options": options},
                output_data=summary,
                outcome="completed",
                rating=None,
            )
        except Exception as train_exc:
            logger.warning("Failed to add training example: %s", train_exc)

    except Exception as exc:
        session.rollback()
        logger.exception(f"[Pipeline {analysis_result_id}] Pipeline job failed with exception: {exc}")
        _log_analysis(session, analysis_result_id, "ERROR", f"Pipeline failed: {exc}", step="error", agent_run_id=payload.get("agent_run_id"))
        result = session.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
        if result:
            result.status = "failed"
            result.result_json = {"error": str(exc)}
            result.completed_at = datetime.utcnow()
            session.commit()
        _log_analysis(session, analysis_result_id, "ERROR", f"Pipeline failed: {exc}", step="error", agent_run_id=agent_run_id)
    finally:
        session.close()


def _execute_hotel_match(
    db: Session,
    result: AIAnalysisResult,
    opportunity: Opportunity,
    options: Dict[str, Any],
    agent_run_id: Optional[int],
) -> None:
    result.status = "running"
    result.updated_at = datetime.utcnow()
    db.commit()
    
    _log_analysis(db, result.id, "INFO", "Hotel match job started", step="init", agent_run_id=agent_run_id)
    
    # Auto-download attachments for hotel match too (in case they need documents)
    attachment_ids = options.get("attachment_ids")
    _auto_download_attachments(
        db,
        opportunity,
        result.id,
        agent_run_id,
        attachment_ids=attachment_ids,
    )
    
    # Get SOW analysis and document analysis results if available to extract requirements
    # Always try to use SOW analysis if available (don't require explicit flag)
    sow_analysis = None
    document_analysis = None
    
    # Always try to get SOW analysis for hotel matching (unless explicitly disabled)
    # Default to True - always use SOW analysis if available
    use_sow = options.get("use_sow_analysis")
    if use_sow is None or use_sow is True:
        # Find latest completed SOW analysis for this opportunity
        # Support both "sow_draft" and "sow" analysis types
        # IMPORTANT: Prefer SOW analysis with Locations array (non-empty)
        sow_results = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.opportunity_id == opportunity.id,
            AIAnalysisResult.analysis_type.in_(["sow_draft", "sow"]),
            AIAnalysisResult.status == "completed"
        ).order_by(AIAnalysisResult.created_at.desc()).all()
        
        sow_result = None
        sow_analysis = None
        document_analysis = None
        
        # First, try to find SOW analysis with Locations array
        for candidate in sow_results:
            if candidate and candidate.result_json:
                candidate_data = candidate.result_json
                if isinstance(candidate_data, str):
                    candidate_data = json.loads(candidate_data) if candidate_data else {}
                candidate_sow_analysis = candidate_data.get("sow_analysis")
                if candidate_sow_analysis:
                    locations = candidate_sow_analysis.get("Locations", [])
                    if locations and len(locations) > 0:
                        sow_result = candidate
                        sow_analysis = candidate_sow_analysis
                        document_analysis = {
                            "analyzed_documents": candidate_data.get("analyzed_documents", []),
                            "combined_text_preview": candidate_data.get("document_analysis", {}).get("combined_text_preview", ""),
                        }
                        _log_analysis(db, result.id, "INFO", f"Found SOW Analysis {sow_result.id} with {len(locations)} locations for hotel match", step="prepare", agent_run_id=agent_run_id)
                        if len(locations) > 0:
                            first_city = locations[0].get("city") or locations[0].get("City", "N/A")
                            _log_analysis(db, result.id, "INFO", f"First city from Locations: {first_city}", step="prepare", agent_run_id=agent_run_id)
                        break
        
        # Fallback: Use latest SOW analysis even if Locations array is empty
        if not sow_result and sow_results:
            sow_result = sow_results[0]
            if sow_result and sow_result.result_json:
                sow_data = sow_result.result_json
                if isinstance(sow_data, str):
                    sow_data = json.loads(sow_data) if sow_data else {}
                sow_analysis = sow_data.get("sow_analysis")
                document_analysis = {
                    "analyzed_documents": sow_data.get("analyzed_documents", []),
                    "combined_text_preview": sow_data.get("document_analysis", {}).get("combined_text_preview", ""),
                }
                if sow_analysis:
                    locations = sow_analysis.get("Locations", [])
                    if locations:
                        _log_analysis(db, result.id, "INFO", f"Found {len(locations)} locations in SOW Analysis {sow_result.id} for hotel match", step="prepare", agent_run_id=agent_run_id)
                    else:
                        _log_analysis(db, result.id, "WARNING", f"No Locations array found in SOW Analysis {sow_result.id}", step="prepare", agent_run_id=agent_run_id)
                _log_analysis(db, result.id, "INFO", f"Using SOW and document analysis from result {sow_result.id} for hotel match requirements", step="prepare", agent_run_id=agent_run_id)
    
    try:
        _log_analysis(db, result.id, "INFO", f"Calling build_hotel_match_requirements with sow_analysis={sow_analysis is not None}, document_analysis={document_analysis is not None}", step="prepare", agent_run_id=agent_run_id)
        requirements = build_hotel_match_requirements(
            opportunity, 
            options, 
            sow_analysis=sow_analysis,
            document_analysis=document_analysis
        )
        _log_analysis(db, result.id, "INFO", f"Requirements built: city_code={requirements.get('city_code')}, city_name={requirements.get('city_name')}, check_in={requirements.get('check_in')}, check_out={requirements.get('check_out')}", step="prepare", agent_run_id=agent_run_id)
    except ValueError as exc:
        result.status = "failed"
        result.result_json = {"error": str(exc)}
        result.completed_at = datetime.utcnow()
        db.commit()
        _log_analysis(db, result.id, "ERROR", f"Hotel match requirements missing: {exc}", step="prepare", agent_run_id=agent_run_id)
        return

    # Extract SOW requirements for hotel analysis
    sow_requirements = None
    if sow_analysis:
        sow_requirements = {
            "LodgingRequirements": sow_analysis.get("LodgingRequirements") or sow_analysis.get("lodging_requirements"),
            "TransportationRequirements": sow_analysis.get("TransportationRequirements") or sow_analysis.get("transportation_requirements"),
            "Locations": sow_analysis.get("Locations") or sow_analysis.get("locations"),
            "PeriodOfPerformance": sow_analysis.get("PeriodOfPerformance") or sow_analysis.get("period_of_performance"),
            "Deliverables": sow_analysis.get("Deliverables") or sow_analysis.get("deliverables"),
            "PerformanceMetrics": sow_analysis.get("PerformanceMetrics") or sow_analysis.get("performance_metrics"),
        }
        # Remove None values
        sow_requirements = {k: v for k, v in sow_requirements.items() if v is not None}
        if sow_requirements:
            _log_analysis(db, result.id, "INFO", f"Extracted SOW requirements for hotel analysis: {list(sow_requirements.keys())}", step="prepare", agent_run_id=agent_run_id)

    decision_context = build_decision_cache_context(opportunity, requirements, options)
    key_hash = None
    signature: Dict[str, Any] = {}
    cached_entry = None
    cached_hotels: List[Dict[str, Any]] = []
    decision_metadata: Dict[str, Any] = {}

    if decision_context:
        key_hash, signature, cached_entry = lookup_decision_cache(
            db,
            opportunity=opportunity,
            context=decision_context,
            notice_id=opportunity.notice_id,
        )
        decision_metadata.update(
            {
                "key_hash": key_hash,
                "signature": signature,
                "matched": cached_entry is not None,
            }
        )
        if cached_entry:
            decision_metadata["pattern_desc"] = cached_entry.pattern_desc
            decision_metadata["cached_at"] = (
                cached_entry.created_at.isoformat() if cached_entry.created_at else None
            )
            raw_hotels = cached_entry.recommended_hotels or []
            if isinstance(raw_hotels, list):
                cached_hotels = raw_hotels
            elif isinstance(raw_hotels, dict):
                cached_hotels = raw_hotels.get("hotels") or []
            decision_metadata["cached_hotels_count"] = len(cached_hotels)
            _log_analysis(
                db,
                result.id,
                "INFO",
                f"Decision cache hit with signature {key_hash}",
                step="decision-cache",
                agent_run_id=agent_run_id,
            )
        else:
            _log_analysis(
                db,
                result.id,
                "INFO",
                f"Decision cache miss for signature {key_hash}",
                step="decision-cache",
                agent_run_id=agent_run_id,
            )

    force_refresh = bool(options.get("force_refresh"))
    use_cache_only = bool(cached_hotels and not force_refresh)

    agent_output: Dict[str, Any] = {}
    decision_hint = None
    if key_hash:
        decision_hint = {
            "key_hash": key_hash,
            "signature": signature,
            "cached_hotels": cached_hotels,
            "pattern_desc": decision_metadata.get("pattern_desc"),
        }

    if use_cache_only:
        decision_metadata["source"] = "cache"
    else:
        decision_metadata["source"] = "agent_with_cache_hint" if cached_hotels else "agent"
        try:
            agent_output = run_hotel_match_for_opportunity(
                requirements, 
                decision_hint=decision_hint,
                sow_requirements=sow_requirements,
                agent_run_id=agent_run_id
            )
        except HotelMatcherUnavailableError as exc:
            result.status = "failed"
            result.result_json = {"error": str(exc)}
            result.completed_at = datetime.utcnow()
            db.commit()
            _log_analysis(db, result.id, "ERROR", str(exc), step="agent", agent_run_id=agent_run_id)
            return
        except Exception as exc:
            result.status = "failed"
            result.result_json = {"error": f"Hotel matcher failed: {exc}"}
            result.completed_at = datetime.utcnow()
            db.commit()
            _log_analysis(db, result.id, "ERROR", f"Hotel matcher failed: {exc}", step="agent", agent_run_id=agent_run_id)
            return

    hotels: List[Dict[str, Any]] = []
    reasoning: Optional[str] = None
    if use_cache_only:
        hotels = cached_hotels
        reasoning = decision_metadata.get("pattern_desc") or "Decision cache recommendation"
    else:
        hotels = agent_output.get("hotels", [])
        reasoning = agent_output.get("reasoning")
        if hotels and decision_context and key_hash:
            persisted = persist_decision_cache(
                db,
                opportunity=opportunity,
                context=decision_context,
                recommended_hotels=hotels,
                pattern_desc=reasoning or f"Hotel match for opportunity {opportunity.id}",
                notice_id=opportunity.notice_id,
                key_hash=key_hash,
                signature=signature,
            )
            decision_metadata["saved_at"] = persisted.created_at.isoformat() if persisted.created_at else None

    summary = {
        "opportunity": {
            "id": opportunity.id,
            "title": opportunity.title,
            "notice_id": opportunity.notice_id,
        },
        "analysis_type": "hotel_match",
        "requirements": requirements,
        "hotels": hotels,
        "reasoning": reasoning,
        "generated_at": datetime.utcnow().isoformat(),
        "decision_metadata": decision_metadata,
    }
    
    # Persist summary to disk
    notice_slug = opportunity.notice_id or f"opp-{opportunity.id}"
    output_dir = DATA_DIR / "opportunities" / notice_slug / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / f"hotel_match_{result.id}.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    result.json_path = str(json_path)
    
    # Generate PDF for hotel match results (separate PDF with "Hotel Suggestions" title)
    pdf_path = output_dir / f"hotel_suggestions_{result.id}.pdf"
    opp_dict = {
        "id": opportunity.id,
        "notice_id": opportunity.notice_id,
        "title": opportunity.title,
        "agency": opportunity.agency,
    }
    from ..services.pdf_generator import generate_hotel_match_pdf
    pdf_generated = generate_hotel_match_pdf(pdf_path, summary, opp_dict)
    if pdf_generated:
        result.pdf_path = str(pdf_path)
        _log_analysis(db, result.id, "INFO", f"Hotel match PDF generated: {pdf_path}", step="generate", agent_run_id=agent_run_id)
    
    result.status = "completed"
    result.result_json = summary
    result.completed_at = datetime.utcnow()
    db.commit()

    _log_analysis(
        db,
        result.id,
        "INFO",
        f"Hotel matcher returned {len(hotels)} options",
        step="complete",
        agent_run_id=agent_run_id,
    )

    try:
        record_opportunity_history(
            db=db,
            opportunity_id=opportunity.id,
            old_status=opportunity.status,
            new_status=f"{result.analysis_type}_completed",
            changed_by="agent:hotel_matcher",
            change_source="hotel_match",
            meta={"analysis_result_id": result.id},
        )
    except Exception as exc:  # pragma: no cover - logging only
        logger.warning("Failed to record hotel match history: %s", exc)

    try:
        add_training_example(
            db=db,
            opportunity_id=opportunity.id,
            example_type="hotel_match",
            input_data={"requirements": requirements},
            output_data={"hotels": hotels},
            outcome="completed",
        )
    except Exception as exc:  # pragma: no cover - logging only
        logger.warning("Failed to store hotel match training example: %s", exc)
    
    # Send email notification for hotel_match (after completion)
    try:
        from ..config import settings
        from ..services.mail_service import build_mail_package, send_email_via_smtp
        
        if settings.pipeline_notification_email and settings.smtp_host and settings.smtp_username:
            _log_analysis(
                db,
                result.id,
                "INFO",
                f"Sending email notification to {settings.pipeline_notification_email}",
                step="email",
                agent_run_id=agent_run_id,
            )
            
            # Build mail package with SOW + Hotel Match results
            notice_id = opportunity.notice_id or str(opportunity.id)
            output_dir = DATA_DIR / "opportunities" / notice_id / "outputs"
            
            # Get SOW analysis for this opportunity
            sow_results = db.query(AIAnalysisResult).filter(
                AIAnalysisResult.opportunity_id == opportunity.id,
                AIAnalysisResult.analysis_type == "sow_draft",
                AIAnalysisResult.status == "completed"
            ).order_by(AIAnalysisResult.created_at.desc()).limit(1).all()
            
            # Combine SOW and Hotel Match data
            analysis_json = summary.copy()  # Start with hotel match summary
            if sow_results:
                sow_result = sow_results[0]
                if sow_result.result_json:
                    sow_data = sow_result.result_json if isinstance(sow_result.result_json, dict) else json.loads(sow_result.result_json) if sow_result.result_json else {}
                    # Add SOW analysis to email
                    analysis_json['sow_analysis'] = sow_data.get('sow_analysis', {})
            
            mail_package = build_mail_package(
                opportunity_code=notice_id,
                folder_path=str(output_dir),
                to_email=settings.pipeline_notification_email,
                from_email=settings.smtp_from_email,
                analysis_result_json=analysis_json,
            )
            
            # Add attachments
            attachments = mail_package.get('attachments', [])
            
            # Add SOW PDF and JSON if available
            if sow_results:
                sow_result = sow_results[0]
                if sow_result.pdf_path and Path(sow_result.pdf_path).exists():
                    attachments.append({
                        'path': sow_result.pdf_path,
                        'filename': f"sow_analysis_{sow_result.id}.pdf",
                        'mime_type': 'application/pdf'
                    })
                if sow_result.json_path and Path(sow_result.json_path).exists():
                    attachments.append({
                        'path': sow_result.json_path,
                        'filename': f"sow_analysis_{sow_result.id}.json",
                        'mime_type': 'application/json'
                    })
            
            # Add Hotel Match PDF and JSON
            if result.pdf_path and Path(result.pdf_path).exists():
                attachments.append({
                    'path': result.pdf_path,
                    'filename': f"hotel_suggestions_{result.id}.pdf",
                    'mime_type': 'application/pdf'
                })
            if result.json_path and Path(result.json_path).exists():
                attachments.append({
                    'path': result.json_path,
                    'filename': f"hotel_match_{result.id}.json",
                    'mime_type': 'application/json'
                })
            
            mail_package['attachments'] = attachments
            
            # SMTP config
            smtp_config = {
                'host': settings.smtp_host,
                'port': settings.smtp_port,
                'username': settings.smtp_username,
                'password': settings.smtp_password,
                'use_tls': settings.smtp_use_tls,
            }
            
            # Send email
            if send_email_via_smtp(mail_package, smtp_config):
                _log_analysis(
                    db,
                    result.id,
                    "INFO",
                    f"Email notification sent successfully to {settings.pipeline_notification_email}",
                    step="email",
                    agent_run_id=agent_run_id,
                )
                logger.info(f"[Pipeline {result.id}] Email notification sent successfully")
            else:
                _log_analysis(
                    db,
                    result.id,
                    "WARNING",
                    f"Failed to send email notification to {settings.pipeline_notification_email}",
                    step="email",
                    agent_run_id=agent_run_id,
                )
                logger.warning(f"[Pipeline {result.id}] Failed to send email notification")
        else:
            logger.info(f"[Pipeline {result.id}] Email notification not configured (missing SMTP settings or notification email)")
    except Exception as email_exc:
        logger.warning(f"[Pipeline {result.id}] Email notification failed: {email_exc}", exc_info=True)
        _log_analysis(
            db,
            result.id,
            "WARNING",
            f"Email notification failed: {email_exc}",
            step="email",
            agent_run_id=agent_run_id,
        )
