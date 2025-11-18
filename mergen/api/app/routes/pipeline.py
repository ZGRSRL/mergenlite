"""
Pipeline API Routes
Manages AutoGen-style analysis jobs, background processing, and artifact serving.
"""
from pathlib import Path
from typing import List
import os
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from typing import Optional
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from ..db import get_db
from ..models import AIAnalysisResult, AnalysisLog, Opportunity, AgentRun, AgentMessage, LLMCall
from ..schemas import (
    PipelineRunRequest,
    PipelineRunResponse,
    AnalysisResultRead,
    AnalysisLogRead,
)
from ..services.pipeline_service import create_pipeline_job, run_pipeline_job

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a pipeline job for the specified opportunity.
    Returns analysis_result_id so the client can poll for status/logs.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == request.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    analysis_result, agent_run_id = create_pipeline_job(
        db=db,
        opportunity_id=opportunity.id,
        analysis_type=request.analysis_type or "sow_draft",
        pipeline_version=request.pipeline_version or "v1",
        agent_name=request.agent_name or "autogen",
        initial_options=request.options,
    )

    payload = request.model_dump()
    payload["agent_run_id"] = agent_run_id
    background_tasks.add_task(run_pipeline_job, analysis_result.id, payload)

    return PipelineRunResponse(
        analysis_result_id=analysis_result.id,
        status=analysis_result.status,
        message="Pipeline job started",
    )


@router.get("/results/{analysis_result_id}", response_model=AnalysisResultRead)
async def get_analysis_result(
    analysis_result_id: int,
    db: Session = Depends(get_db),
):
    """Return a single analysis result."""
    result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result


