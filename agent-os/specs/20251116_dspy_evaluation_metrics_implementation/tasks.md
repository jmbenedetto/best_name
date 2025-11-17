# Task Breakdown: DSPy Evaluation Metrics Implementation

## Overview
Total Tasks: 18

## Task List

### DSPy Framework and Evaluation Logic

#### Task Group 1: DSPy Evaluation Metrics Foundation
**Dependencies:** None

- [ ] 1.0 Complete DSPy evaluation foundation
  - [ ] 1.1 Write 2-5 focused tests for DSPy evaluation logic
    - Test only critical DSPy metrics functionality (evaluation signature, prediction, scoring)
    - Skip exhaustive testing of all DSPy edge cases and configurations
  - [ ] 1.2 Create EvaluationSignature DSPy class
    - Extend existing FilenameSignature pattern from cli.py:38-44
    - Fields: suggested_name, ground_truth_name, evaluation_score
    - Follow DSPy evaluation framework documentation pattern
  - [ ] 1.3 Implement evaluation prediction logic
    - Reuse existing DSPy LM initialization from cli.py:46-55
    - Compare AI suggestion vs ground truth using LLM scoring
    - Return single overall quality score (0-10 scale)
  - [ ] 1.4 Add evaluation result processing
    - Extract score from DSPy prediction result
    - Handle score parsing and validation
    - Sanitize evaluation results for CSV/MD output
  - [ ] 1.5 Ensure DSPy evaluation tests pass
    - Run ONLY the 2-5 tests written in 1.1
    - Verify evaluation scoring works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-5 tests written in 1.1 pass
- EvaluationSignature follows DSPy patterns
- LLM-based scoring produces valid results
- Score extraction and validation work correctly

### CLI Integration

#### Task Group 2: CLI Subcommand Implementation
**Dependencies:** Task Group 1

- [ ] 2.0 Complete CLI subcommand integration
  - [ ] 2.1 Write 2-5 focused tests for CLI evaluation subcommand
    - Test only critical CLI actions (subcommand registration, argument parsing, basic execution)
    - Skip exhaustive testing of all CLI scenarios and error cases
  - [ ] 2.2 Add evaluation subcommand to existing CLI
    - Integrate `@click.group()` for main command with eval subcommand
    - Follow existing CLI patterns from cli.py:283-294
    - Maintain single-file architecture principles
  - [ ] 2.3 Implement CLI argument parsing for evaluation
    - Arguments: file_path (Path), run_id (Optional[str])
    - Support both individual file and directory path parameter
    - Auto-generate run-id with timestamp if not provided
    - Follow existing Click patterns from main CLI
  - [ ] 2.4 Add evaluation configuration loading
    - Reuse existing hierarchical configuration system from cli.py:329-375
    - Load OpenRouter API settings and model configuration
    - Support environment variable overrides (OPENROUTER_API_KEY)
  - [ ] 2.5 Ensure CLI subcommand tests pass
    - Run ONLY the 2-5 tests written in 2.1
    - Verify subcommand registration and argument parsing
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-5 tests written in 2.1 pass
- Evaluation subcommand integrates seamlessly with existing CLI
- Argument parsing works for files and directories
- Auto-generated run-id format is consistent

### Evaluation Data Processing

#### Task Group 3: File Processing and Ground Truth Loading
**Dependencies:** Task Group 2

- [ ] 3.0 Complete evaluation data processing
  - [ ] 3.1 Write 2-5 focused tests for data processing logic
    - Test only critical data loading and processing (CSV parsing, file iteration, content extraction)
    - Skip exhaustive testing of all file formats and edge cases
  - [ ] 3.2 Implement ground truth data loading
    - Parse evals/eval_files.csv with original_file and human_defined_name columns
    - Handle CSV parsing errors gracefully
    - Match ground truth data with actual files in evals/eval_files/
  - [ ] 3.3 Add evaluation file processing logic
    - Reuse existing content extraction from cli.py:154-192
    - Support all file types (PDF, images, Office docs, text files)
    - Extract metadata: file type, text length, extractor (docling)
  - [ ] 3.4 Implement batch evaluation for directories
    - Iterate through files in specified directory
    - Process only files present in ground truth CSV
    - Handle missing files or mismatched entries gracefully
  - [ ] 3.5 Ensure data processing tests pass
    - Run ONLY the 2-5 tests written in 3.1
    - Verify ground truth loading and file processing work
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-5 tests written in 3.1 pass
- Ground truth CSV loads correctly
- File content extraction works for all supported types
- Directory processing handles batch evaluation

### Results Generation and Storage

#### Task Group 4: Results Output Implementation
**Dependencies:** Task Group 3

