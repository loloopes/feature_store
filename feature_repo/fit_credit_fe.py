"""Fit CreditFeatureEngineering and build merged input parquet for Feast."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd

from credit_feature_engineering import (
    ENCODER_PATH,
    FEATURE_NAMES_PATH,
    CreditFeatureEngineering,
)

REPO_DIR = Path(__file__).resolve().parent
DATA_DIR = REPO_DIR / "data"
ARTIFACT_DIR = REPO_DIR / "artifacts"
MERGED_PATH = DATA_DIR / "credit_model_inputs.parquet"


def build_merged_inputs() -> pd.DataFrame:
    emprestimos = pd.read_parquet(DATA_DIR / "historico_emprestimos.parquet")
    cadastral = pd.read_parquet(DATA_DIR / "base_cadastral.parquet")
    merged = emprestimos.merge(cadastral, on="id_cliente", how="left")
    merged["data_decisao"] = pd.to_datetime(merged["data_decisao"], errors="coerce")
    merged.to_parquet(MERGED_PATH, index=False)
    return merged


def main() -> None:
    merged = build_merged_inputs()

    fe = CreditFeatureEngineering()
    fe.fit(merged)

    sample = fe.transform(merged.head(1))
    feature_names = list(sample.columns)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with ENCODER_PATH.open("wb") as f:
        pickle.dump(fe.encoder, f)
    FEATURE_NAMES_PATH.write_text(
        json.dumps(feature_names, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {MERGED_PATH} ({len(merged):,} rows)")
    print(f"Wrote {ENCODER_PATH}")
    print(f"Wrote {FEATURE_NAMES_PATH} ({len(feature_names)} engineered features)")


if __name__ == "__main__":
    main()
