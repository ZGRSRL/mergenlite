"""
SOW PDF Generator using WeasyPrint
Converts HTML to PDF with proper formatting.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    logger.warning(f"weasyprint not available: {e}. PDF generation will be limited. Use ReportLab fallback.")


def html_to_pdf(html: str, output_path: str) -> str:
    """
    Convert HTML to PDF using WeasyPrint.
    
    Args:
        html: HTML string content
        output_path: Path where PDF will be saved
        
    Returns:
        Path to generated PDF file
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("weasyprint not installed. Install with: pip install weasyprint")
    
    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF from HTML
        HTML(string=html).write_pdf(output_path)
        
        logger.info(f"PDF generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating PDF from HTML: {e}", exc_info=True)
        raise


def generate_pdf_from_markdown(markdown_text: str, output_path: str) -> str:
    """
    Convert Markdown to PDF (via HTML).
    
    Args:
        markdown_text: Markdown text content
        output_path: Path where PDF will be saved
        
    Returns:
        Path to generated PDF file
    """
    try:
        import markdown
        from markdown.extensions import codehilite, tables, fenced_code
        
        # Convert Markdown to HTML
        html = markdown.markdown(
            markdown_text,
            extensions=['codehilite', 'tables', 'fenced_code']
        )
        
        # Wrap in basic HTML structure
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            color: #333333;
            line-height: 1.45;
            margin: 1in;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        th {{
            background: #003366;
            color: white;
            padding: 8px 10px;
        }}
        td {{
            padding: 8px 10px;
            border: 1px solid #d7dce2;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
        
        return html_to_pdf(full_html, output_path)
        
    except ImportError:
        logger.error("markdown library not available")
        raise
    except Exception as e:
        logger.error(f"Error generating PDF from Markdown: {e}", exc_info=True)
        raise

