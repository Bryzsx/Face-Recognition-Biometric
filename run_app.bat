@echo off
title Face Biometric System
echo ========================================
echo   Face Biometric System
echo ========================================
echo.
echo Starting application...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found
    echo Running with system Python...
)

REM Run the launcher
echo.
echo Launching application...
python launcher.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application encountered an error.
    pause
)
