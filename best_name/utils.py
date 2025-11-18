"""Utility functions for configuration loading and filename processing."""

from pathlib import Path
from typing import Optional

import yaml


def read_text_file(file_path: Path) -> str:
    """Read text file with encoding fallback."""
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
    """Load YAML configuration file."""
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_path(base_dir: Path, candidate: Optional[str]) -> Optional[Path]:
    """Resolve path relative to base directory if not absolute."""
    if not candidate:
        return None
    p = Path(candidate)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def sanitize_filename(name: str) -> str:
    """Sanitize filename for filesystem compatibility."""
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