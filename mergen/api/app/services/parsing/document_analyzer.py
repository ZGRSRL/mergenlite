"""
Document analysis utilities for PDF and DOCX files.
Extracts text, tables, and metadata from downloaded attachments.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from .pdf_utils import extract_text_from_pdf, extract_tables_from_pdf, extract_metadata_from_pdf
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

try:
    import pandas as pd
    import openpyxl  # For Excel support
    CSV_EXCEL_AVAILABLE = True
except ImportError:
    CSV_EXCEL_AVAILABLE = False
    logger.warning("pandas/openpyxl not available - CSV/Excel files will not be processed")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    if not DOCX_AVAILABLE:
        return ""
    try:
        # Check if file is actually a DOCX (not Excel/XML)
        # Excel files saved as DOCX usually raise ValueError or KeyError
        try:
            doc = DocxDocument(file_path)
        except (ValueError, KeyError) as e:
            # Excel dosyası DOCX diye kaydedilmişse genelde ValueError veya KeyError verir
            logger.warning(f"Skipping file {file_path}: Not a valid DOCX file (might be Excel/XML). Error: {e}")
            return ""
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return ""


def extract_text_from_csv_excel(file_path: str) -> str:
    """
    Extract text from CSV or Excel file using pandas.
    Converts to Markdown table format for better LLM understanding.
    """
    if not CSV_EXCEL_AVAILABLE:
        return ""
    
    try:
        file_ext = Path(file_path).suffix.lower()
        file_name = Path(file_path).name
        text_parts = []
        
        if file_ext == ".csv":
            # Read CSV
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            # Clean empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if not df.empty:
                text_parts.append(f"--- CSV FILE CONTENT ({file_name}) ---\n")
                # Convert to Markdown table (LLM-friendly format)
                try:
                    # Try markdown format first (better for LLM)
                    # Requires tabulate package
                    text_parts.append(df.to_markdown(index=False))
                except (AttributeError, ImportError):
                    # Fallback to string if to_markdown not available
                    text_parts.append(df.to_string(index=False))
                text_parts.append("\n")
                
        elif file_ext in [".xlsx", ".xls"]:
            # Read Excel - try all sheets
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            text_parts.append(f"--- EXCEL FILE CONTENT ({file_name}) ---\n")
            
            for sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # Clean empty rows and columns
                df = df.dropna(how='all').dropna(axis=1, how='all')
                
                if not df.empty:
                    text_parts.append(f"\n--- Sheet: {sheet_name} ---\n")
                    # Convert to Markdown table (LLM-friendly format)
                    try:
                        # Try markdown format first (better for LLM)
                        text_parts.append(df.to_markdown(index=False))
                    except AttributeError:
                        # Fallback to string if to_markdown not available
                        text_parts.append(df.to_string(index=False))
                    text_parts.append("\n")
        else:
            logger.warning(f"Unsupported file type for CSV/Excel extraction: {file_ext}")
            return ""
        
        if text_parts:
            return "\n".join(text_parts)
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting text from CSV/Excel {file_path}: {e}", exc_info=True)
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
                logger.info(f"Extracting text from PDF: {file_path} (size: {result['file_size']} bytes)")
                extracted = extract_text_from_pdf(file_path)
                result["extracted_text"] = extracted
                
                # DEBUG: Log extraction result
                if len(extracted) < 100:
                    logger.warning(f"CRITICAL: PDF extraction returned only {len(extracted)} chars from {file_path}")
                    logger.warning(f"Extracted content: {repr(extracted[:200])}")
                else:
                    logger.info(f"Successfully extracted {len(extracted)} chars from PDF")
                
                result["tables"] = extract_tables_from_pdf(file_path)
                result["metadata"] = extract_metadata_from_pdf(file_path)
            except Exception as e:
                logger.error(f"Error analyzing PDF {file_path}: {e}", exc_info=True)
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
    
    elif file_ext in [".csv", ".xlsx", ".xls"] or (mime_type and ("csv" in mime_type.lower() or "excel" in mime_type.lower() or "spreadsheet" in mime_type.lower())):
        result["document_type"] = "csv_excel"
        if CSV_EXCEL_AVAILABLE:
            try:
                logger.info(f"Extracting text from CSV/Excel: {file_path}")
                extracted = extract_text_from_csv_excel(file_path)
                result["extracted_text"] = extracted
                result["metadata"] = {
                    "file_type": "csv" if file_ext == ".csv" else "excel",
                    "num_rows": len(extracted.split("\n")) if extracted else 0
                }
                # CSV/Excel files are essentially tables, so mark as table
                if extracted:
                    # Try to parse as table structure
                    lines = extracted.split("\n")
                    if lines:
                        # First line is usually header
                        result["tables"] = [[line.split()] for line in lines[:20]]  # Limit to first 20 rows
            except Exception as e:
                logger.error(f"Error analyzing CSV/Excel {file_path}: {e}", exc_info=True)
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

