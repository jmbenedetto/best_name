# Technical Stack

## Core Platform

### Framework & Runtime
- **Language/Runtime:** Python 3.12+ (primary language for CLI tool and core functionality)
- **Package Manager:** uv (modern Python package management, virtual environments, and dependency resolution)
- **Application Framework:** Click (Python CLI framework for argument parsing and command structure)

### Content Processing
- **Document Analysis:** Docling (multi-format content extraction for PDF, DOCX, XLSX, PPTX, images)
- **Text Processing:** Python standard libraries (text parsing, content sanitization, character encoding)
- **File System Operations:** Python pathlib, shutil (cross-platform file operations and path handling)

### AI & Language Processing
- **AI Integration:** OpenAI client library (OpenRouter API integration using OpenAI-compatible interface)
- **Language Models:** OpenRouter (supports multiple providers including Anthropic, OpenAI, Google, etc.)
- **Prompt Engineering:** Custom system prompts with YAML configuration and markdown templates

### Configuration Management
- **Configuration Format:** YAML (hierarchical configuration with environment variable substitution)
- **Environment Variables:** python-dotenv (environment variable management and .env file support)
- **Template System:** Packaged markdown templates for conventions and system prompts

## Development & Testing

### Testing Framework
- **Test Runner:** pytest (Python testing framework)
- **Test Data:** Sample files covering supported formats (tests/test_files/ directory)
- **Rate Limiting:** Built-in delays for API testing (tests/run_tests.sh script)
- **Error Handling:** Graceful API error handling in test scenarios

## CLI Architecture

### Single-File Design
- **Core Logic:** best_name/cli.py (all functionality in single file for simplicity)
- **Package Structure:** Minimal abstraction with linear code flow
- **Entry Point:** best_name/__init__.py (package initialization and cli export)

### File Operations
- **Content Extraction:** Docling integration with defensive programming for version compatibility
- **Name Sanitization:** Custom filename sanitization (illegal character removal, length limits)
- **File Operations:** Safe copy, rename, and suggestion modes with error propagation

## Deployment & Distribution

### Package Distribution
- **Distribution Format:** Python wheel distribution via PyPI-compatible package managers
- **Installation Method:** uv tool install (modern CLI tool installation and management)
- **Package Data:** Bundled configuration files (config.yaml, conventions.md, system_prompt.md)

### Configuration Hierarchy
1. **Package Defaults:** Bundled configuration files in best_name/ directory
2. **Project Directory:** Local configuration files in current working directory
3. **CLI Arguments:** Command-line parameter overrides
4. **Environment Variables:** OPENROUTER_API_KEY and other runtime settings

## Integration Points

### API Integration
- **OpenRouter API:** AI model access with multiple provider support
- **Authentication:** API key-based authentication with secure logging
- **Error Handling:** Graceful API error handling with user-friendly error messages

### File System Integration
- **Cross-Platform Support:** Windows, macOS, Linux compatibility
- **File Type Detection:** Extension-based processing with fallback strategies
- **Path Handling:** Absolute and relative path support with validation

## Supported File Formats

### Text-Based Formats (Direct Reading)
- **Documents:** TXT, MD, CSV, JSON, YAML, XML, HTML, CSS
- **Configuration:** TOML, INI, CONF files (via direct text reading)
- **Source Code:** PY, JS, TS, JAVA, CPP, and other text-based code files (via direct text reading)

### Office Documents (via Docling)
- **Word Processing:** DOCX (Microsoft Word documents)
- **Spreadsheets:** XLSX (Microsoft Excel files)
- **Presentations:** PPTX (Microsoft PowerPoint presentations)

### Images & Media (via Docling)
- **Images:** JPG, JPEG, PNG, GIF, SVG, ICO
- **Vector Graphics:** SVG files with text content extraction

### Complex Documents (via Docling)
- **PDF Documents:** Text extraction from PDF files with layout preservation

## Performance Considerations

### Content Processing
- **Content Limits:** 12,000 character truncation for LLM context windows (cli.py:136)
- **Error Resilience:** Graceful degradation when document parsing fails
- **Filename Sanitization:** Illegal character removal and 120-character limit (cli.py:112-129)

### API Optimization
- **Rate Limiting:** Built-in delays in test script to respect API limits

## Security & Privacy

### Data Handling
- **Local Processing:** Content analysis performed locally before API transmission
- **API Security:** HTTPS communication with encrypted API keys
- **Privacy Compliance:** No permanent storage of user content on external servers

### Error Handling
- **Secure Logging:** Sanitized logging that doesn't expose sensitive information
- **Graceful Failures:** Error propagation without exposing system internals
- **Input Validation**: Comprehensive validation of file paths and user inputs