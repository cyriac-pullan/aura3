"""
AURA Goal-Driven Architecture - Context Engine
Persistent memory of user preferences and system state.
This is what makes the agent feel intelligent.
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


# Context file location
CONTEXT_FILE = Path.home() / ".aura" / "context.json"


@dataclass
class ContextState:
    """
    Persistent context representing what AURA "remembers".
    Updated after each interaction.
    """
    # Current state
    active_app: str = ""
    running_apps: List[str] = field(default_factory=list)
    
    # History (for preference learning)
    last_media_app: str = "spotify"        # Last app used for media
    last_video_app: str = "youtube"        # Last app for video
    last_email_source: str = "gmail"       # Last email client
    last_browser: str = "chrome"           # Default browser
    
    # User preferences (learned over time)
    preferred_music_app: str = "spotify"
    preferred_video_app: str = "youtube"
    preferred_streaming_app: str = "netflix"
    preferred_email_app: str = "gmail"
    
    # Installed apps (cached for strategy selection)
    installed_apps: Dict[str, str] = field(default_factory=dict)  # name -> path
    
    # Recent commands (for context)
    recent_commands: List[str] = field(default_factory=list)
    
    # Timestamps
    last_updated: str = ""
    
    def update_last_used(self, app_type: str, app_name: str):
        """Update the last used app for a category"""
        if app_type == "media":
            self.last_media_app = app_name
        elif app_type == "video":
            self.last_video_app = app_name
        elif app_type == "email":
            self.last_email_source = app_name
        self.last_updated = datetime.now().isoformat()
    
    def add_recent_command(self, command: str):
        """Add to recent commands (keep last 20)"""
        self.recent_commands.append(command)
        if len(self.recent_commands) > 20:
            self.recent_commands = self.recent_commands[-20:]


class ContextEngine:
    """
    Manages persistent context state.
    Loads from disk, saves after changes.
    """
    
    def __init__(self):
        self.state = self._load_context()
        self._detect_installed_apps()
        logging.info("Context Engine initialized")
    
    def _load_context(self) -> ContextState:
        """Load context from disk"""
        try:
            if CONTEXT_FILE.exists():
                with open(CONTEXT_FILE, 'r') as f:
                    data = json.load(f)
                return ContextState(**data)
        except Exception as e:
            logging.warning(f"Could not load context: {e}")
        return ContextState()
    
    def save(self):
        """Save context to disk"""
        try:
            CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONTEXT_FILE, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)
        except Exception as e:
            logging.error(f"Could not save context: {e}")
    
    def _detect_installed_apps(self):
        """Detect commonly used apps"""
        import subprocess
        
        # Common app locations to check
        apps_to_check = {
            "spotify": ["spotify", "Spotify.exe"],
            "chrome": ["chrome", "Google Chrome"],
            "firefox": ["firefox"],
            "vlc": ["vlc"],
            "vscode": ["code", "Code.exe"],
            "whatsapp": ["WhatsApp"],
        }
        
        # Check Start Menu for installed apps
        start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        
        for app_name, patterns in apps_to_check.items():
            for pattern in patterns:
                # Check if executable exists via where command
                try:
                    result = subprocess.run(
                        f'where {pattern}', 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        self.state.installed_apps[app_name] = result.stdout.strip().split('\n')[0]
                        break
                except:
                    pass
    
    def get_preference(self, category: str) -> str:
        """Get user preference for a category"""
        prefs = {
            "music": self.state.preferred_music_app,
            "video": self.state.preferred_video_app,
            "streaming": self.state.preferred_streaming_app,
            "email": self.state.preferred_email_app,
            "browser": self.state.last_browser,
        }
        return prefs.get(category, "")
    
    def is_installed(self, app_name: str) -> bool:
        """Check if an app is installed"""
        return app_name.lower() in self.state.installed_apps
    
    def update_preference(self, category: str, app_name: str):
        """Update a preference after successful use"""
        if category == "music":
            self.state.preferred_music_app = app_name
            self.state.last_media_app = app_name
        elif category == "video":
            self.state.preferred_video_app = app_name
            self.state.last_video_app = app_name
        elif category == "email":
            self.state.preferred_email_app = app_name
            self.state.last_email_source = app_name
        
        self.state.last_updated = datetime.now().isoformat()
        self.save()
    
    def get_context_for_goal(self, goal_type: str) -> Dict[str, Any]:
        """Get relevant context for a goal type"""
        context = {
            "last_media_app": self.state.last_media_app,
            "last_browser": self.state.last_browser,
            "installed_apps": list(self.state.installed_apps.keys()),
        }
        
        if goal_type == "PLAY_MEDIA":
            context["preferred_music"] = self.state.preferred_music_app
            context["preferred_video"] = self.state.preferred_video_app
        elif goal_type == "CHECK_EMAIL":
            context["preferred_email"] = self.state.preferred_email_app
        
        return context


# Global context engine instance
_context_engine = None

def get_context_engine() -> ContextEngine:
    """Get the global context engine"""
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextEngine()
    return _context_engine
