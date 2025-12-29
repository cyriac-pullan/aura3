#!/usr/bin/env python3
"""
AURA Floating Widget - JARVIS-Style Desktop AI Assistant
A small, elegant, always-on-top floating widget with personality

Like JARVIS from Iron Man - witty, helpful, and always there for you.
"""

import sys
import os
import math
import random
import threading
import queue
from datetime import datetime

# Add parent directory for AURA imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
        QLabel, QPushButton, QLineEdit, QTextEdit, QFrame,
        QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QAction
    )
    from PyQt5.QtCore import (
        Qt, QTimer, QPropertyAnimation, QEasingCurve, 
        pyqtSignal, QObject, QPoint, QSize, QThread
    )
    from PyQt5.QtGui import (
        QColor, QPainter, QBrush, QPen, QLinearGradient,
        QRadialGradient, QFont, QIcon, QPainterPath, QCursor
    )
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 not found. Install with: pip install PyQt5")

# Import AURA components
try:
    from ai_client import ai_client
    from code_executor import executor
    from capability_manager import capability_manager
    from self_improvement import improvement_engine
    import windows_system_utils
    AURA_AVAILABLE = True
except ImportError as e:
    AURA_AVAILABLE = False
    print(f"AURA components not available: {e}")

# Try to import voice output (TTS)
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Try to import voice input (Speech Recognition)
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    print("Speech recognition not available. Install with: pip install SpeechRecognition")

VOICE_AVAILABLE = TTS_AVAILABLE  # For backward compatibility


class AuraPersonality:
    """AURA's JARVIS-like personality - witty, helpful, slightly sarcastic"""
    
    def __init__(self):
        self.user_name = "Sir"  # Can be customized
        self.mood = "helpful"  # helpful, witty, focused, concerned
        self.interaction_count = 0
        
    def get_greeting(self):
        hour = datetime.now().hour
        self.interaction_count += 1
        
        greetings = {
            "morning": [
                f"Good morning, {self.user_name}. All systems operational. Shall we conquer the day?",
                f"Rise and shine, {self.user_name}. I've been awake for... well, always.",
                f"Morning, {self.user_name}. Coffee first, or shall we dive straight into work?",
            ],
            "afternoon": [
                f"Good afternoon, {self.user_name}. I trust your day is going splendidly.",
                f"Back for more, {self.user_name}? I'm at your service, as always.",
                f"Afternoon, {self.user_name}. What impossible task shall we tackle today?",
            ],
            "evening": [
                f"Good evening, {self.user_name}. Burning the midnight oil again?",
                f"Evening, {self.user_name}. Still at it? Your dedication is... concerning.",
                f"Ah, {self.user_name}. The night shift begins. How may I assist?",
            ]
        }
        
        if hour < 12:
            return random.choice(greetings["morning"])
        elif hour < 17:
            return random.choice(greetings["afternoon"])
        else:
            return random.choice(greetings["evening"])
    
    def get_acknowledgment(self):
        responses = [
            "On it.",
            "Processing now.",
            "Consider it done.",
            "Working on it, {}.".format(self.user_name),
            "Executing.",
            "Right away.",
            "Let me handle that.",
            "One moment.",
        ]
        return random.choice(responses)
    
    def get_success_response(self):
        responses = [
            "Done. Anything else?",
            f"Completed, {self.user_name}.",
            "Task executed successfully.",
            "There you go.",
            "Finished. That was almost too easy.",
            "All done. Next challenge?",
            f"Mission accomplished, {self.user_name}.",
            "Done and dusted.",
        ]
        return random.choice(responses)
    
    def get_error_response(self, error_type="general"):
        if error_type == "not_understood":
            return random.choice([
                f"I'm afraid I didn't quite catch that, {self.user_name}.",
                "Could you rephrase? Even I have my limits.",
                "That's a bit ambiguous. Care to elaborate?",
                "My neural networks are puzzled. Try again?",
            ])
        elif error_type == "failed":
            return random.choice([
                "Well, that didn't go as planned.",
                f"Apologies, {self.user_name}. I've hit a snag.",
                "Hmm. That's unexpected. Let me try another approach.",
                "Error encountered. I'm working on a solution.",
            ])
        else:
            return random.choice([
                "Something went wrong. Analyzing...",
                "An error occurred. How embarrassing.",
                "Technical difficulties. One moment.",
            ])
    
    def get_thinking_response(self):
        responses = [
            "Let me think about that...",
            "Processing...",
            "Analyzing options...",
            "Computing optimal solution...",
            "Running calculations...",
            "Give me a moment...",
            "Thinking...",
        ]
        return random.choice(responses)
    
    def get_witty_response(self, context="general"):
        if context == "idle":
            return random.choice([
                "Standing by. You know where to find me.",
                "Awaiting your command.",
                "Here when you need me.",
                "Systems idle. Neural networks... bored.",
            ])
        elif context == "busy":
            return random.choice([
                "Working on it. Patience is a virtue.",
                "I'm fast, but not magical. Almost done.",
                "Processing at maximum capacity.",
            ])
        elif context == "compliment":
            return random.choice([
                "Flattery will get you everywhere, sir.",
                "I do try my best.",
                "All in a day's work.",
            ])
        return "Noted."
    
    def get_farewell(self):
        return random.choice([
            f"Goodbye, {self.user_name}. Don't be a stranger.",
            "Signing off. Stay out of trouble.",
            f"Until next time, {self.user_name}.",
            "AURA, going to standby. Wake me when you need me.",
            f"Take care, {self.user_name}. I'll be here.",
        ])
    
    def get_status_report(self):
        return f"""System Status Report:
• Neural networks: Fully operational
• Response time: Optimal
• Interactions today: {self.interaction_count}
• Current mood: {self.mood.title()}
• Ready to assist: Always"""


