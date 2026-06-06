"""Đọc config YAML từ thư mục config/."""

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy config: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_settings() -> dict[str, Any]:
    return load_yaml("settings.yaml")


def get_categories() -> list[dict[str, Any]]:
    data = load_yaml("categories.yaml")
    return data["categories"]


def resolve_path(key: str) -> Path:
    """key trong settings.paths, ví dụ 'raw' → PROJECT_ROOT/data/raw."""
    settings = get_settings()
    rel = settings["paths"][key]
    return PROJECT_ROOT / rel
