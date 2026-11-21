@echo off
title Clipper AI - Viral Video Clipper
cd /d "%~dp0"

echo ==============================================================================
echo                      Starting Clipper AI Platform
echo ==============================================================================

:: Check if virtualenv exists
if exist ".venv\Scripts\python.exe" (
    echo [+] Using Python virtual environment...
    ".venv\Scripts\python.exe" run.py
) else (
    echo [+] Using system Python...
    python run.py
)

pause
