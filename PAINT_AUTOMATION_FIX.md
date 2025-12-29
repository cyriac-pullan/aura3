# Paint Automation Fix

## Problem
Paint was not opening in maximized view, causing automation to fail because:
1. Window size varies
2. Fixed coordinates don't work
3. Canvas dimensions are unpredictable

## Solution Implemented

### 1. Enhanced AI Instructions
**File:** `ai_client.py` lines 357-417

Added critical instructions:
- **CRITICAL: Always maximize Paint window after opening**
- Use `Win+Up` hotkey to maximize
- Wait for window to maximize (time.sleep(1))
- Get window dimensions using `pyautogui.getWindowsWithTitle()`
- Calculate center-relative coordinates
- NEVER use fixed absolute coordinates

### 2. Fixed Self-Improvement Engine
**File:** `self_improvement.py` lines 322-337

Previously when `needs_new_function=False`, it would just give up. Now:
- Attempts to regenerate code anyway
- Shows better error messages
- Continues trying even when analysis suggests no new function

### 3. Better Error Detection
**File:** `aura_gui.py` lines 712-715

Added detection for Paint-specific errors:
- "Failed to read"
- "Failure"
- "image file" errors

## How It Works Now

### Paint Automation Flow:
```
1. Open Paint with subprocess.Popen('mspaint')
   ↓
2. Wait 3 seconds for Paint to open
   ↓
3. Maximize window using Win+Up hotkey (CRITICAL!)
   ↓
4. Wait 1 second for maximization
   ↓
5. Get window dimensions using getWindowsWithTitle()
   ↓
6. Calculate center coordinates (window-aware)
   ↓
7. Draw using center-relative coordinates
```

### Example Code Generated:
```python
import subprocess
import time
import pyautogui

# Open Paint
subprocess.Popen('mspaint')
time.sleep(3)

# ALWAYS maximize first
pyautogui.hotkey('win', 'up')
time.sleep(1)

# Get window dimensions
windows = pyautogui.getWindowsWithTitle("Untitled - Paint")
if windows:
    window = windows[0]
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2
    
    # Draw triangle from center
    pyautogui.moveTo(center_x - 100, center_y + 50)
    pyautogui.drag(200, 0, duration=0.5)
    pyautogui.drag(-100, -150, duration=0.5)
    pyautogui.drag(-100, 150, duration=0.5)
```

## Key Improvements

✅ **Always Maximizes Window** - Ensures consistent canvas size  
✅ **Window-Aware Coordinates** - Uses actual window dimensions  
✅ **No Image Detection** - Never uses locateOnScreen()  
✅ **Better Error Handling** - Regenerates code even when no new function needed  
✅ **Example Code Provided** - Shows AI exactly how to do it

## Test Now

Try: **"Open paint and draw triangle"**

Now should:
1. Open Paint
2. Maximize window automatically
3. Get window dimensions
4. Draw triangle in center
5. Work reliably!


