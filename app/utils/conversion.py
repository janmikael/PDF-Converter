import os
import time
import subprocess
import signal
from pathlib import Path
import shutil
import logging
import magic
from typing import Optional, Union
from app.config import Config

logger = logging.getLogger(__name__)

class ConversionError(Exception):
    """Enhanced conversion error with troubleshooting tips"""
    def __init__(self, message, solution=None):
        super().__init__(message)
        self.solution = solution or (
            "Please check the document and try again. "
            "If the problem persists, try a different file format."
        )

# Expanded supported types with common variants
SUPPORTED_TYPES = {
    'txt': ['text/plain', 'text/plain; charset=utf-8'],
    'doc': ['application/msword', 'application/octet-stream', 'application/vnd.ms-word'],
    'docx': [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
        'application/octet-stream'
    ],
    'xls': ['application/vnd.ms-excel', 'application/octet-stream'],
    'xlsx': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/zip',
        'application/octet-stream'
    ],
    'html': ['text/html', 'text/html; charset=utf-8'],
    'htm': ['text/html', 'text/html; charset=utf-8'],
    'odt': ['application/vnd.oasis.opendocument.text'],
    'rtf': ['text/rtf', 'application/rtf']
}

def _kill_libreoffice_processes():
    """Forcefully terminate any running LibreOffice processes"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'soffice.exe', '/T'], 
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:  # Unix-like
            subprocess.run(['pkill', '-f', 'soffice'], 
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        pass  # No processes to kill is fine

def _validate_file(input_path: Path) -> None:
    """Enhanced file validation with better error messages"""
    if not input_path.exists():
        raise ConversionError(f"File does not exist: {input_path}")
    
    if not input_path.is_file():
        raise ConversionError(f"Path is not a file: {input_path}")

    try:
        if not os.access(input_path, os.R_OK):
            raise ConversionError(
                f"File is not readable: {input_path}",
                "Check file permissions or try a different file"
            )

        # Check for file stability (not being written to)
        initial_size = input_path.stat().st_size
        time.sleep(0.5)
        if input_path.stat().st_size != initial_size:
            raise ConversionError(
                "File size changed during validation",
                "The file might still be uploading or being modified"
            )

        # File type validation
        ext = input_path.suffix[1:].lower()
        if not ext:
            raise ConversionError(
                "File has no extension",
                "Add the correct file extension or try a different file"
            )

        if ext not in SUPPORTED_TYPES:
            raise ConversionError(
                f"Unsupported file extension: .{ext}",
                f"Supported formats: {', '.join(SUPPORTED_TYPES.keys())}"
            )

        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(str(input_path)).lower()
        
        # Special case for zip-based formats
        if detected_mime == 'application/zip' and ext in ['docx', 'xlsx']:
            return  # Skip further validation for these cases
            
        if detected_mime not in SUPPORTED_TYPES[ext]:
            raise ConversionError(
                f"File content doesn't match extension. Detected: {detected_mime}",
                "The file might be corrupted or mislabeled"
            )

    except PermissionError as e:
        raise ConversionError(
            f"Permission error accessing file: {str(e)}",
            "Check file permissions or try a different location"
        )
    except Exception as e:
        raise ConversionError(
            f"Validation failed: {str(e)}",
            "The file might be corrupted or in an unsupported format"
        )

def _run_command(command: list, timeout: int, shell: bool = False) -> None:
    """Robust command execution with process cleanup"""
    process = None
    try:
        # Pre-execution cleanup
        _kill_libreoffice_processes()
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell,
            start_new_session=True  # Important for proper signal handling
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        
        if process.returncode != 0:
            error_msg = (
                f"Command failed with code {process.returncode}\n"
                f"Command: {' '.join(command)}\n"
                f"Error: {stderr or 'No error message'}\n"
                f"Output: {stdout}"
            )
            logger.error(error_msg)
            raise ConversionError(error_msg)

    except subprocess.TimeoutExpired:
        if process:
            try:
                # Try to kill the entire process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except:
                _kill_libreoffice_processes()
        raise ConversionError(f"Command timed out after {timeout} seconds")
        
    except Exception as e:
        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except:
                pass
        raise ConversionError(f"Command execution failed: {str(e)}")
        
    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
            except:
                pass

def _create_temp_html(input_path: Path) -> Path:
    """Create a temporary HTML file from text content"""
    html_path = Config.TEMP_FOLDER / f"{input_path.stem}.html"
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{input_path.stem}</title>
    <style>
        body {{
            margin: 1in;
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
    <pre>{content}</pre>
</body>
</html>""")
        return html_path
    except Exception as e:
        html_path.unlink(missing_ok=True)
        raise ConversionError(f"Failed to create HTML file: {str(e)}")

