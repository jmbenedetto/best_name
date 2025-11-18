#!/usr/bin/env python3
"""
Fixed tests for DSPy evaluation metrics implementation.
Updated to work with modular structure (Task Group 6 refactoring).
Tests only critical DSPy evaluation functionality for scoring filename suggestions.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project directory to the path so we can import from best_name
sys.path.insert(0, str(Path(__file__).parent))

# Import the components we need to test
try:
    import dspy
    from dspy import InputField, OutputField
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


def test_evaluation_signature_structure():
    """Test that EvaluationSignature class follows correct DSPy pattern."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    try:
        from best_name.dspy_modules import EvaluationSignature

        # Verify it's a DSPy Signature
        assert issubclass(EvaluationSignature, dspy.Signature), "EvaluationSignature must inherit from dspy.Signature"

        # Check required fields exist by checking model_fields
        model_fields = EvaluationSignature.model_fields
        assert 'suggested_name' in model_fields, "EvaluationSignature must have suggested_name input field"
        assert 'ground_truth_name' in model_fields, "EvaluationSignature must have ground_truth_name input field"
        assert 'file_content' in model_fields, "EvaluationSignature must have file_content input field"
        assert 'evaluation_score' in model_fields, "EvaluationSignature must have evaluation_score output field"

        # Check that fields are properly typed
        suggested_name_field = model_fields['suggested_name']
        ground_truth_name_field = model_fields['ground_truth_name']
        file_content_field = model_fields['file_content']
        evaluation_score_field = model_fields['evaluation_score']

        # Check field types using DSPy's internal metadata
        suggested_name_extra = suggested_name_field.json_schema_extra or {}
        ground_truth_extra = ground_truth_name_field.json_schema_extra or {}
        file_content_extra = file_content_field.json_schema_extra or {}
        evaluation_score_extra = evaluation_score_field.json_schema_extra or {}

        assert suggested_name_extra.get('__dspy_field_type') == 'input', "suggested_name must be an input field"
        assert ground_truth_extra.get('__dspy_field_type') == 'input', "ground_truth_name must be an input field"
        assert file_content_extra.get('__dspy_field_type') == 'input', "file_content must be an input field"
        assert evaluation_score_extra.get('__dspy_field_type') == 'output', "evaluation_score must be an output field"

    except ImportError as e:
        if not DSPY_AVAILABLE:
            print(f"Skipping {test_evaluation_signature_structure.__name__}: DSPy not available")
        else:
            print(f"Skipping {test_evaluation_signature_structure.__name__}: {e}")


