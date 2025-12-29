@echo off
title AI Assistant - CORTANA (Virtual Environment)
color 0B
mode con: cols=100 lines=30

echo.
echo     ╔══════════════════════════════════════════════════════════════════════════╗
echo     ║                          AI ASSISTANT CORTANA                           ║
echo     ║                            Ready to Assist                              ║
echo     ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo     [CORTANA] Hello! Initializing AI Assistant...
echo     [SYSTEM] Activating virtual environment...
timeout /t 1 /nobreak >nul
echo.

REM Change to the agent directory
cd /d "E:\agent\agent"

REM Activate the virtual environment
call "E:\agent\venv\Scripts\activate.bat"

REM Launch the assistant with the virtual environment Python
python assistant.py

echo.
echo     [CORTANA] Session ended. Have a great day!
timeout /t 2 /nobreak >nul
