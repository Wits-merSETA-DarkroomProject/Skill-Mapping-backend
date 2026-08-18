# File Content Extraction Script

A robust Python script that extracts text and data from various file formats (PDF, DOCX, XLSX, TXT, CSV, JSON, HTML, and Markdown). **Now with automatic saving and database storage!**

## Features

- **Multi-format Support**: PDF, DOCX, DOC, XLSX, XLS, CSV, JSON, HTML, TXT, MD
- **Automatic Saving**: Save extracted content to JSON, text files, and/or SQLite database
- **Batch Processing**: Extract from multiple files at once
- **Detailed Metadata**: File size, creation date, modification date
- **Database Storage**: SQLite database for persistent storage and retrieval
- **Statistics**: View extraction statistics and data volumes
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
pip install PyPDF2 python-docx openpyxl xlrd docx2txt flask
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

### Python Module Usage - Basic Extraction

```python
from extract import FileExtractor
import json

# Create extractor instance
extractor = FileExtractor()

# Extract from single file
result = extractor.extract("document.pdf")
print(json.dumps(result, indent=2))
```

### Python Module Usage - With Automatic Saving

```python
from extract import FileExtractor

# Create extractor instance
extractor = FileExtractor()

# Extract and automatically save to JSON, text, and database
result = extractor.extract_and_save("document.pdf", save_format="all")

# Check where it was saved
if result['success']:
    print(f"File ID: {result['saved']['file_id']}")
    print(f"Saved to JSON: {result['saved']['saved_paths']['json']}")
    print(f"Saved to Text: {result['saved']['saved_paths']['text']}")
    print(f"Saved to DB: {result['saved']['saved_paths']['database']}")
```

### Python Module Usage - Manual Save

```python
from extract import FileExtractor

extractor = FileExtractor()

# Extract
result = extractor.extract("document.pdf")

# Save manually
if result['success']:
    save_result = extractor.save_extraction(result, save_format="all")
    print(f"Saved: {save_result}")
```

### Retrieve Saved Extractions

```python
from extract import FileExtractor

extractor = FileExtractor()

# Get all extractions
all_extractions = extractor.get_saved_extractions()

# Get specific extraction
extraction = extractor.get_saved_extractions(file_id="abc123def456")

# Get statistics
stats = extractor.get_statistics()
print(f"Total extractions: {stats['total_extractions']}")
print(f"By type: {stats['by_file_type']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

### Web Server Usage

Start the Flask server:

```bash
pip install flask
python server.py
```

Server runs on `http://localhost:5000`

## API Endpoints

### Upload and Extract

**POST `/extract`**

Upload a file and extract content. Results are automatically saved by default.

```bash
# Upload with automatic saving
curl -F "file=@document.pdf" http://localhost:5000/extract

# Upload with specific save format
curl -F "file=@document.pdf" \
     -F "save=true" \
     -F "format=json" \
     http://localhost:5000/extract

# Upload without saving
curl -F "file=@document.pdf" \
     -F "save=false" \
     http://localhost:5000/extract
```

**PowerShell Example:**

```powershell
$form = @{
    file = Get-Item -Path "document.pdf"
    save = "true"
    format = "all"
}
Invoke-RestMethod -Uri "http://localhost:5000/extract" -Method Post -Form $form
```

### Batch Upload and Extract

**POST `/extract-batch`**

Upload multiple files for extraction:

```bash
curl -F "files=@file1.pdf" \
     -F "files=@file2.docx" \
     -F "files=@file3.xlsx" \
     http://localhost:5000/extract-batch
```

### Extract from File Path

**POST `/extract/url`**

Extract from a file already on the server:

```bash
curl -X POST http://localhost:5000/extract/url \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "path/to/file.pdf",
    "save": true,
    "format": "all"
  }'
```

### Retrieve Saved Extractions

**GET `/extractions`**

Get all saved extractions:

```bash
curl http://localhost:5000/extractions
```

Get specific extraction by file_id:

```bash
curl "http://localhost:5000/extractions?file_id=abc123def456"
```

**GET `/extractions/<file_id>`**

Get a specific extraction:

```bash
curl http://localhost:5000/extractions/abc123def456
```

### Delete Extraction

**DELETE `/extractions/<file_id>`**

Delete an extraction and associated files:

