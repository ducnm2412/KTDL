"""Hằng số dùng chung pipeline."""

from src.schema.enums import LabelClass

LABEL_TO_ENCODED: dict[str, int] = {
    LabelClass.BEST_DEAL.value: 0,
    LabelClass.BEST_SELLER.value: 1,
    LabelClass.HOT_TREND.value: 2,
    LabelClass.NORMAL.value: 3,
}

ENCODED_TO_LABEL: dict[int, str] = {v: k for k, v in LABEL_TO_ENCODED.items()}

OUTPUT_FILES = {
    "raw_merged": "lazada_raw_merged.json",
    "clean_10k": "lazada_10k_clean.json",
    "features": "lazada_10k_features.json",
    "labeled": "lazada_10k_labeled.json",
    "train": "train.json",
    "test": "test.json",
    "model": "rf_classifier.pkl",
    "scaler": "scaler.pkl",
    "label_encoder": "label_encoder.pkl",
    "feature_mapping": "feature_mapping.json",
    "model_meta": "model_meta.json",
}


def platform_file_prefix(platform: str) -> str:
    return platform.lower().replace(" ", "_")
