"""
Pipeline service utilities.
Simulates AutoGen workflow, writes logs/results, and stores output artifacts.
"""
import json
import os
import logging
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

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


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
    session = SessionLocal()
    try:
        result = session.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
        if not result:
            logger.error("Analysis result %s not found", analysis_result_id)
            return

        opportunity = session.query(Opportunity).filter(Opportunity.id == result.opportunity_id).first()
        if not opportunity:
            _log_analysis(session, analysis_result_id, "ERROR", "Opportunity not found", step="init")
            result.status = "failed"
            result.result_json = {"error": "Opportunity not found"}
            session.commit()
            return

        attachment_ids: Optional[List[int]] = payload.get("attachment_ids")
        options: Dict[str, Any] = payload.get("options") or {}
        agent_run_id = payload.get("agent_run_id")

        if result.analysis_type == "hotel_match":
            _execute_hotel_match(session, result, opportunity, options, agent_run_id)
            return

        result.status = "running"
        result.updated_at = datetime.utcnow()
        session.commit()

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
                import json
                
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

        if not attachments:
            _log_analysis(session, analysis_result_id, "WARNING", "No attachments found; continuing with metadata only", step="prepare")

        attachment_details = []
        analyzed_documents = []
        
        # Download any attachments that are not downloaded yet
        attachments_to_download = [att for att in attachments if not att.downloaded or not att.local_path]
        if attachments_to_download:
            _log_analysis(
                session,
                analysis_result_id,
                "INFO",
                f"Downloading {len(attachments_to_download)} attachment(s) that are not yet downloaded",
                step="prepare",
                agent_run_id=agent_run_id,
            )
            
            # Download attachments synchronously
            import httpx
            import asyncio
            from datetime import datetime
            
            notice_id = opportunity.notice_id or str(opportunity.id)
            opp_dir = Path(os.getenv("DATA_DIR", "data")) / "opportunities" / notice_id / "attachments"
            opp_dir.mkdir(parents=True, exist_ok=True)
            
            async def download_single_attachment(att):
                """Download a single attachment"""
                try:
                    if not att.source_url:
                        return False
                    
                    # Generate safe filename
                    filename = att.name.replace("/", "_").replace("\\", "_")
                    filename = Path(filename).name
                    
                    # If no extension, try to guess from URL
                    if not Path(filename).suffix and att.mime_type:
                        ext_map = {
                            "application/pdf": ".pdf",
                            "application/msword": ".doc",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                            "application/vnd.ms-excel": ".xls",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                        }
                        ext = ext_map.get(att.mime_type, "")
                        if ext:
                            filename = filename + ext
                    
                    local_path = opp_dir / filename
                    
                    # Skip if already exists
                    if local_path.exists():
                        att.local_path = str(local_path)
                        att.downloaded = True
                        att.size_bytes = local_path.stat().st_size
                        att.downloaded_at = datetime.now()
                        session.commit()
                        return True
                    
                    # Download file
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.get(att.source_url)
                        response.raise_for_status()
                        
                        # Save to disk
                        with open(local_path, "wb") as f:
                            f.write(response.content)
                        
                        # Update attachment record
                        att.local_path = str(local_path)
                        att.downloaded = True
                        att.size_bytes = len(response.content)
                        att.downloaded_at = datetime.now()
                        
                        # Update mime_type if not set
                        if not att.mime_type and response.headers.get("content-type"):
                            att.mime_type = response.headers.get("content-type").split(";")[0]
                        
                        session.commit()
                        session.refresh(att)
                        
                        _log_analysis(
                            session,
                            analysis_result_id,
                            "INFO",
                            f"Downloaded {att.name} ({att.size_bytes} bytes)",
                            step="download",
                            agent_run_id=agent_run_id,
                        )
                        return True
                except Exception as e:
                    logger.error(f"Error downloading attachment {att.name}: {e}", exc_info=True)
                    _log_analysis(
                        session,
                        analysis_result_id,
                        "ERROR",
                        f"Failed to download {att.name}: {e}",
                        step="download",
                        agent_run_id=agent_run_id,
                    )
                    return False
            
            # Download all attachments in parallel
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            download_tasks = [download_single_attachment(att) for att in attachments_to_download]
            download_results = loop.run_until_complete(asyncio.gather(*download_tasks))
            
            downloaded_count = sum(1 for r in download_results if r)
            _log_analysis(
                session,
                analysis_result_id,
                "INFO",
                f"Downloaded {downloaded_count}/{len(attachments_to_download)} attachment(s)",
                step="download",
                agent_run_id=agent_run_id,
            )
            
            # Refresh attachments from DB
            session.refresh_all()
        
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
            
            if not att.downloaded or not att.local_path:
                _log_analysis(
                    session,
                    analysis_result_id,
                    "WARNING",
                    f"Attachment {att.name} is not downloaded locally",
                    step="prepare",
                    agent_run_id=agent_run_id,
                )
                continue
            
            # Check if file exists
            local_path_obj = Path(att.local_path)
            if not local_path_obj.exists():
                _log_analysis(
                    session,
                    analysis_result_id,
                    "WARNING",
                    f"Document file not found: {att.local_path}",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                continue
            
            # Analyze downloaded document
            try:
                _log_analysis(
                    session,
                    analysis_result_id,
                    "INFO",
                    f"Analyzing document: {att.name}",
                    step="analyze",
                    agent_run_id=agent_run_id,
                )
                
                analysis_result = analyze_document(att.local_path, att.mime_type)
                analysis_result["attachment_id"] = att.id
                analysis_result["attachment_name"] = att.name
                analyzed_documents.append(analysis_result)
                
                # Log analysis results
                text_len = analysis_result.get("text_length", 0)
                word_count = analysis_result.get("word_count", 0)
                error = analysis_result.get("error")
                
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
        all_extracted_text = "\n\n".join([
            doc.get("extracted_text", "") 
            for doc in analyzed_documents 
            if doc.get("extracted_text")
        ])
        
        # Extract key information from documents
        total_text_length = sum(doc.get("text_length", 0) for doc in analyzed_documents)
        total_word_count = sum(doc.get("word_count", 0) for doc in analyzed_documents)
        total_tables = sum(len(doc.get("tables", [])) for doc in analyzed_documents)
        
        # Use AutoGen SOW Analyzer if we have document text and analysis_type is sow_draft
        sow_analysis = None
        if result.analysis_type == "sow_draft" and all_extracted_text:
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
                sow_analysis = analyze_sow_document(all_extracted_text, llm_model=llm_model)
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
            "notes": f"Analyzed {len(analyzed_documents)} documents. Total: {total_word_count} words, {total_tables} tables extracted." + (f" AutoGen SOW analysis completed." if sow_analysis else " Basic extraction only.") if analyzed_documents else "No documents analyzed. Placeholder output.",
        }

        # Persist summary to disk
        notice_slug = opportunity.notice_id or f"opp-{opportunity.id}"
        output_dir = DATA_DIR / "opportunities" / notice_slug / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f"analysis_{analysis_result_id}.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

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
                event_details = sow_analysis.get("event_details", {})
                location = event_details.get("location") or sow_analysis.get("location")
                start_date = event_details.get("start_date") or sow_analysis.get("dates", {}).get("start")
                end_date = event_details.get("end_date") or sow_analysis.get("dates", {}).get("end")
                
                # Extract attendees from sleeping rooms or function space
                sleeping_rooms = sow_analysis.get("sleeping_rooms", [])
                attendees = 10  # Default
                if sleeping_rooms:
                    # Try to get max rooms per night
                    max_rooms = max([r.get("rooms_per_night", 0) for r in sleeping_rooms if isinstance(r, dict)], default=0)
                    if max_rooms > 0:
                        attendees = max_rooms * 2  # Estimate 2 people per room
                
                # Build hotel match options from SOW analysis
                hotel_options = {}
                if location:
                    hotel_options["city_name"] = location
                if start_date:
                    hotel_options["check_in"] = start_date
                if end_date:
                    hotel_options["check_out"] = end_date
                if attendees:
                    hotel_options["adults"] = attendees
                
                # Only trigger if we have minimum required info (location and dates)
                if location and start_date and end_date:
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
                        f"Insufficient data for auto hotel match (location: {location}, dates: {start_date} to {end_date})",
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
        logger.exception("Pipeline job %s failed", analysis_result_id)
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
    try:
        requirements = build_hotel_match_requirements(opportunity, options)
    except ValueError as exc:
        result.status = "failed"
        result.result_json = {"error": str(exc)}
        result.completed_at = datetime.utcnow()
        db.commit()
        _log_analysis(db, result.id, "ERROR", f"Hotel match requirements missing: {exc}", step="prepare", agent_run_id=agent_run_id)
        return

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
            agent_output = run_hotel_match_for_opportunity(requirements, decision_hint=decision_hint)
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
    
    # Generate PDF for hotel match results
    notice_slug = opportunity.notice_id or f"opp-{opportunity.id}"
    output_dir = DATA_DIR / "opportunities" / notice_slug / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"hotel_match_{result.id}.pdf"
    opp_dict = {
        "id": opportunity.id,
        "notice_id": opportunity.notice_id,
        "title": opportunity.title,
        "agency": opportunity.agency,
    }
    pdf_generated = generate_analysis_pdf(pdf_path, summary, opp_dict)
    if pdf_generated:
        result.pdf_path = str(pdf_path)
        _log_analysis(db, result.id, "INFO", f"PDF generated: {pdf_path}", step="generate", agent_run_id=agent_run_id)
    
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
