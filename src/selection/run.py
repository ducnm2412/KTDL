"""
Chạy toàn bộ Bước 1 — Selection (KDD).

Mục đích: chốt phạm vi bài toán TRƯỚC khi crawl/làm sạch.
Không thu thập dữ liệu, không train model.

Usage:
    python -m src.selection.run
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config_loader import resolve_path
from src.selection.feature_selection import build_feature_selection_report
from src.selection.problem_spec import ProblemSpec
from src.selection.sampling_plan import save_sampling_plan
from src.selection.validate_selection import validate_selection_config


def _write_problem_spec(out_dir: Path, spec: ProblemSpec) -> Path:
    path = out_dir / "problem_spec.json"
    path.write_text(
        json.dumps(spec.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _write_feature_selection(out_dir: Path) -> Path:
    path = out_dir / "feature_selection.json"
    report = build_feature_selection_report()
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_selection_report(out_dir: Path, spec: ProblemSpec, validation) -> Path:
    target_formatted = f"{spec.target_records:,}".replace(",", ".")
    lines = [
        "# Báo cáo Bước 1 — Selection (KDD)",
        "",
        "## Mục đích",
        "",
        "Selection xác định **cái gì sẽ được khai thác** trước khi thu thập và xử lý:",
        "- Phạm vi bài toán (4 lớp phân loại Lazada)",
        "- Biến cần thu thập từ API/crawl",
        f"- Cách lấy mẫu {target_formatted} sản phẩm (stratified 16 danh mục)",
        "- Tiêu chí chất lượng bản ghi",
        "",
        "Bước này **không crawl**, **không clean**, **không gán nhãn**.",
        "",
        "## Đặc tả bài toán",
        "",
    ]
    lines.extend(f"- {line}" for line in spec.summary_lines())
    lines.extend(
        [
            "",
            "## Kết quả validate config",
            "",
            f"- Trạng thái: {'PASS' if validation.ok else 'FAIL'}",
        ]
    )
    if validation.errors:
        lines.append("- Lỗi:")
        lines.extend(f"  - {e}" for e in validation.errors)
    if validation.warnings:
        lines.append("- Cảnh báo:")
        lines.extend(f"  - {w}" for w in validation.warnings)

    lines.extend(
        [
            "",
            "## Output sinh ra",
            "",
            "- `problem_spec.json` — đặc tả bài toán",
            "- `feature_selection.json` — biến thu thập + map nhãn",
            "- `sampling_plan.json` — kế hoạch crawl 16 danh mục",
            "- `selection_report.md` — báo cáo tóm tắt (file này)",
            "",
            "## Bước tiếp theo",
            "",
            "Sau khi Selection PASS → chạy **Bước 2 (Preprocessing)**:",
            "1. Collection: crawl theo `sampling_plan.json`",
            "2. Clean: normalize, missing, outlier, dedup → file clean theo cấu hình",
        ]
    )

    path = out_dir / "selection_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_selection() -> dict:
    """Thực thi Bước 1 và trả về paths + validation."""
    validation = validate_selection_config()
    if not validation.ok:
        raise ValueError(
            "Selection config không hợp lệ:\n" + "\n".join(validation.errors)
        )

    out_dir = resolve_path("selection")
    out_dir.mkdir(parents=True, exist_ok=True)

    spec = ProblemSpec.from_config()
    paths = {
        "problem_spec": _write_problem_spec(out_dir, spec),
        "feature_selection": _write_feature_selection(out_dir),
        "sampling_plan": save_sampling_plan(out_dir),
        "selection_report": _write_selection_report(out_dir, spec, validation),
    }

    print("Bước 1 — Selection hoàn tất")
    for name, path in paths.items():
        print(f"  {name}: {path}")

    return {"validation": validation.to_dict(), "outputs": {k: str(v) for k, v in paths.items()}}


def main() -> None:
    run_selection()


if __name__ == "__main__":
    main()
