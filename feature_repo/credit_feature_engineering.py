"""Feature engineering aligned with credit_risk_forecast/model_notebook/lgbm_test.ipynb."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pickle
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OrdinalEncoder

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ENCODER_PATH = ARTIFACT_DIR / "credit_fe_encoder.joblib"
FEATURE_NAMES_PATH = ARTIFACT_DIR / "credit_fe_feature_names.json"


class CreditFeatureEngineering(BaseEstimator, TransformerMixin):
    def __init__(self, feature_names: Optional[list[str]] = None):
        self.encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=-1
        )
        self.target_cat_cols = [
            "tipo_contrato",
            "status_contrato",
            "tipo_pagamento",
            "finalidade_emprestimo",
            "tipo_cliente",
            "tipo_portfolio",
            "tipo_produto",
            "categoria_bem",
            "setor_vendedor",
            "canal_venda",
        ]
        self.feature_names = feature_names
        self._fitted_cat_cols: list[str] = []

    def fit(self, X, y=None):
        actual_cat = [c for c in self.target_cat_cols if c in X.columns]
        self._fitted_cat_cols = actual_cat
        if actual_cat:
            self.encoder.fit(X[actual_cat].fillna("Missing").astype(str))
        return self

    def transform(self, X):
        X_c = X.copy()

        if "renda_anual" in X_c.columns:
            X_c["renda_mensal"] = X_c["renda_anual"] / 12
            if "valor_parcela" in X_c.columns:
                X_c["feat_comprometimento_renda"] = X_c["valor_parcela"] / X_c[
                    "renda_mensal"
                ].replace(0, np.nan)
            if "qtd_membros_familia" in X_c.columns:
                X_c["feat_renda_per_capita"] = X_c["renda_anual"] / X_c[
                    "qtd_membros_familia"
                ].replace(0, np.nan)

        if "possui_carro" in X_c.columns:
            X_c["feat_possui_carro"] = (
                X_c["possui_carro"].map({"Y": 1, "N": 0}).fillna(0)
            )
        if "possui_imovel" in X_c.columns:
            X_c["feat_possui_imovel"] = (
                X_c["possui_imovel"].map({"Y": 1, "N": 0}).fillna(0)
            )

        if "data_nascimento" in X_c.columns and "data_decisao" in X_c.columns:
            X_c["data_nascimento"] = pd.to_datetime(
                X_c["data_nascimento"], errors="coerce"
            )
            X_c["data_decisao"] = pd.to_datetime(X_c["data_decisao"], errors="coerce")
            X_c["feat_idade"] = (
                (X_c["data_decisao"] - X_c["data_nascimento"]).dt.days // 365
            )

        if "valor_credito" in X_c.columns and "valor_bem" in X_c.columns:
            X_c["feat_ltv"] = X_c["valor_credito"] / X_c["valor_bem"].replace(
                0, np.nan
            ).fillna(X_c["valor_credito"])

        if "hora_solicitacao" in X_c.columns:
            X_c["feat_hora_pico_fraude"] = X_c["hora_solicitacao"].apply(
                lambda x: 1 if x < 7 or x > 21 else 0
            )

        actual_cat = [c for c in self._fitted_cat_cols if c in X_c.columns]
        if not actual_cat:
            actual_cat = [c for c in self.target_cat_cols if c in X_c.columns]
        if actual_cat and hasattr(self.encoder, "categories_"):
            encoded = self.encoder.transform(
                X_c[actual_cat].fillna("Missing").astype(str)
            )
            for i, col in enumerate(actual_cat):
                X_c[f"feat_{col}_enc"] = encoded[:, i]

        cols_to_drop = [
            "id_cliente",
            "id_contrato",
            "data_decisao",
            "data_liberacao",
            "data_primeiro_vencimento",
            "data_ultimo_vencimento",
            "data_ultimo_vencimento_original",
            "data_encerramento",
            "data_nascimento",
            "renda_anual",
            "qtd_membros_familia",
            "possui_carro",
            "possui_imovel",
        ]
        X_final = X_c.drop(
            columns=[c for c in cols_to_drop if c in X_c.columns], errors="ignore"
        )
        X_final = X_final.select_dtypes(include=[np.number])

        if self.feature_names is not None:
            for col in self.feature_names:
                if col not in X_final.columns:
                    X_final[col] = 0
            X_final = X_final[self.feature_names]

        return X_final.astype("float64")


def load_fitted_transformer() -> CreditFeatureEngineering:
    if not ENCODER_PATH.exists() or not FEATURE_NAMES_PATH.exists():
        raise FileNotFoundError(
            "Missing FE artifacts. Run: python fit_credit_fe.py "
            f"(expected {ENCODER_PATH} and {FEATURE_NAMES_PATH})"
        )
    with ENCODER_PATH.open("rb") as f:
        encoder = pickle.load(f)
    feature_names = json.loads(FEATURE_NAMES_PATH.read_text(encoding="utf-8"))
    fe = CreditFeatureEngineering(feature_names=feature_names)
    fe.encoder = encoder
    fe._fitted_cat_cols = list(getattr(encoder, "feature_names_in_", fe.target_cat_cols))
    return fe


def denest_feast_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map Feast multi-source columns (fv__feature) back to raw names."""
    out: dict[str, pd.Series] = {}
    for col in df.columns:
        key = col.split("__", 1)[-1] if "__" in col else col
        out[key] = df[col]
    return pd.DataFrame(out)
