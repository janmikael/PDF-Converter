import os
import time
import subprocess
import signal
from pathlib import Path
import shutil
import logging
import magic
import shlex
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

def _check_libreoffice_ready():
    """Verify LibreOffice is installed and runnable"""
    if not Path(Config.LIBREOFFICE_PATH).exists():
        raise ConversionError(f"LibreOffice not found at {Config.LIBREOFFICE_PATH}")
    
    try:
        subprocess.run(
            [Config.LIBREOFFICE_PATH, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
    except Exception as e:
        raise ConversionError(f"LibreOffice check failed: {str(e)}")

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

        # Check for file stability
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

        if detected_mime == 'application/zip' and ext in ['docx', 'xlsx']:
            return  # Skip further validation for zip-based formats

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

def _run_command(command: list, timeout: int, shell: bool = False, env: Optional[dict] = None) -> None:
    """Robust command execution with process cleanup"""
    process = None
    try:
        _kill_libreoffice_processes()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell,
            start_new_session=True,
            env=env or os.environ
        )

        stdout, stderr = process.communicate(timeout=timeout)

        logger.debug(f"Command stdout: {stdout}")
        if stderr:
            logger.debug(f"Command stderr: {stderr}")

        if process.returncode != 0:
            error_msg = (
                f"Command failed (code {process.returncode}):\n"
                f"Command: {shlex.join(command)}\n"
                f"Stderr: {stderr.strip() or '(empty)'}\n"
                f"Stdout: {stdout.strip() or '(empty)'}"
            )
            logger.error(error_msg)
            raise ConversionError(error_msg)

    except subprocess.TimeoutExpired:
        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait(timeout=5)
            except Exception:
                _kill_libreoffice_processes()
        raise ConversionError(
            f"Command timed out after {timeout} seconds",
            "The document might be too complex. Try simplifying it."
        )

    except Exception as e:
        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception:
                pass
        raise ConversionError(f"Command execution failed: {str(e)}")

    finally:
        if process and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass

def _create_temp_html(input_path: Path) -> Path:
    """Create a temporary HTML file from text content"""
    html_path = Config.TEMP_FOLDER / f"{input_path.stem}.html"
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        lines = content.splitlines()
        html_lines = "\n".join(f"<div>{line}</div>" for line in lines)

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
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        div {{
            page-break-inside: avoid;
        }}
    </style>
</head>
<body>
    {html_lines}
</body>
</html>""")

        return html_path

    except Exception as e:
        html_path.unlink(missing_ok=True)
        raise ConversionError(f"Failed to create HTML file: {str(e)}")

def _try_libreoffice_conversion(input_path: Path, output_path: Path) -> None:
    """Direct LibreOffice conversion attempt with isolated profile"""
    profile_path = Config.TEMP_FOLDER / f"lo_profile_{os.getpid()}_{int(time.time())}"

    try:
        profile_path.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["SAL_USE_VCLPLUGIN"] = "headless"
        env["HOME"] = str(profile_path)

        command = [
            Config.LIBREOFFICE_PATH,
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", str(output_path.parent),
            str(input_path),
            "--norestore",
            "--nodefault",
            "--nologo",
            "--writer",
        ]

        logger.info(f"Attempting LibreOffice conversion: {' '.join(command)}")
        _run_command(command, Config.LIBREOFFICE_TIMEOUT * 2, env=env)

        output_pdf = output_path.parent / f"{input_path.stem}.pdf"
        for _ in range(5):
            if output_pdf.exists() and output_pdf.stat().st_size > 0:
                logger.info(f"LibreOffice successfully created: {output_pdf}")
                break
            time.sleep(1)
        else:
            raise ConversionError("LibreOffice conversion failed: Output file missing or empty")

    finally:
        for _ in range(3):
            try:
                shutil.rmtree(profile_path, ignore_errors=True)
                break
            except Exception:
                time.sleep(1)

def convert_with_libreoffice(input_path: Path, output_path: Path) -> None:
    """Use direct LibreOffice CLI conversion"""
    _check_libreoffice_ready()
    try:
        _try_libreoffice_conversion(input_path, output_path)
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ConversionError("Conversion succeeded but output file is empty")
    except ConversionError as e:
        logger.error(f"LibreOffice conversion failed: {e}")
        raise

def convert_with_wkhtmltopdf(input_path: Path, output_path: Path) -> None:
    """Optimized wkhtmltopdf conversion"""
    try:
        if not Path(Config.WKHTMLTOPDF_PATH).exists():
            raise ConversionError("wkhtmltopdf binary not found")

        if input_path.suffix.lower() == '.txt' and input_path.stat().st_size > 10 * 1024 * 1024:
            return _convert_large_text_with_wkhtmltopdf(input_path, output_path)

        command = [
            Config.WKHTMLTOPDF_PATH,
            "--print-media-type",
            "--encoding", "utf-8",
            "--quiet",
            "--disable-smart-shrinking",
            "--margin-top", "10mm",
            "--margin-bottom", "10mm",
            "--margin-left", "10mm",
            "--margin-right", "10mm",
            str(input_path),
            str(output_path)
        ]

        logger.info(f"Attempting wkhtmltopdf conversion: {' '.join(command)}")
        _run_command(command, Config.WKHTMLTOPDF_TIMEOUT_LARGE)

        if not output_path.exists():
            raise ConversionError("wkhtmltopdf failed to create output file")
        if output_path.stat().st_size == 0:
            raise ConversionError("wkhtmltopdf produced an empty PDF")

    except Exception as e:
        raise ConversionError(f"wkhtmltopdf conversion failed: {str(e)}")

def _convert_large_text_with_wkhtmltopdf(input_path: Path, output_path: Path) -> None:
    """Special handling for very large text files"""
    html_path = Config.TEMP_FOLDER / f"{input_path.stem}_paged.html"
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f_in:
            with open(html_path, 'w', encoding='utf-8') as f_out:
                f_out.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Large Text Conversion</title>
    <style>
        body { font-family: Arial; font-size: 10pt; margin: 10mm; }
        .page-break { page-break-after: always; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>""")
                chunk_size = 500000
                chunk = f_in.read(chunk_size)
                first_chunk = True
                
                while chunk:
                    if not first_chunk:
                        f_out.write('<div class="page-break"></div>')
                    f_out.write(f'<pre>{chunk}</pre>')
                    chunk = f_in.read(chunk_size)
                    first_chunk = False
                
                f_out.write("</body></html>")

        command = [
            Config.WKHTMLTOPDF_PATH,
            "--print-media-type",
            "--encoding", "utf-8",
            "--quiet",
            "--disable-smart-shrinking",
            "--margin-top", "10mm",
            "--margin-bottom", "10mm",
            "--margin-left", "10mm",
            "--margin-right", "10mm",
            "--footer-center", "[page]/[topage]",
            "--footer-font-size", "8",
            str(html_path),
            str(output_path)
        ]

        logger.info("Converting large text file with pagination")
        _run_command(command, Config.WKHTMLTOPDF_TIMEOUT_VERY_LARGE)

    finally:
        html_path.unlink(missing_ok=True)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError("Failed to convert large text file")

