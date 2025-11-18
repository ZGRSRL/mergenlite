"""
Document analysis utilities for PDF and DOCX files.
Extracts text, tables, and metadata from downloaded attachments.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from ..parsing.pdf_utils import extract_text_from_pdf, extract_tables_from_pdf, extract_metadata_from_pdf
    PDF_UTILS_AVAILABLE = True
except ImportError:
    PDF_UTILS_AVAILABLE = False
    logger.warning("PDF utils not available")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = DocxDocument(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return ""


def analyze_document(file_path: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a document (PDF or DOCX) and extract content.
    
    Args:
        file_path: Path to the document file
        mime_type: Optional MIME type hint
        
    Returns:
        Dict with extracted_text, tables, metadata, document_type
    """
    if not Path(file_path).exists():
        logger.warning(f"Document file not found: {file_path}")
        return {
            "extracted_text": "",
            "tables": [],
            "metadata": {},
            "document_type": "unknown",
            "error": "File not found"
        }
    
    file_ext = Path(file_path).suffix.lower()
    result = {
        "extracted_text": "",
        "tables": [],
        "metadata": {},
        "document_type": "unknown",
        "file_path": file_path,
        "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0
    }
    
    # Determine document type
    if file_ext == ".pdf" or (mime_type and "pdf" in mime_type.lower()):
        result["document_type"] = "pdf"
        if PDF_UTILS_AVAILABLE:
            try:
                result["extracted_text"] = extract_text_from_pdf(file_path)
                result["tables"] = extract_tables_from_pdf(file_path)
                result["metadata"] = extract_metadata_from_pdf(file_path)
            except Exception as e:
                logger.error(f"Error analyzing PDF {file_path}: {e}")
                result["error"] = str(e)
    
    elif file_ext in [".docx", ".doc"] or (mime_type and "word" in mime_type.lower()):
        result["document_type"] = "docx"
        if DOCX_AVAILABLE:
            try:
                result["extracted_text"] = extract_text_from_docx(file_path)
                result["metadata"] = {
                    "num_paragraphs": len(result["extracted_text"].split("\n")) if result["extracted_text"] else 0
                }
            except Exception as e:
                logger.error(f"Error analyzing DOCX {file_path}: {e}")
                result["error"] = str(e)
    
    else:
        result["document_type"] = "unknown"
        result["error"] = f"Unsupported file type: {file_ext}"
    
    # Add text statistics
    if result["extracted_text"]:
        result["text_length"] = len(result["extracted_text"])
        result["word_count"] = len(result["extracted_text"].split())
        result["line_count"] = len(result["extracted_text"].split("\n"))
    else:
        result["text_length"] = 0
        result["word_count"] = 0
        result["line_count"] = 0
    
    return result

