#!/usr/bin/env python3
"""
Doküman İşleme Modülü
PDF, DOCX, DOC dosyalarından metin çıkarımı
"""

import io
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfplumber not available, PDF processing will be limited")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, DOCX processing will be limited")

class DocumentProcessor:
    """Doküman işleme servisi"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'docx', 'doc']
    
    def process_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """Yüklenen dosyayı işle"""
        
        try:
            file_extension = Path(uploaded_file.name).suffix.lower().replace('.', '')
            
            if file_extension not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Desteklenmeyen dosya formatı: {file_extension}'
                }
            
            # Dosya içeriğini oku
            file_content = uploaded_file.read()
            
            if file_extension == 'pdf':
                return self._process_pdf(file_content, uploaded_file.name)
            elif file_extension in ['docx', 'doc']:
                return self._process_docx(file_content, uploaded_file.name)
            else:
                return {
                    'success': False,
                    'error': f'Dosya formatı işlenemedi: {file_extension}'
                }
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """PDF dosyasını işle"""
        
        if not PDF_AVAILABLE:
            return {
                'success': False,
                'error': 'PDF işleme kütüphanesi yüklü değil. pip install pdfplumber'
            }
        
        try:
            # BytesIO kullanarak pdfplumber ile aç
            pdf_file = io.BytesIO(file_content)
            
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                page_count = len(pdf.pages)
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # Metadata
                metadata = pdf.metadata or {}
                
                return {
                    'success': True,
                    'data': {
                        'filename': filename,
                        'text': text,
                        'page_count': page_count,
                        'file_type': 'pdf',
                        'metadata': {
                            'title': metadata.get('Title', ''),
                            'author': metadata.get('Author', ''),
                            'subject': metadata.get('Subject', '')
                        }
                    }
                }
        
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                'success': False,
                'error': f'PDF işleme hatası: {str(e)}'
            }
    
    def _process_docx(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """DOCX dosyasını işle"""
        
        if not DOCX_AVAILABLE:
            return {
                'success': False,
                'error': 'DOCX işleme kütüphanesi yüklü değil. pip install python-docx'
            }
        
        try:
            # BytesIO kullanarak docx ile aç
            docx_file = io.BytesIO(file_content)
            doc = DocxDocument(docx_file)
            
            # Tüm paragraflardan metin çıkar
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # Tablolardan metin çıkar
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text for cell in row.cells])
                    text += "\n" + row_text
            
            return {
                'success': True,
                'data': {
                    'filename': filename,
                    'text': text,
                    'page_count': 1,  # DOCX için sayfa sayısı belirsiz
                    'file_type': 'docx',
                    'metadata': {}
                }
            }
        
        except Exception as e:
            logger.error(f"Error processing DOCX: {e}")
            return {
                'success': False,
                'error': f'DOCX işleme hatası: {str(e)}'
            }
    
    def process_file_from_path(self, file_path: str) -> Dict[str, Any]:
        """Dosya yolundan işle"""
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    'success': False,
                    'error': f'Dosya bulunamadı: {file_path}'
                }
            
            file_extension = path.suffix.lower().replace('.', '')
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            if file_extension == 'pdf':
                return self._process_pdf(file_content, path.name)
            elif file_extension in ['docx', 'doc']:
                return self._process_docx(file_content, path.name)
            else:
                return {
                    'success': False,
                    'error': f'Desteklenmeyen dosya formatı: {file_extension}'
                }
        
        except Exception as e:
            logger.error(f"Error processing file from path: {e}")
            return {
                'success': False,
                'error': str(e)
            }

