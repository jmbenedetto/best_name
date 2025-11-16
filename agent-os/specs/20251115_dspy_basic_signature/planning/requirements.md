# Spec Requirements: DSPy Signature Integration for Filename Prediction

## Initial Description
DSPy integration that replaces the existing OpenRouter API call with DSPy's structured prediction capabilities. The feature should maintain the single-file architecture, support all existing file types, and keep it simple. Backward compatibility is not required.

## Requirements Discussion

### First Round Questions

**Q1:** I see from `study_01.py` that you're using `dspy.LM` with OpenRouter models (like `qwen/qwen-2.5-7b-instruct`). Should I completely replace the OpenAI client approach with DSPy's `dspy.LM` throughout the CLI, or would you prefer to keep both as options?

**Answer:** Replace completely with DSPy - the goal is to use DSPy exclusively for all LLM interactions.

**Q2:** The current config.yaml uses OpenAI-specific settings (`openrouter.api_key`, `openrouter.model`, `openrouter.base_url`). Should I adapt this structure to support DSPy's configuration approach, or create a new DSPy-specific configuration section while keeping the existing one for migration reference?

**Answer:** Adapt the existing structure - modify the config.yaml to work with DSPy while keeping the same field names where possible.

**Q3:** In `study_01.py`, you create a custom `FilenameSignature` class that inherits from `dspy.Signature`. For the CLI integration, should I dynamically create this signature based on the conventions.md content, or create a fixed signature structure that gets populated with convention data at runtime?

**Answer:** Statically create the signature. The signature will be composed by 2 inputs (file_content and naiming_conventions), and 1 output (suggested_name). 

**Q4:** DSPy's `dspy.Predict` returns structured objects with confidence scores. Should I expose these confidence scores to users through a new CLI option (like `--confidence`) or integrate them into the existing `--verbose` output, or simply ignore them for now to keep things simple?

**Answer:** Integrate into existing `--verbose` output - keep things simple by not adding new CLI options.

**Q5:** The current implementation has specific error handling for OpenAI API failures. How should I handle DSPy prediction errors? Should I maintain the same "print error and exit" approach, or would you prefer more graceful fallbacks given DSPy's structured nature?

**Answer:** Maintain the same simple approach - print error and exit without complex fallback logic.

**Q6:** For the model selection in DSPy, should I default to the same model from your `study_01.py` (`qwen/qwen-2.5-7b-instruct`) or use the model specified in the current config.yaml? What's your preferred default DSPy model for production use?

**Answer:** Use the model from config.yaml. However, set it to grok 4 fast.

### Existing Code to Reference
Based on the user's response about referencing the study implementation:

**Similar Features Identified:**
- Feature: DSPy Integration Study - Path: `/home/jmb/code/best_name/study_01.py`
- Components to potentially reuse: DSPy LM setup, signature structure, prediction approach
- Backend logic to reference: Content loading, prompt construction, classification example

### Follow-up Questions

**Follow-up 1:** The conventions.md file currently contains both naming conventions and document categories. How should I structure this content for DSPy's signature? Should I split it into separate components (input examples for the signature, and category definitions), or keep it as a single context block that gets included in the prediction?

**Answer:** Keep as a single input called namining_conventions.

**Follow-up 2:** For the file content that gets passed to DSPy (currently truncated to 12,000 characters), should I maintain this same limit or adjust it based on DSPy's token handling capabilities? The current limit was chosen for the OpenAI API's context window.

**Answer:** Maintain the 12,000 character limit for consistency and to avoid exceeding model context windows.

## Visual Assets

### Files Provided:
No visual assets were provided for this feature specification.

### Visual Insights:
- No design mockups or wireframes were referenced
- This is a backend/CLI enhancement with no UI changes required

## Requirements Summary

### Functional Requirements
- Replace OpenAI client with DSPy's `dspy.LM` using OpenRouter models
- Use DSPy `dspy.Signature` for structured input/output definition
- Implement `dspy.Predict` for filename generation (no chain-of-thought)
- Maintain support for all existing file types (PDF, images, documents, text)
- Preserve all existing CLI options and functionality
- Integrate confidence scores into verbose output only

### Reusability Opportunities
- Leverage DSPy patterns from `study_01.py` for LM setup and configuration
- Reuse existing content extraction logic (Docling integration)
- Maintain current CLI argument structure and file operations
- Adapt existing configuration hierarchy for DSPy settings

### Scope Boundaries
**In Scope:**
- Complete replacement of OpenAI API with DSPy integration
- Dynamic signature creation based on conventions.md content
- Confidence score integration in verbose mode
- Configuration adaptation for DSPy LM setup

**Out of Scope:**
- Backward compatibility with existing OpenAI implementation
- New CLI options for DSPy-specific features
- Chain-of-thought or multi-step DSPy modules
- Advanced error handling or fallback mechanisms

### Technical Considerations
- Use model from config.yaml for DSPy LM initialization
- Maintain 12,000 character content limit for predictions
- Keep simple error handling approach (print and exit)
- Preserve existing configuration hierarchy and CLI structure
- Follow single-file architecture with all logic in cli.py