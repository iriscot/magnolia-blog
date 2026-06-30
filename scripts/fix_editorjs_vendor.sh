#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js/npm, then rerun this script." >&2
  exit 1
fi

if [[ -f package-lock.json ]] && grep -Eq 'applied-caas|artifactory|openai\.org' package-lock.json; then
  cp package-lock.json package-lock.json.local-backup
  rm -f package-lock.json
  echo "Backed up package-lock.json to package-lock.json.local-backup and regenerated it from the public npm registry."
fi

rm -rf static/vendor/@editorjs
npm install --registry=https://registry.npmjs.org/
npm run build-vendor
npm run build-css

echo
cat <<'MSG'
EditorJS static files were rebuilt.
Restart Django runserver, then hard-refresh /new/.
MSG
