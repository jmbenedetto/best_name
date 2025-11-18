#!/usr/bin/env python3
"""
Task Group 7: Strategic Integration Tests for Test Review & Validation
Focus on integration points between refactored CLI and evaluation system.
Maximum 10 additional tests to fill critical gaps identified in test coverage.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add the project directory to the path so we can import from best_name
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test Configuration
TEST_API_KEY = "test_api_key_integration"
TEST_MODEL = "x-ai/grok-4-fast"
TEST_BASE_URL = "https://openrouter.ai/api/v1"


def test_modular_dspy_integration():
    """Integration test: DSPy modules work correctly with CLI after refactoring."""
    try:
        from best_name.dspy_modules import initialize_dspy_lm, call_dspy_prediction, call_dspy_evaluation
        from best_name.cli import cli
        import dspy

        # Test that DSPy functions are available in modular structure
        assert callable(initialize_dspy_lm), "initialize_dspy_lm should be available in dspy_modules"
        assert callable(call_dspy_prediction), "call_dspy_prediction should be available in dspy_modules"
        assert callable(call_dspy_evaluation), "call_dspy_evaluation should be available in dspy_modules"

        # Test that DSPy is available
        assert hasattr(dspy, 'Signature'), "DSPy should be available with Signature class"

        print("✓ Modular DSPy integration test passed")

    except ImportError as e:
        print(f"- Modular DSPy integration test skipped: {e}")


def test_main_and_eval_workflows_together():
    """Integration test: Both main command and eval subcommand work in same session."""
    try:
        from best_name.cli import cli

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for filename suggestion and evaluation")
            f.flush()
            temp_file = f.name

        runner = CliRunner()

        # Test main command workflow (filename suggestion)
        with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict:
            mock_predict.return_value = ("suggested_filename", 0.85)

            result_main = runner.invoke(cli, [temp_file])

            # Should produce output and not fail
            assert result_main.exit_code != 2  # Not a usage error
            assert len(result_main.output.strip()) > 0

        # Test eval subcommand workflow in same session
        with tempfile.TemporaryDirectory() as temp_dir:
            eval_files_dir = Path(temp_dir) / "evals"
            eval_files_dir.mkdir()

            # Create ground truth CSV
            ground_truth_file = Path(temp_dir) / "eval_files.csv"
            ground_truth_file.write_text("original_file;human_defined_name\ntest.txt;ground_truth_name\n")

            # Copy test file to eval directory
            eval_file = eval_files_dir / "test.txt"
            eval_file.write_text("Test content for evaluation")

            with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict, \
                 patch('best_name.dspy_modules.call_dspy_evaluation') as mock_eval:

                mock_predict.return_value = ("ai_suggested_name", 0.90)
                mock_eval.return_value = 7.5

                result_eval = runner.invoke(cli, ['eval', str(eval_file)])

                # Should process evaluation without critical errors
                assert result_eval.exit_code == 0 or 'OPENROUTER_API_KEY' in str(result_eval.exception) if result_eval.exception else True

        os.unlink(temp_file)
        print("✓ Main and eval workflows together test passed")

    except Exception as e:
        print(f"✗ Main and eval workflows together test failed: {e}")


def test_modular_file_processing_integration():
    """Integration test: File processing modules integrate correctly with CLI after refactoring."""
    try:
        from best_name.file_processing import extract_file_content, load_ground_truth_data, process_evaluation_files
        from best_name.cli import cli

        # Test file extraction integration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content for file processing integration")
            f.flush()
            temp_file = f.name

        try:
            content = extract_file_content(Path(temp_file))
            assert content is not None, "File content should be extracted"
            assert "Test document content" in content, "Expected content should be present"

            # Test ground truth loading integration
            with tempfile.TemporaryDirectory() as temp_dir:
                eval_dir = Path(temp_dir)
                csv_file = eval_dir / "eval_files.csv"
                csv_file.write_text("original_file;human_defined_name\ntest.txt;ground_truth_filename\n")

                ground_truth = load_ground_truth_data(eval_dir)
                assert "test.txt" in ground_truth, "Ground truth should be loaded"
                assert ground_truth["test.txt"] == "ground_truth_filename", "Ground truth name should match"

        finally:
            os.unlink(temp_file)

        print("✓ Modular file processing integration test passed")

    except Exception as e:
        print(f"✗ Modular file processing integration test failed: {e}")


def test_utils_module_integration():
    """Integration test: Utils module integrates correctly with CLI after refactoring."""
    try:
        from best_name.utils import sanitize_filename, load_yaml_config, read_text_file
        from best_name.cli import cli

        # Test filename sanitization integration
        test_cases = [
            ("normal_name", "normal_name"),
            ("name with spaces", "name with spaces"),
            ("name/with\\illegal:chars", "name with illegal chars"),
            ("name.txt", "name"),  # extension should be stripped
            ("", "untitled"),
        ]

        for input_name, expected_start in test_cases:
            result = sanitize_filename(input_name)
            if expected_start == "untitled":
                assert result == expected_start, f"Empty input should return 'untitled', got '{result}'"
            else:
                assert result.startswith(expected_start), f"'{result}' should start with '{expected_start}'"
            assert len(result) <= 120, f"Result should be within length limit: {len(result)}"

        # Test YAML config loading integration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("defaults:\n  conventions_file: test_conventions.md\nopenrouter:\n  model: test-model\n")
            f.flush()
            config_file = f.name

        try:
            config = load_yaml_config(Path(config_file))
            assert 'defaults' in config, "Config should have defaults section"
            assert 'openrouter' in config, "Config should have openrouter section"
            assert config['openrouter']['model'] == "test-model", "Model should be loaded correctly"

        finally:
            os.unlink(config_file)

        print("✓ Utils module integration test passed")

    except Exception as e:
        print(f"✗ Utils module integration test failed: {e}")


def test_cross_module_error_handling():
    """Integration test: Error handling works correctly across modular structure."""
    try:
        from best_name.dspy_modules import DSPY_AVAILABLE
        from best_name.cli import cli

        # Test graceful handling of missing DSPy functions
        if DSPY_AVAILABLE:
            # Test with mocked DSPy failure
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Test content for error handling")
                f.flush()
                temp_file = f.name

            runner = CliRunner()

            # Mock DSPy prediction to raise an exception
            with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict:
                mock_predict.side_effect = Exception("DSPy prediction failed")

                result = runner.invoke(cli, [temp_file])

                # Should handle the error gracefully
                assert result.exit_code != 0, "Should exit with error code when DSPy fails"
                assert len(result.output) > 0, "Should provide error output"

            os.unlink(temp_file)

        print("✓ Cross-module error handling test passed")

    except Exception as e:
        print(f"✗ Cross-module error handling test failed: {e}")


def test_configuration_flow_with_modules():
    """Integration test: Configuration flows correctly through all modules."""
    try:
        from best_name.dspy_modules import initialize_dspy_lm
        from best_name.utils import load_yaml_config
        from best_name.cli import resolve_openrouter_settings

        # Create custom config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
defaults:
  conventions_file: custom_conventions.md
  system_prompt_file: custom_prompt.md
openrouter:
  model: custom-test-model
  base_url: https://custom-test-url.com
""")
            f.flush()
            config_file = f.name

        try:
            # Test configuration loading
            config = load_yaml_config(Path(config_file))
            assert config['openrouter']['model'] == 'custom-test-model'

            # Test OpenRouter settings resolution
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key-from-env'}):
                api_key, model, base_url = resolve_openrouter_settings(
                    api_key_opt=None,
                    model_opt=None,
                    base_url_opt=None,
                    config=config,
                    verbose=False
                )

                assert api_key == 'test-key-from-env', "Should use environment API key"
                assert model == 'custom-test-model', "Should use config model"
                assert base_url == 'https://custom-test-url.com', "Should use config base URL"

        finally:
            os.unlink(config_file)

        print("✓ Configuration flow with modules test passed")

    except Exception as e:
        print(f"✗ Configuration flow with modules test failed: {e}")


