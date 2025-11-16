#!/usr/bin/env python3
"""
Task 2.1: Write 2-8 focused tests for prediction functionality

Tests for critical prediction behaviors:
- File content processing with 12,000 character limit
- Conventions integration with DSPy predictions
- Name generation and sanitization
- Confidence score extraction and display
- Error handling for DSPy prediction failures
"""

import os
import sys
import tempfile
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

# Add the best_name module to path
sys.path.insert(0, str(Path(__file__).parent / "best_name"))

# Import test utilities
from test_utils import (
    create_test_file,
    mock_dspy_prediction,
    mock_dspy_lm,
    requires_openrouter_api_key,
    DSPY_AVAILABLE
)

# Import CLI functions for testing
from cli import (
    FilenameSignature,
    initialize_dspy_lm,
    call_dspy_prediction,
    extract_file_content,
    sanitize_filename,
    DSPY_AVAILABLE as CLI_DSPY_AVAILABLE
)

def test_file_content_processing_character_limit():
    """Test that file content is properly truncated to 12,000 characters for DSPy predictions."""
    print("Testing file content processing with 12,000 character limit...")

    # Create a test file with content longer than 12,000 characters
    long_content = "This is test content. " * 1000  # ~25,000 characters

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(long_content)
        temp_file = Path(f.name)

    try:
        # Extract content using the same function as CLI
        extracted_content = extract_file_content(temp_file)

        assert extracted_content is not None, "Content should be extracted"
        assert len(extracted_content) > 12000, "Original content should be longer than limit"

        # Mock DSPy prediction to check content truncation
        with patch('cli.initialize_dspy_lm') as mock_init, \
             patch('cli.Predict') as mock_predict_class:

            mock_predictor = Mock()
            mock_predict_class.return_value = mock_predictor

            # Mock prediction result
            mock_result = Mock()
            mock_result.suggested_name = "test_filename"
            mock_result.confidence = 0.85
            mock_predictor.return_value = mock_result
            mock_init.return_value = Mock()

            # Call DSPy prediction
            suggested_name, confidence = call_dspy_prediction(
                file_content=extracted_content,
                naming_conventions="Test conventions",
                model="x-ai/grok-4-fast",
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1"
            )

            # Verify the predictor was called with truncated content
            mock_predictor.assert_called_once()
            call_args = mock_predictor.call_args
            sent_content = call_args[1]['file_content']

            assert len(sent_content) <= 12000, f"Content should be truncated to 12,000 chars, got {len(sent_content)}"
            assert sent_content.startswith("This is test content"), "Truncated content should preserve beginning"

        print("✓ Content properly truncated to 12,000 characters")

    finally:
        temp_file.unlink()

def test_conventions_integration():
    """Test that naming conventions are properly integrated into DSPy predictions."""
    print("Testing conventions integration with DSPy predictions...")

    test_content = " Quarterly financial report for Q1 2024 showing revenue and expenses "
    conventions_md = """
# Naming Conventions

## Financial Documents
- Use format: {type}_{period}_{year}
- Examples: financial_report_q1_2024, budget_summary_annual_2024
- Always lowercase with underscores
"""

    with patch('cli.initialize_dspy_lm') as mock_init, \
         patch('cli.Predict') as mock_predict_class:

        mock_predictor = Mock()
        mock_predict_class.return_value = mock_predictor

        # Mock prediction result that should follow conventions
        mock_result = Mock()
        mock_result.suggested_name = "financial_report_q1_2024"
        mock_result.confidence = 0.92
        mock_predictor.return_value = mock_result
        mock_init.return_value = Mock()

        # Call DSPy prediction with conventions
        suggested_name, confidence = call_dspy_prediction(
            file_content=test_content,
            naming_conventions=conventions_md,
            model="x-ai/grok-4-fast",
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1"
        )

        # Verify conventions were passed to predictor
        mock_predictor.assert_called_once()
        call_args = mock_predictor.call_args

        assert 'naming_conventions' in call_args[1], "naming_conventions should be passed to predictor"
        sent_conventions = call_args[1]['naming_conventions']
        assert "Naming Conventions" in sent_conventions, "Conventions content should be preserved"
        assert "financial_report_q1_2024" in sent_conventions, "Example formats should be included"

        # Verify result follows conventions
        assert suggested_name == "financial_report_q1_2024", f"Expected convention-based name, got '{suggested_name}'"
        assert confidence == 0.92, f"Expected confidence 0.92, got {confidence}"

    print("✓ Conventions properly integrated into DSPy predictions")

