"""DSPy modules for filename prediction and evaluation."""

# DSPy imports
try:
    import dspy
    from dspy import InputField, OutputField, Predict, configure
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    # Create placeholder classes for graceful degradation
    class dspy:
        class Signature:
            pass
        class InputField:
            def __init__(self, desc="", **kwargs):
                self.desc = desc
        class OutputField:
            def __init__(self, desc="", **kwargs):
                self.desc = desc
        class Predict:
            def __init__(self, signature):
                self.signature = signature
        def configure(**kwargs):
            pass


class FilenameSignature(dspy.Signature):
    """Generate appropriate filename based on file content and naming conventions."""

    file_content = InputField(desc="The extracted content from the file")
    naming_conventions = InputField(desc="The naming conventions and categories to follow")
    suggested_name = OutputField(desc="The suggested filename without extension")


class EvaluationSignature(dspy.Signature):
    """Evaluate the quality of a filename suggestion compared to ground truth."""

    suggested_name = InputField(desc="The AI-generated filename suggestion")
    ground_truth_name = InputField(desc="The human-provided correct filename")
    file_content = InputField(desc="The original file content for context")
    evaluation_score = OutputField(desc="Quality score from 0-10 comparing suggestion to ground truth")


def initialize_dspy_lm(api_key: str, model: str, base_url: str):
    """Initialize DSPy LM with OpenRouter configuration."""
    if not DSPY_AVAILABLE:
        raise RuntimeError("DSPy package is not installed")

    # OpenRouter models need to be prefixed with "openrouter/" for DSPy/LiteLLM
    if not model.startswith("openrouter/"):
        openrouter_model = f"openrouter/{model}"
    else:
        openrouter_model = model

    # Create LM instance with OpenRouter settings
    lm = dspy.LM(
        model=openrouter_model,
        api_key=api_key,
        api_base=base_url,
        temperature=0.2
    )

    # Configure DSPy to use this LM
    configure(lm=lm)
    return lm


def call_dspy_prediction(
    file_content: str,
    naming_conventions: str,
    model: str,
    api_key: str,
    base_url: str,
    verbose: bool = False
) -> tuple[str, float | None]:
    """Call DSPy prediction for filename generation."""
    if not DSPY_AVAILABLE:
        raise RuntimeError("DSPy package is not installed")

    # Initialize LM
    lm = initialize_dspy_lm(api_key, model, base_url)

    # Create predictor
    predictor = Predict(FilenameSignature)

    # Truncate content for safety
    max_chars = 12000
    truncated_content = file_content[:max_chars]

    # Make prediction
    if verbose:
        print(f"Making DSPy prediction with {len(truncated_content)} characters of content...")

    result = predictor(
        file_content=truncated_content,
        naming_conventions=naming_conventions
    )

    # Extract suggested name
    suggested_name = getattr(result, 'suggested_name', '').strip()

    # Extract confidence score if available (DSPy may provide this in future versions)
    confidence = None
    if hasattr(result, 'confidence') and result.confidence is not None:
        try:
            confidence = float(result.confidence)
        except (ValueError, TypeError):
            confidence = None
    elif hasattr(result, 'completions') and result.completions and hasattr(result.completions, '__getitem__'):
        try:
            # Try to extract confidence from completions if available
            first_completion = result.completions[0]
            if hasattr(first_completion, 'confidence') and first_completion.confidence is not None:
                try:
                    confidence = float(first_completion.confidence)
                except (ValueError, TypeError):
                    confidence = None
        except (IndexError, TypeError):
            confidence = None

    return suggested_name, confidence


def call_dspy_evaluation(
    suggested_name: str,
    ground_truth_name: str,
    file_content: str,
    model: str,
    api_key: str,
    base_url: str,
    verbose: bool = False
) -> float:
    """Call DSPy evaluation for filename scoring."""
    if not DSPY_AVAILABLE:
        raise RuntimeError("DSPy package is not installed")

    # Initialize LM
    lm = initialize_dspy_lm(api_key, model, base_url)

    # Create evaluator
    evaluator = Predict(EvaluationSignature)

    # Truncate content for safety
    max_chars = 12000
    truncated_content = file_content[:max_chars]

    # Make evaluation prediction
    if verbose:
        print(f"Making DSPy evaluation with {len(truncated_content)} characters of content...")
        print(f"  Suggested name: '{suggested_name}'")
        print(f"  Ground truth: '{ground_truth_name}'")

    result = evaluator(
        suggested_name=suggested_name,
        ground_truth_name=ground_truth_name,
        file_content=truncated_content
    )

    # Extract evaluation score
    raw_score = getattr(result, 'evaluation_score', '').strip()

    # Parse and validate score
    try:
        # Try to extract numeric score from text (including negative numbers)
        import re
        score_match = re.search(r'-?\d+(\.\d+)?', raw_score)
        if score_match:
            score = float(score_match.group())
        else:
            # Fallback: try to convert entire response to float
            score = float(raw_score)

        # Ensure score is within 0-10 range
        score = max(0.0, min(10.0, score))

        if verbose:
            print(f"  Raw evaluation response: '{raw_score}'")
            print(f"  Parsed score: {score}")

        return score

    except (ValueError, TypeError, AttributeError):
        # Default to middle score if parsing fails
        if verbose:
            print(f"  Failed to parse score from: '{raw_score}', using default 5.0")
        return 5.0


def extract_evaluation_score(evaluation_result) -> float:
    """Extract and validate evaluation score from DSPy prediction result."""
    # Extract raw score string
    raw_score = getattr(evaluation_result, 'evaluation_score', '').strip()
    # Debug: uncomment to debug during testing
    # print(f"DEBUG extract_evaluation_score: raw_score='{raw_score}'")

    # Parse and validate score
    try:
        # Try to extract numeric score from text (including negative numbers)
        import re
        score_match = re.search(r'-?\d+(\.\d+)?', raw_score)
        if score_match:
            score = float(score_match.group())
        else:
            # Fallback: try to convert entire response to float
            score = float(raw_score)

        # Ensure score is within 0-10 range
        score = max(0.0, min(10.0, score))
        return score

    except (ValueError, TypeError, AttributeError):
        # Default to middle score if parsing fails
        return 5.0


def sanitize_evaluation_result(score: float) -> str:
    """Sanitize evaluation result for CSV/MD output."""
    # Ensure score is a valid number within range
    try:
        score_float = float(score)
        score_float = max(0.0, min(10.0, score_float))
        return f"{score_float:.1f}"
    except (ValueError, TypeError):
        return "5.0"