def convert_to_pdf(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """Main conversion entry point"""
    try:
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve() if output_path else \
            Config.CONVERTED_FOLDER / f"{input_path.stem}.pdf"

        _validate_file(input_path)
        logger.info(f"Converting {input_path.name} to PDF...")

        if input_path.suffix.lower() == '.txt':
            html_path = _create_temp_html(input_path)
            try:
                if Path(Config.WKHTMLTOPDF_PATH).exists():
                    convert_with_wkhtmltopdf(html_path, output_path)
                else:
                    convert_with_libreoffice(html_path, output_path)
            finally:
                html_path.unlink(missing_ok=True)

        elif input_path.suffix.lower() in ('.html', '.htm'):
            if Path(Config.WKHTMLTOPDF_PATH).exists():
                convert_with_wkhtmltopdf(input_path, output_path)
            else:
                convert_with_libreoffice(input_path, output_path)

        else:
            convert_with_libreoffice(input_path, output_path)
            generated_pdf = output_path.parent / f"{input_path.stem}.pdf"
            if generated_pdf != output_path:
                shutil.move(str(generated_pdf), str(output_path))

        logger.info(f"Conversion complete: {output_path}")
        return output_path

    except ConversionError as e:
        if "timed out" in str(e).lower():
            raise ConversionError(
                "Conversion timed out. The file may be too large or complex.",
                "Try a smaller file or check for corruption."
            ) from e
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during conversion: {str(e)}")
        raise ConversionError(f"Unexpected error: {str(e)}")