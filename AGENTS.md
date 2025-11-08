# AGENTS.md

## Project Overview

`best_name` is a Python CLI tool that suggests optimal filenames for documents based on their content using LLM analysis. It extracts content from various file formats (PDFs, images, Office documents, text files) and generates naming suggestions following user-defined conventions.

## Project Structure

```
best_name/
├── best_name/
│   ├── cli.py              # Single-file architecture containing all CLI logic
│   ├── __init__.py         # Package entry point that exports the cli function
│   ├── config.yaml         # Default OpenRouter settings and file paths
│   ├── conventions.md      # User-specific naming conventions and document categories
│   └── system_prompt.md    # LLM system prompt for name generation
├── test/                   # Test files (13 files of various formats)
├── run_tests.sh            # Automated test script with rate limiting
├── test_results.md         # CSV format test results
├── pyproject.toml          # Project dependencies managed by uv
├── AGENTS.md               # This file - AI agent instructions
├── CLAUDE.md               # Reference to this file
└── README.md               # User documentation
```

## Architecture

### Core Components

- **best_name/cli.py**: Single-file architecture containing all CLI logic
  - Content extraction using Docling library for complex formats (PDF, DOCX, XLSX, PPTX)
  - Direct text reading for simple formats (TXT, MD, CSV, JSON, YAML, HTML, CSS)
  - OpenRouter API integration for LLM-based name generation
  - Click-based CLI with options for conventions, system prompts, and API configuration

- **best_name/__init__.py**: Package entry point that exports the `cli` function

- **Configuration Files** (packaged with the tool):
  - best_name/config.yaml: Default OpenRouter settings and file paths
  - best_name/conventions.md: User-specific naming conventions and document categories
  - best_name/system_prompt.md: LLM system prompt for name generation

### Key Design Principles

- **Single-file core logic**: All functionality in cli.py for simplicity
- **Packaged config files**: Default conventions/prompts are included in the package (see `tool.setuptools.package-data` in pyproject.toml)
- **Cascading configuration**: Package defaults → project directory → CLI arguments → environment variables (highest priority)
- **Minimal abstractions**: Procedural code flow, no complex error handling or logging

## Core Commands

```bash
# Basic usage (outputs suggested filename without extension)
best_name /path/to/file.pdf

# With custom conventions
best_name file.pdf --conventions custom_conventions.md

# Copy file with suggested name (preserves original)
best_name file.pdf --copy

# Rename file with suggested name
best_name file.pdf --rename

# Verbose mode (shows extraction, prompts, and LLM exchange)
best_name file.pdf --verbose

# Custom configuration
best_name file.pdf \
  --config custom_config.yaml \
  --system-prompt custom_system_prompt.md \
  --model gpt-4o-mini \
  --api-key $OPENROUTER_API_KEY
```

## Implementation Requirements

### Functional Requirements
- **Supported file formats**:
  - Text: txt, md, csv, json, yaml, xml, html, css
  - Images: jpg, jpeg, png, gif, svg, ico
  - Documents: pdf, docx, xlsx, pptx
- **Language support**: English, Spanish, French, Portuguese
- **Output**: String with suggested filename (without extension)

### Technical Constraints
- **Single file architecture**: All code in `best_name/cli.py`
- **Package management**: Use `uv` exclusively for all Python operations (virtual environments, package management, running scripts)
- **CLI tool**: Use `uv tool install -e .` for local development, `uv tool install .` for installation
- **File processing**: Use Docling for complex formats, direct text reading for simple formats
- **LLM integration**: OpenRouter API for name generation
- **Configuration**: YAML config file for defaults, packaged with the tool
- **Simplicity first**: Readable over clever, minimal abstractions, linear flow
- **Environment variables**: OPENROUTER_API_KEY required (via env or .env file)
- **No complex error handling**: Let errors bubble up naturally
- **No logging framework**: Use simple print statements or Click's echo

### CLI Arguments Structure
```python
# Required argument
file_path: str  # Path to the file to analyze

# Optional arguments
--conventions: str     # Path to conventions/categories markdown file (default: packaged conventions.md)
--system-prompt: str   # Path to system prompt markdown file (default: packaged system_prompt.md)
--config: str          # Path to config YAML file (default: packaged config.yaml)
--api-key: str         # OpenRouter API key (overrides OPENROUTER_API_KEY env var)
--model: str           # LLM model name (default: from config.yaml)
--base-url: str        # OpenRouter base URL (default: from config.yaml)
--copy                 # Copy file with suggested name (preserves original)
--rename               # Rename file with suggested name (mutually exclusive with --copy)
--verbose              # Show extraction, prompts, and LLM exchange
```

## Development Workflow

### Environment Setup
```bash
# Install dependencies with uv (required - this project uses uv exclusively)
uv sync

# Install as global CLI tool for testing
uv tool install -e .

# Verify installation
best_name --help
```

### Running During Development
```bash
# Option 1: Install locally and run as CLI (recommended)
uv tool install -e .
best_name /path/to/file.pdf

# Option 2: Run module directly with uv
uv run -m best_name /path/to/file.pdf
```

## Configuration Hierarchy

The tool resolves configuration in this order (later overrides earlier):

1. **Package defaults**: Files bundled in `best_name/` (config.yaml, conventions.md, system_prompt.md)
2. **Project directory**: Files in current working directory
3. **CLI arguments**: `--conventions`, `--system-prompt`, `--config`, `--model`, `--base-url`
4. **Environment variables**: `OPENROUTER_API_KEY` (required)

## Required Environment Variables

```bash
# Required for LLM API calls
export OPENROUTER_API_KEY=your_key_here

# Or use .env file in project root
echo "OPENROUTER_API_KEY=your_key_here" > .env
```


## Code Style Guidelines

