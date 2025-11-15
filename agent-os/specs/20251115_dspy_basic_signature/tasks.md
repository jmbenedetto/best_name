# Task Breakdown: DSPy Signature Integration for Filename Prediction

## Overview
Total Tasks: 14 (7 core implementation tasks + 7 testing/validation tasks)

## Task List

### Dependencies and Configuration

#### Task Group 1: DSPy Integration Setup
**Dependencies:** None

- [ ] 1.0 Complete DSPy integration setup
  - [ ] 1.1 Write 2-8 focused tests for DSPy LM configuration and prediction
    - Limit to 2-8 highly focused tests maximum
    - Test only critical DSPy behaviors (LM initialization, prediction execution, confidence score extraction)
    - Skip exhaustive testing of all DSPy features and edge cases
  - [ ] 1.2 Update pyproject.toml dependencies
    - Add dspy dependency with version constraint
    - Remove openai dependency if no longer needed
    - Verify compatibility with existing dependencies (docling, click, pyyaml)
  - [ ] 1.3 Update config.yaml with DSPy-compatible settings
    - Change default model to "x-ai/grok-4-fast" as specified
    - Maintain openrouter structure for API key and base URL
    - Preserve existing defaults section for file paths
  - [ ] 1.4 Create FilenameSignature class
    - Define static signature with two inputs: file_content, naming_conventions
    - Define single output: suggested_name
    - Follow dspy.Signature pattern with proper input/output descriptors
  - [ ] 1.5 Implement DSPy LM initialization function
    - Replace OpenAI client with dspy.LM using OpenRouter models
    - Handle API key authentication via OPENROUTER_API_KEY
    - Configure model from config.yaml with fallback to default
  - [ ] 1.6 Ensure DSPy setup tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify DSPy LM initializes correctly with OpenRouter
    - Confirm signature class structure is valid
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- DSPy dependencies are properly configured
- FilenameSignature class follows correct structure
- DSPy LM initializes with OpenRouter authentication

### Core CLI Integration

#### Task Group 2: Replace OpenAI with DSPy
**Dependencies:** Task Group 1

- [ ] 2.0 Complete OpenAI to DSPy replacement
  - [ ] 2.1 Write 2-8 focused tests for prediction functionality
    - Limit to 2-8 highly focused tests maximum
    - Test only critical prediction behaviors (file content processing, conventions integration, name generation)
    - Skip exhaustive testing of all file formats and edge cases
  - [ ] 2.2 Replace call_openrouter function with call_dspy_prediction
    - Remove OpenAI client usage and replace with dspy.Predict
    - Use FilenameSignature for structured input/output
    - Maintain same function signature for compatibility with existing CLI flow
  - [ ] 2.3 Implement content processing for DSPy predictions
    - Maintain 12,000 character limit for file content as specified
    - Combine file_content and naming_conventions as signature inputs
    - Preserve existing content extraction logic using Docling
  - [ ] 2.4 Handle DSPy prediction results and confidence scores
    - Extract suggested_name from prediction output
    - Capture confidence scores for verbose mode integration
    - Maintain simple error handling (print error and exit on failures)
  - [ ] 2.5 Update verbose output to include DSPy confidence information
    - Add confidence scores to existing --verbose output without new CLI options
    - Maintain existing verbose format for all other processing steps
    - Display structured prediction results when verbose mode is enabled
  - [ ] 2.6 Ensure prediction tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify filename generation works with DSPy predictions
    - Confirm confidence scores are properly extracted and displayed
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- OpenAI client is completely replaced with DSPy
- DSPy predictions generate valid filenames
- Confidence scores appear in verbose output

### CLI Functionality Preservation

#### Task Group 3: Maintain Existing CLI Interface
**Dependencies:** Task Group 2

- [ ] 3.0 Complete CLI functionality preservation
  - [ ] 3.1 Write 2-8 focused tests for CLI operations
    - Limit to 2-8 highly focused tests maximum
    - Test only critical CLI behaviors (argument parsing, file operations, configuration resolution)
    - Skip exhaustive testing of all CLI combinations and edge cases
  - [ ] 3.2 Preserve all existing Click CLI decorators and arguments
    - Maintain same argument structure: --conventions, --system-prompt, --api-key, --model, --base-url, --config, --copy, --rename, --verbose
    - Keep file_path argument validation and type hints
    - Preserve mutual exclusion checks for --copy and --rename
  - [ ] 3.3 Maintain configuration hierarchy and path resolution
    - Keep resolve_path function for config file lookup
    - Preserve load_yaml_config adaptation for DSPy settings
    - Maintain defaults: package → project directory → CLI arguments → environment variables
  - [ ] 3.4 Preserve file operations logic (copy, rename, validation)
    - Keep existing filename sanitization and validation logic
    - Maintain file operation error handling for copy/rename
    - Preserve original file extension handling
  - [ ] 3.5 Ensure CLI functionality tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all CLI options work as before
    - Confirm file operations (copy/rename) function correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All existing CLI options maintain functionality
