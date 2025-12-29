#!/usr/bin/env python3
"""
Advanced Desktop AI Assistant with Custom Icon
"""

import os
import subprocess

def create_advanced_shortcut():
    """Create advanced shortcut with custom icon"""
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    batch_file = os.path.join(desktop, "AI Assistant.bat")
    
    # PowerShell script to create .lnk shortcut with custom icon
    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\🤖 AI Assistant.lnk")
$Shortcut.TargetPath = "{batch_file}"
$Shortcut.WorkingDirectory = "{current_dir}"
$Shortcut.Description = "AI Assistant - Your Personal Digital Assistant (Cortana Style)"
$Shortcut.IconLocation = "C:\\Windows\\System32\\shell32.dll,44"
$Shortcut.Save()

Write-Host "✅ Advanced shortcut created with custom icon!"
'''
    
    try:
        result = subprocess.run(["powershell", "-Command", ps_script], 
                              capture_output=True, text=True, check=True)
        
        print("🎉 Advanced Desktop AI Assistant Created!")
        print()
        print("✅ You now have TWO ways to launch your AI:")
        print("   1. 🤖 AI Assistant.lnk (with custom robot icon)")
        print("   2. AI Assistant.bat (simple batch file)")
        print()
        print("🚀 Double-click either one on your desktop!")
        print()
        print("✨ The .lnk version has:")
        print("   • Custom robot icon 🤖")
        print("   • Professional appearance")
        print("   • Windows integration")
        print("   • Tooltip description")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ PowerShell shortcut creation failed: {e}")
        print("💡 But you still have the working AI Assistant.bat file!")
        return False

if __name__ == "__main__":
    print("🚀 Creating Advanced Desktop AI Assistant...")
    print()
    create_advanced_shortcut()
