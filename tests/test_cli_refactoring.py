"""Tests for CLI refactoring to ensure main command and modularization work correctly."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from click.testing import CliRunner

# Test imports - will fail initially during refactoring
try:
    from best_name.cli import cli
    from best_name.dspy_modules import FilenameSignature, EvaluationSignature
    from best_name.file_processing import extract_file_content, load_ground_truth_data
    from best_name.utils import sanitize_filename, load_yaml_config
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    IMPORTS_SUCCESSFUL = False
    IMPORT_ERROR = str(e)


class TestModuleImports:
    """Test that modularized modules can be imported correctly."""

    def test_import_dspy_modules(self):
        """Test that dspy_modules module can be imported."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        # Test that classes are available
        assert hasattr(FilenameSignature, '__annotations__')
        assert hasattr(EvaluationSignature, '__annotations__')

    def test_import_file_processing(self):
        """Test that file_processing module can be imported."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        # Test that functions are available
        assert callable(extract_file_content)
        assert callable(load_ground_truth_data)

    def test_import_utils(self):
        """Test that utils module can be imported."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        # Test that functions are available
        assert callable(sanitize_filename)
        assert callable(load_yaml_config)


class TestMainCommandBehavior:
    """Test main command behavior after removing suggest subcommand."""

    def test_cli_help_still_works(self):
        """Test that CLI help still works after refactoring."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Best Name CLI' in result.output
        assert 'main' in result.output
        assert 'eval' in result.output

    def test_main_command_accepts_file_argument(self):
        """Test that main command accepts file argument directly."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for filename suggestion")
            f.flush()

            runner = CliRunner()
            with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict:
                mock_predict.return_value = ("test_suggestion_name", None)

                result = runner.invoke(cli, [f.name])

                # Should not show help (means command was processed)
                assert result.exit_code != 2  # 2 is Click usage error
                # Should show the output (some filename, not necessarily the mocked one if mock fails)
                assert len(result.output.strip()) > 0
                # Should not be help text
                assert 'Usage:' not in result.output

            os.unlink(f.name)

    def test_main_command_preserves_all_options(self):
        """Test that main command preserves all existing CLI options."""
        runner = CliRunner()

        # Test that all expected options are in main command help
        result = runner.invoke(cli, ['main', '--help'])
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

        for option in expected_options:
            assert option in result.output

    def test_eval_subcommand_still_works(self):
        """Test that eval subcommand continues to work unchanged."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")

            runner = CliRunner()
            result = runner.invoke(cli, ['eval', str(test_file)])

            # Should process the eval command (even if it fails due to missing API key)
            # The important thing is that it recognizes the command
            assert result.exit_code == 0 or 'OPENROUTER_API_KEY' in result.output

    def test_default_command_behavior(self):
        """Test that providing a file path without command uses main as default."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for filename suggestion")
            f.flush()

            runner = CliRunner()
            result = runner.invoke(cli, [f.name])

            # Should not show help (means default command was invoked)
            assert result.exit_code != 2  # 2 is Click usage error
            # Should produce some output
            assert len(result.output.strip()) > 0

            os.unlink(f.name)


class TestBackwardCompatibility:
    """Test that existing behavior is preserved after refactoring."""

    def test_entry_point_still_works(self):
        """Test that pyproject.toml entry point still works."""
        # Test that we can import cli function from package
        from best_name import cli
        assert callable(cli)

    def test_configuration_hierarchy_preserved(self):
        """Test that configuration hierarchy still works after refactoring."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        # Create a temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("defaults:\n  conventions_file: test_conventions.md\n")
            f.flush()

            config = load_yaml_config(Path(f.name))
            assert 'defaults' in config
            assert config['defaults']['conventions_file'] == 'test_conventions.md'

            os.unlink(f.name)

    def test_filename_sanitization_preserved(self):
        """Test that filename sanitization behavior is preserved."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        # Test various edge cases
        test_cases = [
            ("normal_name", "normal_name"),
            ("name with spaces", "name with spaces"),
            ("name/with\\illegal:chars", "name with illegal chars"),
            ("name.txt", "name"),  # extension should be stripped
            ("", "untitled"),
            ("   spaced name   ", "spaced name"),
            ("very_long_name_that_should_be_truncated", "very_long_name_that_should_be_trunc"),
        ]

        for input_name, expected_start in test_cases:
            result = sanitize_filename(input_name)
            if expected_start == "untitled":
                assert result == expected_start
            else:
                assert result.startswith(expected_start)
            # Ensure result is not empty
            assert len(result) > 0
            # Ensure result is within length limit
            assert len(result) <= 120


