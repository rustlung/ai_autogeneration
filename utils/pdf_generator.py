"""
PDF generation module.
Handles HTML rendering with Jinja2 and PDF conversion with WeasyPrint.
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Union

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from utils.schema import ReportData, DesignBrief

logger = logging.getLogger(__name__)


def render_html(
    report_data: Union[ReportData, DesignBrief],
    template_path: Path,
    css_path: Path,
    transcript_filename: str = "transcript.txt",
    image_uri: Optional[str] = None,
    image_failed: bool = False
) -> str:
    """
    Render HTML from Jinja2 template.
    
    Args:
        report_data: Report data to render
        template_path: Path to HTML template file
        css_path: Path to CSS file
        transcript_filename: Name of source transcript file
        
    Returns:
        Rendered HTML as string
        
    Raises:
        TemplateNotFound: If template file doesn't exist
        TemplateSyntaxError: If template has syntax errors
    """
    try:
        logger.info(f"Rendering HTML from template: {template_path}")
        
        # Load CSS content
        css_content = ""
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            logger.debug(f"Loaded CSS from {css_path}")
        else:
            logger.warning(f"CSS file not found: {css_path}")
        
        # Setup Jinja2 environment
        template_dir = template_path.parent
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Load template
        template = env.get_template(template_path.name)
        
        # Prepare template context
        context = {
            'report_data': report_data,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'transcript_filename': transcript_filename,
            'css_content': css_content,
            'image_uri': image_uri,
            'image_failed': image_failed
        }
        
        # Render
        html = template.render(**context)
        logger.info("HTML rendered successfully")
        
        return html
        
    except TemplateNotFound as e:
        logger.error(f"Template not found: {e}")
        raise Exception(f"Template file not found: {template_path}")
        
    except TemplateSyntaxError as e:
        logger.error(f"Template syntax error: {e}")
        raise Exception(f"Template syntax error in {template_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error rendering template: {e}", exc_info=True)
        raise


def html_to_pdf(html: str, output_path: Path):
    """
    Convert HTML string to PDF file using WeasyPrint.
    
    Args:
        html: HTML content as string
        output_path: Path where to save the PDF
        
    Raises:
        Exception: On WeasyPrint errors
    """
    try:
        logger.info(f"Converting HTML to PDF: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Convert to PDF
        HTML(string=html).write_pdf(
            output_path,
            font_config=font_config
        )
        
        logger.info(f"PDF successfully created: {output_path}")
        
        # Check file size for validation
        file_size = output_path.stat().st_size
        logger.debug(f"PDF file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Generated PDF is empty")
            
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        # Clean up partial file if it exists
        if output_path.exists():
            try:
                output_path.unlink()
            except:
                pass
        raise Exception(f"Failed to generate PDF: {str(e)}")


def generate_pdf_report(
    report_data: Union[ReportData, DesignBrief],
    output_path: Path,
    template_path: Path,
    css_path: Path,
    transcript_filename: str = "transcript.txt",
    image_uri: Optional[str] = None,
    image_failed: bool = False
):
    """
    Generate PDF report from report data.
    
    Main entry point that combines HTML rendering and PDF conversion.
    
    Args:
        report_data: Report data to render
        output_path: Path where to save the PDF
        template_path: Path to HTML template
        css_path: Path to CSS file
        transcript_filename: Name of source transcript file
    """
    logger.info("Starting PDF report generation")
    
    # Render HTML
    html = render_html(
        report_data,
        template_path,
        css_path,
        transcript_filename,
        image_uri=image_uri,
        image_failed=image_failed
    )
    
    # Convert to PDF
    html_to_pdf(html, output_path)
    
    logger.info(f"Report generation completed: {output_path}")
    print(f"\n✓ Отчёт успешно создан: {output_path}")
