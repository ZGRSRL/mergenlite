import pdfplumber
import camelot
from typing import List, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import OCR libraries
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR libraries not available (pytesseract, pdf2image). Scanned PDFs may not be processed correctly.")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not available. Falling back to pdfplumber only.")


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file with table extraction support.
    Tries multiple methods:
    1. pdfplumber (for text-based PDFs + tables) - BEST for SOW documents
    2. PyMuPDF (fitz) - better for some PDFs
    3. OCR (for scanned/image-based PDFs)
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"PDF file not found: {file_path}")
        return ""
    
    text = ""
    
    # Method 1: Try pdfplumber first (BEST for SOW documents - handles tables well)
    try:
        with pdfplumber.open(file_path) as pdf:
            logger.info(f"Extracting text from PDF: {file_path} ({len(pdf.pages)} pages)")
            
            for i, page in enumerate(pdf.pages):
                # Extract regular text - try multiple extraction methods
                page_text = page.extract_text()
                
                # If extract_text() returns little/nothing, try alternative methods
                if not page_text or len(page_text.strip()) < 10:
                    # Try extracting words directly
                    try:
                        words = page.extract_words()
                        if words:
                            # Reconstruct text from words
                            page_text = " ".join([w.get("text", "") for w in words if w.get("text")])
                            logger.info(f"Page {i+1}: Used word extraction method, got {len(page_text)} chars")
                    except Exception as word_error:
                        logger.warning(f"Word extraction failed for page {i+1}: {word_error}")
                
                if page_text and len(page_text.strip()) > 0:
                    text += page_text + "\n"
                    logger.debug(f"Page {i+1}: Extracted {len(page_text)} chars")
                else:
                    logger.warning(f"Page {i+1}: No text extracted (may be image-only)")
                
                # CRITICAL: Extract tables as text (SOW documents often have tables)
                # Tables are crucial for Locations, Deliverables, Performance Metrics, etc.
                # HYBRID STRATEGY: If table extraction fails or produces poor results, fall back to plain text
                try:
                    tables = page.extract_tables()
                    if tables:
                        logger.info(f"Found {len(tables)} table(s) on page {i+1}")
                        for table_idx, table in enumerate(tables):
                            # Check table quality (merged cells, complex structure)
                            table_quality_score = _assess_table_quality(table)
                            
                            if table_quality_score < 0.5:
                                # Table structure is too complex - extract as plain text instead
                                logger.warning(f"Table {table_idx + 1} on page {i+1} has complex structure (score: {table_quality_score:.2f}), extracting as plain text")
                                # Get the table area as plain text
                                try:
                                    # Extract text from table bounding box if available
                                    table_bbox = page.find_tables()[table_idx] if hasattr(page, 'find_tables') else None
                                    if table_bbox:
                                        table_area = page.within_bbox(table_bbox.bbox)
                                        table_text = table_area.extract_text()
                                        if table_text:
                                            text += f"\n[COMPLEX TABLE {table_idx + 1} - EXTRACTED AS TEXT]\n{table_text}\n"
                                    else:
                                        # Fallback: try to extract text from table cells
                                        table_text = "\n[COMPLEX TABLE " + str(table_idx + 1) + " - EXTRACTED AS TEXT]\n"
                                        for row in table:
                                            row_text = " ".join([str(cell) if cell is not None else "" for cell in row if cell])
                                            if row_text.strip():
                                                table_text += row_text + "\n"
                                        text += table_text + "\n"
                                except Exception as fallback_error:
                                    logger.warning(f"Fallback text extraction failed for table {table_idx + 1}: {fallback_error}")
                                    # Last resort: include table as-is
                                    table_text = "\n[TABLE " + str(table_idx + 1) + "]\n"
                                    for row in table:
                                        clean_row = [str(cell) if cell is not None else "" for cell in row]
                                        table_text += " | ".join(clean_row) + "\n"
                                    text += table_text + "\n"
                            else:
                                # Table structure is good - extract as structured table
                                table_text = "\n[TABLE " + str(table_idx + 1) + "]\n"
                                for row in table:
                                    # Clean None values and join row
                                    clean_row = [str(cell) if cell is not None else "" for cell in row]
                                    table_text += " | ".join(clean_row) + "\n"
                                text += table_text + "\n"
                except Exception as table_error:
                    logger.warning(f"Error extracting tables from page {i+1}: {table_error}")
                    # If table extraction completely fails, ensure we at least have the page text
                    if not page_text or len(page_text.strip()) < 10:
                        # Try to get any text from the page
                        try:
                            words = page.extract_words()
                            if words:
                                fallback_text = " ".join([w.get("text", "") for w in words if w.get("text")])
                                if fallback_text:
                                    text += f"\n[PAGE {i+1} TEXT - TABLE EXTRACTION FAILED]\n{fallback_text}\n"
                        except:
                            pass
        
        # If we got substantial text, return it
        if len(text.strip()) > 100:
            logger.info(f"Successfully extracted {len(text)} chars from PDF using pdfplumber (including tables)")
            return text
        else:
            logger.warning(f"pdfplumber extracted only {len(text)} chars - PDF may be scanned/image-based")
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")
    
    # Method 2: Try PyMuPDF (fitz) - sometimes better for certain PDFs
    if PYMUPDF_AVAILABLE and len(text.strip()) < 100:
        try:
            logger.info("Trying PyMuPDF as fallback...")
            doc = fitz.open(file_path)
            fitz_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                fitz_text += page.get_text() + "\n"
            doc.close()
            
            if len(fitz_text.strip()) > len(text.strip()):
                text = fitz_text
                logger.info(f"Extracted {len(text)} chars from PDF using PyMuPDF")
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
    
    # Method 3: If still very little text, try OCR (for scanned PDFs)
    if len(text.strip()) < 100 and OCR_AVAILABLE:
        try:
            logger.warning(f"PDF has very little text ({len(text)} chars), attempting OCR...")
            logger.warning("This may take a while for large PDFs...")
            # Convert PDF pages to images
            images = convert_from_path(file_path, dpi=300)
            ocr_text = ""
            for i, image in enumerate(images):
                logger.info(f"OCR processing page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image, lang='eng')
                ocr_text += page_text + "\n"
            
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                logger.info(f"Extracted {len(text)} chars from PDF using OCR")
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}. PDF may be corrupted or OCR dependencies missing.")
            logger.warning("Note: Tesseract OCR must be installed on the system for OCR to work.")
    
    # Final check
    if not text or len(text.strip()) < 10:
        logger.error(f"CRITICAL: Very little text extracted from PDF ({len(text)} chars)")
        logger.error("Possible reasons:")
        logger.error("  1. PDF is scanned/image-based and OCR failed or not available")
        logger.error("  2. PDF is password-protected")
        logger.error("  3. PDF is corrupted")
        logger.error("  4. PDF contains only images without text layer")
    else:
        logger.info(f"Final extracted text length: {len(text)} characters, {len(text.split())} words")
    
    return text


