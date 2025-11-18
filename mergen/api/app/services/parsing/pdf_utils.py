import pdfplumber
import camelot
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""


def extract_tables_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract tables from PDF file using Camelot"""
    try:
        tables = camelot.read_pdf(file_path, pages='all')
        extracted_tables = []
        
        for i, table in enumerate(tables):
            extracted_tables.append({
                "table_id": i,
                "df": table.df.to_dict('records'),
                "accuracy": table.accuracy,
                "page": table.page
            })
        
        return extracted_tables
    except Exception as e:
        logger.error(f"Error extracting tables from PDF {file_path}: {e}")
        return []


def extract_metadata_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract metadata from PDF file"""
    try:
        with pdfplumber.open(file_path) as pdf:
            metadata = {
                "num_pages": len(pdf.pages),
                "title": pdf.metadata.get("Title", ""),
                "author": pdf.metadata.get("Author", ""),
                "subject": pdf.metadata.get("Subject", ""),
                "creator": pdf.metadata.get("Creator", ""),
                "producer": pdf.metadata.get("Producer", ""),
                "creation_date": str(pdf.metadata.get("CreationDate", "")),
                "modification_date": str(pdf.metadata.get("ModDate", ""))
            }
        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata from PDF {file_path}: {e}")
        return {}


def process_pdf(document_id: int, file_path: str, document_type: str):
    """Process PDF file and extract content"""
    logger.info(f"Processing PDF {file_path} as {document_type}")
    
    # Extract text
    text = extract_text_from_pdf(file_path)
    
    # Extract tables
    tables = extract_tables_from_pdf(file_path)
    
    # Extract metadata
    metadata = extract_metadata_from_pdf(file_path)
    
    # TODO: Store extracted content in database
    # This would involve creating VectorChunk records
    # and calling appropriate extractors based on document_type
    
    logger.info(f"Successfully processed PDF {file_path}")
    
    return {
        "document_id": document_id,
        "text_length": len(text),
        "tables_count": len(tables),
        "metadata": metadata
    }



