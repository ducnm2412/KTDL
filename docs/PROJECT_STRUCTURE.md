# PROJECT_STRUCTURE — Map 5 bước KDD → thư mục

| Bước KDD | Thư mục / module | Output chính |
|----------|------------------|--------------|
| 1 Selection | `config/`, `src/selection/` | Đặc tả, categories.yaml |
| 2 Preprocessing | `src/preprocessing/`, `data/raw/`, `data/clean/` | lazada_10k_clean.json |
| 3 Transformation | `src/transformation/`, `data/features/`, `data/labeled/`, `data/model_ready/` | labeled + train/test |
| 4 Data Mining | `src/mining/`, `models/` | rf_classifier.pkl |
| 5 Evaluation | `src/evaluation/`, `reports/` | figures, evaluation_summary |

## Schema classes (`src/schema/`)

```
ProductRaw
    ↓ clean
ProductClean
    ↓ feature engineering
ProductFeatures
    ↓ labeling
ProductLabeled
```

## Enums (`src/schema/enums.py`)

- `LabelClass` — 4 nhãn đích
- `LabelSource` — nguồn gán nhãn hybrid
- `PopularityCategory`, `PriceSegment`, `QualityTier`, `DiscountIntensity`, `ProductAge` — bucket phụ
