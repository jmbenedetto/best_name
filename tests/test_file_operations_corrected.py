#!/usr/bin/env python3
"""
Corrected file operations tests for Task 3.4.
Handles ClickException and SystemExit properly.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

# Add the best_name module to path
sys.path.insert(0, str(Path(__file__).parent / "best_name"))

from best_name.cli import cli


def test_copy_operation():
    """Test file copy operation with mocked DSPy prediction."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test_document.txt"
        original_file.write_text("Test content for copy operation - this is a meaningful document")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("test_copy", 0.95)

                result = runner.invoke(cli, [
                    str(original_file),
                    '--copy'
                ])

                assert result.exit_code == 0
                assert "File copied to: test_copy.txt" in result.output

                # Verify the copy was created
                copied_file = temp_path / "test_copy.txt"
                assert copied_file.exists()
                assert copied_file.read_text() == "Test content for copy operation - this is a meaningful document"


def test_rename_operation():
    """Test file rename operation with mocked DSPy prediction."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test_original.txt"
        original_file.write_text("Test content for rename operation - this is a meaningful document")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("test_rename", 0.88)

                result = runner.invoke(cli, [
                    str(original_file),
                    '--rename'
                ])

                assert result.exit_code == 0
                assert "File renamed to: test_rename.txt" in result.output

                # Verify the rename was completed
                renamed_file = temp_path / "test_rename.txt"
                assert renamed_file.exists()
                assert renamed_file.read_text() == "Test content for rename operation - this is a meaningful document"

                # Verify original file no longer exists
                assert not original_file.exists()


def test_extension_preservation():
    """Test that file operations preserve original file extensions."""
    runner = CliRunner()

    test_cases = [
        ("document.txt", "suggested_name.txt"),
        ("report.md", "suggested_name.md"),
        ("data.csv", "suggested_name.csv")
    ]

    for original_name, expected_name in test_cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_file = temp_path / original_name
            original_file.write_text("This is test content for the file to ensure proper extraction")

            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
                with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                    mock_prediction.return_value = ("suggested_name", None)

                    result = runner.invoke(cli, [
                        str(original_file),
                        '--copy'
                    ])

                    assert result.exit_code == 0
                    assert expected_name in result.output

                    # Verify the copied file has correct extension
                    copied_file = temp_path / expected_name
                    assert copied_file.exists()


def test_target_exists_error():
    """Test error when target file already exists (ClickException handling)."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "original.txt"
        original_file.write_text("This is test content to ensure proper extraction")

        # Create a target file that already exists
        existing_target = temp_path / "existing_filename.txt"
        existing_target.write_text("Existing content")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("existing_filename", None)

                result = runner.invoke(cli, [
                    str(original_file),
                    '--copy'
                ])

                # ClickException causes SystemExit with code 1
                assert result.exit_code == 1
                assert "Target file 'existing_filename.txt' already exists" in result.output


def run_corrected_file_operation_tests():
    """Run corrected file operation tests."""
    print("Running Corrected File Operation Tests...")
    print("=" * 45)

    tests = [
        test_copy_operation,
        test_rename_operation,
        test_extension_preservation,
        test_target_exists_error
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print("=" * 45)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All corrected file operation tests passed!")
    else:
        print(f"WARNING: {failed} corrected file operation tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_corrected_file_operation_tests()
    sys.exit(0 if success else 1)