#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.local}"
if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.local.example "$ENV_FILE"
  echo "Created $ENV_FILE from .env.local.example"
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable '$PYTHON_BIN' was not found. Set PYTHON_BIN=/path/to/python and retry." >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js/npm, then rerun this script." >&2
  echo "The editor page needs node_modules served through Django staticfiles." >&2
  exit 1
fi

# The lockfile generated in some sandboxes can contain a private registry URL.
# Regenerate it from package.json when such URLs are present.
if [[ -f package-lock.json ]] && grep -Eq 'applied-caas|artifactory|openai\.org' package-lock.json; then
  cp package-lock.json package-lock.json.local-backup
  rm -f package-lock.json
  echo "Backed up package-lock.json to package-lock.json.local-backup and regenerating it from the public npm registry."
fi

npm install --registry=https://registry.npmjs.org/
npm run build-css

python manage.py migrate --noinput
python scripts/create_local_admin.py
python manage.py check

cat <<'EOF'

Local setup is complete.
Run the app with:
  ./scripts/local_run.sh

Default local URLs:
  http://127.0.0.1:8000/
  http://127.0.0.1:8000/admin/
EOF
