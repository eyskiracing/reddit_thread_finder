@echo off
setlocal
cd /d "%~dp0"

echo Setting up Reddit Thread Finder...
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Please install Python and run this setup again.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example.
  echo Please open .env and add your Reddit API credentials before running a search.
) else (
  echo .env already exists.
)

python -m venv .venv
call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Running tests...
python -m unittest discover -s tests

echo.
echo Setup complete.
echo Next: open .env, add your Reddit API credentials, then run run_windows.bat
echo.
pause
