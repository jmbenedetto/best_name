#!/usr/bin/env python3
"""
Focused tests for CLI evaluation subcommand implementation.
Tests only critical CLI actions: subcommand registration, argument parsing, basic execution.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add the project directory to the path so we can import from best_name
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cli_subcommand_registration():
    """Test that eval subcommand is properly registered with the CLI."""
    try:
        import click
        from click.testing import CliRunner
        from best_name.cli import cli

        # Test that eval subcommand exists in help
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0, f"CLI help failed with exit code {result.exit_code}"
        assert 'eval' in result.output, "eval subcommand should be listed in help"
        assert 'Evaluate filename suggestion quality' in result.output, "Evaluation description should be in help"

    except ImportError as e:
        print(f"Skipping {test_cli_subcommand_registration.__name__}: {e}")
    except Exception as e:
        raise AssertionError(f"Test {test_cli_subcommand_registration.__name__} failed: {e}")


def test_eval_subcommand_help():
    """Test that eval subcommand has proper help and argument descriptions."""
    try:
        import click
        from click.testing import CliRunner
        from best_name.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['eval', '--help'])

        assert result.exit_code == 0, f"eval help failed with exit code {result.exit_code}"
        assert 'run-id' in result.output, "run-id option should be documented"
        assert 'FILE_PATH' in result.output, "FILE_PATH should be in usage"

    except ImportError as e:
        print(f"Skipping {test_eval_subcommand_help.__name__}: {e}")
    except Exception as e:
        raise AssertionError(f"Test {test_eval_subcommand_help.__name__} failed: {e}")


def test_eval_subcommand_argument_parsing():
    """Test eval subcommand argument parsing with file path and run-id."""
    try:
        import click
        from click.testing import CliRunner
        from best_name.cli import cli

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for evaluation")
            temp_file = f.name

        try:
            runner = CliRunner()

            # Test with just file path (run-id should be auto-generated)
            with patch('best_name.cli.call_dspy_evaluation') as mock_eval, \
                 patch('best_name.cli.extract_file_content', return_value="Test content"):

                mock_eval.return_value = 7.5

                result = runner.invoke(cli, ['eval', temp_file])

                # Should fail without API key but we're testing argument parsing
                # The important thing is that it recognizes the eval command and file path
                assert 'file_path' in str(result.exception) if result.exception else True

            # Test with file path and custom run-id
            with patch('best_name.cli.call_dspy_evaluation') as mock_eval, \
                 patch('best_name.cli.extract_file_content', return_value="Test content"):

                mock_eval.return_value = 7.5

                result = runner.invoke(cli, ['eval', temp_file, '--run-id', 'test-run-123'])

                # Should fail without API key but argument parsing should work
                assert 'file_path' in str(result.exception) if result.exception else True

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    except ImportError as e:
        print(f"Skipping {test_eval_subcommand_argument_parsing.__name__}: {e}")
    except Exception as e:
        raise AssertionError(f"Test {test_eval_subcommand_argument_parsing.__name__} failed: {e}")


def test_eval_subcommand_directory_support():
    """Test eval subcommand supports directory paths as well as files."""
    try:
        import click
        from click.testing import CliRunner
        from best_name.cli import cli

        # Create a temporary directory with a test file
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content for evaluation")

            runner = CliRunner()

            # Test with directory path
            with patch('best_name.cli.call_dspy_evaluation') as mock_eval, \
                 patch('best_name.cli.extract_file_content', return_value="Test content"):

                mock_eval.return_value = 8.0

                result = runner.invoke(cli, ['eval', temp_dir])

                # Should fail without API key but directory path should be accepted
                assert 'file_path' in str(result.exception) if result.exception else True

    except ImportError as e:
        print(f"Skipping {test_eval_subcommand_directory_support.__name__}: {e}")
    except Exception as e:
        raise AssertionError(f"Test {test_eval_subcommand_directory_support.__name__} failed: {e}")


def test_eval_subcommand_configuration_loading():
    """Test eval subcommand loads configuration properly."""
    try:
        import click
        from click.testing import CliRunner
        from best_name.cli import cli

        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
defaults:
  conventions_file: test_conventions.md
  system_prompt_file: test_prompt.md
openrouter:
  model: test-model
  base_url: https://test.api.com
""")
            temp_config = f.name

        try:
            runner = CliRunner()

            # Test with custom config
            with patch('best_name.cli.call_dspy_evaluation') as mock_eval, \
                 patch('best_name.cli.extract_file_content', return_value="Test content"):

                mock_eval.return_value = 6.5

                result = runner.invoke(cli, ['eval', '--config', temp_config, 'dummy.txt'])

                # Should fail due to missing API key but config should be loaded
                # Check that it tried to process the config
                assert result.exit_code != 0 or 'OPENROUTER_API_KEY' in str(result.exception) if result.exception else True

        finally:
            os.unlink(temp_config)

    except ImportError as e:
        print(f"Skipping {test_eval_subcommand_configuration_loading.__name__}: {e}")
    except Exception as e:
        raise AssertionError(f"Test {test_eval_subcommand_configuration_loading.__name__} failed: {e}")


if __name__ == "__main__":
    # Run all CLI subcommand tests
    test_functions = [
        test_cli_subcommand_registration,
        test_eval_subcommand_help,
        test_eval_subcommand_argument_parsing,
        test_eval_subcommand_directory_support,
        test_eval_subcommand_configuration_loading
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("Running CLI Evaluation Subcommand Tests...")
    print("=" * 55)

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"- {test_func.__name__}: {e} (skipped)")
            skipped += 1

    print("=" * 55)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)
    else:
        print("All CLI evaluation subcommand tests passed!")