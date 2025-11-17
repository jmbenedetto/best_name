#!/usr/bin/env python3
"""
End-to-End Integration Tests for DSPy Evaluation Workflow
Task Group 5: End-to-End Integration Tests
Focus on complete evaluation workflow: CLI → data loading → content extraction → DSPy evaluation → results generation
"""

import os
import tempfile
import shutil
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import csv
from datetime import datetime
import sys

# Add the project directory to the path so we can import from best_name
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ignore deprecation warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Test Configuration
TEST_API_KEY = "test_api_key_for_eval"
TEST_MODEL = "x-ai/grok-4-fast"
TEST_BASE_URL = "https://openrouter.ai/api/v1"


def create_test_eval_setup():
    """Create a temporary evaluation setup with eval_files directory and ground truth data."""
    temp_dir = tempfile.mkdtemp()
    eval_dir = Path(temp_dir) / "evals"
    eval_files_dir = eval_dir / "eval_files"
    eval_files_dir.mkdir(parents=True)

    # Create ground truth CSV with proper format (semicolon delimited)
    ground_truth_file = eval_dir / "eval_files.csv"
    csv_content = """original_file;human_defined_name
test_doc.txt;test_document
report.pdf;quarterly_report
image.png;screenshot_analytics"""
    ground_truth_file.write_text(csv_content, encoding='utf-8')

    # Create test files
    (eval_files_dir / "test_doc.txt").write_text("This is a test document for evaluation")
    (eval_files_dir / "report.pdf").write_bytes(b"fake pdf content for testing")
    (eval_files_dir / "image.png").write_bytes(b"fake png content for testing")

    return temp_dir, eval_dir