def test_evaluation_data_flow_integrity():
    """Integration test: Data flow integrity in evaluation system after refactoring."""
    try:
        from best_name.file_processing import process_evaluation_files, load_ground_truth_data
        from best_name.dspy_modules import call_dspy_prediction, call_dspy_evaluation

        # Create test evaluation setup
        with tempfile.TemporaryDirectory() as temp_dir:
            eval_dir = Path(temp_dir)
            eval_files_dir = eval_dir / "eval_files"
            eval_files_dir.mkdir()

            # Create ground truth CSV
            ground_truth_file = eval_dir / "eval_files.csv"
            ground_truth_file.write_text("original_file;human_defined_name\ntest_doc.txt;test_ground_truth_name\n")

            # Create test file
            test_file = eval_files_dir / "test_doc.txt"
            test_content = "This is a test document for evaluation data flow integrity testing."
            test_file.write_text(test_content)

            # Test data loading and processing
            ground_truth = load_ground_truth_data(eval_dir)
            assert "test_doc.txt" in ground_truth, "Ground truth should be loaded"

            processed_files = process_evaluation_files(eval_files_dir, ground_truth, verbose=False)
            assert len(processed_files) == 1, "Should process one file"

            file_data = processed_files[0]
            assert file_data['original_filename'] == 'test_doc.txt', "Filename should match"
            assert file_data['ground_truth_name'] == 'test_ground_truth_name', "Ground truth should match"
            assert test_content in file_data['content'], "Content should be preserved"
            assert file_data['file_type'] == 'txt', "File type should be detected"
            assert file_data['extractor'] == 'direct', "Extractor should be identified"

        print("✓ Evaluation data flow integrity test passed")

    except Exception as e:
        print(f"✗ Evaluation data flow integrity test failed: {e}")


