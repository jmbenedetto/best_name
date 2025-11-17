#!/usr/bin/env python3
"""
Focused tests for evaluation data processing logic.
Tests only critical data loading and processing: CSV parsing, file iteration, content extraction.
"""
import tempfile
import csv
from pathlib import Path
import sys
import os

# Add the best_name package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from best_name.cli import extract_file_content, load_ground_truth_data


def test_load_ground_truth_csv():
    """Test loading ground truth data from CSV with expected format."""
    # Create temporary directory with CSV file matching evals/eval_files.csv format
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = temp_path / "eval_files.csv"

        csv_content = """original_file;human_defined_name
test_file_01.png;20250623_Ideativa_Receipt paid by Ideativa to RFB 1838BRL.png
test_file_02.pdf;20250620_Ideativa_Tax Ideativa Work INSS and IRPF.pdf
test_file_03.xlsx;20250907_SCM_Inventory policy example workbook.xlsx"""

        csv_path.write_text(csv_content)

        # Load ground truth data (cli.py expects evals directory, not CSV path)
        ground_truth = load_ground_truth_data(temp_path)

        # Verify loaded data structure and content
        assert len(ground_truth) == 3, f"Expected 3 entries, got {len(ground_truth)}"
        assert 'test_file_01.png' in ground_truth
        assert 'test_file_02.pdf' in ground_truth
        assert 'test_file_03.xlsx' in ground_truth

        # Verify ground truth names
        assert ground_truth['test_file_01.png'] == '20250623_Ideativa_Receipt paid by Ideativa to RFB 1838BRL.png'
        assert ground_truth['test_file_02.pdf'] == '20250620_Ideativa_Tax Ideativa Work INSS and IRPF.pdf'
        assert ground_truth['test_file_03.xlsx'] == '20250907_SCM_Inventory policy example workbook.xlsx'


def test_ground_truth_csv_error_handling():
    """Test graceful handling of CSV parsing errors."""
    # Test with malformed CSV
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        csv_path = temp_path / "eval_files.csv"

        malformed_csv = """original_file;human_defined_name
test_file_01.png
missing_column_name
test_file_02.pdf;valid_name.pdf"""

        csv_path.write_text(malformed_csv)

        # Should handle malformed CSV gracefully
        ground_truth = load_ground_truth_data(temp_path)

        # Should load valid entries despite malformed ones
        assert len(ground_truth) >= 1
        if 'test_file_02.pdf' in ground_truth:
            assert ground_truth['test_file_02.pdf'] == 'valid_name.pdf'


def test_file_iteration_and_content_extraction():
    """Test iterating through files and extracting content."""
    # Create temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files of different types
        test_files = {
            "test.txt": "This is a test text file about financial results.",
            "test.json": '{"type": "report", "content": "quarterly analysis"}',
            "test.csv": "date,amount,description\n2024-01-01,100,test transaction"
        }

        created_files = []
        for filename, content in test_files.items():
            file_path = temp_path / filename
            file_path.write_text(content)
            created_files.append(file_path)

        # Test content extraction for each file
        for file_path in created_files:
            content = extract_file_content(file_path)
            assert content is not None, f"Failed to extract content from {file_path.name}"
            assert len(content) > 0, f"Empty content extracted from {file_path.name}"

            # Verify content matches expected
            original_content = test_files[file_path.name]
            assert original_content in content, f"Content mismatch for {file_path.name}"


def test_evaluation_metadata_extraction():
    """Test metadata extraction for evaluation files."""
    # Create temporary file with known content
    test_content = "Sample document content for metadata extraction testing. " * 15

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        file_path = f.name

    try:
        file_obj = Path(file_path)

        # Extract metadata as would be done in evaluation
        content = extract_file_content(file_obj)

        file_type = file_obj.suffix.lstrip(".") or "unknown"
        text_length = len(content) if content else 0
        extractor = "direct" if file_type in ["txt", "md", "csv", "json", "yaml", "yml", "xml", "html", "htm", "css"] else "docling"

        # Verify metadata values
        assert file_type == "txt", f"Expected file_type 'txt', got '{file_type}'"
        assert text_length > 0, f"Expected positive text_length, got {text_length}"
        assert extractor == "direct", f"Expected extractor 'direct' for text file, got '{extractor}'"

    finally:
        os.unlink(file_path)




if __name__ == "__main__":
    # Run just the failing test to debug
    try:
        test_ground_truth_csv_error_handling()
        print("✓ test_ground_truth_csv_error_handling")
    except AssertionError as e:
        print(f"✗ test_ground_truth_csv_error_handling: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"- test_ground_truth_csv_error_handling: {e}")
        import traceback
        traceback.print_exc()