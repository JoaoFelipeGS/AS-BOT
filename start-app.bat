@echo off
REM Start the full AS Marketplace Bot SaaS stack on Windows.
REM Usage: double-click this file or run it from the project root.

cd /d %~dp0

REM Create virtual environment if missing
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)

REM Activate virtual environment and install dependencies
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pydantic-settings
pip install playwright
npx playwright install chromium

REM Start backend and frontend in separate windows
start "AS Marketplace Backend" cmd /k ".venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
start "AS Marketplace Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:4173
echo.
echo Press any key to exit this launcher window...
pause >nul
