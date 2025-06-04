from pathlib import Path
from flask import current_app
import os

def save_uploaded_file(file, filename):
    upload_path = current_app.config['UPLOAD_FOLDER'] / filename
    file.save(upload_path)
    return upload_path

def cleanup_file(filepath):
    """Safely remove a file"""
    try:
        if filepath.exists():
            filepath.unlink()
            current_app.logger.info(f"Deleted temporary file: {filepath}")
        else:
            current_app.logger.info(f"File not found for cleanup: {filepath}")
    except Exception as e:
        current_app.logger.error(f"Error deleting file {filepath}: {e}")

def cleanup_folder(folder_path):
    """Clean all files inside a given folder"""
    try:
        for file in Path(folder_path).glob("*"):
            if file.is_file():
                cleanup_file(file)
    except Exception as e:
        current_app.logger.error(f"Error cleaning folder {folder_path}: {e}")

def cleanup_all_temp_folders():
    """Clean up files in uploads, converted, and temp folders"""
    for folder_name in ['UPLOAD_FOLDER', 'CONVERTED_FOLDER', 'TEMP_FOLDER']:
        folder_path = current_app.config[folder_name]
        current_app.logger.info(f"Cleaning folder: {folder_path}")
        cleanup_folder(folder_path)
