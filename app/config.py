# app/config.py
import os
from pathlib import Path

# Base directory
BASEDIR = Path(__file__).parent.parent

# File paths (using your D:\ drives)
LIBREOFFICE_PATH = r"D:\Program Files\LibreOffice\program\soffice.exe"
WKHTMLTOPDF_PATH = r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

# Flask config
class Config:
    SECRET_KEY = "your-secret-key-here"
    UPLOAD_FOLDER = BASEDIR / "uploads"
    CONVERTED_FOLDER = BASEDIR / "converted"
    ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'xls', 'xlsx'}
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # Create folders if missing
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    CONVERTED_FOLDER.mkdir(exist_ok=True)