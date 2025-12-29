@echo off
title AURA - Neural Interface Widget
echo.
echo     ╔═══════════════════════════════════════╗
echo     ║           A U R A                     ║
echo     ║   Neural Interface Activating...      ║
echo     ╚═══════════════════════════════════════╝
echo.

REM Activate virtual environment
if exist "%~dp0..\venv\Scripts\activate.bat" (
    call "%~dp0..\venv\Scripts\activate.bat"
)

REM Check for PyQt5
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo Installing PyQt5...
    pip install PyQt5
    echo.
)

REM Start the widget
echo Starting AURA floating widget...
pythonw "%~dp0aura_widget.py"
