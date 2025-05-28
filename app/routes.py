from flask import render_template, request, redirect, url_for, flash, send_file
from app import app
import os
import subprocess
from pathlib import Path
import uuid
from werkzeug.utils import secure_filename

# Initialize folders with absolute paths
BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
CONVERTED_FOLDER = BASE_DIR / 'converted'
UPLOAD_FOLDER.mkdir(exist_ok=True)
CONVERTED_FOLDER.mkdir(exist_ok=True)

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.config['LIBREOFFICE_PATH'] = r"D:\Program Files\LibreOffice\program\soffice.exe"
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'doc', 'docx', 'xls', 'xlsx'}

app.downloads = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_to_pdf(input_path, output_path):
    """Convert file to PDF using LibreOffice"""
    try:
        subprocess.run([
            app.config['LIBREOFFICE_PATH'],
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_path.parent),
            str(input_path)
        ], check=True, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Conversion failed: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('home'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            upload_path = UPLOAD_FOLDER / filename
            file.save(upload_path)
            
            download_id = str(uuid.uuid4())
            pdf_filename = f"{Path(filename).stem}.pdf"
            app.downloads[download_id] = pdf_filename
            
            # Convert to PDF
            pdf_path = CONVERTED_FOLDER / pdf_filename
            if not convert_to_pdf(upload_path, pdf_path):
                flash('Conversion failed. Please try again.')
                return redirect(url_for('home'))
            
            return redirect(url_for('conversion_success', download_id=download_id))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('home'))
    else:
        flash('Invalid file type. Allowed types: txt, doc, docx, xls, xlsx')
        return redirect(url_for('home'))

@app.route('/success/<download_id>')
def conversion_success(download_id):
    if download_id not in app.downloads:
        flash('Invalid download ID')
        return redirect(url_for('home'))
    
    filename = app.downloads[download_id]
    file_path = CONVERTED_FOLDER / filename
    
    if not file_path.exists():
        flash('File not found')
        return redirect(url_for('home'))
    
    return render_template('success.html', 
                         download_id=download_id,
                         filename=filename)

@app.route('/download/<download_id>')
def download_file(download_id):
    if download_id not in app.downloads:
        flash('Invalid download ID')
        return redirect(url_for('home'))
    
    filename = app.downloads[download_id]
    file_path = CONVERTED_FOLDER / filename
    
    if not file_path.exists():
        flash('File not found')
        return redirect(url_for('home'))
    
    try:
        response = send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf',
            conditional=True
        )
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except Exception as e:
        flash(f'Download failed: {str(e)}')
        return redirect(url_for('home'))