def _try_libreoffice_conversion(input_path: Path, output_path: Path) -> None:
    """Direct LibreOffice conversion attempt"""
    profile_path = Config.TEMP_FOLDER / f"lo_profile_{os.getpid()}_{int(time.time())}"
    
    try:
        profile_path.mkdir(parents=True, exist_ok=True)

        command = [
            r"D:\Program Files\LibreOffice\program\soffice.exe",
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", str(output_path.parent),
            str(input_path),
            "--norestore",
            "--nodefault",
            "--nologo"
        ]

        logger.info(f"Attempting LibreOffice conversion: {' '.join(command)}")
        _run_command(command, Config.LIBREOFFICE_TIMEOUT * 2)

        # Wait for the output PDF to appear and be non-empty
        output_pdf = output_path.with_suffix(".pdf")
        for _ in range(5):  # Retry for up to ~5 seconds
            if output_pdf.exists() and output_pdf.stat().st_size > 0:
                logger.info(f"LibreOffice successfully created: {output_pdf}")
                break
            time.sleep(1)
        else:
            raise RuntimeError("LibreOffice conversion failed: Output file missing or empty")

    finally:
        for _ in range(3):  # Cleanup with retries
            try:
                shutil.rmtree(profile_path, ignore_errors=True)
                break
            except Exception:
                time.sleep(1)

def convert_with_libreoffice(input_path: Path, output_path: Path) -> None:
    """Use only direct LibreOffice CLI conversion (no unoconv/socket fallback)"""
    try:
        _try_libreoffice_conversion(input_path, output_path)
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ConversionError("Conversion succeeded but output file is empty")
    except ConversionError as e:
        logger.error(f"LibreOffice conversion failed: {e}")
        raise

def convert_to_pdf(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Main conversion function with comprehensive error handling.
    Returns path to converted PDF.
    """
    try:
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve() if output_path else \
            Config.CONVERTED_FOLDER / f"{input_path.stem}.pdf"
        
        _validate_file(input_path)
        logger.info(f"Converting {input_path.name} to PDF...")

        # Special handling for text and HTML files
        if input_path.suffix.lower() == '.txt':
            html_path = _create_temp_html(input_path)
            try:
                if hasattr(Config, 'WKHTMLTOPDF_PATH') and Path(Config.WKHTMLTOPDF_PATH).exists():
                    convert_with_wkhtmltopdf(html_path, output_path)
                else:
                    convert_with_libreoffice(html_path, output_path)
            finally:
                html_path.unlink(missing_ok=True)

        elif input_path.suffix.lower() in ('.html', '.htm'):
            if hasattr(Config, 'WKHTMLTOPDF_PATH') and Path(Config.WKHTMLTOPDF_PATH).exists():
                convert_with_wkhtmltopdf(input_path, output_path)
            else:
                convert_with_libreoffice(input_path, output_path)

        else:
            # LibreOffice will write to --outdir with filename stem + .pdf
            convert_with_libreoffice(input_path, output_path)

            # Determine where LibreOffice wrote the file
            generated_pdf = output_path.parent / f"{input_path.stem}.pdf"

            if not generated_pdf.exists() or generated_pdf.stat().st_size == 0:
                raise ConversionError("LibreOffice conversion failed: Output file missing or empty")

            # Move it to the desired name if needed
            if generated_pdf != output_path:
                generated_pdf.rename(output_path)

        logger.info(f"Conversion completed: {output_path}")
        return output_path

    except ConversionError as ce:
        logger.error(f"Conversion error: {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise ConversionError(f"Unexpected error: {e}")

def convert_with_wkhtmltopdf(input_path: Path, output_path: Path) -> None:
    """Convert HTML or text to PDF using wkhtmltopdf (optional)"""
    command = [
        str(Config.WKHTMLTOPDF_PATH),
        "--quiet",
        str(input_path),
        str(output_path)
    ]
    logger.info(f"Running wkhtmltopdf: {' '.join(command)}")
    _run_command(command, timeout=Config.WKHTMLTOPDF_TIMEOUT)

