"""
Test Script for File Content Extraction
Demonstrates various usage patterns
"""

import json
from extract import FileExtractor
from pathlib import Path


def test_single_file_extraction():
    """Test extracting a single file."""
    print("=" * 60)
    print("TEST 1: Single File Extraction")
    print("=" * 60)
    
    extractor = FileExtractor()
    
    # Test with a non-existent file to show error handling
    result = extractor.extract("non_existent_file.pdf")
    print("\nExtraction Result (non-existent file):")
    print(json.dumps(result, indent=2))
    
    # To test with real files, uncomment and modify:
    # result = extractor.extract("path/to/your/file.pdf")
    # print("\nExtraction Result:")
    # print(json.dumps(result, indent=2))


def test_batch_extraction():
    """Test extracting multiple files."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Extraction")
    print("=" * 60)
    
    extractor = FileExtractor()
    
    # Example files to process (create these for real testing)
    test_files = [
        "sample1.txt",
        "sample2.pdf",
        "sample3.docx"
    ]
    
    # Filter to only existing files
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if existing_files:
        results = extractor.extract_batch(existing_files)
        print("\nBatch Extraction Results:")
        for result in results:
            print(f"\n  File: {result.get('file_name', 'Unknown')}")
            print(f"  Success: {result.get('success', False)}")
            if result.get('success'):
                content_preview = result.get('content', '')[:100]
                print(f"  Content Preview: {content_preview}...")
    else:
        print("\nNo test files found. Create sample files for testing:")
        print("  - sample1.txt")
        print("  - sample2.pdf")
        print("  - sample3.docx")


def test_supported_formats():
    """Display supported file formats."""
    print("\n" + "=" * 60)
    print("TEST 3: Supported File Formats")
    print("=" * 60)
    
    print("\nSupported formats:")
    for ext, description in FileExtractor.SUPPORTED_FORMATS.items():
        print(f"  {ext:8} -> {description}")


def test_metadata_extraction():
    """Test metadata extraction from a file."""
    print("\n" + "=" * 60)
    print("TEST 4: Metadata Extraction")
    print("=" * 60)
    
    extractor = FileExtractor()
    
    # Create a test file
    test_file = Path("test_sample.txt")
    test_file.write_text("This is a test file for extraction.")
    
    result = extractor.extract(str(test_file))
    
    if result.get('success'):
        print("\nFile Metadata:")
        metadata = result.get('metadata', {})
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print("\nExtracted Content:")
        print(f"  {result.get('content', 'No content')}")
    
    # Cleanup
    test_file.unlink()


def test_error_handling():
    """Test error handling capabilities."""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling")
    print("=" * 60)
    
    extractor = FileExtractor()
    
    test_cases = [
        ("non_existent.txt", "Non-existent file"),
        ("test_file.xyz", "Unsupported format"),
    ]
    
    for file_path, description in test_cases:
        print(f"\nTest: {description}")
        print(f"  File: {file_path}")
        result = extractor.extract(file_path)
        
        if not result.get('success'):
            print(f"  Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"  Success: Content extracted")


def create_sample_files():
    """Create sample files for testing."""
    print("\n" + "=" * 60)
    print("Creating Sample Test Files")
    print("=" * 60)
    
    # Create a sample text file
    Path("sample_text.txt").write_text(
        "Sample Text File\n"
        "=" * 50 + "\n"
        "This is a sample text file for testing the extraction script.\n"
        "It contains multiple lines of text.\n"
        "You can extract content from various file formats."
    )
    print("\n✓ Created: sample_text.txt")
    
    # Create a sample CSV file
    Path("sample_data.csv").write_text(
        "Name,Age,City\n"
        "John Doe,28,New York\n"
        "Jane Smith,34,Los Angeles\n"
        "Bob Johnson,45,Chicago"
    )
    print("✓ Created: sample_data.csv")
    
    # Create a sample JSON file
    import json
    json_data = {
        "project": "File Extraction",
        "version": "1.0.0",
        "features": [
            "PDF extraction",
            "Word document extraction",
            "Excel sheet extraction"
        ]
    }
    Path("sample_data.json").write_text(json.dumps(json_data, indent=2))
    print("✓ Created: sample_data.json")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FILE CONTENT EXTRACTION - TEST SUITE")
    print("=" * 60)
    
    # Run tests
    test_supported_formats()
    test_single_file_extraction()
    test_error_handling()
    test_metadata_extraction()
    
    # Optional: Create and test with sample files
    print("\n" + "=" * 60)
    create_sample_files()
    
    # Test batch with created samples
    print("\nTesting batch extraction with created files:")
    extractor = FileExtractor()
    results = extractor.extract_batch([
        "sample_text.txt",
        "sample_data.csv",
        "sample_data.json"
    ])
    
    for result in results:
        if result.get('success'):
            print(f"\n✓ {result['file_name']} ({result['file_type']})")
            print(f"  Size: {result['file_size_bytes']} bytes")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
