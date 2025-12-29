#!/usr/bin/env python3
"""
Create Desktop Launcher for GUI Chatbot
"""

import os
import subprocess
from pathlib import Path

def create_gui_launcher():
    """Create desktop launcher for GUI chatbot"""
    
    # Get paths
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "OneDrive" / "Desktop"
    
    current_dir = Path(__file__).parent.absolute()
    
    # Create batch file launcher
    batch_content = f'''@echo off
title JARVIS AI Assistant - GUI
cd /d "{current_dir}"
call ..\\venv\\Scripts\\activate.bat
python gui_chatbot.py
pause
'''
    
    batch_file = desktop / "🤖 JARVIS AI Assistant.bat"
    
    try:
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ GUI launcher created: {batch_file}")
        
        # Create PowerShell script for advanced shortcut with icon
        icon_path = current_dir / "jarvis_icon.ico"
        icon_location = str(icon_path) if icon_path.exists() else "C:\\Windows\\System32\\shell32.dll,44"

        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop / '🤖 JARVIS AI Assistant.lnk'}")
$Shortcut.TargetPath = "{batch_file}"
$Shortcut.WorkingDirectory = "{current_dir}"
$Shortcut.Description = "JARVIS AI Assistant - Modern GUI Chatbot Interface"
$Shortcut.IconLocation = "{icon_location}"
$Shortcut.Save()

Write-Host "✅ Advanced shortcut created with custom icon!"
'''
        
        # Execute PowerShell to create shortcut with icon
        try:
            result = subprocess.run(["powershell", "-Command", ps_script], 
                                  capture_output=True, text=True, check=True)
            print("✅ Desktop shortcut with custom icon created!")
            
        except subprocess.CalledProcessError:
            print("⚠️ Using batch file launcher (PowerShell shortcut failed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating launcher: {e}")
        return False

def create_startup_launcher():
    """Create startup launcher for auto-start"""
    try:
        startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        current_dir = Path(__file__).parent.absolute()
        
        startup_content = f'''@echo off
title JARVIS AI Assistant - Auto Start
cd /d "{current_dir}"
call ..\\venv\\Scripts\\activate.bat
python gui_chatbot.py
'''
        
        startup_file = startup_folder / "JARVIS_AI_AutoStart.bat"
        
        with open(startup_file, 'w', encoding='utf-8') as f:
            f.write(startup_content)
        
        print(f"✅ Auto-start launcher created: {startup_file}")
        print("🚀 JARVIS will now launch automatically when Windows starts!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating startup launcher: {e}")
        return False

def main():
    """Main setup function"""
    print("🤖 Setting up JARVIS AI Assistant GUI Launcher...")
    print("=" * 50)
    
    # Create desktop launcher
    if create_gui_launcher():
        print("\n🎉 Desktop launcher setup complete!")
        print("\n📍 You can now launch JARVIS from your desktop:")
        print("   • Look for '🤖 JARVIS AI Assistant.lnk' on your desktop")
        print("   • Double-click to launch the modern GUI chatbot")
        
        # Ask about auto-start
        print("\n" + "=" * 50)
        choice = input("🚀 Would you like JARVIS to start automatically with Windows? (y/n): ").lower().strip()
        
        if choice in ['y', 'yes']:
            if create_startup_launcher():
                print("\n✅ Auto-start enabled!")
            else:
                print("\n❌ Auto-start setup failed")
        else:
            print("\n💡 You can enable auto-start later by running this script again")
        
        print("\n🎯 Setup Complete!")
        print("🤖 Your JARVIS AI Assistant GUI is ready to use!")
        
    else:
        print("\n❌ Setup failed!")

if __name__ == "__main__":
    main()