def test_name_generation_and_sanitization():
    """Test DSPy prediction generates names that are properly sanitized."""
    print("Testing name generation and sanitization...")

    test_content = "Meeting notes from the project planning session"
    conventions_md = "Use lowercase with spaces, no special characters"

    # Test various problematic outputs from DSPy that need sanitization
    test_cases = [
        ("Meeting Notes Project Planning", "meeting notes project planning"),  # Spaces preserved, lowercase
        ("Meeting Notes/Project Planning", "meeting notes project planning"),  # Forward slash becomes space
        ("Meeting\\Notes:Project*Planning", "meeting notes project planning"),  # Special chars become spaces
        ("  Meeting Notes  ", "meeting notes"),  # Extra whitespace trimmed
        ("", "untitled"),  # Empty response
        ("Meeting.Notes.Docx", "meeting.notes"),  # Only last extension removed
        ("a" * 150, "a" * 120),  # Too long response
    ]

    for raw_response, expected_sanitized in test_cases:
        with patch('cli.initialize_dspy_lm') as mock_init, \
             patch('cli.Predict') as mock_predict_class:

            mock_predictor = Mock()
            mock_predict_class.return_value = mock_predictor

            mock_result = Mock()
            mock_result.suggested_name = raw_response
            mock_result.confidence = 0.75
            mock_predictor.return_value = mock_result
            mock_init.return_value = Mock()

            # Call DSPy prediction
            suggested_name, confidence = call_dspy_prediction(
                file_content=test_content,
                naming_conventions=conventions_md,
                model="x-ai/grok-4-fast",
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1"
            )

            # Sanitize the result using CLI function
            sanitized_name = sanitize_filename(suggested_name)

            assert sanitized_name == expected_sanitized, \
                f"For raw '{raw_response}', expected '{expected_sanitized}', got '{sanitized_name}'"

    print("✓ Name generation and sanitization working correctly")

def test_confidence_score_extraction():
    """Test confidence scores are properly extracted from DSPy predictions."""
    print("Testing confidence score extraction...")

    test_content = "Test document for confidence extraction"
    conventions_md = "Test conventions"

    # Test different confidence score scenarios
    test_cases = [
        # (mock_result_attributes, expected_confidence)
        ({"suggested_name": "test_doc", "confidence": 0.95}, 0.95),
        ({"suggested_name": "test_doc", "confidence": "0.87"}, 0.87),
        ({"suggested_name": "test_doc"}, None),  # No confidence
        ({"suggested_name": "test_doc", "confidence": None}, None),  # Explicit None
        ({"suggested_name": "test_doc", "confidence": "invalid"}, None),  # Invalid string
    ]

    for mock_attrs, expected_confidence in test_cases:
        with patch('cli.initialize_dspy_lm') as mock_init, \
             patch('cli.Predict') as mock_predict_class:

            mock_predictor = Mock()
            mock_predict_class.return_value = mock_predictor

            mock_result = Mock()
            for attr, value in mock_attrs.items():
                setattr(mock_result, attr, value)
            mock_predictor.return_value = mock_result
            mock_init.return_value = Mock()

            # Call DSPy prediction
            suggested_name, confidence = call_dspy_prediction(
                file_content=test_content,
                naming_conventions=conventions_md,
                model="x-ai/grok-4-fast",
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1"
            )

            assert confidence == expected_confidence, \
                f"Expected confidence {expected_confidence}, got {confidence}"

    print("✓ Confidence score extraction working correctly")

def test_dspy_prediction_error_handling():
    """Test error handling when DSPy prediction fails."""
    print("Testing DSPy prediction error handling...")

    test_content = "Test content for error handling"
    conventions_md = "Test conventions"

    # Test various error scenarios
    error_scenarios = [
        # DSPy not available
        (False, None, RuntimeError, "DSPy package is not installed"),
        # LM initialization failure
        (True, RuntimeError("LM init failed"), RuntimeError, None),
        # Prediction failure
        (True, Exception("Prediction failed"), Exception, None),
    ]

    for dspy_available, init_exception, expected_exception_type, error_msg in error_scenarios:
        with patch('cli.DSPY_AVAILABLE', dspy_available):
            if dspy_available and init_exception:
                with patch('cli.initialize_dspy_lm', side_effect=init_exception):
                    try:
                        call_dspy_prediction(
                            file_content=test_content,
                            naming_conventions=conventions_md,
                            model="x-ai/grok-4-fast",
                            api_key="test_key",
                            base_url="https://openrouter.ai/api/v1"
                        )
                        assert False, "Expected exception was not raised"
                    except expected_exception_type as e:
                        if error_msg:
                            assert error_msg in str(e), f"Expected error message '{error_msg}' in '{str(e)}'"
            elif not dspy_available:
                try:
                    call_dspy_prediction(
                        file_content=test_content,
                        naming_conventions=conventions_md,
                        model="x-ai/grok-4-fast",
                        api_key="test_key",
                        base_url="https://openrouter.ai/api/v1"
                    )
                    assert False, "Expected RuntimeError for unavailable DSPy"
                except RuntimeError as e:
                    assert "DSPy package is not installed" in str(e)

    print("✓ DSPy prediction error handling working correctly")

