#!/usr/bin/env python3
"""
Simple Desktop AI Assistant Creator
"""

import os
import subprocess
from pathlib import Path

def create_desktop_ai():
    """Create desktop AI assistant"""
    
    # Get desktop path
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the launcher batch file
    batch_content = f'''@echo off
title AI Assistant - AURA
color 0B
mode con: cols=100 lines=30

echo.
echo     ╔══════════════════════════════════════════════════════════════════════════╗
echo     ║                          AI ASSISTANT AURA                              ║
echo     ║                            Ready to Assist                              ║
echo     ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo     [AURA] Hello! Initializing AI Assistant...
timeout /t 1 /nobreak >nul
echo.

cd /d "{current_dir}"
python aura_gui.py

echo.
echo     [AURA] Session ended. Have a great day!
timeout /t 2 /nobreak >nul
'''
    
    # Save to desktop
    batch_file = os.path.join(desktop, "AI Assistant.bat")
    
    try:
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ AI Assistant created on desktop!")
        print(f"📍 Location: {batch_file}")
        print()
        print("🚀 Double-click 'AI Assistant.bat' on your desktop to launch!")
        print()
        print("✨ Features:")
        print("   • Cortana-style interface")
        print("   • Professional blue-green styling")
        print("   • One-click desktop launch")
        print("   • Enhanced visual experience")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Creating your Desktop AI Assistant...")
    print()
    create_desktop_ai()
