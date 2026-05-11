@echo off
title Testiny — Main App (Port 5000)
color 0A
echo ==========================================
echo   TESTINY EQUIPMENTS — Main Platform
echo   http://localhost:5000
echo ==========================================
echo.
cd /d "%~dp0"

REM Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
)

REM Run migration on first launch (safe - skips existing tables)
echo [..] Checking database schema...
python migrate_v3.py
echo.
echo [..] Starting main Flask app...
echo.
python app.py
pause