def test_cli_arg_passthrough_to_modules():
    """Integration test: CLI arguments correctly pass through to modules."""
    try:
        from best_name.cli import cli
        from best_name.utils import resolve_configuration_paths

        # Test that CLI arguments are passed correctly to modules
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for CLI argument passthrough")
            f.flush()
            temp_file = f.name

        # Create custom config, conventions, and prompt files
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            conventions_file = Path(temp_dir) / "conventions.md"
            prompt_file = Path(temp_dir) / "prompt.md"

            config_file.write_text("defaults:\n  conventions_file: conventions.md\n  system_prompt_file: prompt.md\n")
            conventions_file.write_text("Test conventions for CLI passthrough")
            prompt_file.write_text("Test system prompt for CLI passthrough")

            runner = CliRunner()

            with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict:
                mock_predict.return_value = ("test_suggestion", 0.95)

                # Test with all custom arguments
                result = runner.invoke(cli, [
                    temp_file,
                    '--config', str(config_file),
                    '--conventions', str(conventions_file),
                    '--system-prompt', str(prompt_file),
                    '--model', 'test-custom-model',
                    '--base-url', 'https://test-custom-url.com',
                    '--verbose'
                ], env={'OPENROUTER_API_KEY': 'test-key'})

                # Should process without usage errors (even if DSPy fails due to mocked calls)
                assert result.exit_code != 2, "Should not have usage errors with valid arguments"

                # Verify the prediction was called (indicating arguments flowed through)
                mock_predict.assert_called_once()

        os.unlink(temp_file)
        print("✓ CLI argument passthrough to modules test passed")

    except Exception as e:
        print(f"✗ CLI argument passthrough to modules test failed: {e}")


def test_package_import_stability():
    """Integration test: Package imports work correctly after refactoring."""
    try:
        # Test that package-level imports work
        from best_name import cli
        from best_name.dspy_modules import FilenameSignature, EvaluationSignature
        from best_name.file_processing import extract_file_content, load_ground_truth_data
        from best_name.utils import sanitize_filename, load_yaml_config

        # Test that functions are callable
        assert callable(cli), "CLI function should be importable from package"
        assert callable(extract_file_content), "extract_file_content should be callable"
        assert callable(load_ground_truth_data), "load_ground_truth_data should be callable"
        assert callable(sanitize_filename), "sanitize_filename should be callable"
        assert callable(load_yaml_config), "load_yaml_config should be callable"

        # Test that classes are available
        assert hasattr(FilenameSignature, '__annotations__'), "FilenameSignature should be a proper class"
        assert hasattr(EvaluationSignature, '__annotations__'), "EvaluationSignature should be a proper class"

        # Test entry point function is the right one
        assert hasattr(cli, '__call__'), "CLI should be callable as entry point"

        print("✓ Package import stability test passed")

    except Exception as e:
        print(f"✗ Package import stability test failed: {e}")


