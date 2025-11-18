# Specification: DSPy Evaluation Metrics Implementation

## Goal
Implement DSPy evaluation metrics to assess the quality and accuracy of DSPy-generated filename suggestions through automated evaluation framework with model-based scoring.

## User Stories
- As a developer, I want to evaluate filename suggestion quality using DSPy metrics so that I can assess the performance of the naming algorithm
- As a developer, I want to run evaluations on individual files or entire directories so that I can test specific scenarios or comprehensive datasets
- As a developer, I want detailed evaluation reports with scores and metadata so that I can analyze and improve the naming suggestions

## Specific Requirements

**DSPy Metrics Implementation**
- Use DSPy evaluation framework approach with model-based scoring comparing predictions against ground truth
- Implement single overall quality score provided by LLM based on prediction vs ground truth comparison
- Follow DSPy metrics documentation pattern for structured evaluation scoring
- Leverage existing OpenRouter API configuration for evaluation model access

**CLI Integration**
- Add `best_name eval` subcommand to existing CLI structure using Click framework
- Support individual file evaluation with file path parameter
- Support directory evaluation with folder path parameter
- Auto-generate run-id with timestamp if not provided by user
- Accept optional run-id parameter for custom evaluation identification

**Evaluation Data Processing**
- Load ground truth data from evals/eval_files.csv with original_file and human_defined_name columns
- Process evaluation files using existing content extraction logic from cli.py
- Generate filename suggestions using existing DSPy prediction framework
- Compare AI-generated suggestions with human-defined ground truth names

**Results Generation**
- Create CSV results file with timestamp, original_filename, suggested_name, ground_truth_name, score, and metadata columns
- Include file type, text length, and extractor (default: docling) as metadata in CSV results
- Generate individual markdown files per evaluation with detailed information beyond CSV data
- Store results in organized directory structure with run-id separation

**Configuration and Error Handling**
- Leverage existing hierarchical configuration system (package defaults → project directory → CLI arguments → environment variables)
- Use existing error handling patterns from test framework for graceful API failures
- Support all file types currently handled by best_name (PDF, images, Office documents, text files)
- Follow single-file architecture principles maintaining code simplicity

## Visual Design
No visual assets provided for this specification.

## Existing Code to Leverage

**DSPy Framework Integration (cli.py:38-44, 46-55)**
- FilenameSignature class for structured predictions can be extended for evaluation
- Existing DSPy LM initialization with OpenRouter configuration
- Model prefixing logic for OpenRouter compatibility
- Content extraction and truncation patterns

**Content Extraction Logic (cli.py:154-192)**
- Docling integration for complex file formats (PDF, DOCX, XLSX, PPTX)
- Direct text reading for simple formats (TXT, MD, CSV, JSON, YAML, HTML, CSS)
- Defensive attribute checking for different Docling versions
- File processing error handling patterns

**CLI Structure (cli.py:283-294)**
- Click framework integration patterns for argument parsing
- Hierarchical configuration loading system
- Environment variable handling (OPENROUTER_API_KEY)
- Existing CLI entry point configuration from pyproject.toml

**CSV Generation and Test Framework (tests/run_tests.sh)**
- CSV output format with timestamp and results tracking
- Error handling for API failures with status codes
- File iteration and processing patterns
- Results summary and reporting structure

**Evaluation Data Setup (evals/eval_files.csv)**
- Ground truth data structure with original_file and human_defined_name columns
- Test file organization in evals/eval_files/ directory
- CSV parsing patterns for evaluation data loading

## Out of Scope
- Evaluation frequency tracking and comparison features across multiple runs
- Web interface or dashboard for evaluation results visualization
- Multi-criteria metrics (focus on single overall quality score only)
- Separate CLI entry point (must integrate as subcommand)
- Batch processing beyond single folder evaluation
- Performance comparison between different models or configurations
- Real-time evaluation monitoring or progress tracking beyond basic CLI output