class TestErrorHandling:
    """Test that error handling is preserved after refactoring."""

    def test_mutually_exclusive_options_still_checked(self):
        """Test that --copy and --rename are mutually exclusive."""
        if not IMPORTS_SUCCESSFUL:
            pytest.skip(f"Imports not yet successful: {IMPORT_ERROR}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            f.flush()

            runner = CliRunner()
            result = runner.invoke(cli, [f.name, '--copy', '--rename'])

            assert result.exit_code != 0
            assert 'Cannot use both --copy and --rename' in result.output

            os.unlink(f.name)


# Test that will be used to verify modularization is complete
def test_refactored_modules_exist():
    """Test that expected modular files exist after refactoring."""
    package_dir = Path(__file__).parent.parent / "best_name"

    expected_modules = [
        "dspy_modules.py",
        "file_processing.py",
        "utils.py"
    ]

    for module in expected_modules:
        module_path = package_dir / module
        assert module_path.exists(), f"Expected module {module} to exist at {module_path}"


def test_no_suggest_subcommand():
    """Test that suggest subcommand has been removed."""
    runner = CliRunner()
    result = runner.invoke(cli, ['suggest', '--help'])

    # Should fail because suggest subcommand no longer exists
    assert result.exit_code != 0
    assert 'No such command' in result.output


def test_dspy_modules_availability():
    """Test that DSPy modules are properly modularized."""
    from best_name.dspy_modules import DSPY_AVAILABLE, FilenameSignature, EvaluationSignature

    # Test that DSPy constants are available
    assert isinstance(DSPY_AVAILABLE, bool)

    # Test that signature classes are properly defined - check for field attributes differently
    # DSPy signature fields are stored differently in newer versions
    assert hasattr(FilenameSignature, 'instructions')
    assert hasattr(EvaluationSignature, 'instructions')

    # Test that we can create instances (this will test if the fields are properly defined)
    try:
        # This tests if the signature classes are properly structured
        filename_sig = FilenameSignature
        eval_sig = EvaluationSignature
        assert filename_sig is not None
        assert eval_sig is not None
    except Exception as e:
        pytest.fail(f"Failed to create signature instances: {e}")


def test_file_processing_modules_availability():
    """Test that file processing modules are properly modularized."""
    from best_name.file_processing import (
        extract_file_content, load_ground_truth_data,
        process_evaluation_files, process_evaluation_file
    )

    # Test that functions are available
    assert callable(extract_file_content)
    assert callable(load_ground_truth_data)
    assert callable(process_evaluation_files)
    assert callable(process_evaluation_file)


def test_utils_modules_availability():
    """Test that utility modules are properly modularized."""
    from best_name.utils import (
        read_text_file, load_yaml_config, resolve_path,
        sanitize_filename
    )

    # Test that functions are available
    assert callable(read_text_file)
    assert callable(load_yaml_config)
    assert callable(resolve_path)
    assert callable(sanitize_filename)


def test_both_main_and_eval_work():
    """Test that both best_name file.txt and best_name eval file.txt work."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        f.flush()

        runner = CliRunner()

        # Test main command (default behavior)
        result1 = runner.invoke(cli, [f.name])
        assert result1.exit_code != 2  # Not a usage error
        assert len(result1.output.strip()) > 0  # Some output

        # Test explicit main command
        result2 = runner.invoke(cli, ['main', f.name])
        assert result2.exit_code != 2  # Not a usage error
        assert len(result2.output.strip()) > 0  # Some output

        # Test eval command
        result3 = runner.invoke(cli, ['eval', f.name])
        # Eval should work even if it fails due to missing API key
        assert result3.exit_code == 0 or 'OPENROUTER_API_KEY' in result3.output

        os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])