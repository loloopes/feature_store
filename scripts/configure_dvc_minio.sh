#!/usr/bin/env bash
# Configure DVC to use MinIO (S3-compatible). Run from correct_phoenix/ repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ROOT}/feature_repo/.env"
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    export "$line"
  done < "$ENV_FILE"
fi

ENDPOINT="${FEAST_S3_ENDPOINT_URL:-${AWS_ENDPOINT_URL:-http://localhost:19000}}"
ACCESS_KEY="${AWS_ACCESS_KEY_ID:-minioadmin}"
SECRET_KEY="${AWS_SECRET_ACCESS_KEY:-minioadmin}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
BUCKET_PATH="${DVC_REMOTE_URL:-s3://feast/dvc-storage}"

if ! command -v dvc >/dev/null 2>&1; then
  echo "dvc not found. Activate conda env: conda activate feast"
  exit 1
fi

[[ -d .dvc ]] || dvc init

dvc remote add -d minio "$BUCKET_PATH" 2>/dev/null || dvc remote modify minio url "$BUCKET_PATH"
dvc remote modify minio endpointurl "$ENDPOINT"
dvc remote modify minio region "$REGION"
dvc remote modify --local minio access_key_id "$ACCESS_KEY"
dvc remote modify --local minio secret_access_key "$SECRET_KEY"

echo "DVC remote 'minio' -> $BUCKET_PATH @ $ENDPOINT"
dvc remote list
