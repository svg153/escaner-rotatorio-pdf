"""
Example Web API using Flask.
Shows how to use the core logic without CLI.
"""

from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
from pathlib import Path

from models.pdf_processor import PDFInput, ProcessingOptions, PDFMergerCore


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()


def allowed_file(filename):
    """Check if file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    """
    Merge multiple PDFs.
    
    Request:
        - files: List of PDF files
        - interleave: Boolean (optional)
        - reverse_indices: List of indices to reverse (optional)
        
    Response:
        - Merged PDF file
    """
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if len(files) == 0:
            return jsonify({'error': 'No files provided'}), 400
        
        # Save uploaded files temporarily
        temp_files = []
        pdf_inputs = []
        
        for idx, file in enumerate(files):
            if file and allowed_file(file.filename):
                # Save file
                temp_path = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    f"upload_{idx}_{secure_filename(file.filename)}"
                )
                file.save(temp_path)
                temp_files.append(temp_path)
                
                # Create PDF input
                reverse = idx in request.form.getlist('reverse_indices', type=int)
                pdf_inputs.append(PDFInput(path=temp_path, reverse=reverse))
        
        if not pdf_inputs:
            return jsonify({'error': 'No valid PDF files'}), 400
        
        # Get options from form
        interleave = request.form.get('interleave', 'false').lower() == 'true'
        
        # Create output path
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"merged_{os.urandom(8).hex()}.pdf"
        )
        
        # Process
        options = ProcessingOptions(verbose=False)
        processor = PDFMergerCore(options)
        
        success = processor.merge_and_process(
            pdf_inputs,
            output_path,
            interleave=interleave
        )
        
        # Cleanup input files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        if not success:
            return jsonify({'error': 'Failed to merge PDFs'}), 500
        
        # Send file
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process', methods=['POST'])
def process_pdf():
    """
    Process a single PDF with various options.
    
    Request:
        - file: PDF file
        - ocr: Boolean
        - ocr_lang: String
        - optimize: Boolean
        - enhance: Boolean
        - ... (all processing options)
        
    Response:
        - Processed PDF file
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        # Save uploaded file
        input_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"input_{secure_filename(file.filename)}"
        )
        file.save(input_path)
        
        # Create output path
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"processed_{os.urandom(8).hex()}.pdf"
        )
        
        # Parse processing options from form
        options = ProcessingOptions(
            ocr=request.form.get('ocr', 'false').lower() == 'true',
            ocr_lang=request.form.get('ocr_lang', 'spa'),
            optimize=request.form.get('optimize', 'false').lower() == 'true',
            enhance=request.form.get('enhance', 'false').lower() == 'true',
            denoise=request.form.get('denoise', 'false').lower() == 'true',
            binarize=request.form.get('binarize', 'false').lower() == 'true',
            sharpen=request.form.get('sharpen', 'false').lower() == 'true',
            despeckle=request.form.get('despeckle', 'false').lower() == 'true',
            autocrop=request.form.get('autocrop', 'false').lower() == 'true',
            remove_blank=request.form.get('remove_blank', 'false').lower() == 'true',
            auto_deskew=request.form.get('auto_deskew', 'false').lower() == 'true',
            compress_level=int(request.form.get('compress_level', 5)),
            title=request.form.get('title'),
            author=request.form.get('author'),
            watermark=request.form.get('watermark'),
            page_numbers=request.form.get('page_numbers', 'false').lower() == 'true',
            verbose=False
        )
        
        # Process
        processor = PDFMergerCore(options)
        success = processor.process_pdf(input_path, output_path)
        
        # Cleanup input file
        try:
            os.remove(input_path)
        except:
            pass
        
        if not success:
            return jsonify({'error': 'Failed to process PDF'}), 500
        
        # Send file
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='processed.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    """Get available processing profiles."""
    profiles_path = Path(__file__).parent / 'config' / 'profiles.yaml'
    
    if not profiles_path.exists():
        return jsonify({'profiles': []})
    
    try:
        import yaml
        with open(profiles_path, 'r') as f:
            profiles = yaml.safe_load(f)
        return jsonify({'profiles': list(profiles.keys())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-with-profile', methods=['POST'])
def process_with_profile():
    """
    Process PDF using a predefined profile.
    
    Request:
        - file: PDF file
        - profile: Profile name (document, photo, ebook, etc.)
        
    Response:
        - Processed PDF file
    """
    try:
        # Check file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        profile_name = request.form.get('profile')
        
        if not profile_name:
            return jsonify({'error': 'No profile specified'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        # Load profile
        profiles_path = Path(__file__).parent / 'config' / 'profiles.yaml'
        import yaml
        with open(profiles_path, 'r') as f:
            profiles = yaml.safe_load(f)
        
        profile = profiles.get(profile_name)
        if not profile:
            return jsonify({'error': f'Profile {profile_name} not found'}), 400
        
        # Save input file
        input_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"input_{secure_filename(file.filename)}"
        )
        file.save(input_path)
        
        # Create output path
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"processed_{os.urandom(8).hex()}.pdf"
        )
        
        # Create options from profile
        options_dict = {k.replace('-', '_'): v for k, v in profile.items()}
        options = ProcessingOptions(**options_dict, verbose=False)
        
        # Process
        processor = PDFMergerCore(options)
        success = processor.process_pdf(input_path, output_path)
        
        # Cleanup
        try:
            os.remove(input_path)
        except:
            pass
        
        if not success:
            return jsonify({'error': 'Failed to process PDF'}), 500
        
        # Send file
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{profile_name}_processed.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
