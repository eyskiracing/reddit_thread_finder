#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found."
  echo "Run ./setup_mac.command first."
  read -p "Press Enter to close..."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo ".env file not found."
  echo "Run ./setup_mac.command first, then add your Reddit API credentials to .env."
  read -p "Press Enter to close..."
  exit 1
fi

source .venv/bin/activate

echo "Starting Reddit Thread Finder..."
echo "You will be asked a few questions."
echo

python reddit_thread_finder.py

echo
read -p "Search complete. Press Enter to close..."
