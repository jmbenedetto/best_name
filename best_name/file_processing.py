"""File processing utilities for content extraction and evaluation data handling."""

import csv
from pathlib import Path
from typing import Optional

import click

# Import read_text_file from utils to avoid duplication
from .utils import read_text_file


def extract_content_with_docling(file_path: Path) -> Optional[str]:
    """Extract content using Docling library for complex formats."""
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
    """Extract content from file using appropriate method based on file type."""
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


def load_ground_truth_data(evals_dir: Path) -> dict:
    """Load ground truth data from evals/eval_files.csv."""
    ground_truth = {}
    csv_path = evals_dir / "eval_files.csv"

    if not csv_path.exists():
        if click.get_current_context(silent=True) and click.get_current_context().obj and click.get_current_context().obj.get('verbose'):
            click.echo(f"Ground truth CSV not found: {csv_path}")
        return ground_truth

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Auto-detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample).delimiter
            except csv.Error:
                # Fallback to semicolon if sniffing fails (matches existing format)
                delimiter = ';'

            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # Handle missing columns gracefully, including None values from malformed rows
                original_file = (row.get('original_file') or '').strip()
                human_defined_name = (row.get('human_defined_name') or '').strip()

                if original_file and human_defined_name:
                    ground_truth[original_file] = human_defined_name

    except Exception as e:
        # Return empty dict if CSV parsing fails
        ctx = click.get_current_context(silent=True)
        if ctx and ctx.obj and ctx.obj.get('verbose'):
            click.echo(f"Error loading ground truth CSV: {e}")

    return ground_truth


def process_evaluation_file(file_path: Path, ground_truth_data: dict) -> Optional[dict]:
    """Process a single evaluation file and extract metadata."""
    # Extract content
    content = extract_file_content(file_path)
    if not content or not content.strip():
        return None

    # Extract metadata
    file_type = file_path.suffix.lstrip(".") or "unknown"
    text_length = len(content)
    text_like_exts = {
        "txt", "md", "csv", "json", "yaml", "yml", "xml", "html", "htm", "css"
    }
    extractor = "direct" if file_type in text_like_exts else "docling"

    # Get ground truth name if available
    ground_truth_name = ground_truth_data.get(file_path.name, "")

    return {
        'file_path': file_path,
        'original_filename': file_path.name,
        'content': content,
        'file_type': file_type,
        'text_length': text_length,
        'extractor': extractor,
        'ground_truth_name': ground_truth_name
    }


def process_evaluation_files(file_path: Path, ground_truth_data: dict, verbose: bool = False) -> list:
    """Process evaluation files from a single file or directory."""
    processed_files = []

    if file_path.is_file():
        # Process single file
        file_data = process_evaluation_file(file_path, ground_truth_data)
        if file_data:
            processed_files.append(file_data)
            if verbose:
                click.echo(f"  Found file: {file_path.name}")
        else:
            if verbose:
                click.echo(f"  Skipped (no content): {file_path.name}")

    elif file_path.is_dir():
        # Process directory - look for eval_files subdirectory or process the directory directly
        eval_files_dir = file_path / "eval_files"
        if eval_files_dir.exists() and eval_files_dir.is_dir():
            search_dir = eval_files_dir
            if verbose:
                click.echo(f"  Using eval_files subdirectory: {search_dir}")
        else:
            search_dir = file_path
            if verbose:
                click.echo(f"  Processing files in: {search_dir}")

        # Find all supported files in the directory
        text_like_exts = {"txt", "md", "csv", "json", "yaml", "yml", "xml", "html", "htm", "css"}
        doc_exts = ["pdf", "docx", "xlsx", "pptx", "png", "jpg", "jpeg", "gif", "svg", "ico"]

        all_files = []

        # Add text-like files
        for ext in text_like_exts:
            all_files.extend(search_dir.glob(f"*.{ext}"))
            all_files.extend(search_dir.glob(f"*.{ext.upper()}"))

        # Add document/image files
        for ext in doc_exts:
            all_files.extend(search_dir.glob(f"*.{ext}"))
            all_files.extend(search_dir.glob(f"*.{ext.upper()}"))

        # Process only files present in ground truth data (if available)
        files_to_process = []
        for file_obj in all_files:
            if ground_truth_data:
                # Only process files that have ground truth data
                if file_obj.name in ground_truth_data:
                    files_to_process.append(file_obj)
                else:
                    if verbose:
                        click.echo(f"  Skipped (no ground truth): {file_obj.name}")
            else:
                # Process all files if no ground truth data available
                files_to_process.append(file_obj)

        # Process each file
        for process_file in files_to_process:
            file_data = process_evaluation_file(process_file, ground_truth_data)
            if file_data:
                processed_files.append(file_data)
                if verbose:
                    click.echo(f"  Found file: {process_file.name}")

    return processed_files