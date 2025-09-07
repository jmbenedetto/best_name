## best_name CLI

Suggest the most appropriate name for a file based on its content using an LLM.

### Installation

Requires Python 3.12+. Install dependencies with uv:

```bash
uv sync
```

Or, add required packages explicitly:

```bash
uv add click python-dotenv pyyaml openai docling
```

### Configuration

Defaults are defined in `config.yaml`:
- OpenRouter settings (`model`, `base_url`)
- Default file paths (`conventions.md`, `system_prompt.md`)

Set your OpenRouter API key via environment variable (preferred) or a `.env` file:

```bash
export OPENROUTER_API_KEY=YOUR_KEY
# or create a .env file containing:
# OPENROUTER_API_KEY=YOUR_KEY
```

### Usage

```bash
best_name /path/to/file.pdf

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
  --model gpt-4o-mini \
  --base-url https://openrouter.ai/api/v1
```

The CLI prints a single line: the suggested filename (without extension).

### Supported Formats
Text: txt, md, csv, json, yaml, xml, html, css
Images: jpg, jpeg, png, gif, svg, ico
Documents: pdf, docx, xlsx, pptx

### Notes
- If parsing fails, a generic name like `untitled_pdf` is returned.
- Environment variables override config settings.

