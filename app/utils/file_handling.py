# app/utils/file_handling.py
import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file):
    """Securely save uploaded file to the uploads folder"""
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return file_path

def get_converted_filename(original_filename):
    """Generate a filename for the converted PDF"""
    base = os.path.splitext(original_filename)[0]
    return f"{base}.pdf"

def save_converted_file(pdf_data, original_filename):
    """Save the converted PDF to the converted folder"""
    if not os.path.exists(current_app.config['CONVERTED_FOLDER']):
        os.makedirs(current_app.config['CONVERTED_FOLDER'])
    
    filename = get_converted_filename(os.path.basename(original_filename))
    file_path = os.path.join(current_app.config['CONVERTED_FOLDER'], filename)
    
    if isinstance(pdf_data, bytes):
        with open(file_path, 'wb') as f:
            f.write(pdf_data)
    else:
        pdf_data.save(file_path)
    
    return file_path