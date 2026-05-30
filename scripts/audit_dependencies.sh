#!/usr/bin/env bash
set -euo pipefail

# Run from the project root after activating your virtual environment.
# This audits the installed environment and the declared requirements file.

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo "Auditing current Python environment..."
python -m pip_audit

echo "Auditing requirements.txt..."
python -m pip_audit -r requirements.txt
