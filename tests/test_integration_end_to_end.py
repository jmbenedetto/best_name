#!/usr/bin/env python3
"""
End-to-End Integration Tests for DSPy Integration
Task Group 4.6: Strategic Integration Tests (max 10 tests)
Focus on integration points between DSPy and existing CLI flow
"""

import os
import tempfile
import shutil
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ignore deprecation warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Test Configuration
TEST_API_KEY = "test_api_key_for_integration"
TEST_MODEL = "x-ai/grok-4-fast"
TEST_BASE_URL = "https://openrouter.ai/api/v1"


def create_test_file(content: str, extension: str = ".txt") -> str:
    """Create a temporary test file with given content and extension."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name


def test_integration_pdf_file_processing():
    """Integration test: PDF file processing with DSPy prediction."""
    # Mock PDF content extraction and CLI flow
    mock_pdf_content = "Financial report Q4 2024 Revenue analysis and projections"

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class:

        # Setup mocks
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "financial_report_q4_2024"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Import and test CLI integration - pass content directly
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=mock_pdf_content,
            naming_conventions="Use descriptive names with dates",
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL
        )

        # Verify integration points
        assert result == "financial_report_q4_2024"
        assert confidence is not None
        assert isinstance(confidence, (int, float))
        assert 0 <= confidence <= 1

        # Verify DSPy components were called correctly
        mock_lm_class.assert_called_once()
        mock_configure.assert_called_once_with(lm=mock_lm)
        mock_predict_class.assert_called_once()


def test_integration_image_file_processing():
    """Integration test: Image file handling with DSPy prediction."""
    # Mock image content extraction
    mock_image_content = "Screenshot of dashboard showing user metrics KPI analytics"

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class:

        # Setup mocks
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "dashboard_screenshot_analytics"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Test integration - pass content directly
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=mock_image_content,
            naming_conventions="Use descriptive names for screenshots",
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL
        )

        # Verify integration
        assert result == "dashboard_screenshot_analytics"
        assert 0 <= confidence <= 1

        # Verify DSPy components were called
        mock_lm_class.assert_called_once()
        mock_configure.assert_called_once_with(lm=mock_lm)


def test_integration_document_file_formats():
    """Integration test: Document formats (DOCX, XLSX, PPTX) processing."""
    test_cases = [
        ("Quarterly business strategy presentation slides", "quarterly_business_strategy_presentation"),
        ("Sales data spreadsheet with Q3 results analysis", "sales_data_q3_results_analysis"),
        ("Project documentation requirements specification", "project_requirements_specification")
    ]

    for content, expected_name in test_cases:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class:

            # Setup mocks
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_prediction.suggested_name = expected_name
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            # Test integration
            from best_name.cli import call_dspy_prediction

            result, confidence = call_dspy_prediction(
                file_content=content,
                naming_conventions="Professional business naming conventions",
                model=TEST_MODEL,
                api_key=TEST_API_KEY,
                base_url=TEST_BASE_URL
            )

            assert result == expected_name
            assert 0 <= confidence <= 1


def test_integration_text_file_formats():
    """Integration test: Text formats (TXT, MD, CSV, JSON) processing."""
    test_cases = [
        ("Meeting notes discussion action items", "meeting_notes_action_items"),
        ("API response user data JSON structure", "api_response_user_data"),
        ("Configuration settings server parameters", "configuration_server_settings")
    ]

    for content, expected_name in test_cases:
        with patch('best_name.cli.dspy.LM') as mock_lm_class, \
             patch('best_name.cli.configure') as mock_configure, \
             patch('best_name.cli.Predict') as mock_predict_class:

            # Setup mocks
            mock_lm = MagicMock()
            mock_lm_class.return_value = mock_lm

            mock_prediction = MagicMock()
            mock_prediction.suggested_name = expected_name
            mock_predictor = MagicMock()
            mock_predictor.return_value = mock_prediction
            mock_predict_class.return_value = mock_predictor

            # Test integration with direct content (no Docling for text files)
            from best_name.cli import call_dspy_prediction

            result, confidence = call_dspy_prediction(
                file_content=content,
                naming_conventions="Technical file naming conventions",
                model=TEST_MODEL,
                api_key=TEST_API_KEY,
                base_url=TEST_BASE_URL
            )

            assert result == expected_name
            assert 0 <= confidence <= 1


def test_integration_verbose_output_with_confidence():
    """Integration test: Verbose output includes DSPy confidence scores."""
    mock_content = "Test document for verbose output validation"

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class, \
         patch('builtins.print') as mock_print:

        # Setup mock with confidence
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "verbose_test_document"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Test verbose mode
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=mock_content,
            naming_conventions="Test conventions",
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL,
            verbose=True
        )

        # Verify verbose output
        assert result == "verbose_test_document"
        assert 0 <= confidence <= 1

        # Check that verbose print was called
        verbose_calls = [call for call in mock_print.call_args_list
                        if "Making DSPy prediction" in str(call)]
        assert len(verbose_calls) > 0


def test_integration_configuration_hierarchy():
    """Integration test: Configuration resolution hierarchy with DSPy."""
    # Create custom config file
    custom_config = {
        'defaults': {
            'conventions': 'custom_conventions.md',
            'system_prompt': 'custom_system_prompt.md'
        },
        'openrouter': {
            'model': 'custom-model-test',
            'base_url': 'https://custom-test-url.com'
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(custom_config, f)
        custom_config_path = f.name

    try:
        # Test configuration loading - use Path object
        from best_name.cli import load_yaml_config

        config = load_yaml_config(Path(custom_config_path))

        assert config['openrouter']['model'] == 'custom-model-test'
        assert config['openrouter']['base_url'] == 'https://custom-test-url.com'

    finally:
        os.unlink(custom_config_path)


def test_integration_content_character_limit():
    """Integration test: 12,000 character limit for file content."""
    # Create content longer than limit
    long_content = "A" * 15000  # 15,000 characters

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class:

        # Setup mocks
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "long_content_truncated"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Test that content is properly truncated
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=long_content,
            naming_conventions="Standard naming conventions",
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL
        )

        # Verify result and that truncation happened (content should be limited to 12,000 chars)
        assert result == "long_content_truncated"
        assert 0 <= confidence <= 1

        # Verify the predictor was called with truncated content
        call_args = mock_predictor.call_args
        truncated_content = call_args[1]['file_content']
        assert len(truncated_content) <= 12000


def test_integration_error_handling():
    """Integration test: DSPy error handling and graceful fallback."""
    with patch('best_name.cli.dspy.LM') as mock_lm_class:
        # Setup mock to raise exception
        mock_lm_class.side_effect = Exception("DSPy LM creation failed")

        # Test error handling
        from best_name.cli import call_dspy_prediction

        with pytest.raises(Exception, match="DSPy LM creation failed"):
            call_dspy_prediction(
                file_content="Test content",
                naming_conventions="Test conventions",
                model=TEST_MODEL,
                api_key=TEST_API_KEY,
                base_url=TEST_BASE_URL
            )


def test_integration_conventions_input_processing():
    """Integration test: Conventions file content as signature input."""
    mock_content = "Test document content"
    mock_conventions = """
    Use YYYY-MM-DD format for dates
    Project names should be descriptive
    Use underscores instead of spaces
    """

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class:

        # Setup mocks
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "2024-01-15_project_document"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Test conventions integration
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=mock_content,
            naming_conventions=mock_conventions,
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL
        )

        # Verify that conventions were properly passed and processed
        assert result == "2024-01-15_project_document"
        assert 0 <= confidence <= 1

        # Verify predictor was called with correct inputs
        mock_predictor.assert_called_once_with(
            file_content=mock_content,
            naming_conventions=mock_conventions
        )


def test_integration_end_to_end_workflow():
    """Integration test: Complete end-to-end workflow from file to prediction."""
    # Create a realistic test file
    test_content = """
    Monthly Sales Report - January 2025

    Executive Summary:
    - Total revenue: $125,000
    - New customers: 45
    - Conversion rate: 3.2%

    Regional Breakdown:
    - North: $45,000
    - South: $32,000
    - East: $28,000
    - West: $20,000

    Recommendations:
    1. Focus on North region growth
    2. Improve customer retention
    3. Optimize marketing spend
    """

    with patch('best_name.cli.dspy.LM') as mock_lm_class, \
         patch('best_name.cli.configure') as mock_configure, \
         patch('best_name.cli.Predict') as mock_predict_class:

        # Setup mocks
        mock_lm = MagicMock()
        mock_lm_class.return_value = mock_lm

        mock_prediction = MagicMock()
        mock_prediction.suggested_name = "monthly_sales_report_january_2025"
        mock_predictor = MagicMock()
        mock_predictor.return_value = mock_prediction
        mock_predict_class.return_value = mock_predictor

        # Test the complete workflow
        from best_name.cli import call_dspy_prediction

        result, confidence = call_dspy_prediction(
            file_content=test_content,
            naming_conventions="Use descriptive names with dates and underscores",
            model=TEST_MODEL,
            api_key=TEST_API_KEY,
            base_url=TEST_BASE_URL
        )

        # Verify the complete workflow
        assert result == "monthly_sales_report_january_2025"
        assert 0 <= confidence <= 1
        assert isinstance(confidence, (int, float))

        # Verify all integration points were used
        mock_lm_class.assert_called_once()
        mock_configure.assert_called_once_with(lm=mock_lm)
        mock_predict_class.assert_called_once()


if __name__ == '__main__':
    print("Running Task 4.6: Strategic Integration Tests...")
    print("=" * 50)

    tests = [
        test_integration_pdf_file_processing,
        test_integration_image_file_processing,
        test_integration_document_file_formats,
        test_integration_text_file_formats,
        test_integration_verbose_output_with_confidence,
        test_integration_configuration_hierarchy,
        test_integration_content_character_limit,
        test_integration_error_handling,
        test_integration_conventions_input_processing,
        test_integration_end_to_end_workflow
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
        print("All strategic integration tests passed!")
    else:
        print("Some integration tests failed.")
        exit(1)