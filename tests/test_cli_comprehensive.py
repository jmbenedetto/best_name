#!/usr/bin/env python3
"""
Comprehensive CLI functionality test for Task Group 3.
Verifies all critical CLI behaviors are preserved.
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


def test_cli_argument_validation():
    """Test all CLI arguments are properly validated."""
    runner = CliRunner()

    # Test all options are available in help
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0

    expected_options = [
        '--conventions PATH', '--system-prompt PATH', '--api-key TEXT',
        '--model TEXT', '--base-url TEXT', '--config PATH',
        '--copy', '--rename', '--verbose'
    ]

    help_output = result.output
    for option in expected_options:
        assert option in help_output, f"Expected option '{option}' missing from help"


def test_mutual_exclusion_enforcement():
    """Test that --copy and --remain are mutually exclusive."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        test_file = Path(f.name)

    try:
        result = runner.invoke(cli, [str(test_file), '--copy', '--rename'])
        assert result.exit_code != 0
        assert "Cannot use both --copy and --rename" in result.output

    finally:
        test_file.unlink()


def test_file_path_validation():
    """Test file path argument validation."""
    runner = CliRunner()

    # Test non-existent file
    result = runner.invoke(cli, ['/non/existent/file.txt'])
    assert result.exit_code != 0


def test_configuration_hierarchy():
    """Test that configuration hierarchy works correctly."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content for configuration testing")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("config_test", None)

                result = runner.invoke(cli, [str(original_file)])
                # Should succeed in loading package configuration
                assert result.exit_code == 0


def test_copy_operation():
    """Test file copy operation."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test_copy.txt"
        original_file.write_text("Test content for copy operation")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("copied_file", None)

                result = runner.invoke(cli, [str(original_file), '--copy'])
                assert result.exit_code == 0
                assert "File copied to: copied_file.txt" in result.output

                copied_file = temp_path / "copied_file.txt"
                assert copied_file.exists()


def test_rename_operation():
    """Test file rename operation."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test_rename.txt"
        original_file.write_text("Test content for rename operation")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("renamed_file", None)

                result = runner.invoke(cli, [str(original_file), '--rename'])
                assert result.exit_code == 0
                assert "File renamed to: renamed_file.txt" in result.output

                renamed_file = temp_path / "renamed_file.txt"
                assert renamed_file.exists()
                assert not original_file.exists()


def test_extension_preservation():
    """Test that file extensions are preserved."""
    runner = CliRunner()

    extensions = ['.txt', '.md', '.csv']
    for ext in extensions:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_file = temp_path / f"test{ext}"
            original_file.write_text("Test content")

            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
                with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                    mock_prediction.return_value = ("preserved_ext", None)

                    result = runner.invoke(cli, [str(original_file), '--copy'])
                    assert result.exit_code == 0

                    copied_file = temp_path / f"preserved_ext{ext}"
                    assert copied_file.exists()


def test_filename_sanitization():
    """Test filename sanitization logic."""
    from best_name.cli import sanitize_filename

    # Test various problematic characters
    assert sanitize_filename("file:name") == "file name"
    assert sanitize_filename("file\\name") == "file name"
    assert sanitize_filename("file?name") == "file name"
    assert sanitize_filename("file*name") == "file name"
    assert sanitize_filename('file"name') == "file name"
    assert sanitize_filename("file<name>") == "file name"
    assert sanitize_filename("file|name") == "file name"
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename(None) == "untitled"
    assert len(sanitize_filename("a" * 200)) <= 120


def test_verbose_output():
    """Test verbose output structure."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content for verbose testing")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("verbose_test", 0.85)

                result = runner.invoke(cli, [str(original_file), '--verbose'])
                assert result.exit_code == 0

                expected_sections = [
                    "Best Name CLI - DSPy Enhanced",
                    "Step 1: Resolving file paths",
                    "Step 2: Loading content files",
                    "Step 3: OpenRouter configuration",
                    "Step 4: Extracting content",
                    "Step 5: Using DSPy for filename prediction",
                    "Step 6: Calling DSPy prediction",
                    "DSPy Prediction Result"
                ]

                for section in expected_sections:
                    assert section in result.output


def test_error_handling():
    """Test error handling for file operations."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "original.txt"
        original_file.write_text("Test content")

        # Create target file that already exists
        existing_target = temp_path / "existing.txt"
        existing_target.write_text("Existing content")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("existing", None)

                result = runner.invoke(cli, [str(original_file), '--copy'])
                assert result.exit_code == 1
                assert "Target file 'existing.txt' already exists" in result.output


def run_comprehensive_cli_tests():
    """Run comprehensive CLI functionality tests."""
    print("Running Comprehensive CLI Functionality Tests...")
    print("=" * 55)

    tests = [
        test_cli_argument_validation,
        test_mutual_exclusion_enforcement,
        test_file_path_validation,
        test_configuration_hierarchy,
        test_copy_operation,
        test_rename_operation,
        test_extension_preservation,
        test_filename_sanitization,
        test_verbose_output,
        test_error_handling
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

    print("=" * 55)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All comprehensive CLI functionality tests passed!")
    else:
        print(f"WARNING: {failed} comprehensive CLI functionality tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_cli_tests()
    sys.exit(0 if success else 1)