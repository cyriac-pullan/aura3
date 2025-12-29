#!/usr/bin/env python3
"""
Desktop AI Assistant Setup
Creates a professional desktop launcher for your AI assistant
"""

import os
import sys
import subprocess
from pathlib import Path

def create_desktop_launcher():
    """Create a professional desktop launcher"""
    
    # Get paths
    desktop = Path.home() / "Desktop"
    current_dir = Path(__file__).parent.absolute()
    
    # Create the main launcher batch file
    launcher_content = f'''@echo off
title AI Assistant - CORTANA Interface
color 0B
mode con: cols=100 lines=30

echo.
echo     ╔══════════════════════════════════════════════════════════════════════════╗
echo     ║                          AI ASSISTANT INTERFACE                         ║
echo     ║                              CORTANA v2.0                               ║
echo     ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo     [SYSTEM] Initializing AI Assistant...
timeout /t 1 /nobreak >nul
echo     [CORTANA] Hello! I'm ready to assist you.
echo.

cd /d "{current_dir}"
python assistant.py

echo.
echo     [CORTANA] Session ended. Have a great day!
timeout /t 2 /nobreak >nul
'''
    
    # Save launcher
    launcher_path = desktop / "AI Assistant.bat"
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print(f"✅ Desktop launcher created: {launcher_path}")
    
    # Create PowerShell script to add custom icon
    icon_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop / 'AI Assistant.lnk'}")
$Shortcut.TargetPath = "{launcher_path}"
$Shortcut.WorkingDirectory = "{current_dir}"
$Shortcut.Description = "AI Assistant - Your Personal Digital Assistant"
$Shortcut.IconLocation = "C:\\Windows\\System32\\shell32.dll,44"
$Shortcut.Save()
'''
    
    # Execute PowerShell to create shortcut with icon
    try:
        subprocess.run(["powershell", "-Command", icon_script], 
                      capture_output=True, text=True, check=True)
        print("✅ Desktop shortcut with custom icon created!")
        
        # Clean up the .bat file since we have the .lnk now
        if launcher_path.exists():
            launcher_path.unlink()
            
    except subprocess.CalledProcessError:
        print("⚠️ Using batch file launcher (PowerShell shortcut failed)")
    
    return True

def create_enhanced_assistant():
    """Create enhanced assistant with better interface"""
    
    enhanced_content = '''#!/usr/bin/env python3
"""
Enhanced AI Assistant with Cortana-style interface
"""

import os
import sys
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_interface():
    """Setup the enhanced interface"""
    if os.name == 'nt':
        os.system('title AI Assistant - CORTANA Interface')
        os.system('color 0B')
        os.system('mode con: cols=100 lines=30')

def show_welcome():
    """Show welcome message"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    elif 17 <= current_hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    
    print()
    print("     ╔══════════════════════════════════════════════════════════════════════════╗")
    print("     ║                          AI ASSISTANT INTERFACE                         ║")
    print("     ║                              CORTANA v2.0                               ║")
    print("     ╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"     [CORTANA] {greeting}! I'm your AI assistant.")
    print("     [CORTANA] I can help you with system tasks, automation, and more.")
    print()
    print("     ──────────────────────────────────────────────────────────────────────────")
    print()

def main():
    """Main enhanced assistant"""
    try:
        setup_interface()
        show_welcome()
        
        # Import and run the original assistant
        from assistant import main as original_main
        original_main()
        
    except KeyboardInterrupt:
        print("\\n     [CORTANA] Goodbye! Have a great day!")
    except Exception as e:
        print(f"     [ERROR] {e}")
        input("     Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    # Save enhanced assistant
    enhanced_path = Path(__file__).parent / "cortana_assistant.py"
    with open(enhanced_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"✅ Enhanced assistant created: {enhanced_path}")
    return True

def main():
    """Setup everything"""
    print("🤖 Setting up your Desktop AI Assistant...")
    print()
    
    try:
        # Create enhanced assistant
        create_enhanced_assistant()
        
        # Create desktop launcher
        create_desktop_launcher()
        
        print()
        print("🎉 Setup Complete!")
        print()
        print("✅ Your AI Assistant is now ready!")
        print("✅ Look for 'AI Assistant.lnk' on your desktop")
        print("✅ Double-click to launch your personal AI assistant")
        print()
        print("🚀 Features:")
        print("   • Professional Cortana-style interface")
        print("   • Custom desktop icon")
        print("   • Enhanced visual styling")
        print("   • One-click launch")
        print()
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