@router.get("/results/{analysis_result_id}/logs", response_model=List[AnalysisLogRead])
async def get_analysis_logs(
    analysis_result_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Max log entries"),
    db: Session = Depends(get_db),
):
    """Return logs for a specific analysis job."""
    logs = (
        db.query(AnalysisLog)
        .filter(AnalysisLog.analysis_result_id == analysis_result_id)
        .order_by(AnalysisLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    if not logs:
        # Ensure the result exists to distinguish "no logs yet" vs invalid id
        exists = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
        if not exists:
            raise HTTPException(status_code=404, detail="Analysis result not found")
    return logs


@router.get("/results", response_model=List[AnalysisResultRead])
async def list_all_analysis_results(
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type"),
    db: Session = Depends(get_db),
):
    """List all analysis results across all opportunities."""
    query = db.query(AIAnalysisResult)
    
    if status:
        query = query.filter(AIAnalysisResult.status == status)
    if analysis_type:
        query = query.filter(AIAnalysisResult.analysis_type == analysis_type)
    
    results = (
        query
        .order_by(AIAnalysisResult.created_at.desc())
        .limit(limit)
        .all()
    )
    return results


@router.get("/opportunity/{opportunity_id}/results", response_model=List[AnalysisResultRead])
async def list_analysis_results_for_opportunity(
    opportunity_id: int,
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    db: Session = Depends(get_db),
):
    """List recent analysis results for a given opportunity."""
    results = (
        db.query(AIAnalysisResult)
        .filter(AIAnalysisResult.opportunity_id == opportunity_id)
        .order_by(AIAnalysisResult.created_at.desc())
        .limit(limit)
        .all()
    )
    return results


@router.get("/results/{analysis_result_id}/download-pdf")
async def download_analysis_pdf(
    analysis_result_id: int,
    db: Session = Depends(get_db),
):
    """
    Download the generated PDF for an analysis result.
    """
    result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    if not result.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated for this analysis")
    
    pdf_path = Path(result.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"analysis_{analysis_result_id}.pdf"
    )


@router.get("/results/{analysis_result_id}/download-json")
async def download_analysis_json(
    analysis_result_id: int,
    db: Session = Depends(get_db),
):
    """
    Download the generated JSON for an analysis result.
    """
    result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Try to find JSON file in outputs directory
    notice_slug = result.opportunity.notice_id if result.opportunity else f"opp-{result.opportunity_id}"
    json_path = DATA_DIR / "opportunities" / notice_slug / "outputs" / f"analysis_{analysis_result_id}.json"
    
    if not json_path.exists():
        # Fallback: return result_json as JSON response
        from fastapi.responses import JSONResponse
        return JSONResponse(content=result.result_json or {})
    
    return FileResponse(
        str(json_path),
        media_type="application/json",
        filename=f"analysis_{analysis_result_id}.json"
    )


@router.get("/files/sow-pdf")
async def get_generated_file(path: str):
    """
    Serve generated artifacts (PDF/JSON/etc.) stored under DATA_DIR.
    The `path` parameter can be absolute or relative; it must resolve under DATA_DIR.
    """
    try:
        candidate = Path(path)
        if not candidate.is_absolute():
            # Try relative to DATA_DIR first
            candidate = (DATA_DIR / candidate).resolve()
            # If that doesn't exist, try relative to cwd
            if not candidate.exists():
                candidate = (Path.cwd() / path).resolve()
        
        data_root = DATA_DIR.resolve()
        # Check if file is within DATA_DIR
        try:
            candidate.relative_to(data_root)
        except ValueError:
            # File is not in DATA_DIR, check if it's a valid absolute path
            if not candidate.exists():
                raise HTTPException(status_code=404, detail="File not found")
            # Allow access if file exists (for backward compatibility)
        
        if not candidate.exists():
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error resolving file path {path}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid file path: {str(e)}")

    media_type = "application/pdf"
    suffix = candidate.suffix.lower()
    if suffix == ".json":
        media_type = "application/json"
    elif suffix == ".md":
        media_type = "text/markdown"
    elif suffix not in {".pdf", ".json", ".md"}:
        media_type = "application/octet-stream"

    return FileResponse(str(candidate), media_type=media_type, filename=candidate.name)


@router.get("/results/{analysis_result_id}/agent-outputs")
async def get_agent_outputs(
    analysis_result_id: int,
    db: Session = Depends(get_db),
):
    """
    Get agent run outputs (messages and LLM calls) for an analysis result.
    """
    result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == analysis_result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    # Find agent run associated with this analysis
    agent_runs = (
        db.query(AgentRun)
        .filter(AgentRun.opportunity_id == result.opportunity_id)
        .order_by(AgentRun.started_at.desc())
        .limit(5)
        .all()
    )
    
    outputs = []
    for run in agent_runs:
        # Get messages for this run
        messages = (
            db.query(AgentMessage)
            .filter(AgentMessage.agent_run_id == run.id)
            .order_by(AgentMessage.created_at.asc())
            .all()
        )
        
        # Get LLM calls for this run
        llm_calls = (
            db.query(LLMCall)
            .filter(LLMCall.agent_run_id == run.id)
            .order_by(LLMCall.created_at.asc())
            .all()
        )
        
        outputs.append({
            "agent_run": {
                "id": run.id,
                "run_type": run.run_type,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "error_message": run.error_message,
                "extra_metadata": run.extra_metadata,
            },
            "messages": [
                {
                    "id": msg.id,
                    "agent_name": msg.agent_name,
                    "role": msg.role,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "meta": msg.meta,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in messages
            ],
            "llm_calls": [
                {
                    "id": call.id,
                    "agent_name": call.agent_name,
                    "provider": call.provider,
                    "model": call.model,
                    "prompt": call.prompt,
                    "response": call.response,
                    "prompt_tokens": call.prompt_tokens,
                    "completion_tokens": call.completion_tokens,
                    "total_tokens": call.total_tokens,
                    "latency_ms": call.latency_ms,
                    "created_at": call.created_at.isoformat() if call.created_at else None,
                }
                for call in llm_calls
            ],
        })
    
    return {"agent_outputs": outputs, "total_runs": len(outputs)}


@router.get("/agent-runs/{agent_run_id}/messages")
async def get_agent_run_messages(
    agent_run_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get all messages for a specific agent run.
    """
    run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    
    messages = (
        db.query(AgentMessage)
        .filter(AgentMessage.agent_run_id == agent_run_id)
        .order_by(AgentMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    
    return {
        "agent_run_id": agent_run_id,
        "run_type": run.run_type,
        "status": run.status,
        "messages": [
            {
                "id": msg.id,
                "agent_name": msg.agent_name,
                "role": msg.role,
                "message_type": msg.message_type,
                "content": msg.content,
                "meta": msg.meta,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


@router.get("/agent-runs/{agent_run_id}/llm-calls")
async def get_agent_run_llm_calls(
    agent_run_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get all LLM calls for a specific agent run.
    """
    run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    
    llm_calls = (
        db.query(LLMCall)
        .filter(LLMCall.agent_run_id == agent_run_id)
        .order_by(LLMCall.created_at.asc())
        .limit(limit)
        .all()
    )
    
    return {
        "agent_run_id": agent_run_id,
        "run_type": run.run_type,
        "status": run.status,
        "llm_calls": [
            {
                "id": call.id,
                "agent_name": call.agent_name,
                "provider": call.provider,
                "model": call.model,
                "prompt": call.prompt,
                "response": call.response,
                "prompt_tokens": call.prompt_tokens,
                "completion_tokens": call.completion_tokens,
                "total_tokens": call.total_tokens,
                "latency_ms": call.latency_ms,
                "created_at": call.created_at.isoformat() if call.created_at else None,
            }
            for call in llm_calls
        ],
    }


@router.get("/files/list")
async def list_generated_files():
    """
    List generated SOW/analysis files saved under DATA_DIR/opportunities/**/outputs.
    Returns metadata for React UI to display download options.
    """
    if not DATA_DIR.exists():
        return {"files": []}

    files = []
    opportunities_dir = DATA_DIR / "opportunities"
    if not opportunities_dir.exists():
        return {"files": []}

    for opp_dir in opportunities_dir.iterdir():
        outputs_dir = opp_dir / "outputs"
        if not outputs_dir.exists():
            continue
        for artifact in outputs_dir.glob("*"):
            if not artifact.is_file():
                continue
            try:
                stat = artifact.stat()
                # Use relative path from DATA_DIR, not from cwd
                try:
                    rel_path = artifact.relative_to(DATA_DIR)
                except ValueError:
                    # If relative_to fails, use absolute path
                    rel_path = Path(artifact)
                
                files.append(
                    {
                        "filename": artifact.name,
                        "path": str(rel_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "notice_id": opp_dir.name,
                    }
                )
            except (OSError, ValueError) as e:
                # Skip files that can't be accessed
                logger.warning(f"Error accessing file {artifact}: {e}")
                continue

    files.sort(key=lambda item: item["modified"], reverse=True)
    return {"files": files}
