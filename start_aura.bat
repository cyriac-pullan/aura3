@echo off
title AURA Neural Network Interface
color 0F

echo.
echo     ██████╗ ██╗   ██╗██████╗  █████╗ 
echo    ██╔═══██╗██║   ██║██╔══██╗██╔══██╗
echo    ██║   ██║██║   ██║██████╔╝███████║
echo    ██║   ██║██║   ██║██╔══██╗██╔══██║
echo    ╚██████╔╝╚██████╔╝██║  ██║██║  ██║
echo     ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
echo.
echo                    NEURAL NETWORK INTERFACE
echo.
echo 🚀 Initializing AURA Neural Networks...
echo 📢 Voice neural processing available (SpeechRecognition, pyttsx3, pyaudio required)
echo.

REM Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment detected
    echo 🔄 Activating neural environment...
    call venv\Scripts\activate.bat
    
    echo 🎯 Launching AURA Neural Interface...
    python aura_gui.py
) else (
    echo ⚠️  Virtual environment not found
    echo 🔄 Attempting direct neural launch...
    python aura_gui.py
)

echo.
echo 👋 AURA neural networks deactivated
pause

