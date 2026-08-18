#!/usr/bin/env python3
"""
Direct extraction test without server
"""
import sys
import json
from extract import FileExtractor

print("=" * 80)
print("FILE EXTRACTION TEST - Direct Mode")
print("=" * 80)

# Create extractor
extractor = FileExtractor()

# Extract and save
file_path = "test-file/mock_cv.pdf"
print(f"\nExtracting: {file_path}")
print("-" * 80)

result = extractor.extract_and_save(file_path, save_format="all")

# Display result
if result.get('success'):
    print("\n✓ EXTRACTION SUCCESSFUL\n")
    print(f"File: {result.get('file_name')}")
    print(f"Type: {result.get('file_type')}")
    print(f"Size: {result.get('file_size_bytes')} bytes")
    print(f"Extracted: {result.get('extracted_at')}")
    
    # Show saved locations
    if result.get('saved'):
        print("\n" + "=" * 80)
        print("SAVED RESULTS")
        print("=" * 80)
        saved_paths = result['saved'].get('saved_paths', {})
        for location, path in saved_paths.items():
            print(f"\n{location.upper()}:")
            print(f"  {path}")
        
        file_id = result['saved'].get('file_id')
        print(f"\nFile ID: {file_id}")
        
        # Show content preview
        print("\n" + "=" * 80)
        print("EXTRACTED CONTENT (PREVIEW)")
        print("=" * 80)
        content = result.get('content', 'No content')
        if isinstance(content, str):
            preview = content[:500]
        else:
            preview = json.dumps(content, indent=2)[:500]
        
        print(f"\n{preview}")
        if len(str(content)) > 500:
            print(f"\n... (truncated, total length: {len(str(content))} characters)")
        
        # Show how to retrieve
        print("\n" + "=" * 80)
        print("RETRIEVE EXTRACTION")
        print("=" * 80)
        print(f"\nPython:")
        print(f"  extractor.get_saved_extractions(file_id='{file_id}')")
        print(f"\nWeb API:")
        print(f"  GET http://localhost:5000/extractions/{file_id}")
        
else:
    print("\n✗ EXTRACTION FAILED\n")
    print(f"Error: {result.get('error')}")

print("\n" + "=" * 80)
