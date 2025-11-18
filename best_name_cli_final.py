"""CLI module - final version with main command and eval subcommand."""

import csv
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import warnings

import click
from dotenv import load_dotenv

# Import from our new modular structure
from .dspy_modules import call_dspy_prediction, call_dspy_evaluation
from .file_processing import (
    extract_file_content,
    load_ground_truth_data,
    process_evaluation_files,
    read_text_file
)
from .utils import load_yaml_config, resolve_path, sanitize_filename


def setup_logging_and_warnings(verbose: bool = False) -> None:
    """Setup logging and warning suppression based on verbosity."""
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


def resolve_configuration_paths(
    package_dir: Path,
    project_dir: Path,
    config_path_opt: Optional[Path],
    conventions_path: Optional[Path],
    system_prompt_path: Optional[Path],
    verbose: bool = False
) -> tuple[Path, Optional[Path], Optional[Path], dict]:
    """Resolve all configuration file paths and load config."""

    # Resolve config file path
    if config_path_opt:
        config_path = config_path_opt
    else:
        package_config = package_dir / "config.yaml"
        project_config = project_dir / "config.yaml"
        config_path = package_config if package_config.exists() else project_config

    config = load_yaml_config(config_path)

    defaults = config.get("defaults") or {}

    if verbose:
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

    # Resolve conventions file
    conventions_filename = defaults.get("conventions_file") or "conventions.md"
    package_conventions = package_dir / conventions_filename
    project_conventions = resolve_path(project_dir, conventions_filename)
    conventions_default = (
        package_conventions if package_conventions.exists() else project_conventions
    )
    conventions_file = conventions_path or conventions_default

    # Resolve system prompt file
    system_prompt_filename = defaults.get("system_prompt_file") or "system_prompt.md"
    package_system_prompt = package_dir / system_prompt_filename
    project_system_prompt = resolve_path(project_dir, system_prompt_filename)
    system_prompt_default = (
        package_system_prompt
        if package_system_prompt.exists()
        else project_system_prompt
    )
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

    return config_path, conventions_file, system_prompt_file, config


def load_conventions_and_prompts(
    conventions_file: Optional[Path],
    system_prompt_file: Optional[Path],
    verbose: bool = False
) -> tuple[str, str]:
    """Load conventions and system prompt from files."""

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
        click.echo(f"  Conventions loaded: {len(conventions_md)} characters")
        click.echo(f"  System prompt loaded: {len(system_prompt)} characters")

    return conventions_md, system_prompt


def resolve_openrouter_settings(
    api_key_opt: Optional[str],
    model_opt: Optional[str],
    base_url_opt: Optional[str],
    config: dict,
    verbose: bool = False
) -> tuple[str, str, str]:
    """Resolve OpenRouter API settings from multiple sources."""

    openrouter_cfg = config.get("openrouter") or {}

    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or api_key_opt
        or openrouter_cfg.get("api_key")
        or ""
    )
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Set env var or pass --api-key."
        )

    model = model_opt or openrouter_cfg.get("model") or "x-ai/grok-4-fast"
    base_url = (
        base_url_opt or openrouter_cfg.get("base_url") or "https://openrouter.ai/api/v1"
    )

    if verbose:
        click.echo(f"  Model: {model}")
        click.echo(f"  Base URL: {base_url}")
        click.echo(
            f"  API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}"
        )

    return api_key, model, base_url


def handle_file_operations(
    file_path: Path,
    suggested_name: str,
    copy: bool,
    rename: bool,
    verbose: bool = False
) -> None:
    """Handle file copy/rename operations."""
    if not (copy or rename):
        click.echo(suggested_name)
        return

    # Preserve the original file extension
    original_ext = file_path.suffix
    new_filename = suggested_name + original_ext
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


@click.group(invoke_without_command=True)
@click.pass_context
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
def cli(ctx,
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
    """Best Name CLI - AI-powered file naming tool."""
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))


