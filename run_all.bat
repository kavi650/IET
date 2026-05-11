@echo off
title Testiny — Full Stack Launcher
color 0E
echo ==========================================
echo   TESTINY FULL STACK LAUNCHER
echo ==========================================
echo   [1] Main App      → http://localhost:5000
echo   [2] Testing App   → http://localhost:8501
echo   [3] Ollama AI     → http://localhost:11434
echo ==========================================
echo.
cd /d "%~dp0"

REM Activate venv if present
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

REM Run migration
echo [1/3] Running v3 migration check...
python migrate_v3.py
echo.

REM Start Ollama in background (if installed)
echo [2/3] Starting Ollama AI...
start "Ollama AI" cmd /c "ollama serve"
timeout /t 2 /nobreak >nul

REM Start testing app in new window
echo [3/3] Starting Testing Software on :8501...
start "Testiny Testing" cmd /k "python -m testing_app.app"
timeout /t 2 /nobreak >nul

REM Start main app in this window
echo.
echo [OK] All services starting...
echo      Main App:     http://localhost:5000
echo      Testing App:  http://localhost:8501
echo      Admin Panel:  http://localhost:5000/admin
echo      AI:           http://localhost:11434
echo.
python app.py
pause
