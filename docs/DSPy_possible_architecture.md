# DSPy Architecture for best_name Project

## Overview

This document outlines comprehensive DSPy integration options for the best_name CLI tool. DSPy provides a structured approach to prompt engineering and LLM interaction that can improve maintainability, optimization, and performance of the filename suggestion system.

## Table of Contents

1. [DSPy Signatures](#dspy-signatures)
2. [DSPy Modules](#dspy-modules)
3. [Training Data Structure](#training-data-structure)
4. [Configuration Integration](#configuration-integration)
5. [Implementation Recommendations](#implementation-recommendations)

---

## DSPy Signatures

DSPy signatures define the structure of LLM interactions, specifying inputs, outputs, and task instructions.

### 1. Primary Signature - Chain of Thought Approach

```python
class FileNameAnalysisSignature(dspy.Signature):
    """Analyze file content step-by-step to generate the optimal filename.

    Follow this analysis process:
    1. Identify the document type and category
    2. Extract key information (dates, names, amounts, etc.)
    3. Determine the appropriate life area
    4. Apply naming conventions
    """

    # Inputs
    file_content = dspy.InputField(
        desc="Text content extracted from the file, may be truncated"
    )
    conventions = dspy.InputField(
        desc="Naming conventions and guidelines to follow"
    )
    file_extension = dspy.InputField(
        desc="Original file extension (without dot)"
    )

    # Step-by-step reasoning outputs
    document_analysis = dspy.OutputField(
        desc="Analysis of document type, purpose, and key characteristics"
    )
    extracted_info = dspy.OutputField(
        desc="Key information extracted: dates, names, amounts, companies, etc."
    )
    category_classification = dspy.OutputField(
        desc="Category: Bank receipt, Invoice, Presentation, Spreadsheet, Academic article, Book, Blog post, Document"
    )
    area_classification = dspy.OutputField(
        desc="Life area: Personal life areas (Improvement/Life/Work spaces)"
    )

    # Final output
    reasoning = dspy.OutputField(
        desc="Step-by-step reasoning for the final filename choice"
    )
    suggested_filename = dspy.OutputField(
        desc="Final suggested filename without extension, following YYYYMMDD_AreaName_File name format"
    )
```

**Advantages:**
- Detailed reasoning process
- Multiple intermediate outputs for better debugging
- Explicit step-by-step instructions improve accuracy
- Rich metadata for optimization

### 2. Alternative Modular Signatures

#### A. Two-Stage Approach

```python
class ContentAnalysisSignature(dspy.Signature):
    """First stage: Analyze and categorize file content."""

    file_content = dspy.InputField(desc="Text content from file")
    file_extension = dspy.InputField(desc="File type")

    content_type = dspy.OutputField(desc="Type: Invoice, Receipt, Report, etc.")
    key_entities = dspy.OutputField(desc="Important entities: names, dates, amounts")
    relevant_dates = dspy.OutputField(desc="Dates found in content, format YYYY-MM-DD")
    business_context = dspy.OutputField(desc="Business/personal context")

class FileNameGenerationSignature(dspy.Signature):
    """Second stage: Generate filename based on analysis."""

    content_type = dspy.InputField(desc="Analyzed content type")
    key_entities = dspy.InputField(desc="Extracted key information")
    relevant_dates = dspy.InputField(desc="Dates found in content")
    business_context = dspy.InputField(desc="Business/personal context")
    conventions = dspy.InputField(desc="Naming conventions to follow")
    file_extension = dspy.InputField(desc="Original file extension")

    suggested_name = dspy.OutputField(desc="Final filename suggestion")
```

**Advantages:**
- Separation of concerns
- Easier optimization of individual stages
- Reusable analysis components
- Better error handling at each stage

#### B. Multi-Output Signature

```python
class ComprehensiveFileNameSignature(dspy.Signature):
    """Generate filename with multiple structured outputs."""

    file_content = dspy.InputField(desc="File text content")
    conventions = dspy.InputField(desc="Naming conventions")
    file_extension = dspy.InputField(desc="File type")

    # Analysis outputs
    confidence_score = dspy.OutputField(
        desc="Confidence in filename suggestion (0-100)"
    )
    alternative_names = dspy.OutputField(
        desc="2-3 alternative filename suggestions"
    )
    warning_flags = dspy.OutputField(
        desc="Any concerns about the content or naming"
    )

    # Primary output
    suggested_filename = dspy.OutputField(
        desc="Best filename suggestion"
    )
```

**Advantages:**
- Confidence scoring for reliability assessment
- Alternative suggestions for user choice
- Early warning system for potential issues
- Rich decision-making information

---

## DSPy Modules

DSPy modules encapsulate the logic and orchestrate signature execution.

### 1. Primary Module - Optimizable Chain of Thought

```python
class BestFileNameSuggester(dspy.Module):
    """Main DSPy module for filename suggestion with optimization capabilities."""

    def __init__(self, use_chain_of_thought=True):
        super().__init__()

        if use_chain_of_thought:
            self.predictor = dspy.ChainOfThought(FileNameAnalysisSignature)
        else:
            self.predictor = dspy.Predict(FileNameAnalysisSignature)

    def forward(self, file_content, conventions, file_extension):
        # Truncate content if too long (DSPy handles this but we can be explicit)
        max_content_length = 12000
        truncated_content = file_content[:max_content_length]

        # Make prediction
        prediction = self.predictor(
            file_content=truncated_content,
            conventions=conventions,
            file_extension=file_extension
        )

        # Return structured prediction
        return dspy.Prediction(
            suggested_filename=prediction.suggested_filename,
            analysis={
                'document_analysis': prediction.document_analysis,
                'category': prediction.category_classification,
                'area': prediction.area_classification,
                'confidence': getattr(prediction, 'confidence_score', None)
            },
            raw_prediction=prediction
        )
```

**Features:**
- Configurable approach (CoT vs simple prediction)
- Automatic content length management
- Structured return values
- Optimization-ready

### 2. Advanced Multi-Step Module

```python
class AdvancedFileNameSuggester(dspy.Module):
    """Multi-step approach with separate analysis and generation phases."""

    def __init__(self):
        super().__init__()

        # Step 1: Content analysis
        self.content_analyzer = dspy.ChainOfThought(ContentAnalysisSignature)

        # Step 2: Filename generation
        self.name_generator = dspy.ChainOfThought(FileNameGenerationSignature)

        # Step 3: Validation and refinement
        self.validator = dspy.Predict(
            "suggested_name, conventions, file_extension -> validated_name, confidence, suggestions"
        )

    def forward(self, file_content, conventions, file_extension):
        # Step 1: Analyze content
        analysis = self.content_analyzer(
            file_content=file_content,
            file_extension=file_extension
        )

        # Step 2: Generate initial filename
        initial_suggestion = self.name_generator(
            content_type=analysis.content_type,
            key_entities=analysis.key_entities,
            relevant_dates=analysis.relevant_dates,
            business_context=analysis.business_context,
            conventions=conventions,
            file_extension=file_extension
        )

        # Step 3: Validate and refine
        validation = self.validator(
            suggested_name=initial_suggestion.suggested_name,
            conventions=conventions,
            file_extension=file_extension
        )

        return dspy.Prediction(
            suggested_filename=validation.validated_name,
            confidence=validation.confidence,
            alternatives=validation.suggestions,
            analysis=analysis,
            reasoning={
                'content_analysis': analysis,
                'initial_suggestion': initial_suggestion,
                'validation': validation
            }
        )
```

**Features:**
- Separate analysis and generation phases
- Built-in validation step
- Confidence scoring and alternatives
- Detailed reasoning trace
- Modular optimization potential

### 3. Hybrid Module with Fallbacks

```python
class HybridFileNameSuggester(dspy.Module):
    """Robust module with multiple approaches and fallbacks."""

    def __init__(self):
        super().__init__()

        # Primary: Chain of Thought
        self.cot_predictor = dspy.ChainOfThought(FileNameAnalysisSignature)

        # Secondary: Simple prediction
        self.simple_predictor = dspy.Predict(ComprehensiveFileNameSignature)

        # Tertiary: Rule-based fallback
        self.rule_based = RuleBasedFileNameGenerator()

    def forward(self, file_content, conventions, file_extension):
        try:
            # Try Chain of Thought first
            prediction = self.cot_predictor(
                file_content=file_content,
                conventions=conventions,
                file_extension=file_extension
            )

            # Validate the result
            if self._validate_prediction(prediction):
                return dspy.Prediction(
                    suggested_filename=prediction.suggested_filename,
                    method='chain_of_thought',
                    analysis=prediction
                )

        except Exception as e:
            print(f"Chain of Thought failed: {e}")

        try:
            # Fallback to simple prediction
            prediction = self.simple_predictor(
                file_content=file_content[:5000],  # Shorter for reliability
                conventions=conventions,
                file_extension=file_extension
            )

            if self._validate_prediction(prediction):
                return dspy.Prediction(
                    suggested_filename=prediction.suggested_filename,
                    method='simple_prediction',
                    analysis=prediction
                )

        except Exception as e:
            print(f"Simple prediction failed: {e}")

        # Final fallback to rule-based
        return self.rule_based.generate(file_content, file_extension)

    def _validate_prediction(self, prediction):
        """Validate that prediction meets basic criteria."""
        if not prediction.suggested_filename:
            return False

        # Add more validation logic as needed
        return len(prediction.suggested_filename.strip()) > 0
```

**Features:**
- Multiple fallback strategies
- Error resilience
- Graceful degradation
- Reliability focus

---

## Training Data Structure

DSPy optimizers require structured training data for prompt optimization and few-shot learning.

### Training Example Creation

```python
class FileNameTrainingData:
    """Structure for creating DSPy training examples."""

    @staticmethod
    def create_example(file_path, correct_name, content):
        """Create a DSPy Example from existing correctly named files."""

        return dspy.Example(
            file_content=content,
            conventions="YYYYMMDD_AreaName_File name.xxx",
            file_extension=Path(file_path).suffix.lstrip('.'),
            suggested_filename=Path(correct_name).stem,  # Remove extension
            # Optional: Add intermediate steps for better training
            category_classification=FileNameTrainingData._infer_category(correct_name),
            area_classification=FileNameTrainingData._infer_area(correct_name)
        ).with_inputs("file_content", "conventions", "file_extension")

    @staticmethod
    def _infer_category(filename):
        """Infer category from filename patterns."""
        filename_lower = filename.lower()
        if 'invoice' in filename_lower:
            return "Invoice"
        elif 'receipt' in filename_lower or 'bank' in filename_lower:
            return "Bank receipt"
        elif 'presentation' in filename_lower or 'slides' in filename_lower:
            return "Presentation support"
        elif 'spreadsheet' in filename_lower or 'excel' in filename_lower:
            return "Spreadsheet"
        elif 'article' in filename_lower or 'paper' in filename_lower:
            return "Academic article"
        elif 'book' in filename_lower:
            return "Book"
        elif 'blog' in filename_lower:
            return "Blog post"
        return "Document"

    @staticmethod
    def _infer_area(filename):
        """Infer life area from filename."""
        # Look for area keywords in filename
        areas = {
            'MyFinance': ['finance', 'invoice', 'receipt', 'bank', 'payment'],
            'MyHealth': ['health', 'medical', 'doctor', 'pharmacy'],
            'MyWork': ['work', 'project', 'meeting', 'presentation'],
            'MyFamily': ['family', 'personal', 'home'],
            'Improvement': ['learning', 'course', 'tutorial'],
            'MyProperties': ['property', 'rent', 'lease', 'mortgage']
        }

        filename_lower = filename.lower()
        for area, keywords in areas.items():
            if any(keyword in filename_lower for keyword in keywords):
                return area
        return "Personal"
```

### Training Set Creation Pipeline

```python
def create_training_dataset(correctly_named_files_directory):
    """Create DSPy training dataset from directory of correctly named files."""

    training_examples = []

    for file_path in Path(correctly_named_files_directory).glob('*'):
        if file_path.is_file():
            # Extract content using existing functions
            content = extract_file_content(file_path)

            if content:
                example = FileNameTrainingData.create_example(
                    file_path=str(file_path),
                    correct_name=file_path.name,
                    content=content
                )
                training_examples.append(example)

    return training_examples

# Usage example:
# training_data = create_training_dataset("/path/to/correctly/named/files")
```

### Optimization Setup

```python
def setup_dspy_optimization(training_data, metric=None):
    """Set up DSPy optimizer for filename suggestion."""

    if metric is None:
        # Default metric: exact match on suggested filename
        def exact_match_metric(example, prediction, trace=None):
            return example.suggested_filename.lower().strip() == prediction.suggested_filename.lower().strip()

    # Create optimizer
    optimizer = dspy.BootstrapFewShot(
        metric=exact_match_metric,
        max_bootstrapped_demos=5,
        max_labeled_demos=3
    )

    return optimizer

# Training pipeline:
# optimizer = setup_dspy_optimization(training_data)
# optimized_module = optimizer.compile(module, trainset=training_data)
```

---

## Configuration Integration

### DSPy Configuration with OpenRouter

```python
class DSPyConfig:
    """Handle DSPy configuration with OpenRouter integration."""

    @staticmethod
    def configure_from_yaml(config_path, api_key):
        """Configure DSPy from existing YAML config."""

        # Load existing config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        openrouter_cfg = config.get('openrouter', {})

        # Configure DSPy LM
        lm = dspy.LM(
            model=openrouter_cfg.get('model', 'gpt-4o-mini'),
            api_base=openrouter_cfg.get('base_url', 'https://openrouter.ai/api/v1'),
            api_key=api_key,
            temperature=0.2,
            max_tokens=200
        )

        # Configure DSPy settings
        dspy.settings.configure(
            lm=lm,
            # Add other DSPy settings as needed
            experimental=True if openrouter_cfg.get('model').startswith('experimental') else False
        )

        return lm

    @staticmethod
    def configure_direct(model, api_key, base_url=None, temperature=0.2):
        """Configure DSPy with direct parameters."""

        lm = dspy.LM(
            model=model,
            api_base=base_url or "https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=temperature,
            max_tokens=200
        )

        dspy.settings.configure(lm=lm)
        return lm
```

### CLI Integration Pattern

```python
def suggest_filename_with_dspy(file_content, conventions, file_extension, verbose=False):
    """Use DSPy module to suggest filename."""

    # Initialize the suggester
    suggester = BestFileNameSuggester(use_chain_of_thought=True)

    # Get prediction
    result = suggester(
        file_content=file_content,
        conventions=conventions,
        file_extension=file_extension
    )

    if verbose:
        # DSPy provides rich inspection capabilities
        dspy.inspect_history(n=1)
        print(f"Method used: {getattr(result, 'method', 'unknown')}")
        print(f"Confidence: {getattr(result, 'confidence', 'N/A')}")

    return result.suggested_filename
```

---

## Implementation Recommendations

### Phase 1: Basic Integration

1. **Start with the Primary Module** (`BestFileNameSuggester`)
2. **Use Chain of Thought signature** for better reasoning
3. **Maintain existing CLI interface** for backward compatibility
4. **Add DSPy dependency** to `pyproject.toml`

### Phase 2: Enhanced Features

1. **Add training data collection** from existing correctly named files
2. **Implement optimization pipeline** using BootstrapFewShot
3. **Add confidence scoring** and alternative suggestions
4. **Enhanced verbose output** with DSPy inspection

### Phase 3: Advanced Features

1. **Multi-step module** with validation phases
2. **Hybrid approach** with fallbacks
3. **Custom metrics** for evaluation
4. **A/B testing** between approaches

### Code Integration Points

#### Modified CLI Function Structure

```python
@click.command(name="best_name")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--use-dspy", is_flag=True, default=False, help="Use DSPy for filename suggestion")
@click.option("--optimize", is_flag=True, default=False, help="Use optimized DSPy module")
@click.option("--training-data", type=click.Path(exists=True), help="Path to training data directory")
# ... existing options
def cli(
    file_path: Path,
    use_dspy: bool,
    optimize: bool,
    training_data: Optional[Path],
    # ... existing parameters
) -> None:
    """Suggest the best filename for FILE_PATH based on its content."""

    # Load configuration and setup DSPy if needed
    if use_dspy:
        lm = DSPyConfig.configure_from_yaml(config_path, api_key)

        if optimize and training_data:
            # Load training data and optimize
            training_examples = create_training_dataset(training_data)
            optimizer = setup_dspy_optimization(training_examples)
            # Use optimized module

        # Use DSPy for suggestion
        suggested = suggest_filename_with_dspy(content, conventions, file_ext, verbose)
    else:
        # Use existing implementation
        suggested = suggest_filename_legacy(content, conventions, file_ext, verbose)

    # Rest of existing CLI logic...
```

### Benefits Summary

1. **Structured Prompting**: Clean separation of instructions and data
2. **Automatic Optimization**: DSPy optimizers improve performance
3. **Better Debugging**: Rich history and reasoning traces
4. **Modularity**: Reusable components and clear architecture
5. **Future-Proof**: Easy to extend and modify approaches

### Migration Strategy

1. **Parallel implementation**: Keep existing code alongside DSPy
2. **Feature flag**: Use `--use-dspy` option to switch between approaches
3. **Gradual rollout**: Start with basic DSPy, add optimization later
4. **Performance comparison**: Track accuracy and user satisfaction

This architecture provides a solid foundation for integrating DSPy while maintaining the existing functionality and providing paths for future enhancements.