def extract_tables_from_pdf(file_path: str) -> List[List[List[str]]]:
    """
    Extract tables from PDF file using camelot or pdfplumber.
    
    Returns:
        List of tables, where each table is a list of rows, and each row is a list of cells.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"PDF file not found: {file_path}")
        return []
    
    tables = []
    
    # Try pdfplumber first (simpler, works well for most PDFs)
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                if page_tables:
                    logger.info(f"Found {len(page_tables)} table(s) on page {i+1}")
                    # Convert to list of lists format
                    for table in page_tables:
                        # Clean None values
                        clean_table = [[str(cell) if cell is not None else "" for cell in row] for row in table]
                        tables.append(clean_table)
    except Exception as e:
        logger.warning(f"pdfplumber table extraction failed: {e}")
    
    # If no tables found with pdfplumber, try camelot (better for complex tables)
    if not tables:
        try:
            camelot_tables = camelot.read_pdf(str(file_path), pages='all', flavor='lattice')
            if camelot_tables:
                logger.info(f"Found {len(camelot_tables)} table(s) using camelot")
                for table in camelot_tables:
                    # Convert camelot table to list of lists
                    df = table.df
                    table_list = df.values.tolist()
                    tables.append(table_list)
        except Exception as e:
            logger.warning(f"camelot table extraction failed: {e}")
    
    return tables


def extract_metadata_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF file.
    
    Returns:
        Dict with metadata like page_count, title, author, etc.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"PDF file not found: {file_path}")
        return {}
    
    metadata = {
        "file_path": str(file_path),
        "file_size": file_path_obj.stat().st_size if file_path_obj.exists() else 0,
    }
    
    # Try pdfplumber for metadata
    try:
        with pdfplumber.open(file_path) as pdf:
            metadata["page_count"] = len(pdf.pages)
            # Try to get PDF metadata
            if hasattr(pdf, 'metadata') and pdf.metadata:
                metadata.update(pdf.metadata)
    except Exception as e:
        logger.warning(f"pdfplumber metadata extraction failed: {e}")
    
    # Try PyMuPDF for additional metadata
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(file_path)
            metadata["page_count"] = len(doc)
            if doc.metadata:
                metadata.update(doc.metadata)
            doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF metadata extraction failed: {e}")
    
    return metadata


def _assess_table_quality(table: List[List[Any]]) -> float:
    """
    Assess the quality/complexity of a table structure.
    Returns a score between 0.0 (very complex/poor) and 1.0 (simple/good).
    
    Factors:
    - Empty cells (None values) indicate merged cells or complex structure
    - Inconsistent row lengths indicate merged cells
    - Very long cell content indicates nested text (complex)
    """
    if not table or len(table) == 0:
        return 0.0
    
    # Count empty cells
    total_cells = 0
    empty_cells = 0
    max_cell_length = 0
    row_lengths = []
    
    for row in table:
        if not row:
            continue
        row_lengths.append(len(row))
        for cell in row:
            total_cells += 1
            if cell is None or (isinstance(cell, str) and len(cell.strip()) == 0):
                empty_cells += 1
            elif isinstance(cell, str):
                max_cell_length = max(max_cell_length, len(cell))
    
    if total_cells == 0:
        return 0.0
    
    # Calculate quality score
    empty_ratio = empty_cells / total_cells if total_cells > 0 else 1.0
    
    # Check row length consistency
    if len(row_lengths) > 1:
        avg_row_length = sum(row_lengths) / len(row_lengths)
        length_variance = sum((l - avg_row_length) ** 2 for l in row_lengths) / len(row_lengths)
        consistency_score = 1.0 / (1.0 + length_variance)  # Lower variance = higher score
    else:
        consistency_score = 1.0
    
    # Long cell content indicates complex nested text
    long_cell_penalty = min(1.0, 500.0 / max(max_cell_length, 1))  # Penalize cells longer than 500 chars
    
    # Final score: lower empty ratio, higher consistency, lower long cell penalty = better
    quality_score = (1.0 - empty_ratio) * 0.4 + consistency_score * 0.4 + long_cell_penalty * 0.2
    
    return max(0.0, min(1.0, quality_score))
    