def test_verbose_output_confidence_integration():
    """Test that verbose output properly integrates confidence scores."""
    print("Testing verbose output confidence integration...")

    test_content = "Test document for verbose output"
    conventions_md = "Test conventions"

    with patch('cli.initialize_dspy_lm') as mock_init, \
         patch('cli.Predict') as mock_predict_class:

        mock_predictor = Mock()
        mock_predict_class.return_value = mock_predictor

        # Test with confidence score
        mock_result = Mock()
        mock_result.suggested_name = "verbose_test_document"
        mock_result.confidence = 0.89
        mock_predictor.return_value = mock_result
        mock_init.return_value = Mock()

        # Capture verbose output
        with patch('builtins.print') as mock_print:
            suggested_name, confidence = call_dspy_prediction(
                file_content=test_content,
                naming_conventions=conventions_md,
                model="x-ai/grok-4-fast",
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1",
                verbose=True
            )

            # Verify verbose messages were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            verbose_message = any("Making DSPy prediction" in call for call in print_calls)
            assert verbose_message, "Expected verbose DSPy prediction message"

        # Verify confidence score is returned
        assert confidence == 0.89, f"Expected confidence 0.89, got {confidence}"
        assert suggested_name == "verbose_test_document", f"Expected 'verbose_test_document', got '{suggested_name}'"

        # Test without confidence score
        mock_result.confidence = None
        with patch('builtins.print') as mock_print:
            suggested_name, confidence = call_dspy_prediction(
                file_content=test_content,
                naming_conventions=conventions_md,
                model="x-ai/grok-4-fast",
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1",
                verbose=True
            )

            assert confidence is None, "Expected None confidence when not provided"

    print("✓ Verbose output confidence integration working correctly")

@requires_openrouter_api_key
def test_end_to_end_prediction_integration():
    """Test end-to-end prediction with real DSPy (if API key available)."""
    print("Testing end-to-end prediction integration with real DSPy...")

    if not CLI_DSPY_AVAILABLE:
        print("  Skipping: DSPy not available")
        return

    # Create test file
    test_file = create_test_file(
        "This document contains the Q3 2023 financial performance metrics including revenue growth and profitability analysis.",
        suffix=".txt"
    )

    conventions_md = """
# Financial Document Conventions
- Format: {type}_{period}_{year}
- Examples: financial_report_q3_2023, performance_metrics_q3_2023
- Use lowercase with underscores
"""

    try:
        # Test with real API
        suggested_name, confidence = call_dspy_prediction(
            file_content=test_file.read_text(),
            naming_conventions=conventions_md,
            model="x-ai/grok-4-fast",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

        assert isinstance(suggested_name, str), "Result should be a string"
        assert len(suggested_name.strip()) > 0, "Result should not be empty"
        assert confidence is None or isinstance(confidence, float), "Confidence should be None or float"

        # Verify name follows conventions (lowercase, spaces/underscores)
        sanitized_name = sanitize_filename(suggested_name)
        assert sanitized_name == suggested_name.lower(), "Name should follow lowercase convention"

        print(f"  Generated filename: {suggested_name}")
        if confidence is not None:
            print(f"  Confidence: {confidence}")

    finally:
        test_file.unlink()

def run_prediction_tests():
    """Run all prediction functionality tests."""
    print("Running Task 2.1: Prediction Functionality Tests...")
    print("=" * 60)

    if not DSPY_AVAILABLE:
        print("WARNING: DSPy not available, some tests may be limited")

    tests = [
        test_file_content_processing_character_limit,
        test_conventions_integration,
        test_name_generation_and_sanitization,
        test_confidence_score_extraction,
        test_dspy_prediction_error_handling,
        test_verbose_output_confidence_integration,
        test_end_to_end_prediction_integration,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✓ {test_func.__name__}")
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All prediction functionality tests passed!")
        return True
    else:
        print("Some prediction functionality tests failed!")
        return False

if __name__ == "__main__":
    # Suppress warnings for cleaner test output
    warnings.filterwarnings("ignore")

    success = run_prediction_tests()
    sys.exit(0 if success else 1)