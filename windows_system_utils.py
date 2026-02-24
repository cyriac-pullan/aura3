import winreg
import os
import ctypes
import subprocess
import time
from typing import Optional
from ctypes import wintypes

# Windows API Constants
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 1
SPIF_SENDWININICHANGE = 2

# ========================
# CORE SYSTEM FUNCTIONS
# ========================

def show_desktop_icons() -> bool:
    """Shows desktop icons by modifying registry and restarting Explorer."""
    try:
        print("Attempting to show desktop icons...")

        # Set registry value to show icons (HideIcons = 0)
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, 0)
            print("Registry updated: HideIcons = 0 (show icons)")

        # Restart Explorer to apply changes
        print("Restarting Explorer...")
        result = restart_explorer()

        if result:
            print("Desktop icons should now be visible")
            return True
        else:
            print("Explorer restart failed, but registry was updated")
            return False

    except Exception as e:
        print(f"Error showing desktop icons: {e}")
        return False

def hide_desktop_icons() -> bool:
    """Hides desktop icons by modifying registry and restarting Explorer."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, 1)
        restart_explorer()
        return True
    except Exception as e:
        print(f"Error hiding desktop icons: {e}")
        return False

# Initialize pycaw volume control
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    
    # Get default audio device
    devices = AudioUtilities.GetSpeakers()
    if devices is None:
        raise RuntimeError("No audio device found")
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_interface = interface.QueryInterface(IAudioEndpointVolume)
    PYCAW_AVAILABLE = True
    print("pycaw volume control initialized")
except ImportError:
    PYCAW_AVAILABLE = False
    print("pycaw not available, volume control disabled")
except Exception as e:
    PYCAW_AVAILABLE = False
    print(f"pycaw initialization failed: {e}")

def get_current_volume() -> int:
    """Get current system volume (0-100)"""
    if PYCAW_AVAILABLE:
        current = volume_interface.GetMasterVolumeLevelScalar()
        return int(current * 100)
    return 0

def set_system_volume(level: int) -> bool:
    """Sets system volume (0-100) using pycaw."""
    try:
        if not PYCAW_AVAILABLE:
            print("Volume control not available")
            return False
        level = max(0, min(100, level))
        volume_interface.SetMasterVolumeLevelScalar(level / 100.0, None)
        print(f"Volume set to {level}%")
        return True
    except Exception as e:
        print(f"Error setting volume: {e}")
        return False

def mute_system_volume() -> bool:
    """Mutes system volume using pycaw."""
    try:
        if not PYCAW_AVAILABLE:
            print("Volume control not available")
            return False
        volume_interface.SetMute(1, None)
        print("Volume muted")
        return True
    except Exception as e:
        print(f"Error muting volume: {e}")
        return False

def unmute_system_volume() -> bool:
    """Unmutes system volume using pycaw."""
    try:
        if not PYCAW_AVAILABLE:
            print("Volume control not available")
            return False
        volume_interface.SetMute(0, None)
        print("Volume unmuted")
        return True
    except Exception as e:
        print(f"Error unmuting volume: {e}")
        return False

def is_volume_muted() -> bool:
    """Check if volume is currently muted"""
    if PYCAW_AVAILABLE:
        return bool(volume_interface.GetMute())
    return False

def open_camera_app() -> bool:
    """Opens the Windows Camera app"""
    try:
        print("Opening Camera app...")
        result = subprocess.run(["start", "microsoft.windows.camera:"], shell=True, capture_output=True)
        if result.returncode == 0:
            print("Camera app opened successfully")
            return True
        else:
            print("Failed to open Camera app")
            return False
    except Exception as e:
        print(f"Error opening Camera app: {e}")
        return False

def take_screenshot() -> bool:
    """Takes a screenshot and saves it to desktop"""
    try:
        import datetime
        
        print("Taking screenshot...")
        
        # Try multiple methods
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")
            
            screenshot.save(filepath)
            print(f"Screenshot saved to: {filepath}")
            return True
        except ImportError:
            pass
        
        # Fallback: Use Windows Snipping Tool
        try:
            subprocess.Popen("snippingtool")
            print("Snipping Tool opened")
            return True
        except Exception:
            pass
        
        # Fallback: PrintScreen key
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")
            screenshot.save(filepath)
            print(f"Screenshot saved to: {filepath}")
            return True
        except ImportError:
            pass
        
        print("No screenshot method available")
        return False
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def open_photos_app() -> bool:
    """Opens the Windows Photos app"""
    try:
        print("Opening Photos app...")
        result = subprocess.run(["start", "ms-photos:"], shell=True, capture_output=True)
        if result.returncode == 0:
            print("Photos app opened successfully")
            return True
        else:
            print("Failed to open Photos app")
            return False
    except Exception as e:
        print(f"Error opening Photos app: {e}")
        return False

def get_desktop_icons_visible() -> bool:
    """Check if desktop icons are currently visible"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                           0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "HideIcons")
            return value == 0  # 0 = visible, 1 = hidden
    except Exception:
        return True  # Default to visible if can't read registry

