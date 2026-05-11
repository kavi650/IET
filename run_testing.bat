@echo off
title Testiny — Testing Software (Port 8501)
color 0B
echo ==========================================
echo   TESTINY — Industrial Testing Software
echo   http://localhost:8501
echo ==========================================
echo.
cd /d "%~dp0"

REM Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
)

echo [..] Starting Testing Software...
echo.
python -m testing_app.app
pause
