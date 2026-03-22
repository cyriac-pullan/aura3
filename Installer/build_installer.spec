# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Configuration for AURA v2 Floating Widget
Creates a standalone Windows executable with all dependencies bundled.

Updated: 2026-03-22 for AURA v2 (goal-driven architecture)
"""

import sys
import os

block_cipher = None

# Find Python DLL location and explicitly include it
python_dll_name = f'python{sys.version_info.major}{sys.version_info.minor}.dll'
python_dll_path = os.path.join(os.path.dirname(sys.executable), python_dll_name)

# Prepare binaries list
binaries_list = []
if os.path.exists(python_dll_path):
    binaries_list.append((python_dll_path, '.'))
    print(f"INFO: Explicitly including Python DLL: {python_dll_path}")
else:
    print(f"WARNING: Python DLL not found at: {python_dll_path}")

# ── Analysis ──
# This .spec file lives in the "Installer" subfolder.
# Entry point is in the top-level "aura_floating_widget" folder.
a = Analysis(
    ['..\\aura_floating_widget\\aura_widget.py'],
    pathex=['e:\\agent'],
    binaries=binaries_list,
    datas=[],
    hiddenimports=[
        # ── Core AURA v2 modules ──
        'ai_client',
        'config',
        'user_config',

        # ── v2 Goal-Driven Architecture ──
        'aura_v2_bridge',
        'goal',
        'goal_router',
        'strategy_planner',
        'plan_executor',
        'intent_router',
        'function_executor',
        'context_engine',
        'multi_task_handler',

        # ── System & Execution ──
        'windows_system_utils',
        'advanced_control',
        'code_executor',
        'capability_manager',
        'self_improvement',
        'response_generator',
        'local_context',
        'app_creator',

        # ── Communication ──
        'email_assistant',
        'telegram_bot',
        'browser_agent',
        'whatsapp_manager',

        # ── Voice & TTS ──
        'tts_manager',
        'wake_word_detector',

        # ── PyQt5 modules ──
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',

        # ── API providers ──
        'requests',
        'google.generativeai',
        'google.ai.generativelanguage',
        'google.genai',

        # ── Voice/Speech ──
        'pyttsx3',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'speech_recognition',

        # ── System utilities ──
        'rapidfuzz',
        'rapidfuzz.process',
        'rapidfuzz.fuzz',
        'pyautogui',
        'PIL',
        'PIL.Image',
        'screen_brightness_control',
        'wmi',
        'comtypes',
        'pycaw',
        'pycaw.pycaw',
        'pycaw.api',
        'pycaw.callbacks',
        'pycaw.constants',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',

        # ── Standard library (ensure bundled) ──
        'json',
        'pathlib',
        'threading',
        'queue',
        'datetime',
        'math',
        'random',
        'dataclasses',
        'enum',
        'logging',
        'asyncio',
        'subprocess',
        'smtplib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'test',
        'unittest',
        # Heavy transitive deps AURA doesn't need
        'torch',
        'torchvision',
        'torchaudio',
        'tensorboard',
        'cv2',
        'opencv-python',
        'pyarrow',
        'IPython',
        'notebook',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AURA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window - GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='jarvis_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AURA',
)
