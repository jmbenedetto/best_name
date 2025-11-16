import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import warnings

import click
from dotenv import load_dotenv
import yaml

# DSPy imports
try:
    import dspy
    from dspy import InputField, OutputField, Predict, configure
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    # Create placeholder classes for graceful degradation
    class dspy:
        class Signature:
            pass
        class InputField:
            def __init__(self, desc="", **kwargs):
                self.desc = desc
        class OutputField:
            def __init__(self, desc="", **kwargs):
                self.desc = desc
        class Predict:
            def __init__(self, signature):
                self.signature = signature
        def configure(**kwargs):
            pass


# FilenameSignature class for DSPy prediction
class FilenameSignature(dspy.Signature):
    """Generate appropriate filename based on file content and naming conventions."""

    file_content = InputField(desc="The extracted content from the file")
    naming_conventions = InputField(desc="The naming conventions and categories to follow")
    suggested_name = OutputField(desc="The suggested filename without extension")


def initialize_dspy_lm(api_key: str, model: str, base_url: str):
    """Initialize DSPy LM with OpenRouter configuration."""
    if not DSPY_AVAILABLE:
        raise RuntimeError("DSPy package is not installed")

    # OpenRouter models need to be prefixed with "openrouter/" for DSPy/LiteLLM
    if not model.startswith("openrouter/"):
        openrouter_model = f"openrouter/{model}"
    else:
        openrouter_model = model

    # Create LM instance with OpenRouter settings
    lm = dspy.LM(
        model=openrouter_model,
        api_key=api_key,
        api_base=base_url,
        temperature=0.2
    )

    # Configure DSPy to use this LM
    configure(lm=lm)
    return lm


