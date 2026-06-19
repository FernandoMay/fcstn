@echo off
title FCSTN - Fractal Cognitive Space-Time Networks
color 0B

echo ============================================
echo    FCSTN - Fractal Cognitive Space-Time
echo           Networks Platform
echo ============================================
echo.
echo 1. Run Platform Demo
echo 2. Run Neurogaming Demo
echo 3. Start Web Dashboard
echo 4. Run Tests
echo 5. Open Presentation
echo 6. Run Everything
echo 7. Exit
echo.

set /p choice="Select option (1-7): "

if "%choice%"=="1" (
    python launch.py demo
    pause
    goto :eof
)
if "%choice%"=="2" (
    python launch.py neurogame
    pause
    goto :eof
)
if "%choice%"=="3" (
    start http://localhost:8000/dashboard
    python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
    pause
    goto :eof
)
if "%choice%"=="4" (
    python -m pytest -v --tb=short
    pause
    goto :eof
)
if "%choice%"=="5" (
    start docs\presentation.html
    pause
    goto :eof
)
if "%choice%"=="6" (
    python launch.py all
    pause
    goto :eof
)
if "%choice%"=="7" exit
goto :eof
