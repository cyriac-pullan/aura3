# 🌟 AURA Modern GUI - Floating Voice Animation Interface

A beautiful, modern web-based interface for AURA (Advanced Neural Network Interface) featuring:

- **Floating Voice Orb** with stunning animations
- **Glassmorphism Design** with modern aesthetics
- **Voice Recognition** using Web Speech API
- **Real-time Communication** via WebSocket
- **Responsive Design** for all screen sizes

## ✨ Features

### 🎨 Visual Design
- **Dark Mode** with cyan/purple accent theme
- **Animated Background** with neural grid pattern
- **Glassmorphism** UI elements with blur effects
- **Smooth Animations** and micro-interactions
- **Particle Effects** on the voice orb

### 🎤 Voice Orb States
The floating voice orb animates based on its state:
- **Idle**: Gentle floating animation with pulsing rings
- **Listening**: Intensified glow with wave bar visualization
- **Processing**: Hue-rotating rainbow effect
- **Speaking**: Rhythmic pulsing animation

### 💬 Chat Interface
- Beautiful message bubbles with gradient styling
- Markdown support (bold, code blocks, lists)
- Timestamps on all messages
- Auto-scroll to latest messages
- Success/Error/Neural message types

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Modern web browser (Chrome, Firefox, Edge)
- AURA backend components (from parent directory)

### Installation

1. **Install aiohttp** (if not already installed):
   ```bash
   pip install aiohttp
   ```

2. **Start the server**:
   ```bash
   # Windows
   start_modern_aura.bat
   
   # Or directly with Python
   python server.py
   ```

3. **Open in browser** (opens automatically):
   - Navigate to `http://localhost:8080`

### Demo Mode
If the AURA backend components aren't available, the GUI will run in **demo mode** with simulated responses. This is great for testing the interface.

## 📁 Project Structure

```
aura_modern_gui/
├── index.html          # Main HTML structure
├── style.css           # All CSS styles and animations
├── app.js              # Frontend JavaScript application
├── server.py           # Python backend server
├── start_modern_aura.bat   # Windows launcher
└── README.md           # This file
```

## 🎛️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line in input |
| `Ctrl+L` | Clear chat |
| `Ctrl+S` | Open settings |
| `Escape` | Close modal / Stop listening |

## 🔧 Configuration

### Server Options
```bash
python server.py --host 0.0.0.0 --port 8080 --no-browser
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | localhost | Host to bind to |
| `--port` | 8080 | Port to listen on |
| `--no-browser` | false | Don't auto-open browser |

### Voice Settings
Voice settings can be adjusted in the Settings modal:
- Voice recognition language
- Text-to-speech speed

## 🌐 Browser Compatibility

| Browser | Support |
|---------|---------|
| Chrome | ✅ Full support |
| Edge | ✅ Full support |
| Firefox | ✅ Full support |
| Safari | ⚠️ Limited voice support |

## 🔗 WebSocket API

The frontend communicates with the backend via WebSocket:

### Send Command
```json
{
    "type": "command",
    "content": "open notepad"
}
```

### Response
```json
{
    "type": "success",
    "message": "Command executed successfully",
    "code": "import subprocess\nsubprocess.Popen(['notepad'])",
    "output": "Notepad opened"
}
```

## 🎨 Customization

### Color Theme
Edit the CSS custom properties in `style.css`:

```css
:root {
    --color-accent-primary: #00d4ff;    /* Main accent color */
    --color-accent-secondary: #7b68ee;  /* Secondary accent */
    --color-bg-primary: #030014;        /* Background */
    /* ... more variables */
}
```

### Orb Animation
Customize the voice orb behavior in the CSS:
- Change pulse speed
- Modify glow intensity
- Adjust particle count/behavior

## 🤝 Integration with AURA

This modern GUI is designed to work with the existing AURA backend:

1. The `server.py` imports AURA components
2. Commands are processed through `ai_client`
3. Code is executed via `code_executor`
4. Self-improvement happens through `improvement_engine`

## 📄 License

MIT License - See parent directory for full license.

---

Made with 💜 for AURA - Advanced Neural Network Interface