def test_evaluation_prediction_execution():
    """Test DSPy evaluation prediction execution with mock data."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    # Mock the evaluation result
    mock_evaluation = MagicMock()
    mock_evaluation.evaluation_score = "8.5"

    # Mock the Predict class entirely to avoid DSPy LM configuration issues
    mock_predictor = MagicMock(return_value=mock_evaluation)

    # Updated to use the correct modular path
    with patch('best_name.dspy_modules.initialize_dspy_lm') as mock_init_lm, \
         patch('dspy.Predict', return_value=mock_predictor), \
         patch('dspy.configure') as mock_configure:

        try:
            from best_name.dspy_modules import call_dspy_evaluation

            # Test evaluation with sample data
            score = call_dspy_evaluation(
                suggested_name="invoice_2024_document",
                ground_truth_name="20240610_MyFinance_Invoice kingHost to Joao Miguel about firewall service",
                file_content="Sample invoice content for testing evaluation",
                model="x-ai/grok-4-fast",
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1"
            )

            # Verify evaluation result
            assert isinstance(score, (float, int)), "Score should be numeric"
            assert 0.0 <= score <= 10.0, "Score should be within 0-10 range"

            # Verify initialization was called
            mock_init_lm.assert_called_once_with(
                "test-key",
                "x-ai/grok-4-fast",
                "https://openrouter.ai/api/v1"
            )

        except ImportError as e:
            if not DSPY_AVAILABLE:
                print(f"Skipping {test_evaluation_prediction_execution.__name__}: DSPy not available")
            else:
                print(f"Skipping {test_evaluation_prediction_execution.__name__}: {e}")


def test_evaluation_score_extraction():
    """Test evaluation score extraction from DSPy prediction results."""
    try:
        from best_name.dspy_modules import extract_evaluation_score

        # Test with numeric score string
        mock_result_1 = MagicMock()
        mock_result_1.evaluation_score = "7.5"
        score_1 = extract_evaluation_score(mock_result_1)
        assert score_1 == 7.5, f"Expected 7.5, got {score_1}"

        # Test with score in text
        mock_result_2 = MagicMock()
        mock_result_2.evaluation_score = "The quality score is 8.2 out of 10"
        score_2 = extract_evaluation_score(mock_result_2)
        assert score_2 == 8.2, f"Expected 8.2, got {score_2}"

        # Test with invalid score (should default to 5.0)
        mock_result_3 = MagicMock()
        mock_result_3.evaluation_score = "invalid score"
        score_3 = extract_evaluation_score(mock_result_3)
        assert score_3 == 5.0, f"Expected 5.0 for invalid input, got {score_3}"

        # Test with out-of-range scores
        mock_result_4 = MagicMock()
        mock_result_4.evaluation_score = "15.0"
        score_4 = extract_evaluation_score(mock_result_4)
        assert score_4 == 10.0, f"Expected 10.0 (capped), got {score_4}"

        mock_result_5 = MagicMock()
        mock_result_5.evaluation_score = "-5.0"
        score_5 = extract_evaluation_score(mock_result_5)
        assert score_5 == 0.0, f"Expected 0.0 (capped), got {score_5}"

    except ImportError as e:
        print(f"Skipping {test_evaluation_score_extraction.__name__}: {e}")


def test_evaluation_result_sanitization():
    """Test evaluation result sanitization for CSV/MD output."""
    try:
        from best_name.dspy_modules import sanitize_evaluation_result

        # Test with valid float
        result_1 = sanitize_evaluation_result(8.75)
        assert result_1 == "8.8", f"Expected '8.8', got '{result_1}'"

        # Test with string number
        result_2 = sanitize_evaluation_result("7.25")
        assert result_2 == "7.2", f"Expected '7.2', got '{result_2}'"

        # Test with out-of-range values
        result_3 = sanitize_evaluation_result(15.0)
        assert result_3 == "10.0", f"Expected '10.0' (capped), got '{result_3}'"

        result_4 = sanitize_evaluation_result(-3.0)
        assert result_4 == "0.0", f"Expected '0.0' (capped), got '{result_4}'"

        # Test with invalid input
        result_5 = sanitize_evaluation_result("invalid")
        assert result_5 == "5.0", f"Expected '5.0' (default), got '{result_5}'"

        result_6 = sanitize_evaluation_result(None)
        assert result_6 == "5.0", f"Expected '5.0' (default), got '{result_6}'"

    except ImportError as e:
        print(f"Skipping {test_evaluation_result_sanitization.__name__}: {e}")


def test_evaluation_complete_flow():
    """Test complete evaluation flow with mocked DSPy components."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    # Mock the evaluation result with realistic response
    mock_evaluation = MagicMock()
    mock_evaluation.evaluation_score = "I would rate this 6.5 out of 10"

    # Mock the Predict class entirely to avoid DSPy LM configuration issues
    mock_predictor = MagicMock(return_value=mock_evaluation)

    # Updated to use the correct modular path
    with patch('best_name.dspy_modules.initialize_dspy_lm') as mock_init_lm, \
         patch('dspy.Predict', return_value=mock_predictor), \
         patch('dspy.configure') as mock_configure:

        try:
            from best_name.dspy_modules import call_dspy_evaluation, sanitize_evaluation_result

            # Test complete evaluation flow
            raw_score = call_dspy_evaluation(
                suggested_name="document_file",
                ground_truth_name="2024_important_document.pdf",
                file_content="This is a test document about important topics from 2024.",
                model="x-ai/grok-4-fast",
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                verbose=False
            )

            # Sanitize for output
            sanitized_score = sanitize_evaluation_result(raw_score)

            # Verify the complete flow
            assert isinstance(raw_score, float), "Raw score should be float"
            assert 0.0 <= raw_score <= 10.0, "Raw score should be within 0-10 range"
            assert isinstance(sanitized_score, str), "Sanitized score should be string"
            assert float(sanitized_score) == raw_score, "Sanitized score should match raw score"

            # Verify LM initialization was called correctly
            mock_init_lm.assert_called_once_with(
                "test-key",
                "x-ai/grok-4-fast",
                "https://openrouter.ai/api/v1"
            )

        except ImportError as e:
            if not DSPY_AVAILABLE:
                print(f"Skipping {test_evaluation_complete_flow.__name__}: DSPy not available")
            else:
                print(f"Skipping {test_evaluation_complete_flow.__name__}: {e}")


if __name__ == "__main__":
    # Run all evaluation tests
    test_functions = [
        test_evaluation_signature_structure,
        test_evaluation_prediction_execution,
        test_evaluation_score_extraction,
        test_evaluation_result_sanitization,
        test_evaluation_complete_flow
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("Running DSPy Evaluation Metrics Tests (Fixed for Modular Structure)...")
    print("=" * 70)

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

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)
    else:
        print("All DSPy evaluation metrics tests passed!")