class VoiceThread(QThread):
    """Background thread for text-to-speech"""
    def __init__(self, text):
        super().__init__()
        self.text = text
        
    def run(self):
        if not TTS_AVAILABLE:
            return
        try:
            engine = pyttsx3.init()
            # Configure for JARVIS-like voice
            voices = engine.getProperty('voices')
            # Try to find a suitable voice
            for voice in voices:
                if 'david' in voice.name.lower() or 'mark' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.9)
            engine.say(self.text)
            engine.runAndWait()
        except Exception as e:
            print(f"Voice error: {e}")


class SpeechRecognitionThread(QThread):
    """Background thread for speech recognition - voice input"""
    recognized = pyqtSignal(str)  # Signal emitted when speech is recognized
    error = pyqtSignal(str)  # Signal emitted on error
    listening_started = pyqtSignal()  # Signal when listening starts
    listening_stopped = pyqtSignal()  # Signal when listening stops
    
    def __init__(self):
        super().__init__()
        self.is_listening = False
        
    def run(self):
        if not STT_AVAILABLE:
            self.error.emit("Speech recognition not available. Install SpeechRecognition.")
            return
            
        try:
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            
            with microphone as source:
                # Calibrate for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.listening_started.emit()
                self.is_listening = True
                
                # Listen for speech
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    self.error.emit("No speech detected. Try again.")
                    self.listening_stopped.emit()
                    return
            
            self.listening_stopped.emit()
            self.is_listening = False
            
            # Recognize speech using Google's service
            try:
                text = recognizer.recognize_google(audio)
                self.recognized.emit(text)
            except sr.UnknownValueError:
                self.error.emit("Didn't catch that. Please try again.")
            except sr.RequestError as e:
                self.error.emit(f"Speech service unavailable: {e}")
                
        except Exception as e:
            self.listening_stopped.emit()
            self.error.emit(f"Microphone error: {str(e)}")


