import os
from pathlib import Path
from typing import Optional

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
        "\n\nYou must strictly adhere to the naming conventions and categories provided by the user message.\n"
    )
    user_text = (
        "\n\nFile content (truncated):\n" + content.strip() +
    )
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    return messages, len(content)


def call_openrouter(api_key: str, base_url: str, model: str, messages: list[dict]) -> str:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    client = OpenAI(base_url=base_url, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=32,
    )
    return resp.choices[0].message.content.strip()


@click.command(name="best_name")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--conventions", "conventions_path", type=click.Path(path_type=Path), default=None, help="Path to conventions markdown file")
@click.option("--system-prompt", "system_prompt_path", type=click.Path(path_type=Path), default=None, help="Path to system prompt markdown file")
@click.option("--api-key", "api_key_opt", type=str, default=None, help="OpenRouter API key")
@click.option("--model", "model_opt", type=str, default=None, help="LLM model name")
@click.option("--base-url", "base_url_opt", type=str, default=None, help="OpenRouter base URL")
def cli(file_path: Path,
        conventions_path: Optional[Path],
        system_prompt_path: Optional[Path],
        api_key_opt: Optional[str],
        model_opt: Optional[str],
        base_url_opt: Optional[str]) -> None:
    """Suggest the best filename for FILE_PATH based on its content."""

    load_dotenv()

    project_dir = Path.cwd()
    config_path = project_dir / "config.yaml"
    config = load_yaml_config(config_path)

    defaults = (config.get("defaults") or {})
    openrouter_cfg = (config.get("openrouter") or {})

    # Resolve defaults
    conventions_default = resolve_path(project_dir, defaults.get("conventions_file"))
    system_prompt_default = resolve_path(project_dir, defaults.get("system_prompt_file"))

    conventions_file = conventions_path or conventions_default
    system_prompt_file = system_prompt_path or system_prompt_default

    conventions_md = read_text_file(conventions_file) if (conventions_file and conventions_file.exists()) else ""
    system_prompt = read_text_file(system_prompt_file) if (system_prompt_file and system_prompt_file.exists()) else "You are a helpful assistant that names files based on content."

    # Determine OpenRouter settings (env > CLI > config)
    api_key = os.getenv("OPENROUTER_API_KEY") or api_key_opt or openrouter_cfg.get("api_key") or ""
    if not api_key:
        # Let errors bubble up naturally per project constraints
        raise RuntimeError("OPENROUTER_API_KEY is required. Set env var or pass --api-key.")

    model = model_opt or openrouter_cfg.get("model") or "gpt-4o-mini"
    base_url = base_url_opt or openrouter_cfg.get("base_url") or "https://openrouter.ai/api/v1"

    # Extract content
    content = extract_file_content(file_path)
    if not content or not content.strip():
        # Generic name based on extension per requirements
        ext = file_path.suffix.lstrip(".") or "file"
        click.echo(f"untitled_{ext}")
        return

    messages, _ = prepare_prompt(system_prompt, conventions_md, content)

    raw_name = call_openrouter(api_key=api_key, base_url=base_url, model=model, messages=messages)
    suggested = sanitize_filename(raw_name)
    click.echo(suggested)


if __name__ == "__main__":
    cli()


