#!/usr/bin/env python3
"""
AURA GUI - Futuristic AI Assistant Interface
Advanced Neural Network Interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import math

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import AURA personality
from aura_responses import aura

class AuraGUI:
    def __init__(self):
        self.root = tk.Tk()
        
        # Initialize core components first
        self.assistant = None
        self.context = {
            "filename": None,
            "last_text": "",
            "session_start": datetime.now(),
            "command_count": 0
        }
        
        # Message queue for thread communication
        self.message_queue = queue.Queue()
        
        # Voice interface
        self.voice_interface = None
        self.voice_enabled = False
        self._voice_listening = False
        
        # Threading control
        self.active_threads = []
        self.is_shutting_down = False
        
        # Setup GUI
        self.setup_window()
        self.setup_futuristic_styles()
        self.setup_widgets()
        
        # Initialize AI components
        self.initialize_ai_assistant()
        
        # Initialize voice interface
        self.initialize_voice_interface()
        
        # Start queue checking and animations
        self.check_queue()
        self.start_animations()
        
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("AURA - Advanced Neural Network Interface")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Set window icon (if available)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "jarvis_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Center window on screen
        self.center_window()
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_futuristic_styles(self):
        """Setup futuristic styling"""
        style = ttk.Style()
        
        # Configure modern theme
        style.theme_use('clam')
        
        # Define futuristic colors
        self.colors = {
            'bg_primary': '#0a0a0f',        # Deep space black
            'bg_secondary': '#1a1a2e',      # Dark purple-blue
            'bg_neural': '#16213e',         # Neural network blue
            'bg_chat': '#0a0a0f',          # Chat area background
            'bg_input': '#2d1b69',         # Input background - purple
            'bg_glass': 'rgba(100, 149, 237, 0.1)',  # Glass effect
            'text_primary': '#e6f3ff',      # Bright white-blue
            'text_secondary': '#b8c5d6',    # Light gray-blue
            'text_aura': '#00d4ff',         # AURA cyan
            'accent': '#7b68ee',            # Medium slate blue
            'accent_glow': '#9370db',       # Purple glow
            'user_bubble': '#32cd32',       # Lime green for user
            'aura_bubble': '#00d4ff',       # AURA cyan for responses
            'success': '#00ff7f',           # Spring green
            'error': '#ff6347',             # Tomato red
            'warning': '#ffd700',           # Gold
            'border': '#4169e1',            # Royal blue
            'neural_active': '#00ffff',     # Bright cyan
            'neural_inactive': '#4a5568',   # Gray
            'glow_primary': '#00bfff',      # Deep sky blue
            'glow_secondary': '#9370db',    # Medium orchid
        }
        
        # Configure root background
        self.root.configure(bg=self.colors['bg_primary'])
        
    def setup_widgets(self):
        """Setup all GUI widgets"""
        # Main container with gradient effect
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header with AURA branding
        self.setup_futuristic_header(main_frame)
        
        # Chat area with neural network styling
        self.setup_neural_chat_area(main_frame)
        
        # Input area with advanced controls
        self.setup_advanced_input_area(main_frame)
        
        # Status bar with system diagnostics
        self.setup_system_status_bar(main_frame)
        
    def setup_futuristic_header(self, parent):
        """Setup futuristic header with AURA branding"""
        header_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], height=100)
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_propagate(False)
        
        # AURA logo and neural network indicator
        logo_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        logo_frame.grid(row=0, column=0, padx=20, pady=15, sticky='w')
        
        # AURA title with glow effect simulation
        aura_label = tk.Label(
            logo_frame,
            text="AURA",
            font=('Orbitron', 28, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_aura']
        )
        aura_label.pack(anchor='w')
        
        # Subtitle
        subtitle_label = tk.Label(
            logo_frame,
            text="Advanced Neural Network Interface",
            font=('Segoe UI', 12),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Neural network status indicator
        center_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        center_frame.grid(row=0, column=1, sticky='')
        
        # Activity rings for neural network visualization
        self.neural_ring = tk.Label(
            center_frame,
            text="◉",
            font=('Segoe UI', 24),
            bg=self.colors['bg_secondary'],
            fg=self.colors['neural_active']
        )
        self.neural_ring.pack(pady=10)
        
        # AURA status text
        self.aura_status = tk.Label(
            center_frame,
            text="NEURAL NETWORKS ACTIVE",
            font=('Orbitron', 10, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['success']
        )
        self.aura_status.pack()
        
        # Control panel
        control_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        control_frame.grid(row=0, column=2, padx=20, pady=15)
        
        # Voice control with futuristic styling
        self.voice_btn = tk.Button(
            control_frame,
            text="🎤",
            font=('Segoe UI', 14),
            bg=self.colors['bg_neural'],
            fg=self.colors['text_primary'],
            relief='flat',
            borderwidth=2,
            width=4,
            height=1,
            command=self.toggle_voice_input,
            cursor='hand2'
        )
        self.voice_btn.pack(pady=5)
        
        # Voice status indicator
        self.voice_status_indicator = tk.Label(
            control_frame,
            text="VOICE",
            font=('Orbitron', 8),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        self.voice_status_indicator.pack()
        
        # Additional control buttons
        button_frame = tk.Frame(control_frame, bg=self.colors['bg_secondary'])
        button_frame.pack(pady=5)
        
        # Clear button
        self.clear_btn = tk.Button(
            button_frame,
            text="⚡",
            font=('Segoe UI', 12),
            bg=self.colors['bg_neural'],
            fg=self.colors['text_primary'],
            relief='flat',
            borderwidth=1,
            width=3,
            command=self.clear_chat
        )
        self.clear_btn.pack(side='left', padx=2)
        
        # File button
        self.file_btn = tk.Button(
            button_frame,
            text="📁",
            font=('Segoe UI', 12),
            bg=self.colors['bg_neural'],
            fg=self.colors['text_primary'],
            relief='flat',
            borderwidth=1,
            width=3,
            command=self.open_file_dialog
        )
        self.file_btn.pack(side='left', padx=2)
        
        # Settings button
        self.settings_btn = tk.Button(
            button_frame,
            text="⚙️",
            font=('Segoe UI', 12),
            bg=self.colors['bg_neural'],
            fg=self.colors['text_primary'],
            relief='flat',
            borderwidth=1,
            width=3,
            command=self.open_settings
        )
        self.settings_btn.pack(side='left', padx=2)
        
    def setup_neural_chat_area(self, parent):
        """Setup neural network styled chat area"""
        chat_frame = tk.Frame(parent, bg=self.colors['bg_chat'])
        chat_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        # Chat display with futuristic styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Consolas', 12),
            bg=self.colors['bg_chat'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=25,
            highlightthickness=0
        )
        self.chat_display.grid(row=0, column=0, sticky='nsew')
        
        # Configure text tags for futuristic styling
        self.chat_display.tag_configure('user', 
            foreground=self.colors['user_bubble'], 
            font=('Consolas', 12, 'bold'))
        self.chat_display.tag_configure('aura', 
            foreground=self.colors['aura_bubble'], 
            font=('Consolas', 12, 'bold'))
        self.chat_display.tag_configure('timestamp', 
            foreground=self.colors['text_secondary'], 
            font=('Consolas', 10))
        self.chat_display.tag_configure('success', 
            foreground=self.colors['success'])
        self.chat_display.tag_configure('error', 
            foreground=self.colors['error'])
        self.chat_display.tag_configure('code', 
            foreground=self.colors['warning'], 
            font=('Consolas', 11))
        self.chat_display.tag_configure('neural', 
            foreground=self.colors['neural_active'],
            font=('Consolas', 12, 'bold'))
        
        # Welcome message from AURA
        welcome_msg = aura.get_greeting() + "\n\nNeural networks initialized. I can assist you with:\n\n• System automation and control\n• File operations and data management\n• Advanced computing tasks\n• Network and security protocols\n• Voice command processing\n• And much more through my neural architecture\n\nState your requirements for processing."
        self.add_aura_message(welcome_msg)
        
    def setup_advanced_input_area(self, parent):
        """Setup advanced input area with futuristic controls"""
        input_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        input_frame.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Input label
        input_label = tk.Label(
            input_frame,
            text="NEURAL INPUT INTERFACE",
            font=('Orbitron', 10, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_aura']
        )
        input_label.grid(row=0, column=0, sticky='w', padx=15, pady=(10, 0))
        
        # Input text box with futuristic styling
        input_container = tk.Frame(input_frame, bg=self.colors['bg_secondary'])
        input_container.grid(row=1, column=0, sticky='ew', padx=15, pady=10)
        input_container.grid_columnconfigure(0, weight=1)
        
        self.input_text = tk.Text(
            input_container,
            height=3,
            font=('Consolas', 12),
            bg=self.colors['bg_input'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_aura'],
            selectbackground=self.colors['accent'],
            relief='flat',
            borderwidth=2,
            highlightthickness=2,
            highlightcolor=self.colors['neural_active'],
            highlightbackground=self.colors['border'],
            padx=20,
            pady=15,
            wrap=tk.WORD
        )
        self.input_text.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        # Add placeholder
        self.placeholder_text = "Input your command for neural processing... (Enter to execute, Shift+Enter for new line)"
        self.add_placeholder()
        self.input_text.bind('<FocusIn>', self.on_input_focus_in)
        self.input_text.bind('<FocusOut>', self.on_input_focus_out)
        
        # Send button with futuristic styling
        self.send_button = tk.Button(
            input_container,
            text="EXECUTE",
            font=('Orbitron', 11, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_glow'],
            activeforeground=self.colors['text_primary'],
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=15,
            cursor='hand2',
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=(0, 5))
        
        # Bind Enter key to send message
        self.input_text.bind('<Return>', self.on_enter_key)
        self.input_text.bind('<Shift-Return>', self.on_shift_enter)
        
        # Add keyboard shortcuts
        self.root.bind('<Control-Key-s>', lambda e: self.open_settings())
        self.root.bind('<Control-Key-f>', lambda e: self.open_file_dialog())
        self.root.bind('<Control-Key-l>', lambda e: self.clear_chat())
        self.root.bind('<F5>', lambda e: self.update_status("Neural networks refreshed", "success"))
        
        # Focus on input
        self.input_text.focus_set()
        
    def setup_system_status_bar(self, parent):
        """Setup system status bar with diagnostics"""
        status_frame = tk.Frame(parent, bg=self.colors['bg_neural'])
        status_frame.grid(row=3, column=0, sticky='ew')
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=0)
        
        # Status text
        self.status_bar = tk.Label(
            status_frame,
            text="AURA SYSTEMS OPERATIONAL - Neural networks ready for input",
            font=('Orbitron', 10),
            bg=self.colors['bg_neural'],
            fg=self.colors['text_aura'],
            anchor='w',
            padx=15,
            pady=10
        )
        self.status_bar.grid(row=0, column=0, sticky='ew')
        
        # System indicator
        self.system_indicator = tk.Label(
            status_frame,
            text="◉ ONLINE",
            font=('Orbitron', 9, 'bold'),
            bg=self.colors['bg_neural'],
            fg=self.colors['success'],
            padx=15
        )
        self.system_indicator.grid(row=0, column=1, padx=(0, 15))
        
    def initialize_ai_assistant(self):
        """Initialize AI assistant components with improved error handling"""
        try:
            # Import AI assistant components with individual error handling
            try:
                from ai_client import ai_client
                self.ai_client = ai_client
                logging.info("AI client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize AI client: {e}")
                self.ai_client = None
                
            try:
                from code_executor import executor
                self.executor = executor
                logging.info("Code executor initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize code executor: {e}")
                self.executor = None
                
            try:
                from capability_manager import capability_manager
                self.capability_manager = capability_manager
                logging.info("Capability manager initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize capability manager: {e}")
                self.capability_manager = None
                
            try:
                from self_improvement import improvement_engine
                self.improvement_engine = improvement_engine
                logging.info("Improvement engine initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize improvement engine: {e}")
                self.improvement_engine = None
            
            # Check if core components are available
            if self.ai_client:
                self.update_status("AURA neural networks online - All systems operational", "success")
                self.add_aura_message("Neural network initialization complete. AURA ready for processing.")
            else:
                self.update_status("AURA neural networks partially operational", "warning")
                self.add_aura_message("Neural network initialization partially complete. Some features may be unavailable.")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"Critical error in AI assistant initialization: {error_details}")
            
            error_msg = f"Neural network initialization failed: {e}"
            self.update_status(error_msg, "error")
            self.add_aura_message(error_msg, "error")
            
            # Show user-friendly error dialog
            messagebox.showerror("Neural Network Error", 
                               f"Failed to initialize AURA systems:\n{e}\n\nPlease check your configuration and try again.")
            
    def initialize_voice_interface(self):
        """Initialize voice interface"""
        try:
            from voice_interface import VoiceInterface, VOICE_AVAILABLE
            
            if VOICE_AVAILABLE:
                self.voice_interface = VoiceInterface()
                self.voice_enabled = True
                self.voice_status_indicator.config(text="VOICE ACTIVE", fg=self.colors['success'])
                self.add_aura_message("Voice interface activated. Neural speech recognition online.")
                self.update_status("Voice neural networks active", "success")
                # Make AURA introduce herself by voice
                self.speak_response(aura.get_voice_introduction())
            else:
                self.voice_enabled = False
                self.voice_status_indicator.config(text="VOICE OFFLINE", fg=self.colors['error'])
                self.voice_btn.config(state='disabled')
                self.show_voice_installation_guide()
                
        except ImportError as e:
            self.voice_enabled = False
            self.voice_status_indicator.config(text="VOICE OFFLINE", fg=self.colors['error'])
            self.voice_btn.config(state='disabled')
            
            if "PyAudio" in str(e):
                self.add_aura_message("Voice neural networks require PyAudio installation for activation.", "error")
                self.show_pyaudio_installation_guide()
            else:
                self.add_aura_message(f"Voice interface initialization failed: {e}", "error")
                
        except Exception as e:
            self.voice_enabled = False
            self.voice_status_indicator.config(text="VOICE OFFLINE", fg=self.colors['error'])
            self.voice_btn.config(state='disabled')
            self.add_aura_message(f"Voice interface initialization failed: {e}", "error")
            
    def add_message(self, sender, message, msg_type="normal"):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.config(state='normal')
        
        # Add timestamp with futuristic styling
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Add sender with appropriate styling
        if sender == "You":
            self.chat_display.insert(tk.END, f"{sender}: ", 'user')
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", 'aura')
        
        # Add message with appropriate styling
        if msg_type == "success":
            self.chat_display.insert(tk.END, f"{message}\n\n", 'success')
        elif msg_type == "error":
            self.chat_display.insert(tk.END, f"{message}\n\n", 'error')
        elif msg_type == "code":
            self.chat_display.insert(tk.END, f"\n{message}\n\n", 'code')
        elif msg_type == "neural":
            self.chat_display.insert(tk.END, f"{message}\n\n", 'neural')
        else:
            self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
    def add_user_message(self, message):
        """Add user message"""
        self.add_message("You", message)
        
    def add_aura_message(self, message, msg_type="normal"):
        """Add AURA message"""
        self.add_message("AURA", message, msg_type)
        
    def update_status(self, message, status_type="normal"):
        """Update status bar"""
        self.status_bar.config(text=message)
        
        if status_type == "success":
            self.system_indicator.config(text="◉ ONLINE", fg=self.colors['success'])
            self.neural_ring.config(fg=self.colors['neural_active'])
        elif status_type == "error":
            self.system_indicator.config(text="◉ ERROR", fg=self.colors['error'])
            self.neural_ring.config(fg=self.colors['error'])
        elif status_type == "warning":
            self.system_indicator.config(text="◉ WARN", fg=self.colors['warning'])
            self.neural_ring.config(fg=self.colors['warning'])
        else:
            self.system_indicator.config(text="◉ ACTIVE", fg=self.colors['text_aura'])
            self.neural_ring.config(fg=self.colors['neural_active'])
            
    def start_animations(self):
        """Start futuristic animations"""
        self.animate_neural_ring()
        
    def animate_neural_ring(self):
        """Animate the neural network indicator"""
        colors = [self.colors['neural_active'], self.colors['accent'], self.colors['glow_primary']]
        if hasattr(self, '_ring_color_index'):
            self._ring_color_index = (self._ring_color_index + 1) % len(colors)
        else:
            self._ring_color_index = 0
            
        if hasattr(self, 'neural_ring'):
            self.neural_ring.config(fg=colors[self._ring_color_index])
        
        # Schedule next animation
        self.root.after(1000, self.animate_neural_ring)
        
    def add_placeholder(self):
        """Add placeholder text to input"""
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors['text_secondary'])
        
    def remove_placeholder(self):
        """Remove placeholder text"""
        if self.input_text.get("1.0", tk.END).strip() == self.placeholder_text:
            self.input_text.delete("1.0", tk.END)
            self.input_text.config(fg=self.colors['text_primary'])
            
    def on_input_focus_in(self, event):
        """Handle input focus in"""
        self.remove_placeholder()
        
    def on_input_focus_out(self, event):
        """Handle input focus out"""
        if not self.input_text.get("1.0", tk.END).strip():
            self.add_placeholder()
            
    def on_enter_key(self, event):
        """Handle Enter key press"""
        self.send_message()
        return 'break'
        
    def on_shift_enter(self, event):
        """Handle Shift+Enter (new line)"""
        return  # Allow default behavior
        
    def send_message(self):
        """Send user message and get AURA response"""
        message = self.input_text.get("1.0", tk.END).strip()
        
        if not message or message == self.placeholder_text:
            return
            
        # Clear input
        self.input_text.delete("1.0", tk.END)
        self.add_placeholder()
        
        # Check for exit commands
        if any(word in message.lower() for word in ["exit", "quit", "goodbye", "stop"]):
            self.add_user_message(message)
            self.add_aura_message(aura.get_goodbye_message())
            self.root.after(2000, self.on_closing)
            return
            
        # Add user message
        self.add_user_message(message)
        
        # Update status
        self.update_status("AURA neural networks processing...", "warning")
        
        # Disable send button
        self.send_button.config(state='disabled', text="PROCESSING...", bg=self.colors['warning'])
        
        # Process message in separate thread with proper tracking
        thread = threading.Thread(target=self.process_message, args=(message,))
        thread.daemon = True
        thread.name = f"AuraProcessor-{self.context['command_count']}"
        self.active_threads.append(thread)
        thread.start()
        
    def process_message(self, message, retry_count=0):
        """Process message with AURA (runs in separate thread)"""
        try:
            self.context["command_count"] += 1
            max_retries = 2  # Maximum 2 retries for syntax errors
            
            # Send processing message
            self.message_queue.put(("aura_response", aura.get_thinking_message(), "neural"))
            
            # Check if we have AI components available
            if not hasattr(self, 'ai_client') or not self.ai_client:
                self.message_queue.put(("aura_response", "Neural AI client not available. Please check initialization.", "error"))
                return
            
            # Always use AI to generate code to ensure user's specific requirements are met
            # This ensures that modifications like "open it", "save to D drive", etc. are handled
            code = self.ai_client.generate_code(message, self.context)
            
            if not code:
                self.message_queue.put(("aura_response", "Neural processing failed. Please rephrase your request for better comprehension.", "error"))
                self.message_queue.put(("button_enable", None, None))
                return
                
            # Show generated code
            self.message_queue.put(("code_display", code, "code"))
            self.message_queue.put(("aura_response", aura.get_acknowledgment(), "neural"))
            
            # Execute the code if executor is available
            if hasattr(self, 'executor') and self.executor:
                success, output, result = self.executor.execute(code, self.get_execution_context())
                
                if success:
                    # Check if the output contains error indicators even though execution "succeeded"
                    has_output_errors = (
                        output and (
                            "An error occurred:" in output or
                            "An unexpected error occurred:" in output or
                            "Error:" in output or
                            "Traceback" in output or
                            "Exception" in output or
                            "No such file or directory" in output or
                            "credentials.json not found" in output or
                            "Failure" in output or
                            "Failed to read" in output or
                            "Failed to" in output or
                            output.strip().endswith("False") and ("error" in output.lower() or "failed" in output.lower() or "Failure" in output)
                        )
                    )
                    
                    if has_output_errors:
                        # Treat as failure and attempt self-improvement
                        self.message_queue.put(("aura_response", "Code executed but produced errors. Attempting neural adaptation...", "neural"))
                        
                        if hasattr(self, 'improvement_engine') and self.improvement_engine:
                            improved, improvement_msg, execution_output = self.improvement_engine.handle_execution_failure(message, code, output)
                            
                            if improved:
                                full_message = f"Neural adaptation successful: {improvement_msg}"
                                if execution_output and execution_output.strip():
                                    full_message += f"\n\nTask completed successfully!\nOutput: {execution_output}"
                                self.message_queue.put(("aura_response", full_message, "success"))
                                self.speak_response("Task completed successfully after neural adaptation.")
                            else:
                                # Show the error even though execution "succeeded"
                                error_msg = f"Code execution produced errors. {improvement_msg}"
                                if output:
                                    error_msg += f"\n\nError details: {output}"
                                self.message_queue.put(("aura_response", error_msg, "error"))
                        else:
                            # Show the error even though execution "succeeded"
                            error_msg = "Code execution produced errors."
                            if output:
                                error_msg += f"\n\nError details: {output}"
                            self.message_queue.put(("aura_response", error_msg, "error"))
                    else:
                        # Record success if capability manager is available
                        if hasattr(self, 'capability_manager') and self.capability_manager:
                            self.capability_manager.record_execution(message, True)
                        
                        success_msg = aura.get_success_message()
                        if output:
                            success_msg += f"\n\nProcessing output:\n{output}"
                            
                        self.message_queue.put(("aura_response", success_msg, "success"))
                        
                        # Make AURA speak the response (extract speakable text)
                        speakable_text = self.extract_speakable_text(aura.get_success_message())
                        self.speak_response(speakable_text)
                else:
                    # Check if this is a validation failure (syntax error)
                    if output and "Validation failed" in output:
                        # This is a syntax/validation error, try to regenerate better code
                        self.message_queue.put(("aura_response", "Neural code generation error detected. Attempting regeneration with improved syntax...", "neural"))
                        
                        try:
                            # Check retry limit
                            if retry_count >= max_retries:
                                error_msg = aura.get_error_message() + f"\n\nSyntax validation failed after {max_retries} attempts. The AI generated code is malformed. Please try rephrasing your command or breaking it into smaller steps."
                                self.message_queue.put(("aura_response", error_msg, "error"))
                                return
                            
                            # Extract just the essential error info from validation error
                            error_match = None
                            if "Syntax error:" in output:
                                import re
                                # Extract the syntax error message
                                error_match = re.search(r'Syntax error: ([^\n]+)', output)
                            
                            # Create a focused prompt for fixing the syntax error
                            if error_match:
                                error_msg = error_match.group(1)
                                fix_prompt = f"""{message}

