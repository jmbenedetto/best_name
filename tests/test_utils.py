#!/usr/bin/env python3
"""
Test utilities for best_name CLI testing.
Provides common test functions and decorators.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

# Add the best_name module to path
sys.path.insert(0, str(Path(__file__).parent / "best_name"))

# Import DSPy availability status
try:
    import dspy
    from dspy import InputField, OutputField, Predict, configure
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

def create_test_file(content: str, suffix: str = ".txt") -> Path:
    """Create a temporary test file with the given content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return Path(f.name)

def requires_openrouter_api_key(func):
    """Decorator to skip test if OPENROUTER_API_KEY is not available."""
    def wrapper(*args, **kwargs):
        if not os.getenv("OPENROUTER_API_KEY"):
            print("  Skipping: OPENROUTER_API_KEY not available")
            return
        return func(*args, **kwargs)
    return wrapper

def mock_dspy_prediction(suggested_name: str = "mocked_filename", confidence: Optional[float] = None):
    """Create a mock DSPy prediction result."""
    mock_result = Mock()
    mock_result.suggested_name = suggested_name
    if confidence is not None:
        mock_result.confidence = confidence
    return mock_result

def mock_dspy_lm():
    """Create a mock DSPy LM."""
    mock_lm = Mock()
    return mock_lm