- File operations work exactly as before
- Configuration hierarchy is preserved

### Testing and Validation

#### Task Group 4: End-to-End Integration Testing
**Dependencies:** Task Groups 1-3

- [ ] 4.0 Complete end-to-end testing and validation
  - [ ] 4.1 Review tests from Task Groups 1-3
    - Review the 2-8 tests written by dependencies-engineer (Task 1.1)
    - Review the 2-8 tests written by backend-engineer (Task 2.1)
    - Review the 2-8 tests written by frontend-engineer (Task 3.1)
    - Total existing tests: approximately 6-24 tests
  - [ ] 4.2 Test with existing test file structure
    - Run integration tests with files in test/ directory
    - Verify support for all existing file types (PDF, images, documents, text)
    - Test both simple and complex file formats using Docling extraction
  - [ ] 4.3 Validate configuration system end-to-end
    - Test configuration resolution hierarchy with different config locations
    - Verify CLI argument overrides work correctly
    - Test environment variable handling for API keys
  - [ ] 4.4 Run comprehensive file format validation
    - Test PDF processing with content extraction and DSPy prediction
    - Test image file handling and filename generation
    - Test document formats (DOCX, XLSX, PPTX) processing
    - Test text formats (TXT, MD, CSV, JSON, YAML, HTML, CSS) handling
  - [ ] 4.5 Execute run_tests.sh script validation
    - Use existing test script format for validation
    - Maintain same CSV result format for comparing performance
    - Verify rate limiting and API error handling work correctly
  - [ ] 4.6 Write up to 10 additional strategic tests maximum
    - Add maximum of 10 new tests to fill identified critical gaps
    - Focus on integration points between DSPy and existing CLI flow
    - Test verbose output with confidence scores specifically
    - Do NOT write comprehensive coverage for all scenarios
  - [ ] 4.7 Run complete feature validation
    - Run ONLY tests related to DSPy integration (tests from 1.1, 2.1, 3.1, and 4.6)
    - Expected total: approximately 16-34 tests maximum
    - Verify critical end-to-end workflows pass
    - Do NOT run the entire application test suite

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 16-34 tests total)
- End-to-end workflows for filename prediction work correctly
- All file types are processed and predictions generated
- Configuration system works across all hierarchy levels
- Verbose output includes DSPy confidence scores appropriately
- No more than 10 additional tests added when filling in testing gaps

## Execution Order

Recommended implementation sequence:
1. **DSPy Integration Setup** (Task Group 1) - Core dependency and signature setup
2. **Replace OpenAI with DSPy** (Task Group 2) - Core prediction logic replacement
3. **Maintain Existing CLI Interface** (Task Group 3) - Preserve user experience
4. **End-to-End Integration Testing** (Task Group 4) - Comprehensive validation

## Key Implementation Notes

### Single-File Architecture Preservation
- All DSPy integration logic must remain in cli.py
- No new modules or files should be created
- Maintain existing code organization and flow structure

### Configuration Adaptation Strategy
- Adapt existing openrouter section structure for DSPy compatibility
- Preserve field names where possible to minimize breaking changes
- Maintain environment variable handling for OPENROUTER_API_KEY

### DSPy Pattern Reference
Since study_01.py was not available, use standard DSPy patterns:
```python
# Signature structure
class FilenameSignature(dspy.Signature):
    """Generate appropriate filename based on file content and naming conventions."""

    file_content = dspy.InputField(desc="The extracted content from the file")
    naming_conventions = dspy.InputField(desc="The naming conventions and categories to follow")
    suggested_name = dspy.OutputField(desc="The suggested filename without extension")

# LM setup and prediction
lm = dspy.LM(model=model_name, api_key=api_key, api_base=base_url)
dspy.configure(lm=lm)
predictor = dspy.Predict(FilenameSignature)
result = predictor(file_content=content, naming_conventions=conventions)
```

### Error Handling Approach
- Maintain simple "print error and exit" pattern
- No complex fallback mechanisms or retry logic
- Preserve existing error message patterns for user consistency

### Verbose Output Enhancement
- Add confidence scores to existing verbose display without new CLI options
- Maintain current verbose format for processing steps
- Show structured prediction results when verbose mode is enabled