#!/usr/bin/env bash
set -euo pipefail

# Run from the project root after creating and activating a clean venv.
# This creates a pinned snapshot of the exact installed packages.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip freeze > requirements.lock.txt

echo "Wrote requirements.lock.txt"
