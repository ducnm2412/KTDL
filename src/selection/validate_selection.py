"""Bước 1 KDD — Kiểm tra config Selection trước khi crawl."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config_loader import get_categories, get_settings, resolve_path
from src.schema.enums import LabelClass


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def validate_selection_config() -> ValidationResult:
    result = ValidationResult(ok=True)
    settings = get_settings()
    categories = get_categories()

    target = settings["project"]["target_records"]
    total = sum(c.get("target_count", 0) for c in categories)

    if total != target:
        result.errors.append(
            f"Tổng target_count ({total}) != target_records ({target}). "
            "Cần chỉnh categories.yaml cho khớp stratified 10k."
        )

    if len(categories) == 0:
        result.errors.append("categories.yaml rỗng.")

    for i, cat in enumerate(categories):
        if not cat.get("name"):
            result.errors.append(f"Danh mục index {i} thiếu name.")
        if not cat.get("path"):
            result.errors.append(f"Danh mục '{cat.get('name')}' thiếu path (Lazada).")
        if cat.get("target_count", 0) <= 0:
            result.errors.append(f"Danh mục '{cat.get('name')}' target_count phải > 0.")

    config_labels = settings["labeling"]["classes"]
    expected = LabelClass.values()
    if set(config_labels) != set(expected):
        result.errors.append(
            f"labeling.classes ({config_labels}) không khớp LabelClass ({expected})."
        )

    for path_key in ("raw", "clean", "selection"):
        path = resolve_path(path_key)
        if not path.exists():
            result.warnings.append(f"Thư mục chưa tồn tại (sẽ tạo khi chạy): {path}")

    min_ratio = settings["labeling"].get("min_class_ratio", 0.05)
    if min_ratio <= 0 or min_ratio > 0.5:
        result.warnings.append(f"min_class_ratio={min_ratio} có vẻ bất thường.")

    if result.errors:
        result.ok = False

    return result