@cli.command()
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
def name(
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
    """Suggest the best filename for FILE_PATH based on its content."""

    # Check that copy and rename are mutually exclusive
    if copy and rename:
        raise click.ClickException(
            "Cannot use both --copy and --rename options together."
        )

    # Setup logging and warnings
    setup_logging_and_warnings(verbose)

    if verbose:
        click.echo("=== Best Name CLI - DSPy Enhanced ===\n")

    load_dotenv()

    # Find package and project directories
    package_dir = Path(__file__).parent
    project_dir = Path.cwd()

    if verbose:
        click.echo(f"Step 1: Resolving file paths")
        click.echo(f"  Package directory: {package_dir}")
        click.echo(f"  Project directory: {project_dir}")

    # Resolve configuration paths
    config_path, conventions_file, system_prompt_file, config = resolve_configuration_paths(
        package_dir, project_dir, config_path_opt, conventions_path,
        system_prompt_path, verbose
    )

    # Load conventions and system prompts
    conventions_md, system_prompt = load_conventions_and_prompts(
        conventions_file, system_prompt_file, verbose
    )

    if verbose:
        click.echo(f"\nStep 2: Loading content files")

    # Resolve OpenRouter settings
    api_key, model, base_url = resolve_openrouter_settings(
        api_key_opt, model_opt, base_url_opt, config, verbose
    )

    if verbose:
        click.echo(f"\nStep 3: OpenRouter configuration")

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
        handle_file_operations(file_path, suggested, copy, rename, verbose)
        return

    if verbose:
        click.echo(f"  Content extracted: {len(content)} characters")
        click.echo(f"\nStep 5: Using DSPy for filename prediction")
        click.echo(f"  Content truncated to: {min(len(content), 12000)} characters")
        click.echo(f"  Using conventions: {len(conventions_md)} characters")
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

    # Handle file operations
    handle_file_operations(file_path, suggested, copy, rename, verbose)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--run-id",
    "run_id_opt",
    type=str,
    default=None,
    help="Custom run ID for evaluation (auto-generated if not provided)"
)
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
    "--verbose", is_flag=True, default=False, help="Show detailed processing steps"
)
def eval(
    file_path: Path,
    run_id_opt: Optional[str],
    conventions_path: Optional[Path],
    system_prompt_path: Optional[Path],
    api_key_opt: Optional[str],
    model_opt: Optional[str],
    base_url_opt: Optional[str],
    config_path_opt: Optional[Path],
    verbose: bool,
) -> None:
    """Evaluate filename suggestion quality for FILE_PATH."""

    # Setup logging and warnings
    setup_logging_and_warnings(verbose)

    if verbose:
        click.echo("=== Best Name CLI - Evaluation Mode ===\n")

    load_dotenv()

    # Generate run ID if not provided
    if run_id_opt:
        run_id = run_id_opt
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"eval_{timestamp}"

    if verbose:
        click.echo(f"Run ID: {run_id}")

    # Find package and project directories
    package_dir = Path(__file__).parent
    project_dir = Path.cwd()

    # Resolve configuration paths
    config_path, conventions_file, system_prompt_file, config = resolve_configuration_paths(
        package_dir, project_dir, config_path_opt, conventions_path,
        system_prompt_path, verbose
    )

    # Load conventions and system prompts
    conventions_md, system_prompt = load_conventions_and_prompts(
        conventions_file, system_prompt_file, verbose
    )

    if verbose:
        click.echo(f"Configuration loaded:")
        click.echo(f"  Conventions: {len(conventions_md)} characters")
        click.echo(f"  System prompt: {len(system_prompt)} characters")

    # Load ground truth data if available
    if verbose:
        click.echo("Loading ground truth data...")

    # Look for evals directory in project or use provided file path parent
    if file_path.is_file():
        evals_dir = file_path.parent
    elif file_path.is_dir():
        evals_dir = file_path
    else:
        evals_dir = project_dir / "evals"

    # If provided path is not the evals directory, check for evals in project
    if not (evals_dir / "eval_files.csv").exists():
        evals_dir = project_dir / "evals"

    ground_truth_data = load_ground_truth_data(evals_dir)

    if verbose:
        if ground_truth_data:
            click.echo(f"  Loaded {len(ground_truth_data)} ground truth entries")
        else:
            click.echo("  No ground truth data found")

    # Resolve OpenRouter settings
    api_key, model, base_url = resolve_openrouter_settings(
        api_key_opt, model_opt, base_url_opt, config, verbose
    )

    if verbose:
        click.echo(f"OpenRouter configuration:")
        click.echo(f"  Model: {model}")
        click.echo(f"  Base URL: {base_url}")

    # Process evaluation files using new batch processing logic
    if verbose:
        click.echo("Processing evaluation files...")

    processed_files = process_evaluation_files(file_path, ground_truth_data, verbose)

    if verbose:
        click.echo(f"Found {len(processed_files)} files to evaluate")

    # Create results directory
    results_dir = project_dir / "evals" / "results" / run_id
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create CSV file for results
    csv_file = results_dir / "evaluation_results.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'original_filename', 'suggested_name',
            'ground_truth_name', 'score', 'file_type', 'text_length', 'extractor'
        ])

    # Process each file
    for file_data in processed_files:
        try:
            process_file = file_data['file_path']
            content = file_data['content']

            if verbose:
                click.echo(f"  Processing: {process_file.name}")

            # Generate filename suggestion
            suggested_name, confidence = call_dspy_prediction(
                file_content=content,
                naming_conventions=conventions_md,
                model=model,
                api_key=api_key,
                base_url=base_url,
                verbose=verbose
            )
            suggested_name = sanitize_filename(suggested_name)

            # Get ground truth name
            ground_truth_name = file_data['ground_truth_name']

            # Evaluate the suggestion
            if ground_truth_name:
                evaluation_score = call_dspy_evaluation(
                    suggested_name=suggested_name,
                    ground_truth_name=ground_truth_name,
                    file_content=content,
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    verbose=verbose
                )
            else:
                evaluation_score = 5.0  # Default score if no ground truth

            # Get metadata
            file_type = file_data['file_type']
            text_length = file_data['text_length']
            extractor = file_data['extractor']

            # Write to CSV
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    process_file.name,
                    suggested_name,
                    ground_truth_name,
                    f"{evaluation_score:.1f}",
                    file_type,
                    text_length,
                    extractor
                ])

            # Create individual markdown file
            md_file = results_dir / f"{process_file.stem}_evaluation.md"
            md_content = f"""# Evaluation Results: {process_file.name}

**Run ID:** {run_id}
**Timestamp:** {datetime.now().isoformat()}
**File Path:** {process_file}

## File Information
- **Original Filename:** {process_file.name}
- **File Type:** {file_type}
- **Content Length:** {text_length} characters
- **Extractor:** {extractor}

## Evaluation Results
- **Suggested Name:** `{suggested_name}`
- **Ground Truth Name:** `{ground_truth_name}`
- **Evaluation Score:** {evaluation_score:.1f}/10

## File Content Preview
```
{content[:500]}{'...' if len(content) > 500 else ''}
```

---
*Generated by best_name evaluation system*
"""
            md_file.write_text(md_content, encoding='utf-8')

            if verbose:
                click.echo(f"    Suggested: {suggested_name}")
                click.echo(f"    Score: {evaluation_score:.1f}/10")

        except Exception as e:
            if verbose:
                click.echo(f"    Error: {e}")
            # Continue processing other files
            continue

    click.echo(f"\nEvaluation complete!")
    click.echo(f"Results saved to: {results_dir}")
    click.echo(f"CSV file: {csv_file}")


if __name__ == "__main__":
    cli()