- **Simplicity**: Prioritize readability over cleverness
- **No complex error handling**: Let errors bubble up naturally
- **No logging**: Use simple print statements if needed
- **Linear flow**: Avoid nested functions or complex control structures
- **Clear variable names**: Use descriptive names over abbreviations
- **Minimal abstractions**: Keep code direct and procedural

## File Operations

The tool supports three modes:

- **Suggest only** (default): Prints suggested filename to stdout
- **Copy** (`--copy`): Creates copy with suggested name, preserves original
- **Rename** (`--rename`): Renames original file (mutually exclusive with --copy)

All operations preserve the original file extension.

## Entry Point Configuration

From pyproject.toml:

```toml
[project.scripts]
best_name = "best_name:cli"
```

This makes the CLI available as `best_name` command after `uv tool install`.

## Implementation Flow

1. Parse command line arguments using Click
2. Load config.yaml for default values (from package or project directory)
3. Override defaults with CLI arguments if provided
4. Read conventions file (default or custom)
5. Read system prompt file (default or custom)
6. Extract content from input file:
   - Use Docling for complex formats (PDF, DOCX, XLSX, PPTX)
   - Direct text reading for simple formats (TXT, MD, CSV, JSON, YAML, HTML, CSS)
7. Truncate content to 12,000 characters for LLM context
8. Prepare LLM prompt combining system prompt, conventions, and file content
9. Call OpenRouter API with prepared prompt
10. Sanitize suggested filename (remove illegal chars, limit to 120 chars)
11. Return suggested filename (without extension) or perform file operation (copy/rename)

## CLI Installation and Setup

```bash
# Install the CLI tool locally from the project directory
cd /path/to/best_name  # Navigate to the project directory
uv tool install .      # Install from current directory

# Alternative: Install from any location by specifying the path
uv tool install /path/to/best_name

# Ensure environment variables are set (required)
export OPENROUTER_API_KEY="your_api_key_here"
# OR create a .env file with:
# OPENROUTER_API_KEY=your_api_key_here

# Verify installation
which best_name        # Should show the installed CLI path
best_name --help       # Should show help information
```

## Running Commands

### Basic Usage
```bash
# Simple usage with defaults (most common)
best_name /path/to/file.pdf

# The tool will output just the suggested filename (without extension)
# Example output: "financial_report_q4_2024"
```

### Advanced Usage
```bash
# Test with custom conventions
best_name test/image.jpg --conventions my_rules.md

# Test with different models
best_name file.pdf --model claude-3-5-sonnet

# Test with all custom options
best_name file.pdf \
  --conventions custom_conventions.md \
  --system-prompt custom_system_prompt.md \
  --api-key YOUR_API_KEY \
  --model gpt-4o-mini
```

## Testing the CLI

### Automated Testing
Use the provided test script to run comprehensive tests:

```bash
# Run all tests (requires test/ directory with test files)
./run_tests.sh

# This will:
# - Test all files in the test/ directory
# - Generate a CSV report (test_results.md) with timestamps
# - Include rate limiting (1 second delay between API calls)
# - Handle API errors gracefully
# - Show progress for each file tested
```

### Test Results
The test script generates a CSV file with:
- `timestamp`: When the test was run
- `original_filename`: The input file name
- `suggested_name`: The AI-generated suggestion (or error message)

```bash
# View test results
cat test_results.md

# Example output format:
# timestamp,original_filename,suggested_name
# 2024-01-15 10:30:15,document.pdf,quarterly_financial_report
# 2024-01-15 10:30:17,image.jpg,ERROR: Failed to generate suggestion
```

### Manual Testing Examples
```bash
# Test with different file types
best_name test/spreadsheet.xlsx
best_name test/presentation.pptx
best_name test/text_document.txt
best_name test/image.png

# Test error handling
best_name non_existent_file.pdf  # Should handle gracefully
```

### Test Directory Structure
```bash
test/
├── document.pdf
├── image.jpg
├── spreadsheet.xlsx
├── presentation.pptx
├── text_file.txt
└── # Add more test files as needed
```

## Key Dependencies

- **click**: CLI framework for argument parsing
- **docling**: File content extraction (handles multiple formats)
- **openai**: OpenRouter API client (OpenRouter uses OpenAI-compatible API)
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management

## Important Implementation Notes

- **Docling API**: Uses defensive attribute checking for different Docling versions (see `extract_content_with_docling` in cli.py:49-87)
- **Content truncation**: File content limited to 12,000 characters for LLM context (see cli.py:136)
- **Filename sanitization**: Removes illegal filesystem characters and limits to 120 characters (see `sanitize_filename` in cli.py:112-129)
- **Package resolution**: Looks for config files in package directory first, then project directory (see cli.py:261-273)

## Common Modifications

When making changes:

- **Modifying naming logic**: Update best_name/conventions.md (packaged with tool)
- **Changing system prompt**: Update best_name/system_prompt.md (packaged with tool)
- **Adding file format support**: Update `text_like_exts` in cli.py:91-102 or rely on Docling
- **Changing default model**: Update `openrouter.model` in best_name/config.yaml
- **Adding CLI options**: Add Click decorators to `cli()` function in cli.py:174-230

## Development Notes

- All logic in cli.py for simplicity
- Use Click decorators for CLI argument handling
- Let Docling handle complex file format extraction
- Use OpenAI client library with OpenRouter base URL
- Config files are packaged with the tool (see pyproject.toml package-data)
- Always use `uv` for all Python operations

## Common Issues

- If Docling fails to parse a file, fallback to direct text reading for supported formats
- If API call fails, print error and exit (no retry logic)
- Environment variables and CLI arguments override config file settings

---

*This AGENTS.md is intentionally minimal to match the project's simplicity requirements. Update only when core functionality changes.*