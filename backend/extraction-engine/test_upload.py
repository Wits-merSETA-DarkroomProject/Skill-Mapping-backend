#!/usr/bin/env python3
"""
Simple test script to upload and extract a PDF file
"""
import requests
import json
from pathlib import Path

# File to upload
file_path = Path("test-file/mock_cv.pdf")

if not file_path.exists():
    print(f"Error: File not found: {file_path}")
    exit(1)

print(f"Uploading file: {file_path.name}")
print(f"File size: {file_path.stat().st_size} bytes\n")

# Upload and extract
try:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:5000/extract', files=files)
    
    result = response.json()
    
    print("=" * 80)
    print("EXTRACTION RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    
    # Check if saved
    if result.get('success') and result.get('saved'):
        print("\n" + "=" * 80)
        print("SAVED LOCATIONS")
        print("=" * 80)
        saved_paths = result['saved'].get('saved_paths', {})
        for location, path in saved_paths.items():
            print(f"{location:10}: {path}")
        
        file_id = result['saved'].get('file_id')
        print(f"\nFile ID: {file_id}")
        print(f"\nRetrieve later with:")
        print(f"  curl http://localhost:5000/extractions/{file_id}")
    
except requests.exceptions.ConnectionError:
    print("Error: Cannot connect to server at http://localhost:5000")
    print("Make sure the Flask server is running: python server.py")
except Exception as e:
    print(f"Error: {e}")
