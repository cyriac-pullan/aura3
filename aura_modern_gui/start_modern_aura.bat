@echo off
title AURA Modern GUI - Advanced Neural Network Interface
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     █████╗ ██╗   ██╗██████╗  █████╗                         ║
echo ║    ██╔══██╗██║   ██║██╔══██╗██╔══██╗                        ║
echo ║    ███████║██║   ██║██████╔╝███████║                        ║
echo ║    ██╔══██║██║   ██║██╔══██╗██╔══██║                        ║
echo ║    ██║  ██║╚██████╔╝██║  ██║██║  ██║                        ║
echo ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                        ║
echo ║                                                              ║
echo ║         Advanced Neural Network Interface                   ║
echo ║         Modern GUI with Floating Voice Animation            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if running from the correct directory
if not exist "%~dp0server.py" (
    echo Error: Cannot find server.py
    echo Please run this from the aura_modern_gui directory.
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist "%~dp0..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%~dp0..\venv\Scripts\activate.bat"
)

REM Check for aiohttp
python -c "import aiohttp" 2>nul
if errorlevel 1 (
    echo.
    echo Installing required packages...
    pip install aiohttp
    echo.
)

REM Start the server
echo Starting AURA Modern GUI Server...
echo.
python "%~dp0server.py"

pause
