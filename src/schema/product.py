"""
Mô hình dữ liệu theo từng giai đoạn pipeline KDD.

Raw → Clean → Features → Labeled
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.schema.enums import LabelClass, LabelSource, Platform


# ---------------------------------------------------------------------------
# Bước 1–2: Thu thập & làm sạch
# ---------------------------------------------------------------------------


class ProductRaw(BaseModel):
    """Bản ghi ngay sau crawl (Lazada AJAX API)."""

    crawl_timestamp: datetime
    platform: Platform = Platform.LAZADA
    category_name: str
    id: str
    shop_id: Optional[str] = None
    name: str
    price: float = Field(ge=0)
    original_price: Optional[float] = Field(default=None, ge=0)
    discount_rate: Optional[float] = Field(default=None, ge=0, le=100)
    rating_average: Optional[float] = Field(default=None, ge=0, le=5)
    review_count: Optional[int] = Field(default=None, ge=0)
    quantity_sold_value: Optional[int] = Field(default=None, ge=0)
    quantity_sold_text: Optional[str] = None
    brand: Optional[str] = None
    location: Optional[str] = None
    seller_name: Optional[str] = None
    url: str


class ProductClean(BaseModel):
    """Sau preprocessing — schema chuẩn 10k."""

    id: str
    crawl_date: datetime
    platform: Platform = Platform.LAZADA
    category: str
    product_name: str
    current_price: float = Field(gt=0)
    original_price: float = Field(gt=0)
    discount_rate: float = Field(ge=0, le=95)
    rating_average: float = Field(ge=1.0, le=5.0)
    num_reviews: int = Field(ge=0)
    quantity_sold: int = Field(ge=0)
    brand: str = "Unknown"
    seller_location: str = "Unknown"
    product_url: str


# ---------------------------------------------------------------------------
# Bước 3: Feature engineering
# ---------------------------------------------------------------------------


class ProductFeatures(ProductClean):
    """Clean + engineered features (trước labeling)."""

    # Time & velocity
    days_active: int = Field(ge=1)
    sales_velocity: float = Field(ge=0)
    sales_velocity_normalized: float = 0.0
    review_velocity: float = Field(ge=0)
    review_velocity_normalized: float = 0.0

    # Price
    absolute_saving: float = Field(ge=0)
    discount_score: float = Field(ge=0)

    # Scores
    popularity_score: float = Field(ge=0)
    engagement_score: float = Field(ge=0)
    trend_momentum: float = 0.0
    value_score: float = 0.0
    deal_quality_score: float = 0.0

    # Categorical buckets
    popularity_category: str
    price_segment: str
    quality_tier: str
    discount_intensity: str
    product_age: str

    # Category context
    category_popularity_rank: float = 0.0
    category_price_percentile: float = 0.0


# ---------------------------------------------------------------------------
# Bước 3: Labeling
# ---------------------------------------------------------------------------


class ProductLabeled(ProductFeatures):
    """Bản ghi có nhãn phân loại (output bộ dataset đề tài)."""

    seed_label: Optional[LabelClass] = None
    seed_reason: Optional[str] = None
    label_source: Optional[LabelSource] = None
    label: LabelClass
    label_encoded: Optional[int] = Field(default=None, ge=0, le=3)


# ---------------------------------------------------------------------------
# Bước 4: ML artifacts (metadata, không phải 1 row)
# ---------------------------------------------------------------------------


class ModelBundleMeta(BaseModel):
    """Metadata lưu cùng model.pkl."""

    model_name: str
    sklearn_version: str
    feature_columns: list[str]
    label_classes: list[str]
    trained_at: datetime
    train_size: int
    test_size: int
    cv_folds: int = 5
    metrics: dict[str, float] = Field(default_factory=dict)
