import os
from pathlib import Path

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    CONVERTED_FOLDER = BASE_DIR / 'converted'
    TEMP_FOLDER = BASE_DIR / 'temp'
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'htm'}
    
    # File size limits (in bytes)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    MAX_FILE_SIZE_MB = 100  # For display purposes
    
    # Conversion tools
    LIBREOFFICE_PATH = r"D:\Program Files\LibreOffice\program\soffice.exe"
    WKHTMLTOPDF_PATH = r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    
    # Timeouts (seconds)
    LIBREOFFICE_TIMEOUT = 300  # 5 minutes
    WKHTMLTOPDF_TIMEOUT = 60   # 1 minute
    
    @classmethod
    def init_app(cls, app=None):
        """Initialize required directories"""
        for folder in [cls.UPLOAD_FOLDER, cls.CONVERTED_FOLDER, cls.TEMP_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)