"""Bước 2b - Clean: pandas mapping + hybrid cleaning cho Lazada."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.config_loader import get_settings, resolve_path
from src.constants import OUTPUT_FILES
from src.preprocessing.crawl_progress import merge_raw_files

# Mapping cho Lazada: cột raw -> cột chuẩn ProductClean
RAW_TO_CLEAN_MAPPING = {
    "crawl_timestamp": "crawl_date",
    "category_name": "category",
    "name": "product_name",
    "price": "current_price",
    "review_count": "num_reviews",
    "quantity_sold_value": "quantity_sold",
    "location": "seller_location",
    "url": "product_url",
}

# Bộ cột chuẩn đầu ra sau bước mapping.
# Lưu ý: bước này chưa parse số/outlier nên giá trị vẫn có thể là string.
CLEAN_COLUMNS = [
    "id",
    "crawl_date",
    "platform",
    "category",
    "product_name",
    "current_price",
    "original_price",
    "discount_rate",
    "rating_average",
    "num_reviews",
    "quantity_sold",
    "brand",
    "seller_location",
    "product_url",
]


def _extract_price(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    digits = re.sub(r"[^\d]", "", str(value))
    return float(digits) if digits else None


def _extract_discount(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def _safe_to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _extract_sold_value(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return int(max(0, value))

    text = str(value).strip().upper()
    match = re.search(r"([\d.]+)\s*([KMB]?)", text)
    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2)
    if unit == "K":
        number *= 1000
    elif unit == "M":
        number *= 1_000_000
    elif unit == "B":
        number *= 1_000_000_000
    return int(max(0, number))


def _load_raw_records(raw_dir: Path, platform: str) -> list[dict[str, Any]]:
    """Load raw merged; nếu chưa có thì tự merge từ categories."""
    merged_path = raw_dir / OUTPUT_FILES["raw_merged"]
    if not merged_path.exists():
        merge_raw_files(raw_dir, OUTPUT_FILES["raw_merged"], platform=platform)
    if not merged_path.exists():
        return []
    return json.loads(merged_path.read_text(encoding="utf-8"))


def _map_with_pandas(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Mapping cột bằng pandas theo hướng raw -> clean schema."""
    if not records:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    df = pd.DataFrame(records)
    df = df.rename(columns=RAW_TO_CLEAN_MAPPING)

    # Đảm bảo đủ cột schema clean ngay từ bước mapping
    for col in CLEAN_COLUMNS:
        if col not in df.columns:
            df[col] = None

    if "crawl_date" in df.columns:
        df["crawl_date"] = pd.to_datetime(df["crawl_date"], errors="coerce", utc=True)
        df["crawl_date"] = df["crawl_date"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    return df[CLEAN_COLUMNS]


def run_clean_mapping(*, output_name: str = "lazada_mapped_step1.json") -> dict[str, Any]:
    """Chạy bước 1: mapping raw -> clean schema."""
    settings = get_settings()
    platform = settings["project"]["platform"]
    raw_dir = resolve_path("raw")
    clean_dir = resolve_path("clean")
    clean_dir.mkdir(parents=True, exist_ok=True)

    raw_records = _load_raw_records(raw_dir, platform)
    mapped_df = _map_with_pandas(raw_records)

    out_path = clean_dir / output_name
    out_path.write_text(
        json.dumps(mapped_df.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "status": "ok",
        "step": "clean_mapping",
        "input_raw_records": len(raw_records),
        "output_records": len(mapped_df),
        "output_file": str(out_path),
        "columns": CLEAN_COLUMNS,
    }


def _parse_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["current_price"] = out["current_price"].apply(_extract_price)
    out["original_price"] = out["original_price"].apply(_extract_price)
    out["discount_rate"] = out["discount_rate"].apply(_extract_discount)
    out["rating_average"] = out["rating_average"].apply(_safe_to_float)
    out["num_reviews"] = out["num_reviews"].apply(_safe_to_float)
    out["quantity_sold"] = out["quantity_sold"].apply(_safe_to_float)
    return out


def _apply_missing_and_business_rules(df: pd.DataFrame, max_discount_rate: float) -> pd.DataFrame:
    out = df.copy()

    # Dùng quantity_sold_text khi quantity_sold_value thiếu (nếu cột này tồn tại trong raw)
    if "quantity_sold_text" in out.columns:
        sold_from_text = out["quantity_sold_text"].apply(_extract_sold_value)
        out["quantity_sold"] = out["quantity_sold"].fillna(sold_from_text)

    # Critical fields: thiếu là drop
    critical_cols = ["id", "category", "product_name", "current_price", "product_url"]
    out = out.dropna(subset=[c for c in critical_cols if c in out.columns])

    # Giá hợp lệ
    out = out[out["current_price"] > 0]
    out["original_price"] = out["original_price"].fillna(out["current_price"])
    out.loc[out["original_price"] <= 0, "original_price"] = out["current_price"]
    out["original_price"] = out[["original_price", "current_price"]].max(axis=1)

    # Review/sold/rating theo hướng hybrid: giữ dữ liệu tối đa, fill rule-based
    out["num_reviews"] = out["num_reviews"].fillna(0).clip(lower=0).astype(int)
    out["quantity_sold"] = out["quantity_sold"].fillna(0).clip(lower=0).astype(int)
    out["rating_average"] = out["rating_average"].fillna(0).clip(lower=0, upper=5)
    out.loc[out["num_reviews"] == 0, "rating_average"] = 0

    # discount mặc định 0, chặn giá trị bất thường theo config
    out["discount_rate"] = out["discount_rate"].fillna(0).clip(lower=0, upper=max_discount_rate)

    # Text defaults
    out["brand"] = out["brand"].fillna("No Brand").astype(str).str.strip()
    out["brand"] = out["brand"].replace({"": "No Brand", "none": "No Brand", "n/a": "No Brand"})
    out["seller_location"] = out["seller_location"].fillna("Unknown").astype(str).str.strip()
    out["seller_location"] = out["seller_location"].replace({"": "Unknown"})

    return out


def _handle_outliers(df: pd.DataFrame, clean_cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = df.copy()
    before = len(out)

    # Giá: lọc theo percentile + min price
    price_low_q = float(clean_cfg.get("price_lower_percentile", 0.1)) / 100
    price_high_q = float(clean_cfg.get("price_upper_percentile", 99.9)) / 100
    price_low = max(1000.0, float(out["current_price"].quantile(price_low_q)))
    price_high = float(out["current_price"].quantile(price_high_q))
    out = out[(out["current_price"] >= price_low) & (out["current_price"] <= price_high)]

    # Sold/reviews upper outliers (threshold tính từ data trước khi cắt sold/review)
    sold_high_q = float(clean_cfg.get("sold_upper_percentile", 99.5)) / 100
    reviews_high_q = float(clean_cfg.get("reviews_upper_percentile", 99.0)) / 100
    sold_high = float(out["quantity_sold"].quantile(sold_high_q))
    reviews_high = float(out["num_reviews"].quantile(reviews_high_q))
    out = out[(out["quantity_sold"] <= sold_high) & (out["num_reviews"] <= reviews_high)]

    stats = {
        "price_range": {
            "lower_percentile": price_low_q * 100,
            "upper_percentile": price_high_q * 100,
            "lower_value": round(price_low, 4),
            "upper_value": round(price_high, 4),
        },
        "quantity_sold_upper": {
            "percentile": sold_high_q * 100,
            "value": round(sold_high, 4),
        },
        "num_reviews_upper": {
            "percentile": reviews_high_q * 100,
            "value": round(reviews_high, 4),
        },
        "records_before": before,
        "records_after": len(out),
        "records_removed": before - len(out),
    }
    return out, stats


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values(by=["quantity_sold", "num_reviews"], ascending=[False, False])
    # Khóa kép để an toàn khi mở rộng đa nền tảng.
    out = out.drop_duplicates(subset=["platform", "id"], keep="first")
    return out.reset_index(drop=True)


def _load_sampling_plan() -> dict[str, Any] | None:
    selection_dir = resolve_path("selection")
    path = selection_dir / "sampling_plan.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_stratified_sampling(
    df: pd.DataFrame,
    *,
    sampling_plan: dict[str, Any] | None,
    random_seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Bước 7: Chốt dataset theo kế hoạch stratified.

    Nếu một danh mục thiếu dữ liệu so với target, giữ toàn bộ bản ghi có sẵn
    và ghi deficit vào thống kê.
    """
    if sampling_plan is None:
        return df.reset_index(drop=True), {
            "enabled": False,
            "reason": "missing_sampling_plan",
            "target_total": None,
            "sampled_total": len(df),
            "category_stats": [],
        }

    category_plan = {
        c["category_name"]: int(c.get("target_count_clean", 0))
        for c in sampling_plan.get("categories", [])
    }
    category_stats: list[dict[str, Any]] = []
    sampled_parts: list[pd.DataFrame] = []

    for category_name, target in category_plan.items():
        cat_df = df[df["category"] == category_name]
        available = len(cat_df)
        take = min(available, target)
        deficit = max(target - available, 0)

        if take > 0:
            # random_state cố định để tái lập kết quả
            sampled = cat_df.sample(n=take, random_state=random_seed)
            sampled_parts.append(sampled)

        category_stats.append(
            {
                "category": category_name,
                "target": target,
                "available": available,
                "selected": take,
                "deficit": deficit,
            }
        )

    if sampled_parts:
        sampled_df = pd.concat(sampled_parts, ignore_index=True)
    else:
        sampled_df = df.iloc[0:0].copy()

    target_total = int(sampling_plan.get("total_planned_clean", 0))
    sampled_total = len(sampled_df)
    return sampled_df, {
        "enabled": True,
        "target_total": target_total,
        "sampled_total": sampled_total,
        "total_deficit": max(target_total - sampled_total, 0),
        "category_stats": category_stats,
    }


def run_clean_hybrid(*, output_name: str | None = None) -> dict[str, Any]:
    """Chạy clean theo hướng hybrid, phù hợp mapping pandas ở bước 1."""
    settings = get_settings()
    platform = settings["project"]["platform"]
    random_seed = int(settings["project"].get("random_seed", 42))
    clean_cfg = settings.get("clean", {})
    raw_dir = resolve_path("raw")
    clean_dir = resolve_path("clean")
    clean_dir.mkdir(parents=True, exist_ok=True)

    raw_records = _load_raw_records(raw_dir, platform)
    mapped_df = _map_with_pandas(raw_records)
    parsed_df = _parse_numeric_fields(mapped_df)
    ruled_df = _apply_missing_and_business_rules(
        parsed_df,
        max_discount_rate=float(clean_cfg.get("max_discount_rate", 95)),
    )
    outlier_df, outlier_stats = _handle_outliers(ruled_df, clean_cfg)
    dedup_df = _deduplicate(outlier_df)
    sampling_plan = _load_sampling_plan()
    final_df, stratified_stats = _apply_stratified_sampling(
        dedup_df,
        sampling_plan=sampling_plan,
        random_seed=random_seed,
    )

    out_name = output_name or OUTPUT_FILES["clean_10k"]
    out_path = clean_dir / out_name
    out_path.write_text(
        json.dumps(final_df[CLEAN_COLUMNS].to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "status": "ok",
        "step": "clean_hybrid",
        "input_raw_records": len(raw_records),
        "mapped_records": len(mapped_df),
        "after_rules_records": len(ruled_df),
        "after_outlier_records": len(outlier_df),
        "after_dedup_records": len(dedup_df),
        "final_records": len(final_df),
        "outlier_stats": outlier_stats,
        "stratified_stats": stratified_stats,
        "output_file": str(out_path),
    }

