#!/usr/bin/env python3
"""
Voice Dependencies Installation Script
Helps install PyAudio and other voice-related packages
"""

import subprocess
import sys
import platform

def run_command(command, description):
    """Run a pip command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("⚠️  WARNING: You don't appear to be in a virtual environment!")
        print("It's recommended to activate your virtual environment first:")
        if platform.system() == "Windows":
            print("   .\\venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    else:
        print("✅ Virtual environment detected")
    return True

def install_pyaudio_windows():
    """Try to install PyAudio on Windows with multiple methods"""
    print("\n🎤 Installing PyAudio for Windows...")
    
    methods = [
        ("pip install pyaudio", "Standard pip install"),
        ("pip install pipwin && pipwin install pyaudio", "Using pipwin (Windows wheel repository)"),
    ]
    
    for command, description in methods:
        if run_command(command, description):
            return True
    
    print("\n❌ Automatic installation failed. Manual installation required:")
    print("1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print("2. Download the .whl file matching your Python version")
    print("3. Install with: pip install path/to/downloaded/file.whl")
    return False

def install_voice_dependencies():
    """Install all voice dependencies"""
    print("🚀 Installing Voice Dependencies for JARVIS...")
    print("=" * 50)
    
    if not check_virtual_environment():
        return False
    
    # Install basic packages first
    packages = [
        ("SpeechRecognition", "Speech Recognition library"),
        ("pyttsx3", "Text-to-Speech library"),
    ]
    
    for package, description in packages:
        if not run_command(f"pip install {package}", f"Installing {description}"):
            print(f"Failed to install {package}")
            return False
    
    # Handle PyAudio installation
    if platform.system() == "Windows":
        if not install_pyaudio_windows():
            return False
    else:
        if not run_command("pip install pyaudio", "Installing PyAudio"):
            print("PyAudio installation failed. You may need to install system dependencies.")
            print("Ubuntu/Debian: sudo apt-get install python3-pyaudio")
            print("macOS: brew install portaudio")
            return False
    
    print("\n🎉 Voice dependencies installation completed!")
    print("You can now restart JARVIS GUI to use voice features.")
    return True

def test_voice_libraries():
    """Test if voice libraries can be imported"""
    print("\n🧪 Testing voice libraries...")
    
    try:
        import speech_recognition as sr
        print("✅ SpeechRecognition imported successfully")
    except ImportError as e:
        print(f"❌ SpeechRecognition import failed: {e}")
        return False
    
    try:
        import pyttsx3
        print("✅ pyttsx3 imported successfully")
    except ImportError as e:
        print(f"❌ pyttsx3 import failed: {e}")
        return False
    
    try:
        import pyaudio
        print("✅ PyAudio imported successfully")
    except ImportError as e:
        print(f"❌ PyAudio import failed: {e}")
        return False
    
    print("✅ All voice libraries are working!")
    return True

def main():
    """Main installation routine"""
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            # Just test the libraries
            return 0 if test_voice_libraries() else 1
        
        if install_voice_dependencies():
            print("\n🔍 Testing installation...")
            if test_voice_libraries():
                print("\n🎤 Voice features are ready to use!")
                return 0
            else:
                print("\n⚠️  Installation completed but some libraries may have issues.")
                return 1
        else:
            print("\n❌ Installation failed. Please check the error messages above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

