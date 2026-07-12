# Credit risk feature store (Feast)

Feast project **`correct_phoenix`**: centralizes credit-scoring features for the [credit_risk_forecast](../../README.md) workspace. Raw loan and customer data are versioned with DVC, merged and transformed with sklearn, registered in Feast, materialized to Redis, and served through the `credit_scoring` feature service (29 engineered numeric features per `id_contrato`).

---

## Prerequisites

| Dependency | Purpose |
|------------|---------|
| Python 3.12 | Feast and ML stack (`requirements.txt`) |
| Redis | Online feature store (`localhost:6379` by default) |
| MinIO (S3-compatible) | Feast registry (`s3://feast/db/registry.pb`) and DVC remote (`s3://feast/dvc-storage`) |

MinIO is provided by the parent stack: from `credit_risk_forecast/`, run `docker compose up -d minio` (API port defaults to **9000**; use **19000** if your `.env` sets `MINIO_API_HOST_PORT=19000`).

Start Redis locally, for example:

```bash
docker run -d --name feast-redis -p 6379:6379 redis:7.2-bookworm
```

Or use the Redis service from `docker-compose.airflow.yml` in the parent repo (also exposes port 6379).

Create the `feast` bucket on MinIO once (adjust host/port and credentials to match your setup):

```bash
mc alias set local http://localhost:19000 minioadmin minioadmin
mc mb --ignore-existing local/feast
```

---

## 1. Python environment (Feast)

From this directory (`feature_store/`):

```bash
conda create -n feast python=3.12 -y
conda activate feast
pip install -r requirements.txt
```

---

## 2. Configure MinIO / S3 credentials

```bash
cp feature_repo/.env.example feature_repo/.env
```

Edit `feature_repo/.env` so `FEAST_S3_ENDPOINT_URL` matches your MinIO API port (e.g. `http://localhost:9000` or `http://localhost:19000`).

Load these variables before any Feast or AWS CLI command. On Linux/WSL:

```bash
source feature_repo/load_env.sh
```

On Windows PowerShell, set the same variables manually or dot-source equivalent exports.

---

## 3. Pull training data (DVC)

Parquet files under `feature_repo/data/` are tracked by DVC and stored on MinIO. DVC uses a **separate** conda env because its `s3fs` pin conflicts with Feast 0.63:

```bash
conda create -n dvc python=3.12 -y
conda activate dvc
pip install -r requirements-dvc.txt
```

Configure the DVC remote (reads `feature_repo/.env`):

```bash
bash scripts/configure_dvc_minio.sh
dvc pull
```

Expected files after pull:

- `feature_repo/data/historico_emprestimos.parquet`
- `feature_repo/data/base_cadastral.parquet`
- `feature_repo/data/historico_parcelas.parquet`
- `feature_repo/data/credit_model_inputs.parquet` (generated locally if missing; see next step)

Switch back to the Feast env: `conda activate feast`.

---

## 4. Fit feature engineering artifacts

Merge loan + customer tables and fit the sklearn transformer (aligned with `credit_risk_forecast/model_notebook/lgbm_test.ipynb`):

```bash
cd feature_repo
python fit_credit_fe.py
```

This writes:

- `data/credit_model_inputs.parquet` — merged inputs for Feast
- `artifacts/credit_fe_encoder.joblib` — fitted ordinal encoder
- `artifacts/credit_fe_feature_names.json` — list of 29 served feature names

Re-run this script whenever raw data or `credit_feature_engineering.py` changes.

---

## 5. Register and materialize features in Feast

From `feature_repo/` with env vars loaded:

```bash
source load_env.sh   # Linux/WSL; skip if already exported

feast apply
```

`feast apply` pushes feature definitions to the S3 registry. Then materialize the online-enabled view `credit_model_inputs` into Redis:

```bash
feast materialize 2016-01-01T00:00:00 2030-12-31T23:59:59
```

Use a date range that covers all `data_decisao` values in your parquet files. For day-to-day updates after new data arrives:

```bash
feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)
```

Engineered features are **not** pre-materialized; they are computed on demand via an on-demand feature view when you call the `credit_scoring` service.

---

## 6. Retrieve features

### Python client

```python
import os
from pathlib import Path
from feast import FeatureStore

repo = Path("feature_repo")  # or absolute path
store = FeatureStore(repo_path=str(repo))

entity_rows = [{"id_contrato": 2802425}]
df = store.get_online_features(
    entity_rows=entity_rows,
    features=store.get_feature_service("credit_scoring"),
).to_df()
```

### Notebook

Open [`consume.ipynb`](consume.ipynb) from `feature_store/` (parent of `feature_repo/`). It loads `.env`, connects to the store, and batch-fetches engineered features for all contracts materialized in Redis.

### Optional: Feast feature server

```bash
cd feature_repo
feast serve
```

Exposes HTTP endpoints for online retrieval ([Feast Python feature server](https://docs.feast.dev/reference/feature-servers/python-feature-server)).

---

## Project layout

```
feature_store/
├── README.md
├── requirements.txt          # Feast + ML stack
├── requirements-dvc.txt      # DVC only (separate env)
├── consume.ipynb             # Online feature retrieval demo
├── scripts/
│   └── configure_dvc_minio.sh
└── feature_repo/
    ├── feature_store.yaml    # Registry (S3), online (Redis), offline (file)
    ├── feature_definitions_emprestimos.py   # Loan history (offline)
    ├── feature_definitions_parcelas.py      # Installment history (offline)
    ├── feature_definitions_inputs.py        # Merged inputs (online, internal)
    ├── feature_definitions_engineered.py    # ODFV + credit_scoring service
    ├── credit_feature_engineering.py
    ├── fit_credit_fe.py
    ├── load_env.sh
    ├── data/                 # Parquet sources (DVC)
    └── artifacts/            # Fitted encoder + feature names
```

### Feature surfaces

| Name | Type | Served to models? |
|------|------|-------------------|
| `historico_emprestimos` | Feature view | No (offline / exploration) |
| `historico_parcelas` | Feature view | No (offline / exploration) |
| `credit_model_inputs` | Feature view | No (internal; materialized to Redis) |
| `credit_engineered_features` | On-demand feature view | Yes (via service) |
| `credit_scoring` | Feature service | **Yes** — use this in scoring code |

---

## Development workflow

1. Change feature definitions or engineering code under `feature_repo/`.
2. If engineering logic changed: `python fit_credit_fe.py`.
3. `feast apply` to update the registry.
4. `feast materialize …` (or `materialize-incremental`) to refresh Redis.
5. Validate with `consume.ipynb` or a small `get_online_features` script.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| S3 / registry errors | `feature_repo/.env` loaded; MinIO running; `feast` bucket exists; endpoint port matches compose |
| `Missing engineered feature list` | Run `python fit_credit_fe.py` first |
| Redis connection refused | Redis listening on `localhost:6379` (see `feature_store.yaml`) |
| Empty online features | Run `feast materialize` after `feast apply`; entity `id_contrato` must exist in materialized data |
| DVC / Feast pip conflict | Keep DVC in the `dvc` conda env; Feast in the `feast` env |

---

## Further reading

- [Feast documentation](https://docs.feast.dev/)
- [Running Feast in production](https://docs.feast.dev/how-to-guides/running-feast-in-production)
- Parent MLOps stack: [`credit_risk_forecast/README.md`](../../README.md)