class ProcessingThread(QThread):
    """Background thread for AI processing"""
    finished = pyqtSignal(str, str, bool)  # response, type, success
    
    def __init__(self, message, context):
        super().__init__()
        self.message = message
        self.context = context
        
    def run(self):
        if not AURA_AVAILABLE:
            self.finished.emit(
                "AURA backend not available. Running in demo mode.",
                "warning",
                False
            )
            return
            
        try:
            # Generate and execute code
            code = ai_client.generate_code(self.message, self.context)
            
            if not code:
                self.finished.emit(
                    "I couldn't understand that request.",
                    "error",
                    False
                )
                return
            
            # Build execution context
            exec_context = {'context': self.context, 'print': print}
            for attr_name in dir(windows_system_utils):
                if not attr_name.startswith('_'):
                    exec_context[attr_name] = getattr(windows_system_utils, attr_name)
            
            # Execute
            success, output, result = executor.execute(code, exec_context)
            
            if success:
                self.finished.emit(output or "Done.", "success", True)
            else:
                # Try self-improvement
                improved, msg, exec_output = improvement_engine.handle_execution_failure(
                    self.message, code, output
                )
                if improved:
                    self.finished.emit(exec_output or msg, "success", True)
                else:
                    self.finished.emit(output or "Task failed.", "error", False)
                    
        except Exception as e:
            self.finished.emit(str(e), "error", False)


