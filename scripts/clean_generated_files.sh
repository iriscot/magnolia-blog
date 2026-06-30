#!/usr/bin/env bash
set -euo pipefail

# Removes generated/local-only files from the Git index and working tree where safe.
# User uploads in media/ are removed from the Git index only, not deleted locally.

git rm -r --cached --ignore-unmatch media static_root node_modules static/vendor || true
git rm --cached --ignore-unmatch .env .env.local db.sqlite3 db.sqlite3-journal static/styles/core.css.map || true

rm -rf static_root node_modules static/vendor .pytest_cache .mypy_cache .ruff_cache htmlcov
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
find . -name '*.pyc' -type f -delete
find . -name '*.pyo' -type f -delete
find . -name '.DS_Store' -type f -delete

printf '\nCleanup done. Check the result with:\n  git status --short\n  git diff --cached --stat\n'
