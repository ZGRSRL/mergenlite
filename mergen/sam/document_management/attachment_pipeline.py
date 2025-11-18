"""
Attachment Pipeline - Document Processing and Chunking
Extracts text, tables, and metadata from PDF/DOCX/XLSX files
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import hashlib

# Document processing libraries
try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pypdf not available, PDF processing disabled")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, DOCX processing disabled")

try:
    import pandas as pd
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False
    logger.warning("pandas not available, XLSX processing disabled")

logger = logging.getLogger(__name__)

class AttachmentPipeline:
    """Document processing and chunking pipeline"""
    
    def __init__(self):
        self.chunk_size = 1200  # characters
        self.chunk_overlap = 120  # characters
        self.max_tokens = 4000  # tokens per chunk
        
        logger.info("Attachment Pipeline initialized")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract text chunks"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            # Determine file type
            file_type = self._get_file_type(file_path)
            
            # Extract text based on file type
            if file_type == 'pdf':
                text = self._extract_pdf_text(file_path)
            elif file_type == 'docx':
                text = self._extract_docx_text(file_path)
            elif file_type == 'xlsx':
                text = self._extract_xlsx_text(file_path)
            else:
                return {'success': False, 'error': f'Unsupported file type: {file_type}'}
            
            if not text:
                return {'success': False, 'error': 'No text extracted'}
            
            # Create chunks
            chunks = list(self._create_chunks(text))
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, text)
            
            return {
                'success': True,
                'file_path': str(file_path),
                'file_type': file_type,
                'text': text,
                'chunks': chunks,
                'metadata': metadata,
                'chunk_count': len(chunks),
                'total_characters': len(text),
                'processed_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Process document failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension"""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.doc', '.docx']:
            return 'docx'
        elif ext in ['.xls', '.xlsx']:
            return 'xlsx'
        else:
            return 'unknown'
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF"""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf not available")
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available")
        
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            return ""
    
    def _extract_xlsx_text(self, file_path: Path) -> str:
        """Extract text from XLSX"""
        if not XLSX_AVAILABLE:
            raise ImportError("pandas not available")
        
        try:
            text = ""
            
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                text += f"\n--- Sheet: {sheet_name} ---\n"
                
                # Convert DataFrame to text
                for index, row in df.iterrows():
                    row_text = " | ".join([str(cell) for cell in row if pd.notna(cell)])
                    if row_text.strip():
                        text += row_text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"XLSX text extraction failed: {e}")
            return ""
    
    def _create_chunks(self, text: str) -> Generator[Dict[str, Any], None, None]:
        """Create overlapping text chunks"""
        if not text:
            return
        
        # Simple chunking by character count
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    'chunk_idx': chunk_idx,
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end,
                    'char_count': len(chunk_text),
                    'token_estimate': len(chunk_text.split()) * 1.3  # Rough token estimate
                }
                
                yield chunk
                chunk_idx += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
    
    def _extract_metadata(self, file_path: Path, text: str) -> Dict[str, Any]:
        """Extract document metadata"""
        try:
            stat = file_path.stat()
            
            metadata = {
                'filename': file_path.name,
                'file_size': stat.st_size,
                'file_hash': self._calculate_file_hash(file_path),
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'word_count': len(text.split()),
                'character_count': len(text),
                'line_count': len(text.split('\n'))
            }
            
            # Extract key information from text
            metadata.update(self._extract_key_info(text))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return ""
    
    def _extract_key_info(self, text: str) -> Dict[str, Any]:
        """Extract key information from text"""
        try:
            key_info = {
                'has_deadline': any(word in text.lower() for word in ['deadline', 'due date', 'submission date']),
                'has_requirements': any(word in text.lower() for word in ['requirement', 'mandatory', 'must']),
                'has_evaluation': any(word in text.lower() for word in ['evaluation', 'criteria', 'scoring']),
                'has_scope': any(word in text.lower() for word in ['scope', 'work', 'deliverable']),
                'language': 'english'  # Default, could be enhanced
            }
            
            # Extract potential dates
            import re
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            dates = re.findall(date_pattern, text)
            key_info['extracted_dates'] = dates
            
            # Extract potential dollar amounts
            money_pattern = r'\$[\d,]+(?:\.\d{2})?'
            amounts = re.findall(money_pattern, text)
            key_info['extracted_amounts'] = amounts
            
            return key_info
            
        except Exception as e:
            logger.error(f"Key info extraction failed: {e}")
            return {}

# Global instance
pipeline = AttachmentPipeline()

def process_document(file_path: str) -> Dict[str, Any]:
    """Process a document and extract text chunks"""
    return pipeline.process_document(file_path)

def create_chunks(text: str) -> List[Dict[str, Any]]:
    """Create chunks from text"""
    return list(pipeline._create_chunks(text))

if __name__ == "__main__":
    # Test the pipeline
    print("Attachment Pipeline Test")
    
    # Test with a sample file (if exists)
    test_file = "test_document.pdf"
    if os.path.exists(test_file):
        result = process_document(test_file)
        print(f"Processing result: {result}")
    else:
        print("No test file found")

