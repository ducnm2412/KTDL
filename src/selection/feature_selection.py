"""Bước 1 KDD — Chọn biến thu thập và map biến → mục tiêu phân loại."""

from __future__ import annotations

from typing import Any

from src.schema.product import ProductClean, ProductRaw


# Biến thu thập ngay khi crawl (schema ProductRaw)
RAW_FIELDS: list[dict[str, str]] = [
    {"field": "crawl_timestamp", "type": "datetime", "purpose": "Thời điểm snapshot realtime"},
    {"field": "id", "type": "string", "purpose": "Định danh, dedup"},
    {"field": "category_name", "type": "string", "purpose": "Stratified sampling theo ngành hàng"},
    {"field": "name", "type": "string", "purpose": "Metadata sản phẩm"},
    {"field": "price", "type": "float", "purpose": "Giá hiện tại — phục vụ Best Deal, phân khúc giá"},
    {"field": "original_price", "type": "float", "purpose": "Giá gốc — tính ưu đãi"},
    {"field": "discount_rate", "type": "float", "purpose": "Mức giảm giá — Best Deal"},
    {"field": "rating_average", "type": "float", "purpose": "Chất lượng — Best Seller, Best Deal"},
    {"field": "review_count", "type": "int", "purpose": "Engagement — Hot Trend"},
    {"field": "quantity_sold_value", "type": "int", "purpose": "Doanh số — Best Seller, Hot Trend"},
    {"field": "brand", "type": "string", "purpose": "Metadata, phân tích theo thương hiệu"},
    {"field": "location", "type": "string", "purpose": "Ngữ cảnh shop"},
    {"field": "url", "type": "string", "purpose": "Truy vết nguồn"},
]

# Map nhãn → biến gốc (trước feature engineering)
LABEL_VARIABLE_MAP: dict[str, list[str]] = {
    "Hot Trend": [
        "quantity_sold_value",
        "review_count",
        "crawl_timestamp",
        "(sau FE) trend_momentum, engagement_score, product_age",
    ],
    "Best Seller": [
        "quantity_sold_value",
        "rating_average",
        "review_count",
        "(sau FE) popularity_score, sales_velocity",
    ],
    "Best Deal": [
        "price",
        "original_price",
        "discount_rate",
        "(sau FE) deal_quality_score, value_score",
    ],
    "Normal": ["Các sản phẩm không đạt ngưỡng 3 nhóm trên"],
}

# Tiêu chí chất lượng bản ghi (Selection — chốt trước khi crawl)
QUALITY_CRITERIA: list[dict[str, str]] = [
    {"rule": "Không trùng id", "reason": "Mỗi sản phẩm 1 bản ghi trong bộ 10k"},
    {"rule": "current_price > 0", "reason": "Loại sản phẩm giá không hợp lệ"},
    {"rule": "discount_rate trong [0, 95]", "reason": "Loại giảm giá ảo"},
    {"rule": "rating trong [1, 5]", "reason": "Chuẩn thang đánh giá Lazada"},
    {"rule": "Mỗi nhãn >= 5% tổng mẫu", "reason": "Tránh lệch lớp quá mức (sau labeling)"},
]


def get_raw_schema_fields() -> list[str]:
    return list(ProductRaw.model_fields.keys())


def get_clean_schema_fields() -> list[str]:
    return list(ProductClean.model_fields.keys())


def build_feature_selection_report() -> dict[str, Any]:
    return {
        "raw_fields_selected": RAW_FIELDS,
        "raw_schema_fields": get_raw_schema_fields(),
        "clean_schema_fields": get_clean_schema_fields(),
        "label_variable_mapping": LABEL_VARIABLE_MAP,
        "quality_criteria": QUALITY_CRITERIA,
    }