```bash
curl -X DELETE http://localhost:5000/extractions/abc123def456
```

### Get Statistics

**GET `/statistics`**

Get extraction statistics:

```bash
curl http://localhost:5000/statistics
```

Example response:

```json
{
  "success": true,
  "statistics": {
    "total_extractions": 42,
    "by_file_type": {
      "PDF Document": 15,
      "Word Document": 12,
      "Excel Spreadsheet": 10,
      "Text File": 5
    },
    "total_size_bytes": 125000000,
    "total_size_mb": 119.21
  }
}
```

### Get Supported Formats

**GET `/supported-formats`**

```bash
curl http://localhost:5000/supported-formats
```

### Health Check

**GET `/health`**

```bash
curl http://localhost:5000/health
```

## Directory Structure

After first use, the extraction engine creates the following structure:

```
extraction-engine/
├── extract.py                 # Main extraction module
├── server.py                  # Flask web server
├── requirements.txt           # Python dependencies
├── uploads/                   # Uploaded files (temporary)
└── extraction_results/        # Saved extraction results
    ├── json/                  # JSON format results
    │   └── file_name_hash.json
    ├── text/                  # Text format results
    │   └── file_name_hash.txt
    └── database/
        └── extractions.db     # SQLite database with all records
```

## Output Format

### Extraction Result (JSON)

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
  "extracted_at": "2024-01-17T09:15:22.123456",
  "saved": {
    "success": true,
    "file_id": "abc123def456789",
    "saved_paths": {
      "json": "extraction_results/json/document_pdf_abc123def456789.json",
      "text": "extraction_results/text/document_pdf_abc123def456789.txt",
      "database": "Saved to database: extraction_results/database/extractions.db"
    },
    "saved_at": "2024-01-17T09:15:23.456789"
  }
}
```

### Database Schema

The SQLite database includes the following fields:

```sql
CREATE TABLE extractions (
    id INTEGER PRIMARY KEY,
    file_id TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_path TEXT,
    file_size_bytes INTEGER,
    content TEXT,
    content_summary TEXT (first 500 chars),
    metadata TEXT (JSON),
    extracted_at TIMESTAMP,
    saved_at TIMESTAMP,
    status TEXT
);
```

## Error Handling

The script handles various error scenarios:

- **File Not Found**: Returns error if file doesn't exist
- **Unsupported Format**: Lists supported formats
- **Missing Dependencies**: Provides installation instructions
- **Encoding Issues**: Attempts multiple encodings for text files
- **Database Errors**: Gracefully handles database operations

Example error response:

```json
{
  "success": false,
  "error": "Unsupported file type: .xyz",
  "supported_formats": [".pdf", ".txt", ".docx", ...]
}
```

## Performance Tips

1. **For Large PDFs**: Results are still processed quickly; the database stores efficiently
2. **For Large Spreadsheets**: Consider processing sheet by sheet
3. **Batch Processing**: Use `extract_batch()` or `/extract-batch` endpoint for multiple files
4. **Database Queries**: Use file_id for quick lookups of previous extractions
5. **Storage**: Monitor `extraction_results/` directory size; delete old extractions as needed

## Database Queries

### Direct SQLite Access

```bash
sqlite3 extraction_results/database/extractions.db "SELECT file_name, file_type, saved_at FROM extractions ORDER BY saved_at DESC;"
```

### Python Database Query

```python
from extract import FileExtractor

extractor = FileExtractor()

# Get all PDFs
extractions = extractor.get_saved_extractions()
pdfs = [e for e in extractions if e['file_type'] == 'PDF Document']

# Get statistics
stats = extractor.get_statistics()
```

## Troubleshooting

### ImportError: No module named 'PyPDF2'

```bash
pip install PyPDF2
```

### Database Lock Error

Ensure only one process is writing to the database at a time. The script handles this, but if you're directly accessing the database, close other connections.

### Large File Handling

For files larger than 50MB:

1. Increase `MAX_CONTENT_LENGTH` in `server.py`
2. Or use the `/extract/url` endpoint with the file path

### Storage Space

Monitor the `extraction_results/` directory size. Delete old extractions if needed:

```python
extractor.delete_extraction(file_id)
```

## License

MIT License

## Contributing

Feel free to extend with more file formats, improve extraction quality, or add new storage backends.
