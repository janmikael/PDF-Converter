import subprocess
from pathlib import Path
import pythoncom
from win32com import client as wc
import pdfkit
from docx import Document
from typing import Union
import logging
from app.config import Config

logger = logging.getLogger(__name__)

class ConversionError(Exception):
    pass

def convert_to_pdf(input_path: Union[str, Path], output_path: Union[str, Path, None] = None) -> Path:
    """Main conversion function with LibreOffice fallback"""
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else Config.CONVERTED_FOLDER / f"{input_path.stem}.pdf"

    try:
        ext = input_path.suffix.lower()
        if ext == ".txt":
            _convert_txt_to_pdf(input_path, output_path)
        elif ext in (".doc", ".docx"):
            _convert_word_to_pdf(input_path, output_path)
        elif ext in (".xls", ".xlsx"):
            _convert_excel_to_pdf(input_path, output_path)
        else:
            raise ConversionError(f"Unsupported file type: {ext}")
        
        if not output_path.exists():
            raise ConversionError("Conversion succeeded but output file missing")
        
        return output_path
    except Exception as e:
        logger.error(f"Conversion failed for {input_path}: {str(e)}", exc_info=True)
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        raise ConversionError(f"Conversion failed: {str(e)}")

def _convert_txt_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert text files using wkhtmltopdf"""
    try:
        config = pdfkit.configuration(wkhtmltopdf=Config.WKHTMLTOPDF_PATH)
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
        pdfkit.from_string(text, str(output_path), configuration=config)
    except Exception as e:
        raise ConversionError(f"Text conversion failed: {str(e)}")

def _convert_word_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert Word files using LibreOffice"""
    try:
        subprocess.run([
            Config.LIBREOFFICE_PATH,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_path.parent),
            str(input_path)
        ], check=True, shell=True)
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"LibreOffice Word conversion failed: {e.stderr}")

def _convert_excel_to_pdf(input_path: Path, output_path: Path) -> None:
    """Convert Excel files using LibreOffice"""
    try:
        subprocess.run([
            Config.LIBREOFFICE_PATH,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_path.parent),
            str(input_path)
        ], check=True, shell=True)
    except subprocess.CalledProcessError as e:
        raise ConversionError(f"LibreOffice Excel conversion failed: {e.stderr}")