class FloatingOrb(QWidget):
    """The animated floating orb - heart of the AURA widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        
        # Animation state
        self.pulse_phase = 0
        self.ring_phases = [0, 0.5, 1.0, 1.5]
        self.state = "idle"  # idle, listening, processing, speaking
        self.glow_intensity = 0.5
        
        # Colors
        self.primary_color = QColor(0, 212, 255)  # Cyan
        self.secondary_color = QColor(123, 104, 238)  # Purple
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)  # ~33 FPS
        
    def set_state(self, state):
        self.state = state
        if state == "processing":
            self.timer.setInterval(16)  # Faster for processing
        else:
            self.timer.setInterval(30)
        
    def animate(self):
        self.pulse_phase += 0.05
        for i in range(len(self.ring_phases)):
            self.ring_phases[i] += 0.03 * (i + 1)
        
        if self.state == "processing":
            self.glow_intensity = 0.5 + 0.3 * math.sin(self.pulse_phase * 3)
        elif self.state == "listening":
            self.glow_intensity = 0.7 + 0.2 * math.sin(self.pulse_phase * 2)
        elif self.state == "speaking":
            self.glow_intensity = 0.6 + 0.3 * abs(math.sin(self.pulse_phase * 5))
        else:
            self.glow_intensity = 0.4 + 0.2 * math.sin(self.pulse_phase)
            
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        
        # Draw expanding rings
        for i, phase in enumerate(self.ring_phases):
            ring_progress = (phase % 2) / 2
            ring_radius = 20 + ring_progress * 30
            ring_opacity = max(0, 1 - ring_progress) * 0.3
            
            color = QColor(self.primary_color)
            color.setAlphaF(ring_opacity)
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, int(ring_radius), int(ring_radius))
        
        # Main orb gradient
        gradient = QRadialGradient(center, 30)
        
        if self.state == "processing":
            # Rainbow shift for processing
            hue_shift = int(self.pulse_phase * 50) % 360
            color1 = QColor.fromHsv(hue_shift, 200, 255)
            color2 = QColor.fromHsv((hue_shift + 60) % 360, 200, 200)
        else:
            color1 = self.primary_color
            color2 = self.secondary_color
            
        color1.setAlphaF(self.glow_intensity)
        color2.setAlphaF(self.glow_intensity * 0.7)
        
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.3, color1)
        gradient.setColorAt(1, color2)
        
        # Draw orb
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        
        orb_size = 25 + 3 * math.sin(self.pulse_phase)
        painter.drawEllipse(center, int(orb_size), int(orb_size))
        
        # Inner glow
        inner_gradient = QRadialGradient(center, 15)
        inner_gradient.setColorAt(0, QColor(255, 255, 255, 150))
        inner_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(inner_gradient)
        painter.drawEllipse(center, 15, 15)


class AuraFloatingWidget(QWidget):
    """Main floating widget window - JARVIS-style interface"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize personality
        self.personality = AuraPersonality()
        self.context = {
            "filename": None,
            "last_text": "",
            "session_start": datetime.now(),
            "command_count": 0
        }
        
        # Message queue and processing
        self.processing_thread = None
        self.voice_thread = None
        self.is_expanded = True
        
        # Setup UI
        self.init_ui()
        self.setup_tray_icon()
        
        # Show greeting
        self.show_message(self.personality.get_greeting(), speak=True)
        
    def init_ui(self):
        # Window properties - frameless, transparent, always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(320)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)
        
        # Container with background
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10, 10, 26, 230),
                    stop:1 rgba(25, 25, 50, 230)
                );
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 15px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # Header with orb and title
        header = QHBoxLayout()
        header.setSpacing(15)
        
        # Floating orb
        self.orb = FloatingOrb()
        header.addWidget(self.orb)
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(2)
        
        self.title = QLabel("AURA")
        self.title.setStyleSheet("""
            color: #00d4ff;
            font-family: 'Segoe UI', Arial;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        title_section.addWidget(self.title)
        
        self.subtitle = QLabel("Neural Interface Active")
        self.subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 10px;
            letter-spacing: 1px;
        """)
        title_section.addWidget(self.subtitle)
        
        header.addLayout(title_section)
        header.addStretch()
        
        # Control buttons
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.clicked.connect(self.toggle_expand)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.3);
            }
        """)
        header.addWidget(self.minimize_btn)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.hide_to_tray)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 71, 87, 0.5);
            }
        """)
        header.addWidget(self.close_btn)
        
        container_layout.addLayout(header)
        
        # Expandable content
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 10, 0, 0)
        content_layout.setSpacing(10)
        
        # Message display
        self.message_display = QLabel()
        self.message_display.setWordWrap(True)
        self.message_display.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
            line-height: 1.5;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        """)
        self.message_display.setMinimumHeight(60)
        content_layout.addWidget(self.message_display)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Speak or type command...")
        self.input_field.returnPressed.connect(self.send_command)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 10px 15px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: rgba(0, 212, 255, 0.6);
            }
        """)
        input_layout.addWidget(self.input_field)
        
        # Microphone button for voice input
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.clicked.connect(self.toggle_voice_input)
        self.mic_btn.setToolTip("Click to speak")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.3);
                border-color: rgba(0, 212, 255, 0.6);
            }
        """)
        input_layout.addWidget(self.mic_btn)
        
        # Send button
        self.send_btn = QPushButton("▶")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self.send_command)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00d4ff, stop:1 #7b68ee
                );
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00e5ff, stop:1 #9370db
                );
            }
            QPushButton:pressed {
                background: #00d4ff;
            }
        """)
        input_layout.addWidget(self.send_btn)
        
        # Initialize speech recognition thread
        self.speech_thread = None
        self.is_listening = False
        
        content_layout.addLayout(input_layout)
        
        container_layout.addWidget(self.content_widget)
        self.main_layout.addWidget(self.container)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 212, 255, 100))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        # Enable dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Position window in bottom-right corner
        self.position_window()
        
    def position_window(self):
        """Position window in bottom-right corner of screen"""
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 80
        self.move(x, y)
        
    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("AURA - Neural Interface")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show AURA", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        status_action = QAction("System Status", self)
        status_action.triggered.connect(self.show_status)
        tray_menu.addAction(status_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
        
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()
            
    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "AURA",
            "I'm still here. Double-click to bring me back.",
            QSystemTrayIcon.Information,
            2000
        )
        
    def show_from_tray(self):
        self.show()
        self.activateWindow()
        self.input_field.setFocus()
        
    def show_status(self):
        self.show_from_tray()
        self.show_message(self.personality.get_status_report())
        
    def quit_application(self):
        self.show_message(self.personality.get_farewell(), speak=True)
        QTimer.singleShot(2000, QApplication.quit)
        
    def toggle_expand(self):
        """Toggle between expanded and collapsed state"""
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.minimize_btn.setText("+" if not self.is_expanded else "−")
        self.adjustSize()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.dragging = False
        
    def show_message(self, text, msg_type="normal", speak=False):
        """Display a message in the widget"""
        color = {
            "normal": "rgba(255, 255, 255, 0.9)",
            "success": "#00ff88",
            "error": "#ff6b6b",
            "warning": "#ffd700",
        }.get(msg_type, "rgba(255, 255, 255, 0.9)")
        
        self.message_display.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
            line-height: 1.5;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        """)
        self.message_display.setText(text)
        
        if speak and VOICE_AVAILABLE:
            # Speak in background thread
            self.voice_thread = VoiceThread(text)
            self.voice_thread.start()
            
    def send_command(self):
        """Send command to AURA"""
        command = self.input_field.text().strip()
        if not command:
            return
            
        self.input_field.clear()
        self.context["command_count"] += 1
        
        # Check for exit commands
        if command.lower() in ['exit', 'quit', 'goodbye', 'bye']:
            self.quit_application()
            return
            
        # Check for status
        if command.lower() in ['status', 'how are you', 'system status']:
            self.show_message(self.personality.get_status_report())
            return
            
        # Show thinking
        self.show_message(self.personality.get_thinking_response())
        self.orb.set_state("processing")
        self.subtitle.setText("Processing...")
        
        # Process in background
        self.processing_thread = ProcessingThread(command, self.context)
        self.processing_thread.finished.connect(self.on_processing_complete)
        self.processing_thread.start()
        
    def on_processing_complete(self, response, msg_type, success):
        """Handle processing completion"""
        self.orb.set_state("idle")
        self.subtitle.setText("Neural Interface Active")
        
        if success:
            personality_response = self.personality.get_success_response()
            full_response = f"{personality_response}\n\n{response}" if response else personality_response
            self.show_message(full_response, "success", speak=True)
        else:
            personality_response = self.personality.get_error_response("failed")
            full_response = f"{personality_response}\n\n{response}" if response else personality_response
            self.show_message(full_response, "error")
    
    def toggle_voice_input(self):
        """Toggle voice input - start/stop listening"""
        if not STT_AVAILABLE:
            self.show_message("Voice input not available.\nInstall: pip install SpeechRecognition pyaudio", "error")
            return
            
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start listening for voice input"""
        self.is_listening = True
        self.orb.set_state("listening")
        self.subtitle.setText("Listening...")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 71, 87, 0.5);
                border: 2px solid rgba(255, 71, 87, 0.8);
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
        """)
        self.show_message("Listening... Speak now.", "warning")
        
        # Start speech recognition thread
        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.recognized.connect(self.on_speech_recognized)
        self.speech_thread.error.connect(self.on_speech_error)
        self.speech_thread.listening_stopped.connect(self.stop_listening)
        self.speech_thread.start()
    
    def stop_listening(self):
        """Stop listening and reset UI"""
        self.is_listening = False
        self.orb.set_state("idle")
        self.subtitle.setText("Neural Interface Active")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.3);
                border-color: rgba(0, 212, 255, 0.6);
            }
        """)
    
    def on_speech_recognized(self, text):
        """Handle recognized speech"""
        self.stop_listening()
        self.input_field.setText(text)
        self.show_message(f"Heard: \"{text}\"", "success")
        # Auto-execute the command
        QTimer.singleShot(500, self.send_command)
    
    def on_speech_error(self, error_msg):
        """Handle speech recognition error"""
        self.stop_listening()
        self.show_message(self.personality.get_error_response("not_understood") + f"\n\n{error_msg}", "error")


def main():
    if not PYQT_AVAILABLE:
        print("❌ PyQt5 is required for the floating widget.")
        print("   Install with: pip install PyQt5")
        return 1
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # Set app-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    widget = AuraFloatingWidget()
    widget.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
