from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from ..db import get_db
from ..models import Document
from ..schemas import Document as DocumentSchema
from ..services.parsing.pdf_utils import process_pdf
from ..services.parsing.excel_reader import process_excel

router = APIRouter()


@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    kind: str = "unknown",
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    document = Document(
        kind=kind,
        title=file.filename,
        path=file_path,
        meta_json={"original_filename": file.filename}
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document in background
    if kind in ["rfq", "sow", "facility", "past_performance"]:
        background_tasks.add_task(process_pdf, document.id, file_path, kind)
    elif kind == "pricing":
        background_tasks.add_task(process_excel, document.id, file_path)
    
    return document


@router.post("/local")
async def process_local_files(db: Session = Depends(get_db)):
    """Process files from samples directory"""
    samples_dir = "samples"
    
    if not os.path.exists(samples_dir):
        raise HTTPException(status_code=404, detail="Samples directory not found")
    
    processed_files = []
    
    for filename in os.listdir(samples_dir):
        file_path = os.path.join(samples_dir, filename)
        
        if os.path.isfile(file_path):
            # Determine file type
            if filename.endswith('.pdf'):
                if 'rfq' in filename.lower():
                    kind = "rfq"
                elif 'sow' in filename.lower():
                    kind = "sow"
                elif 'facility' in filename.lower() or 'technical' in filename.lower():
                    kind = "facility"
                elif 'performance' in filename.lower():
                    kind = "past_performance"
                else:
                    kind = "unknown"
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                kind = "pricing"
            else:
                continue
            
            # Create document record
            document = Document(
                kind=kind,
                title=filename,
                path=file_path,
                meta_json={"source": "local_samples"}
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            
            processed_files.append({
                "id": document.id,
                "filename": filename,
                "kind": kind,
                "path": file_path
            })
    
    return {
        "message": f"Processed {len(processed_files)} files from samples directory",
        "files": processed_files
    }

