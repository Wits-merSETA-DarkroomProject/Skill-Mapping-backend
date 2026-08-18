# File Content Extraction Script

A robust Python script that extracts text and data from various file formats (PDF, DOCX, XLSX, TXT, CSV, JSON, HTML, and Markdown).

## Features

- **Multi-format Support**: PDF, DOCX, DOC, XLSX, XLS, CSV, JSON, HTML, TXT, MD
- **Batch Processing**: Extract from multiple files at once
- **Detailed Metadata**: File size, creation date, modification date
- **Error Handling**: Comprehensive error messages and format validation
- **Flexible Output**: JSON-structured results with content and metadata

## Supported File Types

| Format | Description |
|--------|-------------|
| `.pdf` | PDF Documents (text extraction per page) |
| `.docx` | Microsoft Word Documents |
| `.doc` | Legacy Word Documents |
| `.xlsx` | Excel Spreadsheets |
| `.xls` | Legacy Excel Spreadsheets |
| `.csv` | Comma-Separated Values |
| `.txt` | Plain Text Files |
| `.json` | JSON Files |
| `.html` | HTML Files |
| `.md` | Markdown Files |

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install PyPDF2 python-docx openpyxl xlrd docx2txt
```

### 2. Verify Installation

```bash
python extract.py
```

## Usage

### Command Line Usage

Extract from a single file:

```bash
python extract.py path/to/file.pdf
```

Examples:

```bash
python extract.py document.pdf
python extract.py spreadsheet.xlsx
python extract.py data.csv
```

### Python Module Usage

```python
from extract import FileExtractor
import json

# Create extractor instance
extractor = FileExtractor(upload_dir="uploads")

# Extract from single file
result = extractor.extract("document.pdf")
print(json.dumps(result, indent=2))

# Extract from multiple files
files = ["file1.pdf", "file2.docx", "file3.xlsx"]
results = extractor.extract_batch(files)
for result in results:
    print(f"Processed: {result['file_name']}")
```

## Output Format

The extraction returns a structured JSON response:

```json
{
  "success": true,
  "file_name": "document.pdf",
  "file_type": "PDF Document",
  "file_size_bytes": 125000,
  "content": "Extracted text content...",
  "metadata": {
    "file_path": "/path/to/document.pdf",
    "file_size_kb": 122.07,
    "created": "2024-01-15T10:30:00",
    "modified": "2024-01-16T14:45:30",
    "extension": ".pdf"
  },
  "extracted_at": "2024-01-17T09:15:22.123456"
}
```

## Advanced Usage with Flask Web Server

Create a `server.py` file to serve extraction via HTTP:

```python
from flask import Flask, request, jsonify
from extract import FileExtractor
import os

app = Flask(__name__)
extractor = FileExtractor(upload_dir="uploads")

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save uploaded file
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    # Extract content
    result = extractor.extract(file_path)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

Then install Flask:

```bash
pip install flask
python server.py
```

Upload files via curl:

```bash
curl -F "file=@document.pdf" http://localhost:5000/extract
```

## Error Handling

The script handles various error scenarios:

- **File Not Found**: Returns error if file doesn't exist
- **Unsupported Format**: Lists supported formats
- **Missing Dependencies**: Provides installation instructions
- **Encoding Issues**: Attempts multiple encodings for text files

Example error response:

```json
{
  "success": false,
  "error": "Unsupported file type: .xyz",
  "supported_formats": [".pdf", ".txt", ".docx", ...]
}
```

## Performance Tips

1. **For Large PDFs**: Consider extracting page ranges instead of entire document
2. **For Large Spreadsheets**: Consider processing sheet by sheet
3. **Batch Processing**: Use `extract_batch()` for multiple files to optimize I/O

## Troubleshooting

### ImportError: No module named 'PyPDF2'

```bash
pip install PyPDF2
```

### UnicodeDecodeError for text files

The script automatically tries UTF-8 and Latin-1 encodings.

### Excel file issues

For `.xls` files, ensure `xlrd` is installed:

```bash
pip install xlrd
```

For `.xlsx` files, ensure `openpyxl` is installed:

```bash
pip install openpyxl
```

## License

MIT License

## Contributing

Feel free to extend with more file formats or improve extraction quality.
