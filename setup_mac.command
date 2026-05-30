#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Setting up Reddit Thread Finder..."
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo "Please install Python 3 and run this setup again."
  exit 1
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from .env.example."
  echo "Please open .env and add your Reddit API credentials before running a search."
else
  chmod 600 .env || true
  echo ".env already exists. Permissions checked."
fi

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Running tests..."
python -m unittest discover -s tests

echo
echo "Setup complete."
echo "Next: open .env, add your Reddit API credentials, then run ./run_mac.command"
echo
read -p "Press Enter to close..."
