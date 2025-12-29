#!/usr/bin/env python3
"""
Auto-Start Setup for AI Assistant
"""

import os
import subprocess

def setup_auto_start():
    """Setup AI Assistant to start with Windows"""
    
    # Get startup folder
    startup_folder = os.path.join(
        os.path.expanduser("~"), 
        "AppData", "Roaming", "Microsoft", "Windows", 
        "Start Menu", "Programs", "Startup"
    )
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create startup batch file
    startup_content = f'''@echo off
title AI Assistant - Auto Start
color 0B
mode con: cols=80 lines=20

echo [AURA] AI Assistant starting automatically...
timeout /t 2 /nobreak >nul

cd /d "{current_dir}"
python aura_gui.py
'''
    
    startup_file = os.path.join(startup_folder, "AI_Assistant_AutoStart.bat")
    
    try:
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        print("✅ Auto-start setup complete!")
        print(f"📍 Startup file: {startup_file}")
        print()
        print("🚀 Your AI Assistant will now launch automatically when Windows starts!")
        print()
        print("💡 To disable auto-start:")
        print(f"   Delete: {startup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto-start setup failed: {e}")
        return False

def remove_auto_start():
    """Remove auto-start"""
    startup_folder = os.path.join(
        os.path.expanduser("~"), 
        "AppData", "Roaming", "Microsoft", "Windows", 
        "Start Menu", "Programs", "Startup"
    )
    
    startup_file = os.path.join(startup_folder, "AI_Assistant_AutoStart.bat")
    
    try:
        if os.path.exists(startup_file):
            os.remove(startup_file)
            print("✅ Auto-start disabled!")
        else:
            print("ℹ️ Auto-start was not enabled")
        return True
    except Exception as e:
        print(f"❌ Failed to remove auto-start: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AI Assistant Auto-Start Setup")
    print()
    print("Choose an option:")
    print("1. Enable auto-start (launch with Windows)")
    print("2. Disable auto-start")
    print("3. Exit")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        setup_auto_start()
    elif choice == "2":
        remove_auto_start()
    else:
        print("👋 Goodbye!")
