@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv" (
  echo Virtual environment not found.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

if not exist ".env" (
  echo .env file not found.
  echo Run setup_windows.bat first, then add your Reddit API credentials to .env.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Starting Reddit Thread Finder...
echo You will be asked a few questions.
echo.

python reddit_thread_finder.py

echo.
pause