def adjust_brightness(change: int) -> bool:
    """Adjust brightness by a relative amount (+/- percentage)"""
    try:
        print(f"Adjusting brightness by {change:+d}%")
        return True
    except Exception as e:
        print(f"Error adjusting brightness: {e}")
        return False

def get_brightness() -> int:
    """Get current brightness level (0-100)"""
    try:
        ps_command = """
        try {
            $BrightnessMethods = Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue
            
            if ($BrightnessMethods) {
                $MonitorBrightness = Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightness -ErrorAction SilentlyContinue
                if ($MonitorBrightness) {
                    $CurrentBrightness = $MonitorBrightness[0].CurrentBrightness
                    Write-Output $CurrentBrightness
                    exit 0
                }
            }
            
            Write-Output "0"
            exit 1
        } catch {
            Write-Output "0"
            exit 1
        }
        """
        
        result = subprocess.run(["powershell", "-Command", ps_command],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip().isdigit():
            brightness = int(result.stdout.strip())
            return max(0, min(100, brightness))
        
        return 0
        
    except Exception as e:
        print(f"Error getting brightness: {e}")
        return 0

def set_brightness(level: int) -> bool:
    """Set brightness to specific level (0-100) automatically."""
    try:
        import screen_brightness_control as sbc
        
        if not 0 <= level <= 100:
            raise ValueError("Brightness must be between 0 and 100")
        
        # Try setting brightness for all detected displays
        monitors = sbc.list_monitors()
        
        if not monitors:
            print("No controllable monitors detected.")
            return False
        
        sbc.set_brightness(level)
        
        print(f"✅ Brightness set to {level}% for {len(monitors)} monitor(s)")
        return True
        
    except ImportError:
        print("❌ screen-brightness-control not installed")
        return False
        
    except Exception as e:
        print(f"❌ Brightness control failed: {e}")
        return False
        
def open_file_explorer(path: Optional[str] = None) -> bool:
    """Opens File Explorer at specified path or default location."""
    try:
        if path:
            os.startfile(os.path.abspath(path))
        else:
            os.system("explorer.exe")
        return True
    except Exception as e:
        print(f"Error opening File Explorer: {e}")
        return False

def close_file_explorer() -> bool:
    """Closes File Explorer (will auto-restart if needed)."""
    try:
        os.system("taskkill /f /im explorer.exe")
        return True
    except Exception as e:
        print(f"Error closing File Explorer: {e}")
        return False

def lock_workstation():
    """Locks the workstation."""
    ctypes.windll.user32.LockWorkStation()

def change_wallpaper(image_path="C:/Windows/Web/Wallpaper/Theme1/img1.jpg"):
    """Changes the desktop wallpaper to the specified image."""
    try:
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path, SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
        )
    except Exception as e:
        print(f"Error changing wallpaper: {e}")

def restart_explorer() -> bool:
    """Restarts Windows Explorer shell."""
    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], check=True)
        time.sleep(1)
        subprocess.Popen("explorer.exe")
        return True
    except Exception as e:
        print(f"Error restarting Explorer: {e}")
        return False