CRITICAL: The previous code had a syntax error: {error_msg}

Please generate CORRECT Python code without any syntax errors. Ensure all strings are properly terminated, all parentheses/brackets are balanced, and all syntax follows Python standards. Double-check your code before responding.
"""
                            else:
                                fix_prompt = f"""{message}

CRITICAL: The previous generated code had syntax errors that prevented execution. Please generate clean, valid Python code without any syntax errors. Ensure proper string termination, balanced brackets, and valid Python syntax. Review your code carefully for syntax errors.
"""
                            
                            # Generate new code with explicit instructions to fix syntax
                            fixed_code = self.ai_client.generate_code(fix_prompt, self.context)
                            
                            # If fixed code also has issues, recurse with incremented counter
                            if not fixed_code:
                                if retry_count < max_retries:
                                    self.process_message(message, retry_count + 1)
                                    return
                            
                            if fixed_code:
                                self.message_queue.put(("code_display", fixed_code, "code"))
                                
                                # Try executing the fixed code
                                fixed_success, fixed_output, fixed_result = self.executor.execute(fixed_code, self.get_execution_context())
                                
                                if fixed_success:
                                    if hasattr(self, 'capability_manager') and self.capability_manager:
                                        self.capability_manager.record_execution(message, True)
                                    
                                    success_msg = aura.get_success_message()
                                    if fixed_output:
                                        success_msg += f"\n\nProcessing output:\n{fixed_output}"
                                    self.message_queue.put(("aura_response", success_msg, "success"))
                                    self.speak_response("Task completed successfully after code regeneration.")
                                else:
                                    # Fixed code still failed
                                    # Check if it's another validation error - retry if we haven't exceeded max
                                    if fixed_output and "Validation failed" in fixed_output and retry_count < max_retries:
                                        # Recursively retry with incremented counter
                                        self.process_message(message, retry_count + 1)
                                        return
                                    
                                    # Fixed code still failed, use normal self-improvement flow
                                    if hasattr(self, 'improvement_engine') and self.improvement_engine:
                                        improved, improvement_msg, execution_output = self.improvement_engine.handle_execution_failure(message, fixed_code, fixed_output)
                                        
                                        if improved:
                                            full_message = f"Neural adaptation successful: {improvement_msg}"
                                            if execution_output and execution_output.strip():
                                                full_message += f"\n\nTask completed successfully!\nOutput: {execution_output}"
                                            self.message_queue.put(("aura_response", full_message, "success"))
                                            self.speak_response("Task completed successfully after neural adaptation.")
                                        else:
                                            error_msg = aura.get_error_message()
                                            if fixed_output:
                                                error_msg += f"\n\nTechnical analysis: {fixed_output}"
                                            self.message_queue.put(("aura_response", error_msg, "error"))
                                    else:
                                        error_msg = aura.get_error_message()
                                        if fixed_output:
                                            error_msg += f"\n\nTechnical analysis: {fixed_output}"
                                        self.message_queue.put(("aura_response", error_msg, "error"))
                            else:
                                # Couldn't regenerate, show error
                                error_msg = aura.get_error_message() + f"\n\nSyntax error in generated code. Please try rephrasing your command."
                                self.message_queue.put(("aura_response", error_msg, "error"))
                        except Exception as e:
                            logging.error(f"Error in code regeneration: {e}")
                            error_msg = aura.get_error_message() + f"\n\nCode regeneration failed: {str(e)}"
                            self.message_queue.put(("aura_response", error_msg, "error"))
                    else:
                        # Normal execution failure, use self-improvement
                        # Attempt self-improvement if available
                        if hasattr(self, 'improvement_engine') and self.improvement_engine:
                            improved, improvement_msg, execution_output = self.improvement_engine.handle_execution_failure(message, code, output)
                            
                            if improved:
                                # Show both the improvement message and the execution results
                                full_message = f"Neural adaptation successful: {improvement_msg}"
                                if execution_output and execution_output.strip():
                                    full_message += f"\n\nTask completed successfully!\nOutput: {execution_output}"
                                self.message_queue.put(("aura_response", full_message, "success"))
                                
                                # Make AURA speak the success response
                                self.speak_response("Task completed successfully after neural adaptation.")
                            else:
                                error_msg = aura.get_error_message()
                                if output:
                                    error_msg += f"\n\nTechnical analysis: {output}"
                                self.message_queue.put(("aura_response", error_msg, "error"))
                        else:
                            error_msg = aura.get_error_message()
                            if output:
                                error_msg += f"\n\nTechnical analysis: {output}"
                            self.message_queue.put(("aura_response", error_msg, "error"))
            else:
                self.message_queue.put(("aura_response", "Code executor not available. Code generated but not executed.", "warning"))
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"Error in process_message: {error_details}")
            error_msg = aura.get_error_message() + f"\n\nNeural error analysis: {str(e)}"
            self.message_queue.put(("aura_response", error_msg, "error"))
        finally:
            # Always re-enable the button and clean up thread tracking
            self.message_queue.put(("button_enable", None, None))
            
            # Remove this thread from active threads
            current_thread = threading.current_thread()
            if current_thread in self.active_threads:
                self.active_threads.remove(current_thread)
            
    def get_execution_context(self) -> Dict[str, Any]:
        """Get context for code execution"""
        context = {
            'context': self.context,
            'print': print,
            'input': input,
        }
        
        # Import system utilities
        try:
            import windows_system_utils
            for attr_name in dir(windows_system_utils):
                if not attr_name.startswith('_'):
                    context[attr_name] = getattr(windows_system_utils, attr_name)
        except Exception as e:
            logging.warning(f"Could not import system utilities: {e}")
        
        # Load dynamically generated capabilities
        try:
            self._load_generated_capabilities_into_context(context)
        except Exception as e:
            logging.warning(f"Could not load generated capabilities: {e}")
            
        return context
    
    def _load_generated_capabilities_into_context(self, context: Dict[str, Any]):
        """Load generated capabilities into execution context"""
        try:
            # Check if capability manager is available
            if not hasattr(self, 'capability_manager') or not self.capability_manager:
                return
                
            capabilities_count = len(self.capability_manager.capabilities)
            logging.info(f"GUI: Loading {capabilities_count} capabilities into execution context")
            
            # Get all capabilities from capability manager
            for capability_name, capability_data in self.capability_manager.capabilities.items():
                try:
                    # Execute the function code to make it available in context
                    function_code = capability_data.get("code", "")
                    if function_code:
                        # Create a temporary execution environment to define the function
                        temp_context = context.copy()
                        # Add builtins to temp context for proper execution
                        import builtins
                        temp_context['__builtins__'] = builtins.__dict__.copy()
                        exec(function_code, temp_context)
                        
                        # Extract the function from the temporary context and add to main context
                        function_loaded = False
                        for name, value in temp_context.items():
                            if not name.startswith('_') and callable(value) and name == capability_name:
                                context[capability_name] = value
                                logging.info(f"GUI: Successfully loaded capability {capability_name}")
                                function_loaded = True
                                break
                        
                        if not function_loaded:
                            logging.warning(f"GUI: Could not find function {capability_name} after execution")
                    else:
                        logging.warning(f"No function code found for capability: {capability_name}")
                except Exception as e:
                    logging.warning(f"Could not load capability {capability_name}: {e}")
        except Exception as e:
            logging.error(f"Error loading generated capabilities: {e}")
        
    def check_queue(self):
        """Check message queue for updates from worker threads"""
        try:
            while True:
                msg_type, message, style = self.message_queue.get_nowait()
                
                if msg_type == "aura_response":
                    self.add_aura_message(message, style)
                elif msg_type == "code_display":
                    self.add_aura_message("Neural code generation:", "neural")
                    self.add_aura_message(message, "code")
                elif msg_type == "button_enable":
                    # Re-enable send button
                    self.send_button.config(
                        state='normal',
                        text="EXECUTE",
                        bg=self.colors['accent']
                    )
                    self.update_status("AURA neural networks ready - Awaiting input", "success")
                
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Error in message queue processing: {e}")
            
        # Schedule next check
        self.root.after(100, self.check_queue)
        
    def toggle_voice_input(self):
        """Toggle voice input mode"""
        if not self.voice_enabled or not self.voice_interface:
            self.add_aura_message("Voice neural networks not available", "error")
            return
            
        if not hasattr(self, '_voice_listening') or not self._voice_listening:
            self.start_voice_input()
        else:
            self.stop_voice_input()
            
    def start_voice_input(self):
        """Start listening for voice input"""
        if not self.voice_enabled or not self.voice_interface:
            return
            
        self._voice_listening = True
        self.voice_btn.config(text="⏹", bg=self.colors['error'])
        self.voice_status_indicator.config(text="LISTENING", fg=self.colors['warning'])
        self.update_status("AURA voice recognition active - Speak now", "warning")
        
        # Start voice input in separate thread
        voice_thread = threading.Thread(target=self.process_voice_input, daemon=True)
        voice_thread.start()
        
    def stop_voice_input(self):
        """Stop listening for voice input"""
        if hasattr(self, '_voice_listening'):
            self._voice_listening = False
        self.voice_btn.config(text="🎤", bg=self.colors['bg_neural'])
        self.voice_status_indicator.config(text="VOICE ACTIVE", fg=self.colors['success'])
        self.update_status("Voice input terminated", "normal")
        
    def process_voice_input(self):
        """Process voice input in separate thread"""
        try:
            if not self.voice_enabled or not self.voice_interface:
                self.root.after(0, lambda: self.stop_voice_input())
                return
                
            if not hasattr(self, '_voice_listening') or not self._voice_listening:
                self.root.after(0, lambda: self.stop_voice_input())
                return
                
            # Get voice input
            voice_command = self.voice_interface.get_input()
            
            # Reset voice listening state
            self._voice_listening = False
            
            # Reset voice button state
            self.root.after(0, lambda: self.voice_btn.config(text="🎤", bg=self.colors['bg_neural']))
            
            if voice_command and voice_command.strip():
                # Add voice command to input field and process it
                self.root.after(0, lambda: self.process_voice_command(voice_command))
            else:
                # Voice input failed or was empty
                self.root.after(0, lambda: self.voice_status_indicator.config(text="VOICE ACTIVE", fg=self.colors['success']))
                self.root.after(0, lambda: self.update_status("Voice input failed - Neural analysis incomplete", "error"))
                
        except Exception as e:
            if hasattr(self, '_voice_listening'):
                self._voice_listening = False
            self.root.after(0, lambda: self.voice_btn.config(text="🎤", bg=self.colors['bg_neural']))
            self.root.after(0, lambda: self.voice_status_indicator.config(text="VOICE ERROR", fg=self.colors['error']))
            self.root.after(0, lambda: self.update_status(f"Voice neural error: {e}", "error"))
            
    def process_voice_command(self, command):
        """Process a voice command"""
        # Clear input and set the voice command
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", command)
        
        # Add user message showing it was voice input
        self.add_user_message(f"🎤 {command}")
        
        # Make AURA acknowledge voice command
        self.speak_response(aura.get_voice_confirmation())
        
        # Process the command
        self.send_message()
        
        # Reset voice status
        self.voice_status_indicator.config(text="VOICE ACTIVE", fg=self.colors['success'])
        
    def speak_response(self, text):
        """Speak AURA response using TTS"""
        if self.voice_enabled and self.voice_interface:
            try:
                self.voice_interface.output(text)
            except Exception as e:
                logging.error(f"TTS error: {e}")
        
    def extract_speakable_text(self, message):
        """Extract text suitable for TTS from AURA response"""
        lines = message.split('\n')
        speakable_lines = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('```') and 
                not line.startswith('Output:') and
                not line.startswith('Neural code generation:') and
                len(line) < 200 and
                not line.startswith('Technical analysis:') and
                not line.startswith('Neural error analysis:')):
                
                if line.startswith('Task completed successfully'):
                    speakable_lines.append("Task completed successfully")
                elif line.startswith('Neural networks'):
                    speakable_lines.append("Neural networks operational")
                elif line.startswith('Voice interface'):
                    speakable_lines.append("Voice interface activated")
                elif any(greeting in line.lower() for greeting in ['good morning', 'good afternoon', 'good evening']):
                    speakable_lines.append(line)
                elif line and not any(char in line for char in ['{', '}', '[', ']', '<', '>']):
                    speakable_lines.append(line)
        
        result = ' '.join(speakable_lines[:3])
        return result if len(result) < 300 else result[:300] + "..."
        
    def show_voice_installation_guide(self):
        """Show voice installation guide with AURA styling"""
        guide_msg = """🔧 Voice Neural Network Activation Guide:

