@echo off
REM Install Face Biometric System as Windows Service
REM Requires: NSSM (Non-Sucking Service Manager)
REM Download from: https://nssm.cc/download

echo ========================================
echo   Install Face Biometric System Service
echo ========================================
echo.

set "NSSM_PATH=%~dp0nssm.exe"
set "PYTHON_PATH=%~dp0venv\Scripts\python.exe"
set "SCRIPT_PATH=%~dp0launcher.py"
set "SERVICE_NAME=FaceBiometricSystem"

REM Check if NSSM exists
if not exist "%NSSM_PATH%" (
    echo ERROR: nssm.exe not found in current directory
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to this folder and run this script again.
    echo.
    pause
    exit /b 1
)

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo WARNING: Virtual environment Python not found
    echo Trying system Python...
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found
        pause
        exit /b 1
    )
    set "PYTHON_PATH=python"
)

echo Installing service...
echo Service Name: %SERVICE_NAME%
echo Python Path: %PYTHON_PATH%
echo Script Path: %SCRIPT_PATH%
echo.

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

REM Set service to start automatically
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Set working directory
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%~dp0"

echo.
echo ========================================
echo   Service installed successfully!
echo ========================================
echo.
echo To start the service:
echo   net start %SERVICE_NAME%
echo.
echo To stop the service:
echo   net stop %SERVICE_NAME%
echo.
echo To uninstall the service:
echo   "%NSSM_PATH%" remove %SERVICE_NAME% confirm
echo.
pause
