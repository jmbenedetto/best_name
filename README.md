## best_name CLI

Suggest the most appropriate name for a file based on its content using DSPy-enhanced LLM predictions.

### Installation

Requires Python 3.12+.

Install as a global CLI with uv (after cloning/downloading this repo):

```bash
cd /path/to/best_name
uv tool install -e .

# verify
best_name --help
```

Alternatively, install dependencies for local development:

```bash
uv sync
```

Or, add required packages explicitly:

```bash
uv add click python-dotenv pyyaml docling dspy
```

### Configuration

Defaults are defined in `config.yaml`:
- OpenRouter settings (`model`, `base_url`) - defaults to `x-ai/grok-4-fast`
- Default file paths (`conventions.md`, `system_prompt.md`)

Set your OpenRouter API key via environment variable (preferred) or a `.env` file:

```bash
export OPENROUTER_API_KEY=YOUR_KEY
# or create a .env file containing:
# OPENROUTER_API_KEY=YOUR_KEY
```

### Usage

```bash
# Basic usage - outputs suggested filename
best_name /path/to/file.pdf

# Copy file with suggested name (preserves original)
best_name /path/to/file.pdf --copy

# Rename file with suggested name
best_name /path/to/file.pdf --rename

# Verbose mode - shows detailed processing steps
best_name /path/to/file.pdf --verbose

# With custom conventions
best_name /path/to/file.pdf \
  --conventions examples/custom_conventions.md

# With custom system prompt
best_name /path/to/file.pdf \
  --system-prompt examples/custom_system_prompt.md

# With all optional arguments
best_name /path/to/file.pdf \
  --conventions examples/custom_conventions.md \
  --system-prompt examples/custom_system_prompt.md \
  --api-key $OPENROUTER_API_KEY \
  --model x-ai/grok-4-fast \
  --base-url https://openrouter.ai/api/v1 \
  --verbose
```

The CLI prints a single line: the suggested filename (without extension), or performs file operations when `--copy` or `--rename` are used.

### Architecture

This tool uses **DSPy** (Structured Programming for Language Models) for enhanced LLM predictions:

- **FilenameSignature**: DSPy signature class that defines the prediction task
- **Structured Prediction**: Uses DSPy's `Predict` class for consistent, structured outputs
- **Error Handling**: Graceful degradation when DSPy package is not available
- **Confidence Scores**: Optional confidence scoring from DSPy predictions (when available)

### Supported Formats
Text: txt, md, csv, json, yaml, xml, html, css
Images: jpg, jpeg, png, gif, svg, ico
Documents: pdf, docx, xlsx, pptx

### Notes
- If parsing fails, a generic name like `untitled_pdf` is returned.
- Environment variables override config settings.
- The tool uses DSPy framework for structured LLM predictions with OpenRouter models.
- `--copy` and `--rename` flags are mutually exclusive.
- Verbose mode shows step-by-step processing including DSPy prediction details.

