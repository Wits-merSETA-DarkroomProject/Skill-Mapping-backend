"""
Flask Web Server for File Content Extraction
Provides REST API endpoints for extracting content from uploaded files
"""

from flask import Flask, request, jsonify
import os
import json
from pathlib import Path
from extract import FileExtractor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize extractor
extractor = FileExtractor(upload_dir=app.config['UPLOAD_FOLDER'])


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "File Content Extractor",
        "version": "1.0.0"
    }), 200


@app.route('/supported-formats', methods=['GET'])
def supported_formats():
    """Get list of supported file formats."""
    return jsonify({
        "supported_formats": FileExtractor.SUPPORTED_FORMATS
    }), 200


@app.route('/extract', methods=['POST'])
def extract_file():
    """
    Extract content from uploaded file.
    
    Form parameters:
        file: The file to extract (required)
        save: Whether to save results ('true' or 'false', default 'true')
        format: Save format ('json', 'text', 'all', default 'all')
    
    Returns:
        JSON with extracted content and metadata
    """
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({
            "error": "No file provided",
            "message": "Please provide a file in the 'file' form parameter"
        }), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({
            "error": "No file selected",
            "message": "The file must have a filename"
        }), 400
    
    try:
        # Get save parameters
        save_results = request.form.get('save', 'true').lower() == 'true'
        save_format = request.form.get('format', 'all')
        
        # Save uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Extract content
        if save_results:
            result = extractor.extract_and_save(file_path, save_format)
        else:
            result = extractor.extract(file_path)
        
        # Return result with appropriate status code
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/extract-batch', methods=['POST'])
def extract_batch():
    """
    Extract content from multiple uploaded files.
    
    Form parameters:
        files: Multiple files to extract (required)
    
    Returns:
        JSON array with extraction results for each file
    """
    # Check if files are in request
    if 'files' not in request.files:
        return jsonify({
            "error": "No files provided",
            "message": "Please provide files in the 'files' form parameter"
        }), 400
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({
            "error": "No files selected",
            "message": "At least one file must be selected"
        }), 400
    
    try:
        results = []
        
        for file in files:
            if file.filename != '':
                # Save uploaded file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                
                # Extract content
                result = extractor.extract(file_path)
                results.append(result)
        
        return jsonify({
            "success": True,
            "total_files": len(results),
            "results": results
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/extract/url', methods=['POST'])
def extract_from_url():
    """
    Extract content from file at specified path.
    
    JSON body:
        {
            "file_path": "path/to/file",
            "save": true/false,
            "format": "json|text|all"
        }
    
    Returns:
        JSON with extracted content and metadata
    """
    data = request.get_json()
    
    if not data or 'file_path' not in data:
        return jsonify({
            "error": "Invalid request",
            "message": "Please provide 'file_path' in the request body"
        }), 400
    
    file_path = data['file_path']
    
    if not Path(file_path).exists():
        return jsonify({
            "error": "File not found",
            "message": f"The file '{file_path}' does not exist"
        }), 404
    
    try:
        save_results = data.get('save', True)
        save_format = data.get('format', 'all')
        
        if save_results:
            result = extractor.extract_and_save(file_path, save_format)
        else:
            result = extractor.extract(file_path)
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/extractions', methods=['GET'])
def get_extractions():
    """
    Retrieve all saved extractions from database.
    
    Query parameters:
        file_id: Optional specific file ID to retrieve
    
    Returns:
        JSON list of extraction records
    """
    try:
        file_id = request.args.get('file_id')
        extractions = extractor.get_saved_extractions(file_id)
        
        return jsonify({
            "success": True,
            "total": len(extractions),
            "extractions": extractions
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/extractions/<file_id>', methods=['GET'])
def get_extraction(file_id):
    """
    Retrieve a specific extraction by file ID.
    
    Returns:
        JSON extraction record
    """
    try:
        extractions = extractor.get_saved_extractions(file_id)
        
        if not extractions:
            return jsonify({
                "error": "Not found",
                "message": f"No extraction found with file_id: {file_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "extraction": extractions[0]
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/extractions/<file_id>', methods=['DELETE'])
def delete_extraction_route(file_id):
    """Delete an extraction and its associated files."""
    try:
        result = extractor.delete_extraction(file_id)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get statistics about saved extractions."""
    try:
        stats = extractor.get_statistics()
        return jsonify({
            "success": True,
            "statistics": stats
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500




@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        "error": "File too large",
        "message": "Maximum file size is 50MB"
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "/health",
            "/supported-formats",
            "/extract",
            "/extract-batch",
            "/extract/url",
            "/extractions (GET)",
            "/extractions/<file_id> (GET)",
            "/extractions/<file_id> (DELETE)",
            "/statistics"
        ]
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
