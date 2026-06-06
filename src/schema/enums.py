from enum import Enum


class Platform(str, Enum):
    LAZADA = "Lazada"
    SHOPEE = "Shopee"
    TIKI = "Tiki"


class LabelClass(str, Enum):
    """4 lớp phân loại sản phẩm (đề tài)."""

    HOT_TREND = "Hot Trend"
    BEST_SELLER = "Best Seller"
    BEST_DEAL = "Best Deal"
    NORMAL = "Normal"

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]


class LabelSource(str, Enum):
    """Nguồn gán nhãn trong pipeline hybrid."""

    RULE_SEED = "rule_seed"
    MODEL = "model"
    RULE_FULL = "rule_full"


class PopularityCategory(str, Enum):
    VIRAL = "Viral"
    HOT = "Hot"
    WARM = "Warm"
    COLD = "Cold"


class PriceSegment(str, Enum):
    BUDGET = "Budget"
    MID = "Mid"
    PREMIUM = "Premium"


class QualityTier(str, Enum):
    PREMIUM = "Premium"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DiscountIntensity(str, Enum):
    AGGRESSIVE = "Aggressive"
    HEAVY = "Heavy"
    MODERATE = "Moderate"
    LIGHT = "Light"
    NONE = "None"


class ProductAge(str, Enum):
    BRAND_NEW = "Brand New"
    NEW = "New"
    RECENT = "Recent"
    ESTABLISHED = "Established"
    MATURE = "Mature"