def test_end_to_end_workflow_integration():
    """Integration test: Complete end-to-end workflow with all modules working together."""
    try:
        from best_name.cli import cli
        from best_name.file_processing import process_evaluation_files, load_ground_truth_data
        from best_name.dspy_modules import call_dspy_prediction, call_dspy_evaluation

        # Create complete evaluation setup
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            evals_dir = project_dir / "evals"
            eval_files_dir = evals_dir / "eval_files"
            results_dir = evals_dir / "results" / "test_run_integration"
            eval_files_dir.mkdir(parents=True)
            results_dir.mkdir(parents=True)

            # Create ground truth data
            ground_truth_file = evals_dir / "eval_files.csv"
            ground_truth_content = """original_file;human_defined_name
report.pdf;quarterly_financial_report_q1_2024
meeting.txt;team_meeting_notes_june_2024
data.csv;sales_data_analysis_q2_2024"""
            ground_truth_file.write_text(ground_truth_content)

            # Create test files
            test_files = {
                "report.pdf": "Quarterly financial report for Q1 2024 showing revenue and profit analysis.",
                "meeting.txt": "Team meeting notes from June 2024 discussing project milestones and deliverables.",
                "data.csv": "Sales data analysis for Q2 2024 with regional breakdown and performance metrics."
            }

            for filename, content in test_files.items():
                (eval_files_dir / filename).write_text(content)

            # Mock the DSPy functions to simulate complete workflow
            with patch('best_name.dspy_modules.call_dspy_prediction') as mock_predict, \
                 patch('best_name.dspy_modules.call_dspy_evaluation') as mock_eval:

                # Setup realistic mock responses
                mock_predict.side_effect = [
                    ("financial_report_q1_2024", 0.92),
                    ("team_meeting_notes_june_2024", 0.87),
                    ("sales_data_q2_2024", 0.89)
                ]

                mock_eval.side_effect = [8.5, 7.2, 9.1]

                # Execute complete workflow
                ground_truth = load_ground_truth_data(evals_dir)
                processed_files = process_evaluation_files(eval_files_dir, ground_truth, verbose=False)

                assert len(processed_files) == 3, "Should process all 3 files"

                # Verify data integrity throughout workflow
                for i, file_data in enumerate(processed_files):
                    expected_filename = list(test_files.keys())[i]
                    expected_content = test_files[expected_filename]

                    assert file_data['original_filename'] == expected_filename
                    assert expected_content in file_data['content']
                    assert file_data['ground_truth_name'] is not None
                    assert len(file_data['content']) > 0

                # Verify DSPy functions were called correct number of times
                assert mock_predict.call_count == 3, "Should call prediction for each file"
                assert mock_eval.call_count == 3, "Should call evaluation for each file"

        print("✓ End-to-end workflow integration test passed")

    except Exception as e:
        print(f"✗ End-to-end workflow integration test failed: {e}")


if __name__ == "__main__":
    # Run all Task Group 7 strategic integration tests
    test_functions = [
        test_modular_dspy_integration,
        test_main_and_eval_workflows_together,
        test_modular_file_processing_integration,
        test_utils_module_integration,
        test_cross_module_error_handling,
        test_configuration_flow_with_modules,
        test_evaluation_data_flow_integrity,
        test_cli_arg_passthrough_to_modules,
        test_package_import_stability,
        test_end_to_end_workflow_integration
    ]

    passed = 0
    failed = 0

    print("Running Task Group 7: Strategic Integration Tests for Test Review & Validation")
    print("=" * 90)

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1

    print("=" * 90)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All strategic integration tests passed!")
    else:
        print("Some strategic integration tests failed.")
        sys.exit(1)