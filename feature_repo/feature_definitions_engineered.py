"""Engineered credit features served to models (CreditFeatureEngineering output)."""

import json
from pathlib import Path

from feast import FeatureService, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import Float64

from feature_definitions_inputs import credit_model_inputs_fv

_ARTIFACTS = Path(__file__).resolve().parent / "artifacts" / "credit_fe_feature_names.json"
if not _ARTIFACTS.is_file():
    raise FileNotFoundError(
        "Missing engineered feature list. Run first: python fit_credit_fe.py"
    )

ENGINEERED_FEATURE_NAMES: list[str] = json.loads(_ARTIFACTS.read_text(encoding="utf-8"))


@on_demand_feature_view(
    sources=[credit_model_inputs_fv],
    schema=[Field(name=name, dtype=Float64) for name in ENGINEERED_FEATURE_NAMES],
    mode="pandas",
)
def credit_engineered_features(inputs):
    import sys
    from pathlib import Path

    for root in (Path.cwd() / "feature_repo", Path.cwd()):
        repo = root.resolve()
        if (repo / "credit_feature_engineering.py").is_file():
            repo_str = str(repo)
            if repo_str not in sys.path:
                sys.path.insert(0, repo_str)
            break
    else:
        raise ModuleNotFoundError(
            "credit_feature_engineering not found. Run from correct_phoenix/ "
            "or add feature_repo to PYTHONPATH."
        )

    from credit_feature_engineering import denest_feast_columns, load_fitted_transformer

    raw = denest_feast_columns(inputs)
    return load_fitted_transformer().transform(raw).astype("float64")


credit_scoring_service = FeatureService(
    name="credit_scoring",
    features=[credit_engineered_features],
)