def call_dspy_prediction(
    file_content: str,
    naming_conventions: str,
    model: str,
    api_key: str,
    base_url: str,
    verbose: bool = False
) -> tuple[str, Optional[float]]:
    """Call DSPy prediction for filename generation."""
    if not DSPY_AVAILABLE:
        raise RuntimeError("DSPy package is not installed")

    # Initialize LM
    lm = initialize_dspy_lm(api_key, model, base_url)

    # Create predictor
    predictor = Predict(FilenameSignature)

    # Truncate content for safety
    max_chars = 12000
    truncated_content = file_content[:max_chars]

    # Make prediction
    if verbose:
        print(f"Making DSPy prediction with {len(truncated_content)} characters of content...")

    result = predictor(
        file_content=truncated_content,
        naming_conventions=naming_conventions
    )

    # Extract suggested name
    suggested_name = getattr(result, 'suggested_name', '').strip()

    # Extract confidence score if available (DSPy may provide this in future versions)
    confidence = None
    if hasattr(result, 'confidence') and result.confidence is not None:
        try:
            confidence = float(result.confidence)
        except (ValueError, TypeError):
            confidence = None
    elif hasattr(result, 'completions') and result.completions and hasattr(result.completions, '__getitem__'):
        try:
            # Try to extract confidence from completions if available
            first_completion = result.completions[0]
            if hasattr(first_completion, 'confidence') and first_completion.confidence is not None:
                try:
                    confidence = float(first_completion.confidence)
                except (ValueError, TypeError):
                    confidence = None
        except (IndexError, TypeError):
            confidence = None

    return suggested_name, confidence


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
        for attr in (
            "export_to_markdown",
            "export_to_text",
            "export_markdown",
            "export_text",
        ):
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
        "txt",
        "md",
        "csv",
        "json",
        "yaml",
        "yml",
        "xml",
        "html",
        "htm",
        "css",
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

    # Remove file extension if present (we'll preserve the original extension)
    name_without_ext = name
    if "." in name:
        # Check if it looks like a file extension (last part after dot is 1-5 chars, no spaces)
        parts = name.rsplit(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 5 and " " not in parts[1]:
            name_without_ext = parts[0]

    # Remove path separators and illegal characters for common filesystems
    illegal = "\n\r\t:/\\?*\"'<>|"
    cleaned = "".join(ch if ch not in illegal else " " for ch in name_without_ext)
    cleaned = " ".join(cleaned.split())  # collapse whitespace

    return cleaned.strip(" .")[:120] or "untitled"


@click.command(name="best_name")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--conventions",
    "conventions_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to conventions markdown file",
)
@click.option(
    "--system-prompt",
    "system_prompt_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to system prompt markdown file",
)
@click.option(
    "--api-key", "api_key_opt", type=str, default=None, help="OpenRouter API key"
)
@click.option("--model", "model_opt", type=str, default=None, help="LLM model name")
@click.option(
    "--base-url", "base_url_opt", type=str, default=None, help="OpenRouter base URL"
)
@click.option(
    "--config",
    "config_path_opt",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to config YAML file (default: config.yaml)",
)
@click.option(
    "--copy",
    is_flag=True,
    default=False,
    help="Create a copy of the file with the suggested name",
)
@click.option(
    "--rename",
    is_flag=True,
    default=False,
    help="Rename the file with the suggested name",
)
@click.option(
    "--verbose", is_flag=True, default=False, help="Show detailed processing steps"
)
def cli(
    file_path: Path,
    conventions_path: Optional[Path],
    system_prompt_path: Optional[Path],
    api_key_opt: Optional[str],
    model_opt: Optional[str],
    base_url_opt: Optional[str],
    config_path_opt: Optional[Path],
    copy: bool,
    rename: bool,
    verbose: bool,
) -> None:
    """Suggest the best filename for FILE_PATH based on its content.

    Use --copy to create a copy with the suggested name.
    Use --rename to rename the original file with the suggested name.
    """

    # Check that copy and rename are mutually exclusive
    if copy and rename:
        raise click.ClickException(
            "Cannot use both --copy and --rename options together."
        )

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
        click.echo("=== Best Name CLI - DSPy Enhanced ===\n")

    load_dotenv()

    # Find package directory (where this module is installed)
    package_dir = Path(__file__).parent
    project_dir = Path.cwd()

    # Use custom config path if provided, otherwise look in package dir first,
    # then current directory
    if config_path_opt:
        config_path = config_path_opt
    else:
        package_config = package_dir / "config.yaml"
        project_config = project_dir / "config.yaml"
        config_path = package_config if package_config.exists() else project_config
    config = load_yaml_config(config_path)

    defaults = config.get("defaults") or {}
    openrouter_cfg = config.get("openrouter") or {}

    if verbose:
        click.echo(f"Step 1: Resolving file paths")
        click.echo(f"  Package directory: {package_dir}")
        click.echo(f"  Project directory: {project_dir}")
        config_source = (
            "(custom)"
            if config_path_opt
            else (
                "(package)"
                if config_path == package_dir / "config.yaml"
                else "(project)"
            )
        )
        click.echo(f"  Config file: {config_path} {config_source}")

    # Resolve defaults - look in package dir first, then project dir
    conventions_filename = defaults.get("conventions_file") or "conventions.md"
    system_prompt_filename = defaults.get("system_prompt_file") or "system_prompt.md"

    # For conventions file: check package dir first, then project dir
    package_conventions = package_dir / conventions_filename
    project_conventions = resolve_path(project_dir, conventions_filename)
    conventions_default = (
        package_conventions if package_conventions.exists() else project_conventions
    )

    # For system prompt file: check package dir first, then project dir
    package_system_prompt = package_dir / system_prompt_filename
    project_system_prompt = resolve_path(project_dir, system_prompt_filename)
    system_prompt_default = (
        package_system_prompt
        if package_system_prompt.exists()
        else project_system_prompt
    )

    conventions_file = conventions_path or conventions_default
    system_prompt_file = system_prompt_path or system_prompt_default

    if verbose:
        conventions_source = (
            "(custom)"
            if conventions_path
            else "(package)" if conventions_file == package_conventions else "(project)"
        )
        system_prompt_source = (
            "(custom)"
            if system_prompt_path
            else (
                "(package)"
                if system_prompt_file == package_system_prompt
                else "(project)"
            )
        )
        click.echo(f"  Conventions file: {conventions_file} {conventions_source}")
        click.echo(f"  System prompt file: {system_prompt_file} {system_prompt_source}")

    conventions_md = (
        read_text_file(conventions_file)
        if (conventions_file and conventions_file.exists())
        else ""
    )
    system_prompt = (
        read_text_file(system_prompt_file)
        if (system_prompt_file and system_prompt_file.exists())
        else "You are a helpful assistant that names files based on content."
    )

    if verbose:
        click.echo(f"\nStep 2: Loading content files")
        click.echo(f"  Conventions loaded: {len(conventions_md)} characters")
        click.echo(f"  System prompt loaded: {len(system_prompt)} characters")

    # Determine OpenRouter settings (env > CLI > config)
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or api_key_opt
        or openrouter_cfg.get("api_key")
        or ""
    )
    if not api_key:
        # Let errors bubble up naturally per project constraints
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Set env var or pass --api-key."
        )

    model = model_opt or openrouter_cfg.get("model") or "x-ai/grok-4-fast"
    base_url = (
        base_url_opt or openrouter_cfg.get("base_url") or "https://openrouter.ai/api/v1"
    )

    if verbose:
        click.echo(f"\nStep 3: OpenRouter configuration")
        click.echo(f"  Model: {model}")
        click.echo(f"  Base URL: {base_url}")
        click.echo(
            f"  API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}"
        )

    # Extract content
    if verbose:
        click.echo(f"\nStep 4: Extracting content from {file_path}")

    content = extract_file_content(file_path)
    if not content or not content.strip():
        # Generic name based on extension per requirements
        ext = file_path.suffix.lstrip(".") or "file"
        suggested = f"untitled_{ext}"

        if verbose:
            click.echo(f"  No content extracted, using generic name: '{suggested}'")

        # Handle file operations for generic names too
        if copy or rename:
            original_ext = file_path.suffix
            new_filename = suggested + original_ext
            new_path = file_path.parent / new_filename

            if new_path.exists():
                raise click.ClickException(
                    f"Target file '{new_filename}' already exists."
                )

            try:
                if copy:
                    shutil.copy2(file_path, new_path)
                    if verbose:
                        click.echo(f"  Copied '{file_path.name}' to '{new_filename}'")
                    click.echo(f"File copied to: {new_filename}")
                elif rename:
                    file_path.rename(new_path)
                    if verbose:
                        click.echo(f"  Renamed '{file_path.name}' to '{new_filename}'")
                    click.echo(f"File renamed to: {new_filename}")
            except Exception as e:
                operation = "copy" if copy else "rename"
                raise click.ClickException(f"Failed to {operation} file: {e}")
        else:
            click.echo(suggested)
        return

    if verbose:
        click.echo(f"  Content extracted: {len(content)} characters")

    # Use DSPy for filename prediction
    if verbose:
        click.echo(f"\nStep 5: Using DSPy for filename prediction")
        click.echo(f"  Content truncated to: {min(len(content), 12000)} characters")
        click.echo(f"  Using conventions: {len(conventions_md)} characters")

    if verbose:
        click.echo(f"\nStep 6: Calling DSPy prediction")

    try:
        raw_name, confidence = call_dspy_prediction(
            file_content=content,
            naming_conventions=conventions_md,
            model=model,
            api_key=api_key,
            base_url=base_url,
            verbose=verbose
        )

        if verbose:
            click.echo(f"\n--- DSPy Prediction Result ---")
            click.echo(f"  Raw response: '{raw_name}'")
            if confidence is not None:
                click.echo(f"  Confidence score: {confidence}")
            else:
                click.echo(f"  Confidence score: Not available")

    except Exception as e:
        if verbose:
            click.echo(f"\n--- DSPy Prediction Error ---")
            click.echo(f"  Error: {e}")
        # Let errors bubble up naturally per project constraints
        raise

    suggested = sanitize_filename(raw_name)

    if verbose:
        click.echo(f"  Sanitized filename: '{suggested}'")
        click.echo(f"\n=== Final Result ===")

    # Handle file operations if requested
    if copy or rename:
        # Preserve the original file extension
        original_ext = file_path.suffix
        new_filename = suggested + original_ext
        new_path = file_path.parent / new_filename

        # Check if target file already exists
        if new_path.exists():
            raise click.ClickException(f"Target file '{new_filename}' already exists.")

        try:
            if copy:
                shutil.copy2(file_path, new_path)
                if verbose:
                    click.echo(f"  Copied '{file_path.name}' to '{new_filename}'")
                click.echo(f"File copied to: {new_filename}")
            elif rename:
                file_path.rename(new_path)
                if verbose:
                    click.echo(f"  Renamed '{file_path.name}' to '{new_filename}'")
                click.echo(f"File renamed to: {new_filename}")
        except Exception as e:
            operation = "copy" if copy else "rename"
            raise click.ClickException(f"Failed to {operation} file: {e}")
    else:
        # Just output the suggested name as before
        click.echo(suggested)


if __name__ == "__main__":
    cli()