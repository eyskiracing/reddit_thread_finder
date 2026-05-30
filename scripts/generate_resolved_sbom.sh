#!/usr/bin/env bash
set -euo pipefail

# Run from the project root after activating your virtual environment and
# installing runtime dependencies.

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

# Capture exact installed versions.
python -m pip freeze > requirements.lock.txt

# Generate a CycloneDX SBOM from the active virtual environment.
cyclonedx-py environment --output-format json --output-file sbom.resolved.cyclonedx.json

echo "Wrote requirements.lock.txt and sbom.resolved.cyclonedx.json"
