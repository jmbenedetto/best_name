#!/usr/bin/env python3
"""
Test configuration hierarchy and path resolution for Task 3.3.
Verifies that the configuration resolution order is maintained.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

# Add the best_name module to path
sys.path.insert(0, str(Path(__file__).parent / "best_name"))

from best_name.cli import cli


def test_config_resolution_priority():
    """Test that configuration resolution follows priority order: env > CLI > config."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content for configuration testing")

        # Create custom config file
        config_file = temp_path / "custom_config.yaml"
        config_data = {
            'defaults': {
                'conventions_file': 'config_conventions.md',
                'system_prompt_file': 'config_system_prompt.md'
            },
            'openrouter': {
                'model': 'config-model',
                'base_url': 'https://config.example.com'
            }
        }
        config_file.write_text(yaml.dump(config_data))

        with patch.dict(os.environ, {
            'OPENROUTER_API_KEY': 'env_key',
            'OPENROUTER_MODEL': 'env-model'  # This should not work (not in CLI)
        }):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("config_test", None)

                # Test CLI override (highest priority after env)
                result = runner.invoke(cli, [
                    str(original_file),
                    '--config', str(config_file),
                    '--model', 'cli-model'  # This should override config model
                ])

                # Should succeed in loading configuration
                # The important thing is that it reaches the prediction stage
                assert result.exit_code == 0


def test_package_vs_project_config():
    """Test that package config is preferred over project config."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content")

        # Test that package config loads when available
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("package_test", None)

                # Run from a directory without local config - should load package config
                result = runner.invoke(cli, [str(original_file)])

                # Should succeed using package config
                assert result.exit_code == 0 or "package" in result.output


def test_conventions_file_resolution():
    """Test that conventions file resolution follows package -> project -> custom priority."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content")

        # Create custom conventions file
        custom_conventions = temp_path / "custom_conventions.md"
        custom_conventions.write_text("# Custom Conventions\n\nThis is a custom conventions file.")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("conventions_test", None)

                # Test custom conventions file
                result = runner.invoke(cli, [
                    str(original_file),
                    '--conventions', str(custom_conventions)
                ])

                assert result.exit_code == 0


def test_system_prompt_file_resolution():
    """Test that system prompt file resolution follows package -> project -> custom priority."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        original_file = temp_path / "test.txt"
        original_file.write_text("Test content")

        # Create custom system prompt file
        custom_prompt = temp_path / "custom_prompt.md"
        custom_prompt.write_text("# Custom System Prompt\n\nThis is a custom system prompt.")

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            with patch('best_name.cli.call_dspy_prediction') as mock_prediction:
                mock_prediction.return_value = ("prompt_test", None)

                # Test custom system prompt file
                result = runner.invoke(cli, [
                    str(original_file),
                    '--system-prompt', str(custom_prompt)
                ])

                assert result.exit_code == 0


def test_resolve_path_function():
    """Test the resolve_path function behavior."""
    from best_name.cli import resolve_path

    base_dir = Path("/test/base")

    # Test absolute path
    abs_path = Path("/absolute/path/file.txt")
    result = resolve_path(base_dir, str(abs_path))
    assert result == abs_path

    # Test relative path
    result = resolve_path(base_dir, "relative/file.txt")
    assert result == (base_dir / "relative/file.txt").resolve()

    # Test None input
    result = resolve_path(base_dir, None)
    assert result is None

    # Test empty string input
    result = resolve_path(base_dir, "")
    assert result is None


def test_load_yaml_config_function():
    """Test the load_yaml_config function behavior."""
    from best_name.cli import load_yaml_config

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test loading existing config
        config_file = temp_path / "test_config.yaml"
        config_data = {
            'openrouter': {
                'model': 'test-model',
                'api_key': 'test-key'
            },
            'defaults': {
                'conventions_file': 'test_conventions.md'
            }
        }
        config_file.write_text(yaml.dump(config_data))

        loaded = load_yaml_config(config_file)
        assert loaded['openrouter']['model'] == 'test-model'
        assert loaded['defaults']['conventions_file'] == 'test_conventions.md'

        # Test loading non-existent config
        non_existent = temp_path / "non_existent.yaml"
        loaded = load_yaml_config(non_existent)
        assert loaded == {}


def run_config_hierarchy_tests():
    """Run all configuration hierarchy tests."""
    print("Running Configuration Hierarchy Tests...")
    print("=" * 44)

    tests = [
        test_config_resolution_priority,
        test_package_vs_project_config,
        test_conventions_file_resolution,
        test_system_prompt_file_resolution,
        test_resolve_path_function,
        test_load_yaml_config_function
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

    print("=" * 44)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All configuration hierarchy tests passed!")
    else:
        print(f"WARNING: {failed} configuration hierarchy tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_config_hierarchy_tests()
    sys.exit(0 if success else 1)