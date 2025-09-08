import json
import logging
import os
from pathlib import Path
from typing import Optional
import warnings

import click
from dotenv import load_dotenv
import yaml

try:
    from openai import OpenAI  # OpenRouter is OpenAI-compatible
except Exception:  # pragma: no cover - allow import-time failures in environments without openai
    OpenAI = None  # type: ignore


def read_text_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        # fallback to binary read and decode best-effort
        data = file_path.read_bytes()
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def load_yaml_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_path(base_dir: Path, candidate: Optional[str]) -> Optional[Path]:
    if not candidate:
        return None
    p = Path(candidate)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def extract_content_with_docling(file_path: Path) -> Optional[str]:
    try:
        # Docling API can change; try common usage patterns defensively
        from docling.document_converter import DocumentConverter  # type: ignore

        converter = DocumentConverter()
        result = converter.convert(str(file_path))

        # Preferred: document provides export to markdown or plain text
        for attr in ("export_to_markdown", "export_to_text", "export_markdown", "export_text"):
            if hasattr(result.document, attr):
                try:
                    exported = getattr(result.document, attr)()
                    if isinstance(exported, str) and exported.strip():
                        return exported
                except Exception:
                    pass

        # Fallback exporters if available
        try:
            from docling.datamodel.export import MdExport  # type: ignore

            exporter = MdExport()
            return exporter.export(result.document)
        except Exception:
            pass

        # Last resort: stringify
        try:
            return str(result.document)
        except Exception:
            return None
    except Exception:
        return None


def extract_file_content(file_path: Path) -> Optional[str]:
    text_like_exts = {
        "txt", "md", "csv", "json", "yaml", "yml", "xml", "html", "htm", "css",
    }

    ext = file_path.suffix.lower().lstrip(".")
    if ext in text_like_exts:
        return read_text_file(file_path)

    # Use Docling for everything else
    return extract_content_with_docling(file_path)


def sanitize_filename(name: str) -> str:
    # Handle empty or None input
    if not name or not name.strip():
        return "untitled"
    
    # Remove path separators and illegal characters for common filesystems
    illegal = "\n\r\t:/\\?*\"'<>|"
    cleaned = "".join(ch if ch not in illegal else " " for ch in name)
    cleaned = " ".join(cleaned.split())  # collapse whitespace
    return cleaned.strip(" .")[:120] or "untitled"


def prepare_prompt(system_prompt: str, conventions_md: str, file_content: str) -> tuple[list[dict], int]:
    # Truncate content for safety
    max_chars = 12000
    content = file_content[:max_chars]

    system_text = (
        system_prompt.strip() + "\n\n" + conventions_md.strip()
    )
    user_text = (
        "\n\nFile content (truncated):\n" + content.strip()
    )
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return messages, len(content)


def call_openrouter(api_key: str, base_url: str, model: str, messages: list[dict], verbose: bool = False) -> tuple[str, dict]:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    client = OpenAI(base_url=base_url, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=32,
    )
    
    # Return both the content and full response for verbose mode
    content = resp.choices[0].message.content.strip() if resp.choices[0].message.content else ""
    full_response = resp.model_dump() if verbose else {}
    
    return content, full_response


