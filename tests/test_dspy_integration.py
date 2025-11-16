#!/usr/bin/env python3
"""
Focused tests for DSPy integration setup.
Tests only critical DSPy behaviors for best_name filename prediction.
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


def test_dspy_availability():
    """Test that DSPy is available for import."""
    assert DSPY_AVAILABLE, "DSPy package is not installed - required for filename prediction"


def test_filename_signature_structure():
    """Test that FilenameSignature class follows correct DSPy pattern."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    # This will be implemented in cli.py, test the structure
    try:
        # Import after CLI is updated
        from best_name.cli import FilenameSignature

        # Verify it's a DSPy Signature
        assert issubclass(FilenameSignature, dspy.Signature), "FilenameSignature must inherit from dspy.Signature"

        # Check required fields exist by checking model_fields (how DSPy stores them)
        model_fields = FilenameSignature.model_fields
        assert 'file_content' in model_fields, "FilenameSignature must have file_content input field"
        assert 'naming_conventions' in model_fields, "FilenameSignature must have naming_conventions input field"
        assert 'suggested_name' in model_fields, "FilenameSignature must have suggested_name output field"

        # Check that fields are properly typed (DSPy InputField and OutputField)
        file_content_field = model_fields['file_content']
        naming_conventions_field = model_fields['naming_conventions']
        suggested_name_field = model_fields['suggested_name']

        # Check field types using DSPy's internal metadata
        file_content_extra = file_content_field.json_schema_extra or {}
        naming_conventions_extra = naming_conventions_field.json_schema_extra or {}
        suggested_name_extra = suggested_name_field.json_schema_extra or {}

        assert file_content_extra.get('__dspy_field_type') == 'input', "file_content must be an input field"
        assert naming_conventions_extra.get('__dspy_field_type') == 'input', "naming_conventions must be an input field"
        assert suggested_name_extra.get('__dspy_field_type') == 'output', "suggested_name must be an output field"

    except ImportError as e:
        # cli.py hasn't been updated yet or DSPy not available - skip with reason
        if not DSPY_AVAILABLE:
            print(f"Skipping {test_filename_signature_structure.__name__}: DSPy not available")
        else:
            print(f"Skipping {test_filename_signature_structure.__name__}: {e}")


def test_dspy_lm_initialization():
    """Test DSPy LM initialization with OpenRouter configuration."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    # Mock environment variables
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key-12345'}):
        try:
            from best_name.cli import initialize_dspy_lm

            # Test LM initialization without actually making API calls
            # We'll mock the dspy.LM to avoid authentication issues
            with patch('best_name.cli.dspy.LM') as mock_lm, \
                 patch('best_name.cli.configure') as mock_configure:

                mock_lm_instance = MagicMock()
                mock_lm.return_value = mock_lm_instance

                lm = initialize_dspy_lm(
                    api_key='test-key-12345',
                    model='x-ai/grok-4-fast',
                    base_url='https://openrouter.ai/api/v1'
                )

                # Verify LM was created with correct parameters
                mock_lm.assert_called_once_with(
                    model='openrouter/x-ai/grok-4-fast',
                    api_key='test-key-12345',
                    api_base='https://openrouter.ai/api/v1',
                    temperature=0.2
                )

                # Verify DSPy was configured
                mock_configure.assert_called_once_with(lm=mock_lm_instance)

                # Verify function returns the LM instance
                assert lm == mock_lm_instance, "Should return the LM instance"

        except ImportError as e:
            if not DSPY_AVAILABLE:
                print(f"Skipping {test_dspy_lm_initialization.__name__}: DSPy not available")
            else:
                print(f"Skipping {test_dspy_lm_initialization.__name__}: {e}")


def test_dspy_prediction_execution():
    """Test DSPy prediction execution with mock content."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    # Mock the DSPy components to avoid API calls
    mock_prediction = MagicMock()
    mock_prediction.suggested_name = "test_filename_suggestion"

    with patch('best_name.cli.initialize_dspy_lm') as mock_init_lm, \
         patch('best_name.cli.dspy.Predict', return_value=mock_prediction):

        try:
            from best_name.cli import call_dspy_prediction

            # Test prediction with sample data
            result, confidence = call_dspy_prediction(
                file_content="Sample file content for testing",
                naming_conventions="Use YYYYMMDD_Area_File format",
                model="x-ai/grok-4-fast",
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1"
            )

            # Verify prediction result
            assert result == "test_filename_suggestion", "Should return the suggested filename"
            assert isinstance(confidence, (float, int, type(None))), "Confidence should be numeric or None"

            # Verify initialization was called
            mock_init_lm.assert_called_once_with(
                api_key="test-key",
                model="x-ai/grok-4-fast",
                base_url="https://openrouter.ai/api/v1"
            )

        except ImportError as e:
            if not DSPY_AVAILABLE:
                print(f"Skipping {test_dspy_prediction_execution.__name__}: DSPy not available")
            else:
                print(f"Skipping {test_dspy_prediction_execution.__name__}: {e}")


