# Spec Requirements: DSPy Evaluation Metrics Implementation

## Initial Description
This spec is for implementing evaluation metrics for the best_name project's DSPy integration. The goal is to create a comprehensive evaluation framework that can assess the quality and accuracy of DSPy-generated filename suggestions.

Key aspects to consider:
- The best_name project uses DSPy for structured predictions to generate filenames
- We need evaluation metrics to measure the quality of filename suggestions
- This will not integrate with the existing test framework.
- Metrics might include accuracy, naming convention compliance, etc.
- Should support automated evaluation and reporting
- There's an existing evals/ directory with eval_files/ containing test files with ground truth names
- This is item #2 on the product roadmap and foundational for all subsequent DSPy-based functionality

## Requirements Discussion

### First Round Questions

**Q1:** I assume you want to implement this using the DSPy metrics approach from their evaluation documentation, using the model to score predictions against ground truth. Is that correct, or do you prefer a simpler string-matching or rule-based approach?

**Answer:** Use DSPy metrics approach from https://dspy.ai/learn/evaluation/metrics/#what-is-a-metric-and-how-do-i-define-a-metric-for-my-task. Use the model to give a score and then decide what to return as metric based on the score.

**Q2:** For the evaluation CLI interface, I'm thinking it should support evaluating individual files, all files in the evals directory, or both. Should we have separate commands like `best_name eval file` and `best_name eval all`, or a single `best_name eval` command that accepts either a file path or folder path?

**Answer:** CLI must be able to run evals over files in a folder (folder path parameter) or individual file (file path parameter). Use run-id as parameter instead of description. No other features for eval.

**Q3:** For the evaluation results CSV format, should we include just the basic metrics (score, pass/fail) or also detailed metadata like file type, content length, processing time, model used, etc.?

**Answer:** Include file type, text length, extractor (default to docling) as metadata in CSV.

**Q4:** How should detailed evaluation results be presented? Should we generate individual markdown files per evaluation with full details, or create a single comprehensive HTML/MD report, or both?

**Answer:** Individual MD files should include all detailed information beyond what's in the CSV.

**Q5:** Should the evaluation system support tracking performance over time (comparing different runs, model versions, or configuration changes) or focus on single-run evaluation for now?

**Answer:** No support for evaluation frequency and comparison features.

### Existing Code to Reference

**Similar Features Identified:**
- Test framework: tests/run_tests.sh script that processes files and generates CSV results
- File processing: Content extraction logic in cli.py using Docling and direct text reading
- CSV reporting: test_results.md file generation with timestamp and results tracking
- Error handling: Graceful API error handling in test scenarios

### Follow-up Questions

Based on your answers, I have a few follow-up questions:

1. For the DSPy metrics implementation, should the evaluation metrics include multiple criteria (accuracy, naming convention compliance, semantic relevance) and average them, or focus on a single overall quality score?

2. Should the evaluation CLI integrate with the existing best_name CLI as a subcommand (`best_name eval`) or be a separate CLI entry point?

3. For the run-id parameter, should this be auto-generated with timestamp if not provided, or required as a mandatory parameter?

**Follow-up 1:** For the DSPy metrics implementation, should the evaluation metrics include multiple criteria (accuracy, naming convention compliance, semantic relevance) and average them, or focus on a single overall quality score?
**Answer:** Focus on single overall quality score that the LLM provides based on comparing the prediction with ground truth.

**Follow-up 2:** Should the evaluation CLI integrate with the existing best_name CLI as a subcommand (`best_name eval`) or be a separate CLI entry point?
**Answer:** Integrate as a subcommand: `best_name eval`

**Follow-up 3:** For the run-id parameter, should this be auto-generated with timestamp if not provided, or required as a mandatory parameter?
**Answer:** Should be auto-generated with timestamp if not provided.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
No visual insights available as no mockups or wireframes were provided.

## Requirements Summary

### Functional Requirements
- Implement DSPy evaluation metrics using model-based scoring approach
- Create evaluation CLI that supports both individual files and folder processing
- Generate CSV results with metadata (file type, text length, extractor)
- Create individual markdown files with detailed evaluation information
- Auto-generate run-id with timestamp if not provided
- Integrate as `best_name eval` subcommand

### Reusability Opportunities
- Content extraction logic from existing cli.py for consistent file processing
- Error handling patterns from existing test framework
- Configuration loading from existing hierarchical system
- CLI argument parsing patterns using Click framework

### Scope Boundaries
**In Scope:**
- DSPy metrics implementation using model scoring
- Evaluation CLI with file/folder support
- CSV results with metadata columns
- Individual MD files for detailed results
- Auto-generated run-id with timestamp
- Integration with existing best_name CLI

**Out of Scope:**
- Evaluation frequency tracking and comparison features
- Web interface for evaluation results
- Multi-criteria metrics (focus on single quality score)
- Separate CLI entry point (use subcommand instead)
- Batch processing beyond single folder

### Technical Considerations
- Must follow DSPy evaluation framework documentation
- Integration with existing OpenRouter API configuration
- Leverage existing Docling content extraction
- Use existing hierarchical configuration system
- Follow single-file architecture patterns where possible
- Maintain error handling consistency with current codebase
- Support all file types currently handled by best_name
- Use existing CSV and markdown generation patterns