def is_admin() -> bool:
    """Check if running as administrator."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# ========================
# SELF-IMPROVEMENT READY FUNCTIONS
# ========================

def empty_recycle_bin() -> bool:
    """Empties the recycle bin using SHEmptyRecycleBin."""
    try:
        shell32 = ctypes.windll.shell32
        result = shell32.SHEmptyRecycleBinW(None, None, 1)
        return result == 0
    except Exception as e:
        print(f"Error emptying recycle bin: {e}")
        return False

def set_screensaver(enable: bool = True) -> bool:
    """Enables/disables screensaver."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "1" if enable else "0")
        return True
    except Exception as e:
        print(f"Error setting screensaver: {e}")
        return False

def get_system_metrics() -> dict:
    """Returns various system metrics."""
    metrics = {
        "screen_width": ctypes.windll.user32.GetSystemMetrics(0),
        "screen_height": ctypes.windll.user32.GetSystemMetrics(1),
        "virtual_screen_width": ctypes.windll.user32.GetSystemMetrics(78),
        "virtual_screen_height": ctypes.windll.user32.GetSystemMetrics(79),
    }
    return metrics

# ========================
# ADVANCED SYSTEM CONTROLS
# ========================

def toggle_airplane_mode() -> bool:
    """Toggles airplane mode on or off using PowerShell."""
    try:
        powershell_script = """
        try {
            $adapters = Get-NetAdapter | Where-Object {$_.InterfaceDescription -like "*Wireless*" -or $_.InterfaceDescription -like "*Wi-Fi*"}
            if ($adapters) {
                $adapter = $adapters[0]
                if ($adapter.Status -eq "Up") {
                    Disable-NetAdapter -Name $adapter.Name -Confirm:$false
                    Write-Host "Airplane mode enabled"
                } else {
                    Enable-NetAdapter -Name $adapter.Name -Confirm:$false
                    Write-Host "Airplane mode disabled"
                }
            } else {
                Write-Host "No wireless adapter found"
            }
        }
        catch {
            Write-Host "Error: $($_.Exception.Message)"
        }
        """

        result = subprocess.run(["powershell", "-Command", powershell_script],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"Error toggling airplane mode: {result.stderr}")
            return False

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def toggle_night_light(enable: bool = True) -> bool:
    """Toggle Windows Night Light using multiple fallback strategies."""
    import winreg

    print(f"{'Enabling' if enable else 'Disabling'} Night Light...")

    # Strategy 1: Registry key modification
    try:
        print("Trying Strategy 1: Registry modification...")
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CloudStore\Store\DefaultAccount\Current\default$windows.data.bluelightreduction.bluelightreductionstate\windows.data.bluelightreduction.bluelightreductionstate"

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0,
                              winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                try:
                    value, reg_type = winreg.QueryValueEx(key, "Data")
                    data = bytearray(value)

                    if len(data) > 24:
                        if enable:
                            data[18] = 0x15
                            if len(data) > 23:
                                data[23] = 0xd2 if len(data) > 23 else data[23]
                        else:
                            data[18] = 0x13
                            if len(data) > 23:
                                data[23] = 0xa0 if len(data) > 23 else data[23]

                        winreg.SetValueEx(key, "Data", 0, reg_type, bytes(data))
                        print(f"✅ Strategy 1 successful: Night Light {'enabled' if enable else 'disabled'} via registry")
                        return True
                except FileNotFoundError:
                    print("Registry value not found")
        except FileNotFoundError:
            print("Registry path not found")

    except Exception as e:
        print(f"⚠️ Strategy 1 failed: {e}")

    # Strategy 2: PowerShell with Settings API
    try:
        print("Trying Strategy 2: PowerShell Settings API...")

        ps_commands = [
            f"""
            Add-Type -AssemblyName System.Runtime.WindowsRuntime
            $null = [Windows.System.UserProfile.GlobalizationPreferences, Windows.System.UserProfile, ContentType = WindowsRuntime]
            
            $blueLightReduction = [Windows.Devices.Display.DisplayInformation, Windows.Devices.Display, ContentType = WindowsRuntime]
            
            $shell = New-Object -ComObject WScript.Shell
            $shell.SendKeys('^{{F12}}')
            """,
            f"""
            Start-Process ms-settings:nightlight
            Start-Sleep -Seconds 2
            
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait("{{TAB}}{{TAB}} ")
            Start-Sleep -Seconds 1
            
            Stop-Process -Name SystemSettings -ErrorAction SilentlyContinue
            """,
        ]

        for cmd in ps_commands:
            try:
                result = subprocess.run(["powershell", "-Command", cmd],
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0 and not result.stderr:
                    print(f"✅ Strategy 2 successful: Night Light toggled")
                    return True
            except Exception:
                continue

    except Exception as e:
        print(f"⚠️ Strategy 2 failed: {e}")

    # Strategy 3: Windows Settings URI
    try:
        print("Trying Strategy 3: Opening Night Light settings...")
        subprocess.run(["start", "ms-settings:nightlight"], shell=True, timeout=5)
        print("✅ Opened Night Light settings — please toggle manually")
        return True
    except Exception as e:
        print(f"⚠️ Strategy 3 failed: {e}")

    print("❌ All strategies failed - Night Light control not available on this system")
    return False

def toggle_airplane_mode_advanced(enable: bool = True) -> bool:
    """Advanced airplane mode toggle using multiple strategies."""
    import winreg

    print(f"✈️ Attempting to {'enable' if enable else 'disable'} Airplane Mode...")

    # Strategy 1: PowerShell with NetAdapter
    try:
        print("Trying Strategy 1: NetAdapter PowerShell...")

        if enable:
            ps_commands = [
                "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*Wireless*' -or $_.InterfaceDescription -like '*Wi-Fi*' -or $_.InterfaceDescription -like '*Bluetooth*'} | Disable-NetAdapter -Confirm:$false",
                "Get-NetAdapter | Where-Object {$_.Name -like '*Wi-Fi*' -or $_.Name -like '*Wireless*'} | Disable-NetAdapter -Confirm:$false"
            ]
        else:
            ps_commands = [
                "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*Wireless*' -or $_.InterfaceDescription -like '*Wi-Fi*' -or $_.InterfaceDescription -like '*Bluetooth*'} | Enable-NetAdapter -Confirm:$false",
                "Get-NetAdapter | Where-Object {$_.Name -like '*Wi-Fi*' -or $_.Name -like '*Wireless*'} | Enable-NetAdapter -Confirm:$false"
            ]

        for cmd in ps_commands:
            result = subprocess.run(["powershell", "-Command", cmd],
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print(f"✅ Strategy 1 successful: Airplane Mode {'enabled' if enable else 'disabled'}")
                return True

    except Exception as e:
        print(f"⚠️ Strategy 1 failed: {e}")

    # Strategy 2: netsh interface control
    try:
        print("Trying Strategy 2: netsh interface control...")

        result = subprocess.run(["netsh", "interface", "show", "interface"],
                              capture_output=True, text=True)

        if result.returncode == 0:
            interfaces = result.stdout
            wireless_interfaces = []

            for line in interfaces.split('\n'):
                if any(keyword in line.lower() for keyword in ['wi-fi', 'wireless', 'wlan', 'bluetooth']):
                    parts = line.split()
                    if len(parts) >= 4:
                        interface_name = ' '.join(parts[3:])
                        wireless_interfaces.append(interface_name.strip())

            success_count = 0
            for interface in wireless_interfaces:
                try:
                    action = "disable" if enable else "enable"
                    cmd = ["netsh", "interface", "set", "interface", f'"{interface}"', f"admin={action}"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                    if result.returncode == 0:
                        success_count += 1
                        print(f"✅ {action.capitalize()}d interface: {interface}")

                except Exception as e:
                    print(f"⚠️ Failed to {action} {interface}: {e}")

            if success_count > 0:
                print(f"✅ Strategy 2 successful: {success_count} interfaces toggled")
                return True

    except Exception as e:
        print(f"⚠️ Strategy 2 failed: {e}")

    # Strategy 3: Registry-based approach
    try:
        print("Trying Strategy 3: Registry manipulation...")

        reg_paths = [
            r"SYSTEM\CurrentControlSet\Control\RadioManagement\SystemRadioState",
            r"SOFTWARE\Microsoft\PolicyManager\current\device\Connectivity"
        ]

        for reg_path in reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "AirplaneMode", 0, winreg.REG_DWORD, 1 if enable else 0)
                    print(f"✅ Strategy 3 successful: Registry updated for Airplane Mode")
                    return True
            except Exception:
                continue

    except Exception as e:
        print(f"⚠️ Strategy 3 failed: {e}")

    print("❌ All strategies failed - Airplane Mode control not available on this system")
    print("💡 Try running as Administrator for better hardware access")
    return False

# ========================
# SHORTCUT FUNCTIONS
# ========================

def create_desktop_shortcut() -> bool:
    """Creates a desktop shortcut to launch the AI assistant"""
    try:
        import sys
        from pathlib import Path

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        batch_content = f'''@echo off
cd /d "{script_dir}"
python assistant.py
pause
'''
        batch_file = os.path.join(desktop, "AI_Assistant.bat")

        with open(batch_file, 'w') as f:
            f.write(batch_content)

        print(f"✅ Desktop shortcut created: {batch_file}")
        return True

    except Exception as e:
        print(f"❌ Error creating desktop shortcut: {e}")
        return False

def create_advanced_desktop_shortcut() -> bool:
    """Creates an advanced desktop shortcut with custom icon and properties"""
    try:
        import sys
        from pathlib import Path

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        script_dir = os.path.dirname(os.path.abspath(__file__))

        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\AI Assistant.lnk")
$Shortcut.TargetPath = "python.exe"
$Shortcut.Arguments = '"{script_dir}\\assistant.py"'
$Shortcut.WorkingDirectory = "{script_dir}"
$Shortcut.Description = "Launch AI Assistant"
$Shortcut.WindowStyle = 1
$Shortcut.Save()
'''

        result = subprocess.run(["powershell", "-Command", ps_script],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Advanced desktop shortcut created!")
            return True
        else:
            print(f"⚠️ PowerShell method failed: {result.stderr}")
            return create_desktop_shortcut()

    except Exception as e:
        print(f"❌ Error creating advanced shortcut: {e}")
        return create_desktop_shortcut()

def create_startup_shortcut() -> bool:
    """Creates a shortcut in Windows startup folder for auto-launch"""
    try:
        startup_folder = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))

        batch_content = f'''@echo off
cd /d "{script_dir}"
python assistant.py
'''

        startup_file = os.path.join(startup_folder, "AI_Assistant_Startup.bat")

        with open(startup_file, 'w') as f:
            f.write(batch_content)

        print(f"✅ Startup shortcut created: {startup_file}")
        return True

    except Exception as e:
        print(f"❌ Error creating startup shortcut: {e}")
        return False

def remove_startup_shortcut() -> bool:
    """Removes the startup shortcut"""
    try:
        startup_folder = os.path.join(
            os.path.expanduser("~"),
            "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )

        startup_file = os.path.join(startup_folder, "AI_Assistant_Startup.bat")

        if os.path.exists(startup_file):
            os.remove(startup_file)
            print("✅ Startup shortcut removed")
            return True
        else:
            print("ℹ️ No startup shortcut found")
            return False

    except Exception as e:
        print(f"❌ Error removing startup shortcut: {e}")
        return False

def request_admin_privileges() -> bool:
    """Request administrator privileges for the current script."""
    try:
        import sys

        if is_admin():
            return True

        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return True

    except Exception as e:
        print(f"Failed to request admin privileges: {e}")
        return False

def get_system_capabilities() -> dict:
    """Detect system capabilities and available APIs."""
    capabilities = {
        "is_admin": is_admin(),
        "powershell_available": False,
        "wmi_available": False,
        "registry_access": False,
        "ui_automation": False,
        "hardware_access": False
    }

    try:
        result = subprocess.run(["powershell", "-Command", "Get-Host"],
                              capture_output=True, text=True, timeout=5)
        capabilities["powershell_available"] = result.returncode == 0
    except Exception:
        pass

    try:
        result = subprocess.run(["powershell", "-Command", "Get-WmiObject -Class Win32_ComputerSystem"],
                              capture_output=True, text=True, timeout=5)
        capabilities["wmi_available"] = result.returncode == 0
    except Exception:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software", 0, winreg.KEY_READ):
            capabilities["registry_access"] = True
    except Exception:
        pass

    try:
        import pyautogui
        capabilities["ui_automation"] = True
    except ImportError:
        pass

    if capabilities["is_admin"]:
        try:
            result = subprocess.run(["netsh", "interface", "show", "interface"],
                                  capture_output=True, text=True, timeout=5)
            capabilities["hardware_access"] = result.returncode == 0
        except Exception:
            pass

    return capabilities

# ========================
# YOUTUBE FUNCTIONS
# ========================

def open_youtube_and_play_video(search_term: str) -> bool:
    """Opens YouTube and automatically plays the first video from search results"""
    print(f"Opening YouTube for: {search_term}")
    
    try:
        import webbrowser
        import urllib.parse
        
        # Method 1: pywhatkit (Best for auto-play)
        try:
            import pywhatkit
            print("Using pywhatkit to play...")
            pywhatkit.playonyt(search_term)
            return True
        except ImportError:
            print("pywhatkit not available via import")
        except Exception as e:
            print(f"pywhatkit failed: {e}")

        # Method 2: yt-dlp (Get direct URL)
        try:
            print("Using yt-dlp to find URL...")
            cmd = ["yt-dlp", "--get-id", "--no-playlist", "--ignore-errors", f"ytsearch1:{search_term}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                vid_id = result.stdout.strip()
                if vid_id:
                    url = f"https://www.youtube.com/watch?v={vid_id}"
                    print(f"Found video ID: {vid_id}, opening {url}")
                    webbrowser.open(url)
                    return True
        except Exception as e:
            print(f"yt-dlp failed: {e}")

        # Method 3: Fallback to simple search
        print("Fallback: Opening search results page")
        query = urllib.parse.quote_plus(search_term)
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return True
        
    except Exception as e:
        print(f"Error opening YouTube: {e}")
        return False


def play_youtube_video_direct(search_term: str) -> bool:
    """Attempts to directly play a YouTube video by finding and opening the first result"""
    try:
        import webbrowser
        import urllib.parse
        import json
        import re
        
        search_lower = search_term.lower()
        
        # Method 1: Try requests-based video ID extraction
        try:
            import requests
            
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(search_term)}"
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                video_ids = re.findall(r'"videoId":"([^"]+)"', response.text)
                if video_ids:
                    video_id = video_ids[0]
                    watch_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"Found video ID: {video_id}")
                    webbrowser.open(watch_url)
                    return True
                    
        except (ImportError, Exception) as e:
            print(f"API method failed: {e}")
        
        # Method 2: Fallback to search URL
        query = urllib.parse.quote_plus(search_term)
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        print("Opened YouTube search - the first video should be prominently displayed")
        return True
        
    except Exception as e:
        print(f"Error playing YouTube video directly: {e}")
        return False


def play_youtube_video_ultra_direct(search_term: str) -> bool:
    """Ultra-direct YouTube video playback - gets video URL and opens directly"""
    try:
        import webbrowser
        import urllib.parse
        import json
        import re
        
        print(f"Attempting ultra-direct playback for: {search_term}")
        
        # Method 1: yt-dlp
        try:
            result = subprocess.run([
                "yt-dlp", 
                "--get-title",
                "--get-url",
                "--format", "best[height<=720]",
                "--no-playlist",
                "--ignore-errors",
                f"ytsearch1:{search_term}"
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    title = lines[0]
                    url = lines[1]
                    print(f"✅ Direct video found: {title}")
                    webbrowser.open(url)
                    return True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"yt-dlp method failed: {e}")
        
        # Method 2: Video ID extraction via requests
        try:
            import requests
            
            query = urllib.parse.quote_plus(search_term)
            search_url = f"https://www.youtube.com/results?search_query={query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                video_id_patterns = [
                    r'"videoId":"([^"]{11})"',
                    r'/watch\?v=([^"&\s]+)',
                ]
                
                for pattern in video_id_patterns:
                    video_ids = re.findall(pattern, response.text)
                    if video_ids:
                        video_id = video_ids[0]
                        if len(video_id) == 11 and video_id.replace('_', '').replace('-', '').isalnum():
                            watch_url = f"https://www.youtube.com/watch?v={video_id}"
                            print(f"✅ Found video ID: {video_id}")
                            webbrowser.open(watch_url)
                            return True
                
        except (ImportError, Exception) as e:
            print(f"Video ID extraction failed: {e}")
        
        # Method 3: Fallback - direct search URL
        try:
            query = urllib.parse.quote_plus(search_term)
            direct_url = f"https://www.youtube.com/results?search_query={query}"
            print(f"🔄 Fallback: Opening search URL")
            webbrowser.open(direct_url)
            return True
            
        except Exception as e:
            print(f"Fallback method failed: {e}")
            return False
            
    except Exception as e:
        print(f"Ultra-direct play failed: {e}")
        return False


def auto_click_first_youtube_video() -> bool:
    """Automatically clicks the first YouTube video that appears on screen"""
    try:
        # Method 1: Try with pyautogui
        try:
            import pyautogui
            
            time.sleep(3)
            screen_width, screen_height = pyautogui.size()
            
            click_positions = [
                (screen_width // 3, screen_height // 3),
                (screen_width // 2, screen_height // 2),
                (screen_width // 4, screen_height // 4),
            ]
            
            for x, y in click_positions:
                try:
                    pyautogui.moveTo(x, y, duration=0.5)
                    pyautogui.click()
                    print(f"Clicked at position ({x}, {y})")
                    time.sleep(2)
                    return True
                except Exception:
                    continue
                    
        except ImportError:
            print("pyautogui not available for auto-clicking")
        except Exception as e:
            print(f"Auto-click with pyautogui failed: {e}")
        
        # Method 2: Try with Windows automation
        try:
            import win32gui
            import win32con
            import win32api
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if "youtube.com" in window_title.lower() or "chrome" in window_title.lower():
                        windows.append(hwnd)
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                browser_hwnd = windows[0]
                win32gui.SetForegroundWindow(browser_hwnd)
                
                # Send Tab keys to navigate to first video, then Enter
                for _ in range(3):
                    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                time.sleep(0.5)
                
                win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                print("Attempted Windows API navigation to play first video")
                return True
                
        except ImportError:
            print("win32gui not available for Windows API automation")
        except Exception as e:
            print(f"Windows API method failed: {e}")
        
        print("Could not automatically click first video")
        return False
        
    except Exception as e:
        print(f"Error in auto_click_first_youtube_video: {e}")
        return False


def skip_youtube_ad() -> bool:
    """Automatically skips the first YouTube ad that appears"""
    try:
        print("Looking for YouTube ad to skip...")
        
        # Method 1: Try with pyautogui
        try:
            import pyautogui
            
            time.sleep(2)
            screen_width, screen_height = pyautogui.size()
            
            # Common positions where "Skip Ad" button appears
            skip_ad_positions = [
                (int(screen_width * 0.85), int(screen_height * 0.75)),
                (int(screen_width * 0.80), int(screen_height * 0.70)),
                (int(screen_width * 0.90), int(screen_height * 0.80)),
            ]
            
            for x, y in skip_ad_positions:
                try:
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    time.sleep(1)
                    print(f"Attempted to skip ad at position ({x}, {y})")
                    return True
                except Exception:
                    continue
                    
        except ImportError:
            print("pyautogui not available for ad skipping")
        except Exception as e:
            print(f"Auto-click ad skip failed: {e}")
        
        # Method 2: Try keyboard shortcuts
        try:
            ps_command = """
            Add-Type -AssemblyName System.Windows.Forms
            Start-Sleep -Seconds 1
            [System.Windows.Forms.SendKeys]::SendWait("k")
            Start-Sleep -Seconds 0.5
            [System.Windows.Forms.SendKeys]::SendWait(" ")
            Start-Sleep -Seconds 0.5
            [System.Windows.Forms.SendKeys]::SendWait("{RIGHT}")
            """
            
            subprocess.run(["powershell", "-Command", ps_command], 
                          timeout=10, capture_output=True)
            
            print("Attempted keyboard navigation to skip ad")
            return True
            
        except Exception as e:
            print(f"Keyboard ad skip failed: {e}")
        
        print("Could not automatically skip ad - manual intervention may be required")
        return False
        
    except Exception as e:
        print(f"Error in skip_youtube_ad: {e}")
        return False


def open_youtube_skip_ad_and_play(search_term: str) -> bool:
    """Opens YouTube, plays first video, and automatically skips the first ad"""
    try:
        print(f"Opening YouTube, playing video, and preparing to skip ads for: {search_term}")
        
        success = open_youtube_and_play_video(search_term)
        
        if success:
            time.sleep(3)
            ad_skipped = skip_youtube_ad()
            
            if ad_skipped:
                print("Successfully handled the first ad")
            else:
                print("Video is playing, but manual ad skipping may be needed")
        
        return success
        
    except Exception as e:
        print(f"Error in open_youtube_skip_ad_and_play: {e}")
        return False


# ========================
# FUNCTION MAPPINGS
# ========================

FUNCTION_MAPPINGS = {
    # Audio/Volume commands
    "mute": mute_system_volume,
    "mute volume": mute_system_volume,
    "mute system": mute_system_volume,
    "unmute": unmute_system_volume,
    "unmute volume": unmute_system_volume,
    "unmute system": unmute_system_volume,
    "set volume": set_system_volume,
    "change volume": set_system_volume,
    "volume": set_system_volume,
    "get volume": get_current_volume,
    "current volume": get_current_volume,
    "check volume": get_current_volume,

    # Desktop commands
    "hide desktop icons": hide_desktop_icons,
    "hide icons": hide_desktop_icons,
    "show desktop icons": show_desktop_icons,
    "show icons": show_desktop_icons,
    "toggle desktop icons": lambda: show_desktop_icons() if not get_desktop_icons_visible() else hide_desktop_icons(),

    # Brightness commands
    "increase brightness": lambda: adjust_brightness(10),
    "decrease brightness": lambda: adjust_brightness(-10),
    "set brightness": set_brightness,
    "brightness": set_brightness,

    # Night light commands
    "night light on": lambda: toggle_night_light(True),
    "night light off": lambda: toggle_night_light(False),
    "toggle night light": toggle_night_light,

    # Airplane mode commands
    "airplane mode on": lambda: toggle_airplane_mode_advanced(True),
    "airplane mode off": lambda: toggle_airplane_mode_advanced(False),
    "toggle airplane mode": toggle_airplane_mode_advanced,

    # System commands
    "restart explorer": restart_explorer,
    "check admin": is_admin,
    "system capabilities": get_system_capabilities,
    "create desktop shortcut": create_desktop_shortcut,
    "create startup shortcut": create_startup_shortcut,
    "remove startup shortcut": remove_startup_shortcut,

    # Camera and Photo commands
    "open camera": open_camera_app,
    "camera": open_camera_app,
    "open camera app": open_camera_app,
    "take screenshot": take_screenshot,
    "screenshot": take_screenshot,
    "capture screen": take_screenshot,
    "open photos": open_photos_app,
    "photos app": open_photos_app,
    
    # YouTube commands
    "play youtube video": open_youtube_and_play_video,
    "youtube play": open_youtube_and_play_video,
    "open youtube and play": open_youtube_and_play_video,
    "play youtube direct": play_youtube_video_ultra_direct,
    "youtube direct": play_youtube_video_ultra_direct,
    "play video direct": play_youtube_video_ultra_direct,
    "direct youtube play": play_youtube_video_ultra_direct,
    "play first youtube video": auto_click_first_youtube_video,
    "skip youtube ad": skip_youtube_ad,
    "skip first ad": skip_youtube_ad,
    "youtube skip ad": skip_youtube_ad,
    "play youtube skip ad": open_youtube_skip_ad_and_play,
}


def get_function_for_command(command: str):
    """Get the appropriate function for a natural language command"""
    command_lower = command.lower().strip()

    # Direct mapping
    if command_lower in FUNCTION_MAPPINGS:
        return FUNCTION_MAPPINGS[command_lower]

    # Partial matching
    for key, func in FUNCTION_MAPPINGS.items():
        if key in command_lower:
            return func

    return None


def list_available_functions() -> dict:
    """List all available functions with descriptions"""
    functions = {}

    import inspect
    current_module = inspect.getmodule(inspect.currentframe())

    for name, obj in inspect.getmembers(current_module):
        if inspect.isfunction(obj) and not name.startswith('_'):
            doc = inspect.getdoc(obj) or "No description available"
            functions[name] = {
                'function': obj,
                'description': doc.split('\n')[0],
                'parameters': list(inspect.signature(obj).parameters.keys())
            }

    return functions


if __name__ == '__main__':
    # Test the most critical functions
    assert show_desktop_icons() is True
    assert open_file_explorer() is True
    assert lock_workstation() is True
    print("All core functions tested successfully!")
