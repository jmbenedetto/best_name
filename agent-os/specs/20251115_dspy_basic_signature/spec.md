# Specification: DSPy Signature Integration for Filename Prediction

## Goal
Replace the existing OpenRouter API integration with DSPy's structured prediction capabilities while maintaining the single-file architecture and all existing CLI functionality.

## User Stories
- As a CLI user, I want the tool to use DSPy for filename generation so that I get more consistent and structured predictions
- As a developer, I want the OpenRouter API completely replaced with DSPy so that the codebase is more maintainable and follows modern practices
- As a user, I want all existing CLI options and file operations to work exactly as before so that my workflows are not disrupted

## Specific Requirements

**DSPy Integration**
- Replace OpenAI client with dspy.LM using OpenRouter models exclusively
- Create static FilenameSignature class with two inputs (file_content, naming_conventions) and one output (suggested_name)
- Use dspy.Predict for filename generation without chain-of-thought complexity
- Configure DSPy LM using model from config.yaml (default: grok-4-fast)
- Maintain same API key authentication via OPENROUTER_API_KEY environment variable

**Configuration Management**
- Adapt existing config.yaml structure for DSPy LM settings while preserving field names
- Update default model to "x-ai/grok-4-fast" in config.yaml
- Maintain configuration hierarchy: package defaults → project directory → CLI arguments → environment variables
- Preserve all existing CLI option functionality and argument structure

**Content Processing**
- Maintain 12,000 character limit for file content passed to DSPy predictions
- Preserve existing file type support (PDF, images, documents, text files)
- Keep all current content extraction logic using Docling for complex formats
- Integrate naming_conventions as single input parameter from conventions.md

**Verbose Output Enhancement**
- Add DSPy confidence scores to existing --verbose output without new CLI options
- Display prediction confidence information alongside current verbose details
- Show structured prediction results when verbose mode is enabled
- Maintain existing verbose format for all other processing steps

**Error Handling**
- Keep simple error handling approach - print error and exit on DSPy failures
- Maintain same error message patterns and user experience
- No complex fallback mechanisms or retry logic
- Preserve existing file operation error handling for copy/rename

## Visual Design
No visual assets provided - this is a backend/CLI enhancement with no UI changes required.

## Existing Code to Leverage

**study_01.py DSPy patterns**
- Use dspy.LM setup pattern with OpenRouter model configuration
- Reference signature class structure from ClassifyFileClass
- Apply dspy.Predict usage pattern for structured predictions
- Follow confidence score extraction and display approach

**Current CLI architecture (cli.py)**
- Reuse all existing Click CLI decorators and argument structure
- Maintain file operations logic (copy, rename, validation)
- Preserve content extraction functions using Docling
- Keep configuration resolution hierarchy and path resolution logic
- Use existing filename sanitization and validation logic

**Configuration system**
- Adapt current load_yaml_config function for DSPy settings
- Maintain resolve_path function for configuration file lookup
- Preserve defaults section structure in config.yaml
- Keep environment variable handling for API keys

**Testing and validation**
- Leverage existing test file structure in test/ directory
- Use current run_tests.sh script format for validation
- Maintain same CSV result format for comparing performance

## Out of Scope
- Backward compatibility with existing OpenAI implementation
- New CLI options for DSPy-specific features
- Chain-of-thought or multi-step DSPy modules
- Advanced error handling or retry mechanisms
- Configuration file format changes beyond model default
- Changes to file operation logic or validation
- Modifications to packaging or installation procedures
- Performance optimizations beyond current approach
- Additional file format support beyond existing types
- Integration with other DSPy modules or frameworks