To enable voice recognition neural networks, install the following modules:

1. Activate your virtual environment:
   • Windows: .\\venv\\Scripts\\activate

2. Install voice processing modules:
   pip install SpeechRecognition pyttsx3

3. For microphone neural interface (PyAudio):
   • Primary: pip install pyaudio
   • Alternative: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

4. Restart AURA interface for neural network activation."""
        
        self.add_aura_message(guide_msg, "error")
        self.update_status("Voice neural networks require additional modules", "warning")
        
    def show_pyaudio_installation_guide(self):
        """Show PyAudio installation guide with AURA styling"""
        guide_msg = """🎤 Neural Microphone Interface Required:

PyAudio is essential for microphone neural network access:

WINDOWS NEURAL INSTALLATION:
1. Download PyAudio neural driver:
   • Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
   • Select matching Python version wheel file
   • Execute: pip install downloaded_file.whl

2. Alternative neural activation:
   pip install pyaudio

3. If neural errors occur, install Visual C++ Build Tools:
   • Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

CRITICAL: Ensure virtual environment is active before neural installation!

After installation, restart AURA for full neural microphone integration."""
        
        self.add_aura_message(guide_msg, "error")
        self.update_status("Neural microphone interface requires PyAudio", "warning")
        
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
        
        # Add welcome message back
        welcome_msg = aura.get_greeting() + "\n\nNeural networks ready for processing."
        self.add_aura_message(welcome_msg)
        
    def open_file_dialog(self):
        """Open file dialog for neural processing"""
        filename = filedialog.askopenfilename(
            title="Select file for AURA neural processing",
            filetypes=[
                ("All files", "*.*"),
                ("Python files", "*.py"),
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
            ]
        )
        
        if filename:
            self.context["filename"] = filename
            self.add_aura_message(f"Neural file analysis ready: {os.path.basename(filename)}")
            
    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("AURA Settings")
        settings_window.geometry("600x400")
        settings_window.configure(bg=self.colors['bg_secondary'])
        
        # Center the settings window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        settings_frame = tk.Frame(settings_window, bg=self.colors['bg_secondary'])
        settings_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            settings_frame,
            text="AURA Configuration",
            font=('Orbitron', 16, 'bold'),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_aura']
        )
        title_label.pack(pady=(0, 20))
        
        # System status
        status_frame = tk.LabelFrame(
            settings_frame,
            text="System Status",
            font=('Orbitron', 12),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        status_frame.pack(fill='x', pady=(0, 15))
        
        # Status indicators
        ai_status = "✓ Online" if hasattr(self, 'ai_client') and self.ai_client else "✗ Offline"
        voice_status = "✓ Active" if self.voice_enabled else "✗ Inactive"
        executor_status = "✓ Ready" if hasattr(self, 'executor') and self.executor else "✗ Unavailable"
        
        tk.Label(status_frame, text=f"AI Client: {ai_status}", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        tk.Label(status_frame, text=f"Voice Interface: {voice_status}", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        tk.Label(status_frame, text=f"Code Executor: {executor_status}", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        
        # Session info
        session_frame = tk.LabelFrame(
            settings_frame,
            text="Session Information",
            font=('Orbitron', 12),
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary']
        )
        session_frame.pack(fill='x', pady=(0, 15))
        
        session_duration = datetime.now() - self.context["session_start"]
        tk.Label(session_frame, text=f"Session Duration: {str(session_duration).split('.')[0]}", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        tk.Label(session_frame, text=f"Commands Processed: {self.context['command_count']}", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', padx=10, pady=5)
        
        # Close button
        close_btn = tk.Button(
            settings_frame,
            text="Close",
            font=('Orbitron', 11, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            command=settings_window.destroy,
            padx=20,
            pady=10
        )
        close_btn.pack(pady=(20, 0))
            
    def on_closing(self):
        """Handle window closing with proper cleanup"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        self.add_aura_message("AURA neural networks shutting down gracefully...")
        self.update_status("AURA offline - Neural systems terminated", "error")
        
        # Cleanup voice interface
        if self.voice_interface:
            try:
                self.voice_interface.cleanup()
            except Exception as e:
                logging.error(f"Voice interface cleanup error: {e}")
        
        # Wait for active threads to finish (with timeout)
        if self.active_threads:
            self.root.after(2000, self._force_shutdown)
            # Give threads time to finish
            for thread in self.active_threads[:]:
                if thread.is_alive():
                    logging.info(f"Waiting for thread {thread.name} to finish...")
        else:
            self.root.after(1000, self.root.destroy)
            
    def _generate_parameter_extraction_code(self, function_name: str, message: str) -> str:
        """Generate code that extracts parameters from command and calls the function"""
        import re
        
        # Extract numerical parameters based on function type
        if function_name == "set_brightness":
            # Extract brightness level from commands like "set brightness to 34"
            brightness_match = re.search(r'(\d+)', message)
            if brightness_match:
                brightness_level = brightness_match.group(1)
                return f"""try:
    from windows_system_utils import {function_name}
    result = {function_name}({brightness_level})
    if result:
        print("Brightness set to {brightness_level}%")
    else:
        print("Failed to set brightness")
except Exception as e:
    print(f"Error calling {function_name}: {{e}}")"""
            else:
                return f"""print("Could not extract brightness level from: {message}")
print("Please specify a brightness level (0-100)")"""
        
        elif function_name == "set_system_volume":
            # Extract volume level from commands like "set volume to 50"
            volume_match = re.search(r'(\d+)', message)
            if volume_match:
                volume_level = volume_match.group(1)
                return f"""try:
    from windows_system_utils import {function_name}
    result = {function_name}({volume_level})
    if result:
        print("Volume set to {volume_level}%")
    else:
        print("Failed to set volume")
except Exception as e:
    print(f"Error calling {function_name}: {{e}}")"""
            else:
                return f"""print("Could not extract volume level from: {message}")
print("Please specify a volume level (0-100)")"""
        
        else:
            # For other functions without required parameters, call directly
            return f"""try:
    from windows_system_utils import {function_name}
    result = {function_name}()
    print(f"Function {function_name} executed: {{result}}")
except Exception as e:
    print(f"Error calling existing function: {{e}}")"""

    def _force_shutdown(self):
        """Force shutdown if threads don't finish gracefully"""
        logging.info("Forcing shutdown after timeout")
        self.root.destroy()
        
    def run(self):
        """Start the AURA GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()


def main():
    """Main entry point"""
    try:
        # Check if running in virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("⚠️  Warning: Virtual environment not detected!")
            print("Please activate your virtual environment before running AURA interface.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
        
        # Start the AURA GUI
        app = AuraGUI()
        app.run()
        return 0
        
    except Exception as e:
        messagebox.showerror("Neural Network Error", f"Failed to start AURA interface:\n{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