- [ ] 4.0 Complete results generation and storage
  - [ ] 4.1 Write 2-5 focused tests for results generation
    - Test only critical results creation (CSV format, MD file content, directory structure)
    - Skip exhaustive testing of all result formatting scenarios
  - [ ] 4.2 Implement CSV results generation
    - Columns: timestamp, original_filename, suggested_name, ground_truth_name, score, file_type, text_length, extractor
    - Follow CSV pattern from tests/run_tests.sh and test_results.md
    - Include proper timestamp formatting and run-id separation
  - [ ] 4.3 Create individual markdown files for detailed results
    - Generate MD files with comprehensive evaluation details
    - Include content beyond CSV data (full evaluation context, reasoning)
    - Organize files by run-id in results directory structure
  - [ ] 4.4 Add results directory management
    - Create organized directory structure: evals/results/[run-id]/
    - Handle existing run-id conflicts with timestamps
    - Ensure proper file permissions and cleanup
  - [ ] 4.5 Ensure results generation tests pass
    - Run ONLY the 2-5 tests written in 4.1
    - Verify CSV and MD file generation work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-5 tests written in 4.1 pass
- CSV results contain all required columns and metadata
- Individual MD files contain detailed evaluation information
- Directory structure organizes results by run-id

### Integration and Error Handling

#### Task Group 5: End-to-End Integration
**Dependencies:** Task Groups 1-4

- [ ] 5.0 Complete end-to-end evaluation integration
  - [ ] 5.1 Write 2-5 focused tests for complete evaluation workflow
    - Test only critical end-to-end scenarios (single file eval, directory eval, results generation)
    - Skip exhaustive testing of all integration edge cases
  - [ ] 5.2 Integrate evaluation workflow end-to-end
    - Connect CLI → data loading → content extraction → DSPy evaluation → results generation
    - Ensure smooth data flow between all components
    - Follow existing error handling patterns from test framework
  - [ ] 5.3 Add comprehensive error handling
    - Graceful API failure handling (reuse patterns from tests/run_tests.sh)
    - File processing error recovery
    - DSPy prediction error handling with fallback behavior
  - [ ] 5.4 Implement verbose output for evaluation
    - Show evaluation progress and key steps when --verbose flag used
    - Display evaluation scores and results summary
    - Follow existing verbose patterns from main CLI
  - [ ] 5.5 Ensure end-to-end integration tests pass
    - Run ONLY the 2-5 tests written in 5.1
    - Verify complete evaluation workflow functions correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-5 tests written in 5.1 pass
- Complete evaluation workflow functions correctly
- Error handling provides graceful degradation
- Verbose output shows meaningful progress information

### Testing and Validation

#### Task Group 6: Test Review & Validation
**Dependencies:** Task Groups 1-5

- [ ] 6.0 Review existing tests and validate evaluation system
  - [ ] 6.1 Review tests from Task Groups 1-5
    - Review the 2-5 tests written by DSPy framework team (Task 1.1)
    - Review the 2-5 tests written by CLI integration team (Task 2.1)
    - Review the 2-5 tests written by data processing team (Task 3.1)
    - Review the 2-5 tests written by results generation team (Task 4.1)
    - Review the 2-5 tests written by integration team (Task 5.1)
    - Total existing tests: approximately 10-25 tests
  - [ ] 6.2 Analyze test coverage gaps for evaluation system
    - Identify critical evaluation workflows that lack test coverage
    - Focus ONLY on gaps related to this spec's evaluation requirements
    - Do NOT assess entire application test coverage
    - Prioritize end-to-end evaluation scenarios over unit test gaps
  - [ ] 6.3 Write up to 8 additional strategic tests maximum
    - Add maximum of 8 new tests to fill identified critical gaps
    - Focus on integration points and end-to-end evaluation workflows
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases, performance tests, and accessibility tests unless business-critical
  - [ ] 6.4 Run evaluation system tests only
    - Run ONLY tests related to this spec's evaluation feature (tests from 1.1, 2.1, 3.1, 4.1, 5.1, and 6.3)
    - Expected total: approximately 18-33 tests maximum
    - Do NOT run the entire application test suite
    - Verify critical evaluation workflows pass

**Acceptance Criteria:**
- All evaluation-specific tests pass (approximately 18-33 tests total)
- Critical evaluation workflows for this feature are covered
- No more than 8 additional tests added when filling in testing gaps
- Testing focused exclusively on this spec's evaluation requirements

## Execution Order

Recommended implementation sequence:
1. DSPy Framework and Evaluation Logic (Task Group 1)
2. CLI Integration (Task Group 2)
3. Evaluation Data Processing (Task Group 3)
4. Results Generation and Storage (Task Group 4)
5. Integration and Error Handling (Task Group 5)
6. Testing and Validation (Task Group 6)

## Key Technical Constraints

- **Single-file architecture**: All evaluation logic should integrate into existing cli.py structure
- **DSPy framework compliance**: Follow DSPy evaluation framework documentation patterns
- **Configuration reuse**: Leverage existing hierarchical configuration system
- **Content extraction reuse**: Use existing Docling integration and text processing logic
- **Error handling consistency**: Follow existing patterns from test framework
- **CLI integration**: Must integrate as `best_name eval` subcommand, not separate CLI
- **File support**: Must handle all file types currently supported by best_name
- **Minimal abstractions**: Keep code direct and procedural, following project patterns