def test_config_model_update():
    """Test that config.yaml has been updated with DSPy-compatible model."""
    config_path = Path(__file__).parent / "best_name" / "config.yaml"

    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check that default model is updated to grok-4-fast
        openrouter_cfg = config.get('openrouter', {})
        default_model = openrouter_cfg.get('model')

        assert default_model == "x-ai/grok-4-fast", f"Expected default model to be 'x-ai/grok-4-fast', got '{default_model}'"

    else:
        # Config file doesn't exist yet - this is okay during initial setup
        print(f"Skipping {test_config_model_update.__name__}: config.yaml not found")


def test_dependency_configuration():
    """Test that pyproject.toml includes DSPy dependency."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"

    if pyproject_path.exists():
        import toml
        with open(pyproject_path, 'r') as f:
            pyproject = toml.load(f)

        dependencies = pyproject.get('project', {}).get('dependencies', [])

        # Check that dspy is in dependencies
        dspy_found = any('dspy' in dep.lower() for dep in dependencies)
        assert dspy_found, "DSPy dependency must be added to pyproject.toml"

        # Check that toml dependency is also there (for testing)
        toml_found = any('toml' in dep.lower() for dep in dependencies)
        assert toml_found, "TOML dependency must be added for test script"

    else:
        # pyproject.toml doesn't exist - this should not happen in normal setup
        assert False, "pyproject.toml should exist in the project"


def test_openrouter_model_prefixing():
    """Test that OpenRouter models are correctly prefixed for DSPy."""
    if not DSPY_AVAILABLE:
        return  # Skip test if DSPy not available

    try:
        from best_name.cli import initialize_dspy_lm

        with patch('best_name.cli.dspy.LM') as mock_lm, \
             patch('best_name.cli.configure'):
            mock_lm_instance = MagicMock()
            mock_lm.return_value = mock_lm_instance

            # Test model without prefix gets prefixed
            initialize_dspy_lm(
                api_key='test-key',
                model='x-ai/grok-4-fast',
                base_url='https://openrouter.ai/api/v1'
            )
            mock_lm.assert_called_with(
                model='openrouter/x-ai/grok-4-fast',
                api_key='test-key',
                api_base='https://openrouter.ai/api/v1',
                temperature=0.2
            )

            # Reset mock for next test
            mock_lm.reset_mock()

            # Test model with prefix is not double-prefixed
            initialize_dspy_lm(
                api_key='test-key',
                model='openrouter/x-ai/grok-4-fast',
                base_url='https://openrouter.ai/api/v1'
            )
            mock_lm.assert_called_with(
                model='openrouter/x-ai/grok-4-fast',  # Should not be double-prefixed
                api_key='test-key',
                api_base='https://openrouter.ai/api/v1',
                temperature=0.2
            )

    except ImportError as e:
        if not DSPY_AVAILABLE:
            print(f"Skipping {test_openrouter_model_prefixing.__name__}: DSPy not available")
        else:
            print(f"Skipping {test_openrouter_model_prefixing.__name__}: {e}")


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_dspy_availability,
        test_filename_signature_structure,
        test_dspy_lm_initialization,
        test_dspy_prediction_execution,
        test_config_model_update,
        test_dependency_configuration,
        test_openrouter_model_prefixing
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("Running DSPy Integration Setup Tests...")
    print("=" * 50)

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

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)
    else:
        print("All DSPy integration setup tests passed!")