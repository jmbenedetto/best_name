# AGENTS.md

## Project Overview

This is a CLI tool that suggests the most appropriate name for any given file using LLM call. The tool processes various file formats, extracts their content, and generates intelligent naming suggestions based on the file's actual content.

## Project Structure

```
file-namer-cli/
├── best_name_core.py          # Single Python file containing all CLI logic
├── config.yaml                # Default configuration and settings
├── conventions.md     # Default naming conventions and categories
├── system_prompt.md   # Default system prompt for LLM
├── README.md                  # User documentation
├── AGENTS.md                  # This file - AI agent instructions
├── pyproject.toml             # Project dependencies managed by uv
└── examples/                  # Optional: example files for testing
    ├── custom_conventions.md
    └── custom_system_prompt.md
```

## Core Commands


```bash
# Basic usage - suggest name for a file (uses defaults)
best_name /path/to/file.pdf

# With custom conventions and categories
best_name /path/to/file.pdf \
  --conventions custom_conventions.md

# With custom system prompt
best_name /path/to/file.pdf \
  --system-prompt custom_system_prompt.md

# With all optional arguments
best_name /path/to/file.pdf \
  --conventions custom_conventions.md \
  --system-prompt custom_system_prompt.md \
  --api-key YOUR_API_KEY \
  --model gpt-4o-mini \
  --base-url https://openrouter.ai/api/v1
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
- **Single file architecture**: All code in `best_name_core.py`
- **Package management and script running**: Use `uv add` for all dependencies and `uv run` to run the script.
- **CLI tool**: Use `uv tool install best_name` to install the CLI tool.
- **File processing**: Use Docling for file content extraction
- **LLM integration**: OpenRouter API for name generation
- **Configuration**: YAML config file for defaults
- **Simplicity first**: Avoid complex Python features, error handling, and logging
- **Environment variables**: Use environment variables for sensitive data
- **.env file**: Use .env file for environment variables
- **Version control**: Use git for version control.
- **Code style**: Follow pydantic style guide.

### CLI Arguments Structure
```python
# Required argument
file_path: str  # Path to the file to be renamed

# Optional arguments
--conventions: str     # Path to conventions/categories markdown file (default: conventions.md)
--system-prompt: str   # Path to system prompt markdown file (default: system_prompt.md)
--api-key: str        # OpenRouter API key
--model: str          # LLM model name (default: from config.yaml)
--base-url: str       # OpenRouter base URL (default: from config.yaml)
```

## Configuration and defaults
- default conventions and categories are stored in the conventions.md file.
- default system prompt is stored in the system_prompt.md file.
- default openrouter settings are stored in the config.yaml file.
- default file paths are stored in the config.yaml file.
- default supported formats are stored in the config.yaml file.
- default supported languages are stored in the config.yaml file.
- OPENROUTER_API_KEY is stored in the environment variables or loaded from the .env file.


## Code Style Guidelines

- **Simplicity**: Prioritize readability over cleverness
- **No complex error handling**: Let errors bubble up naturally
- **No logging**: Use simple print statements if needed
- **Linear flow**: Avoid nested functions or complex control structures
- **Clear variable names**: Use descriptive names over abbreviations
- **Minimal abstractions**: Keep code direct and procedural

## Implementation Flow

1. Parse command line arguments using Click
2. Load config.yaml for default values
3. Override defaults with CLI arguments if provided
4. Read conventions file (default or custom)
5. Read system prompt file (default or custom)
6. Use Docling to extract content from input file
7. Prepare LLM prompt combining system prompt, conventions, and file content
8. Call OpenRouter API with prepared prompt
9. Return suggested filename (without extension)

## Testing Approach

```bash
# Test with default conventions and prompt
best_name test_files/document.pdf

# Test with custom conventions
best_name test_files/image.jpg --conventions my_rules.md

# Test with different models
best_name file.pdf --model claude-3-5-sonnet

# Test with different file types
best_name test_files/spreadsheet.xlsx
best_name test_files/presentation.pptx
```

## Key Dependencies

- **click**: CLI framework for argument parsing
- **docling**: File content extraction (handles multiple formats)
- **openai**: OpenRouter API client (OpenRouter uses OpenAI-compatible API)
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management

## Development Notes

- Keep all logic in a single `main()` function when possible
- Use Click decorators for CLI argument handling
- Let Docling handle all file format complexity
- Use OpenAI client library with OpenRouter base URL
- Always use the default files if custom ones are not provided.

## Common Issues

- If Docling fails to parse a file, return a generic name based on file extension
- If API call fails, print error and exit (no retry logic)
- Environment variables take precedence over config file

---

*This AGENTS.md is intentionally minimal to match the project's simplicity requirements. Update only when core functionality changes.*