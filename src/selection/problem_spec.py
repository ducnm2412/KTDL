"""Bước 1 KDD — Đặc tả bài toán (Selection)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config_loader import get_categories, get_settings
from src.schema.enums import LabelClass


@dataclass
class ProblemSpec:
    """Đặc tả phạm vi bài toán — output chính của Bước 1 Selection."""

    project_name: str
    platform: str
    target_records: int
    random_seed: int
    label_classes: list[str]
    min_class_ratio: float
    category_count: int
    total_planned_samples: int
    stratified: bool
    problem_type: str = "multi_class_classification"
    data_source: str = "lazada.vn AJAX API (realtime snapshot)"
    categories: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_config(cls) -> ProblemSpec:
        settings = get_settings()
        categories = get_categories()
        project = settings["project"]
        labeling = settings["labeling"]

        total = sum(c["target_count"] for c in categories)

        return cls(
            project_name=project["name"],
            platform=project["platform"],
            target_records=project["target_records"],
            random_seed=project["random_seed"],
            label_classes=labeling["classes"],
            min_class_ratio=labeling.get("min_class_ratio", 0.05),
            category_count=len(categories),
            total_planned_samples=total,
            stratified=total == project["target_records"],
            categories=categories,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "problem_type": self.problem_type,
            "platform": self.platform,
            "data_source": self.data_source,
            "target_records": self.target_records,
            "random_seed": self.random_seed,
            "label_classes": self.label_classes,
            "expected_label_count": len(LabelClass),
            "min_class_ratio": self.min_class_ratio,
            "category_count": self.category_count,
            "total_planned_samples": self.total_planned_samples,
            "stratified_by_category": self.stratified,
            "categories": self.categories,
        }

    def summary_lines(self) -> list[str]:
        return [
            f"Dự án: {self.project_name}",
            f"Bài toán: {self.problem_type} — {len(self.label_classes)} lớp",
            f"Nền tảng: {self.platform} ({self.data_source})",
            f"Mục tiêu: {self.target_records:,} sản phẩm, stratified {self.category_count} danh mục",
            f"Nhãn: {', '.join(self.label_classes)}",
        ]
