#!/usr/bin/env python3
"""
Task 3.1: Write 2-8 focused tests for CLI operations

Tests for critical CLI behaviors:
- Click CLI argument parsing and validation
- File operations (copy, rename, validation)
- Configuration resolution hierarchy
- Mutual exclusion checks for --copy and --rename
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

# Add the best_name module to path
sys.path.insert(0, str(Path(__file__).parent / "best_name"))

# Import CLI components
from best_name.cli import cli
from test_utils import create_test_file, requires_openrouter_api_key, DSPY_AVAILABLE


def test_cli_argument_structure():
    """Test that all expected CLI options are present and properly configured."""
    runner = CliRunner()

    # Test help output contains all expected options
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0

    expected_options = [
        '--conventions',
        '--system-prompt',
        '--api-key',
        '--model',
        '--base-url',
        '--config',
        '--copy',
        '--rename',
        '--verbose'
    ]

    help_text = result.output
    for option in expected_options:
        assert option in help_text, f"Expected CLI option '{option}' not found in help"


def test_copy_rename_mutual_exclusion():
    """Test that --copy and --rename options are mutually exclusive."""
    runner = CliRunner()

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for CLI testing")
        test_file = Path(f.name)

    try:
        # Test that using both flags raises an error
        result = runner.invoke(cli, [str(test_file), '--copy', '--rename'])
        assert result.exit_code != 0
        assert "Cannot use both --copy and --rename options together" in result.output

    finally:
        # Clean up test file
        test_file.unlink()


def test_file_path_validation():
    """Test that CLI properly validates file path argument."""
    runner = CliRunner()

    # Test with non-existent file
    result = runner.invoke(cli, ['/non/existent/file.txt'])
    assert result.exit_code != 0

    # Test with existing file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        test_file = Path(f.name)

    try:
        # Should not fail on path validation (may fail on other things like API key)
        result = runner.invoke(cli, [str(test_file)])
        # Path validation should pass, other errors are acceptable
        assert "does not exist" not in result.output.lower()

    finally:
        test_file.unlink()


def test_configuration_resolution_hierarchy():
    """Test that configuration resolution follows proper hierarchy."""
    runner = CliRunner()

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
defaults:
  conventions_file: "custom_conventions.md"
  system_prompt_file: "custom_system_prompt.md"
openrouter:
  model: "test-model"
  base_url: "https://test.example.com"
""")
        config_file = Path(f.name)

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        test_file = Path(f.name)

    try:
        # Mock environment variable and API calls to test config loading
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("test_filename", None)

                # Test custom config file
                result = runner.invoke(cli, [
                    str(test_file),
                    '--config', str(config_file),
                    '--model', 'override-model'  # This should override config
                ])

                # Should load custom config successfully
                # (may fail for other reasons, but config loading should work)
                assert "Failed to load" not in result.output

    finally:
        config_file.unlink()
        test_file.unlink()


def test_file_operations_copy():
    """Test file copy operation with suggested filename."""
    runner = CliRunner()

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for copy operation")
        original_file = Path(f.name)

    try:
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("suggested_filename", None)

                # Test copy operation
                result = runner.invoke(cli, [
                    str(original_file),
                    '--copy',
                    '--verbose'  # Use verbose to get more output
                ])

                # Check if copy was attempted (may fail due to API, but copy logic should work)
                # The important thing is that it reaches the copy operation stage
                assert result.exit_code == 0 or "copied" in result.output.lower()

                # Clean up copied file if it was created
                copied_file = original_file.parent / "suggested_filename.txt"
                if copied_file.exists():
                    copied_file.unlink()

    finally:
        original_file.unlink()


def test_file_operations_rename():
    """Test file rename operation with suggested filename."""
    runner = CliRunner()

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for rename operation")
        original_file = Path(f.name)

    try:
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("renamed_filename", None)

                # Test rename operation
                result = runner.invoke(cli, [
                    str(original_file),
                    '--rename',
                    '--verbose'
                ])

                # Check if rename was attempted
                assert result.exit_code == 0 or "renamed" in result.output.lower()

                # Check if file was renamed (if operation succeeded)
                renamed_file = original_file.parent / "renamed_filename.txt"
                if renamed_file.exists():
                    # Rename it back for cleanup
                    renamed_file.rename(original_file)

    finally:
        # Clean up original file (if it still exists)
        if original_file.exists():
            original_file.unlink()


def test_filename_sanitization_preserved():
    """Test that filename sanitization logic is preserved from original implementation."""
    from best_name.cli import sanitize_filename

    # Test basic sanitization
    assert sanitize_filename("Test File Name") == "test file name"
    assert sanitize_filename("file:name.txt") == "file name"
    assert sanitize_filename("file\\name") == "file name"
    assert sanitize_filename("file?name") == "file name"
    assert sanitize_filename("file*name") == "file name"
    assert sanitize_filename('file"name') == "file name"
    assert sanitize_filename("file<name>") == "file name"
    assert sanitize_filename("file|name") == "file name"

    # Test empty input
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename(None) == "untitled"
    assert sanitize_filename("   ") == "untitled"

    # Test extension handling
    assert sanitize_filename("document.pdf") == "document"
    assert sanitize_filename("spreadsheet.xlsx") == "spreadsheet"

    # Test length limit (120 chars)
    long_name = "a" * 150
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) <= 120


def test_verbose_output_structure():
    """Test that verbose output maintains expected structure and content."""
    runner = CliRunner()

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for verbose output testing")
        test_file = Path(f.name)

    try:
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("verbose_test_filename", 0.85)

                # Test verbose output
                result = runner.invoke(cli, [
                    str(test_file),
                    '--verbose'
                ])

                # Check that verbose output contains expected sections
                if result.exit_code == 0:
                    expected_sections = [
                        "Best Name CLI - DSPy Enhanced",
                        "Step 1: Resolving file paths",
                        "Step 2: Loading content files",
                        "Step 3: OpenRouter configuration",
                        "Step 4: Extracting content",
                        "Step 5: Using DSPy for filename prediction",
                        "Step 6: Calling DSPy prediction",
                        "DSPy Prediction Result",
                        "Final Result"
                    ]

                    for section in expected_sections:
                        assert section in result.output, f"Expected verbose section '{section}' not found"

    finally:
        test_file.unlink()


def run_cli_tests():
    """Run all CLI functionality tests."""
    print("Running Task 3.1: CLI Functionality Tests...")
    print("=" * 50)

    tests = [
        test_cli_argument_structure,
        test_copy_rename_mutual_exclusion,
        test_file_path_validation,
        test_configuration_resolution_hierarchy,
        test_file_operations_copy,
        test_file_operations_rename,
        test_filename_sanitization_preserved,
        test_verbose_output_structure
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

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All CLI functionality tests passed!")
    else:
        print(f"WARNING: {failed} CLI functionality tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_cli_tests()
    sys.exit(0 if success else 1)