@click.command(name="best_name")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--conventions", "conventions_path", type=click.Path(path_type=Path), default=None, help="Path to conventions markdown file")
@click.option("--system-prompt", "system_prompt_path", type=click.Path(path_type=Path), default=None, help="Path to system prompt markdown file")
@click.option("--api-key", "api_key_opt", type=str, default=None, help="OpenRouter API key")
@click.option("--model", "model_opt", type=str, default=None, help="LLM model name")
@click.option("--base-url", "base_url_opt", type=str, default=None, help="OpenRouter base URL")
@click.option("--verbose", is_flag=True, default=False, help="Show detailed processing steps")
def cli(file_path: Path,
        conventions_path: Optional[Path],
        system_prompt_path: Optional[Path],
        api_key_opt: Optional[str],
        model_opt: Optional[str],
        base_url_opt: Optional[str],
        verbose: bool) -> None:
    """Suggest the best filename for FILE_PATH based on its content."""

    # Suppress logs from external libraries when not in verbose mode
    if not verbose:
        # Suppress all logging except critical errors
        logging.getLogger().setLevel(logging.CRITICAL)
        logging.getLogger("docling").setLevel(logging.CRITICAL)
        logging.getLogger("torch").setLevel(logging.CRITICAL)
        logging.getLogger("transformers").setLevel(logging.CRITICAL)
        logging.getLogger("openai").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)
        logging.getLogger("httpcore").setLevel(logging.CRITICAL)
        # Suppress all warnings
        warnings.filterwarnings("ignore")

    if verbose:
        click.echo("=== Best Name CLI - Verbose Mode ===\n")
        click.echo(f"Step 1: Loading configuration from {Path.cwd()}")

    load_dotenv()

    project_dir = Path.cwd()
    config_path = project_dir / "config.yaml"
    config = load_yaml_config(config_path)

    defaults = (config.get("defaults") or {})
    openrouter_cfg = (config.get("openrouter") or {})

    if verbose:
        click.echo(f"Step 2: Resolving file paths")
        click.echo(f"  Project directory: {project_dir}")
        click.echo(f"  Config file: {config_path}")

    # Resolve defaults
    conventions_default = resolve_path(project_dir, defaults.get("conventions_file"))
    system_prompt_default = resolve_path(project_dir, defaults.get("system_prompt_file"))

    conventions_file = conventions_path or conventions_default
    system_prompt_file = system_prompt_path or system_prompt_default

    if verbose:
        click.echo(f"  Conventions file: {conventions_file}")
        click.echo(f"  System prompt file: {system_prompt_file}")

    conventions_md = read_text_file(conventions_file) if (conventions_file and conventions_file.exists()) else ""
    system_prompt = read_text_file(system_prompt_file) if (system_prompt_file and system_prompt_file.exists()) else "You are a helpful assistant that names files based on content."

    if verbose:
        click.echo(f"\nStep 3: Loading content files")
        click.echo(f"  Conventions loaded: {len(conventions_md)} characters")
        click.echo(f"  System prompt loaded: {len(system_prompt)} characters")

    # Determine OpenRouter settings (env > CLI > config)
    api_key = os.getenv("OPENROUTER_API_KEY") or api_key_opt or openrouter_cfg.get("api_key") or ""
    if not api_key:
        # Let errors bubble up naturally per project constraints
        raise RuntimeError("OPENROUTER_API_KEY is required. Set env var or pass --api-key.")

    model = model_opt or openrouter_cfg.get("model") or "gpt-5-mini"
    base_url = base_url_opt or openrouter_cfg.get("base_url") or "https://openrouter.ai/api/v1"

    if verbose:
        click.echo(f"\nStep 4: OpenRouter configuration")
        click.echo(f"  Model: {model}")
        click.echo(f"  Base URL: {base_url}")
        click.echo(f"  API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}")

    # Extract content
    if verbose:
        click.echo(f"\nStep 5: Extracting content from {file_path}")

    content = extract_file_content(file_path)
    if not content or not content.strip():
        # Generic name based on extension per requirements
        ext = file_path.suffix.lstrip(".") or "file"
        if verbose:
            click.echo(f"  No content extracted, using generic name")
        click.echo(f"untitled_{ext}")
        return

    if verbose:
        click.echo(f"  Content extracted: {len(content)} characters")

    messages, content_len = prepare_prompt(system_prompt, conventions_md, content)

    if verbose:
        click.echo(f"\nStep 6: Preparing LLM prompt")
        click.echo(f"  Content truncated to: {content_len} characters")
        click.echo(f"\n--- System Message ---")
        click.echo(messages[0]["content"])
        click.echo(f"\n--- User Message ---")
        click.echo(messages[1]["content"])
        click.echo(f"\n--- Combined Message (sent to LLM) ---")
        for i, msg in enumerate(messages):
            click.echo(f"Message {i+1} ({msg['role']}): {len(msg['content'])} characters")

    if verbose:
        click.echo(f"\nStep 7: Calling OpenRouter API")

    raw_name, full_response = call_openrouter(api_key=api_key, base_url=base_url, model=model, messages=messages, verbose=verbose)
    
    if verbose:
        click.echo(f"\n--- Complete LLM Exchange ---")
        if full_response:
            click.echo(f"Request sent to LLM:")
            request_info = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 32
            }
            click.echo(json.dumps(request_info, indent=2, ensure_ascii=False))
            
            click.echo(f"\nFull LLM Response:")
            click.echo(json.dumps(full_response, indent=2, ensure_ascii=False))
            
            # Extract and display reasoning if available
            if full_response.get("choices") and len(full_response["choices"]) > 0:
                choice = full_response["choices"][0]
                if choice.get("message", {}).get("content"):
                    click.echo(f"\nLLM Reasoning/Content:")
                    click.echo(f"'{choice['message']['content']}'")
                
                # Show usage statistics if available
                if full_response.get("usage"):
                    usage = full_response["usage"]
                    click.echo(f"\nToken Usage:")
                    click.echo(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                    click.echo(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                    click.echo(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
        
        click.echo(f"\n--- Processing Result ---")
        click.echo(f"  Raw response: '{raw_name}'")

    suggested = sanitize_filename(raw_name)
    
    if verbose:
        click.echo(f"  Sanitized filename: '{suggested}'")
        click.echo(f"\n=== Final Result ===")
    
    click.echo(suggested)


if __name__ == "__main__":
    cli()


