from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from app import app
from pathlib import Path
import uuid
import threading
from werkzeug.utils import secure_filename
from .utils.conversion import convert_to_pdf, ConversionError
from .utils.file_handling import save_uploaded_file, cleanup_file
from .utils.validators import allowed_file
import logging
import os
from flask import jsonify
from app.utils.file_handling import cleanup_all_temp_folders

logger = logging.getLogger(__name__)

# Store conversion statuses
app.conversion_status = {}

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large. Maximum allowed size is 100 MB.'
    }), 413

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        cleanup_all_temp_folders()

        filename = secure_filename(file.filename)
        upload_path = save_uploaded_file(file, filename)

        download_id = str(uuid.uuid4())
        pdf_filename = f"{Path(filename).stem}.pdf"
        app.downloads[download_id] = pdf_filename

                # Initialize status as 'processing' right away
        app.conversion_status[download_id] = {'status': 'processing', 'message': 'Conversion in progress...'}

        # Background conversion
        def background_task():
            with app.app_context():
                try:
                    pdf_path = app.config['CONVERTED_FOLDER'] / pdf_filename
                    if convert_to_pdf(upload_path, pdf_path):
                        logger.info(f"Converted {filename} successfully")
                        app.conversion_status[download_id] = {'status': 'completed', 'message': 'Conversion successful.'}
                    cleanup_file(upload_path)
                except ConversionError as e:
                    logger.error(f"Conversion failed: {e}")
                    app.conversion_status[download_id] = {'status': 'failed', 'message': str(e)}
                except Exception as e:
                    logger.error(f"Background conversion error: {e}")
                    app.conversion_status[download_id] = {'status': 'failed', 'message': 'Unexpected error occurred during conversion.'}

        thread = threading.Thread(target=background_task)
        thread.start()

        return jsonify({
            'status': 'processing',
            'download_id': download_id,
            'redirect': url_for('conversion_status', download_id=download_id)
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<download_id>')
def conversion_status(download_id):
    if download_id not in app.downloads:
        return jsonify({'error': 'Invalid download ID'}), 404

    filename = app.downloads[download_id]
    file_path = app.config['CONVERTED_FOLDER'] / filename
    status_info = app.conversion_status.get(download_id, {'status': 'unknown', 'message': ''})

    return jsonify({
        'status': status_info['status'],
        'message': status_info['message'],
        'filename': filename,
        'complete': status_info['status'] == 'completed',
        'download_url': url_for('download_file', download_id=download_id) if status_info['status'] == 'completed' else None
    })

@app.route('/success/<download_id>')
def conversion_success(download_id):
    if download_id not in app.downloads:
        flash('Invalid download ID')
        return redirect(url_for('home'))

    filename = app.downloads[download_id]
    file_path = app.config['CONVERTED_FOLDER'] / filename

    if not file_path.exists():
        flash('File not ready yet')
        return redirect(url_for('home'))

    file_size = f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MB"

    return render_template('success.html',
                           download_id=download_id,
                           filename=filename,
                           file_size=file_size)

@app.route('/download/<download_id>')
def download_file(download_id):
    if download_id not in app.downloads:
        flash('Invalid download ID')
        return redirect(url_for('home'))

    filename = app.downloads[download_id]
    file_path = app.config['CONVERTED_FOLDER'] / filename

    try:
        response = send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    except Exception as e:
        flash(f'Download failed: {str(e)}')
        return redirect(url_for('home'))
