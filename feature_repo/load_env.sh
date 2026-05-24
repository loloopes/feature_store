#!/usr/bin/env bash
# Load .env without Windows CRLF breaking AWS region/credentials (WSL + /mnt/c).
set -a
_env_file="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%$'\r'}"
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  export "$line"
done < "$_env_file"
set +a