def create_custom_config():
    """Create a custom config file for testing."""
    config_content = """
defaults:
  conventions_file: conventions.md
  system_prompt_file: system_prompt.md

openrouter:
  model: x-ai/grok-4-fast
  base_url: https://openrouter.ai/api/v1
"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    temp_file.write(config_content)
    temp_file.close()
    return temp_file.name


def test_end_to_end_single_file_evaluation():
    """End-to-end test: Single file evaluation workflow."""
    temp_dir, eval_dir = create_test_eval_setup()
    test_file = eval_dir / "eval_files" / "test_doc.txt"

    try:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class, \
             patch('best_name.cli.call_dspy_evaluation') as mock_eval:

            # Setup mocks for prediction
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_prediction.suggested_name = "test_document"
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            # Setup mocks for evaluation
            mock_eval.return_value = 8.5

            # Run evaluation using CliRunner
            from click.testing import CliRunner
            from best_name.cli import cli

            runner = CliRunner()
            with runner.isolated_filesystem(temp_dir=temp_dir):
                # Change to the temp directory so relative paths work
                os.chdir(temp_dir)

                result = runner.invoke(cli, [
                    'eval',
                    str(test_file),
                    '--run-id', 'test_run_single',
                    '--api-key', TEST_API_KEY,
                    '--model', TEST_MODEL,
                    '--base-url', TEST_BASE_URL
                ])

                # Should exit successfully
                assert result.exit_code == 0, f"CLI failed with exit code {result.exit_code}: {result.output}"

                # Verify results directory and files were created
                results_dir = Path(temp_dir) / "evals" / "results" / "test_run_single"
                assert results_dir.exists()

                csv_file = results_dir / "evaluation_results.csv"
                assert csv_file.exists()

                # Check CSV content
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]['original_filename'] == 'test_doc.txt'
                    assert rows[0]['suggested_name'] == 'test_document'
                    assert rows[0]['ground_truth_name'] == 'test_document'
                    assert rows[0]['score'] == '8.5'

                # Check markdown file was created
                md_file = results_dir / "test_doc_evaluation.md"
                assert md_file.exists()
                md_content = md_file.read_text()
                assert "Evaluation Results: test_doc.txt" in md_content
                assert "test_document" in md_content

    finally:
        shutil.rmtree(temp_dir)


def test_end_to_end_directory_evaluation():
    """End-to-end test: Directory evaluation workflow with multiple files."""
    temp_dir, eval_dir = create_test_eval_setup()

    try:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class, \
             patch('best_name.cli.call_dspy_evaluation') as mock_eval:

            # Setup mocks for prediction
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            # Setup different predictions for different files
            def side_effect_func(*args, **kwargs):
                content = kwargs.get('file_content', '')
                if 'test document' in content.lower():
                    mock_prediction.suggested_name = "test_document"
                elif 'report' in content.lower():
                    mock_prediction.suggested_name = "quarterly_report"
                else:
                    mock_prediction.suggested_name = "screenshot_analytics"
                return mock_prediction

            mock_predictor.side_effect = side_effect_func

            # Setup mocks for evaluation
            mock_eval.return_value = 7.0  # Consistent score for all files

            # Run evaluation using CliRunner
            from click.testing import CliRunner
            from best_name.cli import cli

            runner = CliRunner()
            with runner.isolated_filesystem(temp_dir=temp_dir):
                # Change to the temp directory so relative paths work
                os.chdir(temp_dir)

                result = runner.invoke(cli, [
                    'eval',
                    str(eval_dir / "eval_files"),
                    '--run-id', 'test_run_directory',
                    '--api-key', TEST_API_KEY,
                    '--model', TEST_MODEL,
                    '--base-url', TEST_BASE_URL
                ])

                # Should exit successfully
                assert result.exit_code == 0, f"CLI failed with exit code {result.exit_code}: {result.output}"

                # Verify results
                results_dir = Path(temp_dir) / "evals" / "results" / "test_run_directory"
                assert results_dir.exists()

                csv_file = results_dir / "evaluation_results.csv"
                assert csv_file.exists()

                # Check CSV has all files
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 3  # Should have all 3 files

                    filenames = [row['original_filename'] for row in rows]
                    assert 'test_doc.txt' in filenames
                    assert 'report.pdf' in filenames
                    assert 'image.png' in filenames

                # Check markdown files were created for each
                md_files = list(results_dir.glob("*_evaluation.md"))
                assert len(md_files) == 3

    finally:
        shutil.rmtree(temp_dir)


def test_end_to_end_evaluation_with_verbose_output():
    """End-to-end test: Evaluation workflow with verbose output enabled."""
    temp_dir, eval_dir = create_test_eval_setup()
    test_file = eval_dir / "eval_files" / "test_doc.txt"

    try:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class, \
             patch('best_name.cli.call_dspy_evaluation') as mock_eval:

            # Setup mocks
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_prediction.suggested_name = "test_document"
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            mock_eval.return_value = 9.2

            # Run evaluation with verbose flag using CliRunner
            from click.testing import CliRunner
            from best_name.cli import cli

            runner = CliRunner()
            with runner.isolated_filesystem(temp_dir=temp_dir):
                os.chdir(temp_dir)

                result = runner.invoke(cli, [
                    'eval',
                    str(test_file),
                    '--run-id', 'test_run_verbose',
                    '--api-key', TEST_API_KEY,
                    '--model', TEST_MODEL,
                    '--base-url', TEST_BASE_URL,
                    '--verbose'
                ])

                # Should exit successfully
                assert result.exit_code == 0, f"CLI failed with exit code {result.exit_code}: {result.output}"

                # Verify verbose output contains expected messages
                verbose_messages = [
                    "Best Name CLI - Evaluation Mode",
                    "Run ID: test_run_verbose",
                    "Processing evaluation files",
                    "Processing: test_doc.txt",
                    "Suggested: test_document",
                    "Score: 9.2/10",
                    "Evaluation complete"
                ]

                output = result.output
                for message in verbose_messages:
                    assert message in output, f"Missing verbose message: {message}"

    finally:
        shutil.rmtree(temp_dir)


def test_end_to_end_evaluation_error_handling():
    """End-to-end test: Evaluation workflow error handling and graceful degradation."""
    temp_dir, eval_dir = create_test_eval_setup()
    test_file = eval_dir / "eval_files" / "test_doc.txt"

    try:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class:

            # Setup mock to raise exception during prediction
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_predictor = MagicMock()
            mock_predictor.side_effect = Exception("DSPy prediction failed")
            mock_predict_class.return_value = mock_predictor

            # Run evaluation using CliRunner - should handle error gracefully
            from click.testing import CliRunner
            from best_name.cli import cli

            runner = CliRunner()
            with runner.isolated_filesystem(temp_dir=temp_dir):
                os.chdir(temp_dir)

                result = runner.invoke(cli, [
                    'eval',
                    str(test_file),
                    '--run-id', 'test_run_error',
                    '--api-key', TEST_API_KEY,
                    '--model', TEST_MODEL,
                    '--base-url', TEST_BASE_URL,
                    '--verbose'
                ])

                # Should still exit successfully despite errors (graceful handling)
                assert result.exit_code == 0, f"CLI should handle errors gracefully, but failed with exit code {result.exit_code}: {result.output}"

                # Verify error handling in verbose output
                assert "Error:" in result.output, "Expected error message in verbose output"

                # Results directory should still be created
                results_dir = Path(temp_dir) / "evals" / "results" / "test_run_error"
                assert results_dir.exists()

    finally:
        shutil.rmtree(temp_dir)


def test_end_to_end_evaluation_no_ground_truth():
    """End-to-end test: Evaluation workflow without ground truth data."""
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "standalone.txt"
    test_file.write_text("This is a standalone file without ground truth")

    try:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class:

            # Setup mocks
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_prediction.suggested_name = "standalone_file"
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            # Run evaluation without ground truth using CliRunner
            from click.testing import CliRunner
            from best_name.cli import cli

            runner = CliRunner()
            with runner.isolated_filesystem(temp_dir=temp_dir):
                os.chdir(temp_dir)

                result = runner.invoke(cli, [
                    'eval',
                    str(test_file),
                    '--run-id', 'test_run_no_ground_truth',
                    '--api-key', TEST_API_KEY,
                    '--model', TEST_MODEL,
                    '--base-url', TEST_BASE_URL
                ])

                # Should exit successfully
                assert result.exit_code == 0, f"CLI failed with exit code {result.exit_code}: {result.output}"

                # Verify results
                results_dir = Path(temp_dir) / "evals" / "results" / "test_run_no_ground_truth"
                assert results_dir.exists()

                csv_file = results_dir / "evaluation_results.csv"
                assert csv_file.exists()

                # Check CSV content
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]['original_filename'] == 'standalone.txt'
                    assert rows[0]['suggested_name'] == 'standalone_file'
                    assert rows[0]['ground_truth_name'] == ''  # Empty when no ground truth
                    assert rows[0]['score'] == '5.0'  # Default score when no ground truth

    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    print("Running Task Group 5: End-to-End Evaluation Integration Tests...")
    print("=" * 70)

    tests = [
        test_end_to_end_single_file_evaluation,
        test_end_to_end_directory_evaluation,
        test_end_to_end_evaluation_with_verbose_output,
        test_end_to_end_evaluation_error_handling,
        test_end_to_end_evaluation_no_ground_truth
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

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All end-to-end evaluation integration tests passed!")
    else:
        print("Some evaluation integration tests failed.")
        exit(1)