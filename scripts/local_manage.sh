#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.local}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "$ENV_FILE not found. Run ./scripts/local_bootstrap.sh first or copy .env.local.example to $ENV_FILE." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ ! -x .venv/bin/python ]]; then
  echo ".venv was not found. Run ./scripts/local_bootstrap.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python manage.py "$@"
