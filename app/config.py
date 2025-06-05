import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    CONVERTED_FOLDER = BASE_DIR / 'converted'
    TEMP_FOLDER = BASE_DIR / 'temp'

    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'html', 'htm', 'odt', 'rtf'}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    MAX_FILE_SIZE_MB = 100

    # More reliable Docker detection (checks multiple indicators)
    IS_DOCKER = (
        os.path.exists("/.dockerenv") or 
        os.environ.get("DOCKER_CONTAINER", "").lower() == "true" or
        os.environ.get("RUNNING_IN_DOCKER", "").lower() == "true"
    )

    # Environment variables take highest precedence
    LIBREOFFICE_PATH = os.environ.get("LIBREOFFICE_PATH")
    WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH")

    # Set defaults if environment variables not provided
    if not LIBREOFFICE_PATH:
        LIBREOFFICE_PATH = "/usr/bin/soffice" if IS_DOCKER else r"D:\Program Files\LibreOffice\program\soffice.exe"

    if not WKHTMLTOPDF_PATH:
        WKHTMLTOPDF_PATH = "/usr/bin/wkhtmltopdf" if IS_DOCKER else r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

    # Timeout settings (in seconds)
    LIBREOFFICE_TIMEOUT = int(os.environ.get("LIBREOFFICE_TIMEOUT", 300))
    WKHTMLTOPDF_TIMEOUT_LARGE = int(os.environ.get("WKHTMLTOPDF_TIMEOUT", 90))
    WKHTMLTOPDF_TIMEOUT_VERY_LARGE = int(os.environ.get("WKHTMLTOPDF_TIMEOUT_VERY_LARGE", 300))

    # Additional LibreOffice settings
    LIBREOFFICE_PROFILE_DIR = TEMP_FOLDER / "lo_profile"
    SAL_USE_VCLPLUGIN = "headless"  # Force headless mode

    @classmethod
    def init_app(cls, app=None):
        """Initialize required directories"""
        for folder in [cls.UPLOAD_FOLDER, cls.CONVERTED_FOLDER, cls.TEMP_FOLDER, cls.LIBREOFFICE_PROFILE_DIR]:
            folder.mkdir(parents=True, exist_ok=True)