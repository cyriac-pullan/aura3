"""
AURA v3 - LLM-Based Intent Router
Uses LLM to understand user intent instead of regex patterns.
If intent matches a known tool, call it. Otherwise, generate code.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import IntEnum


class MatchQuality(IntEnum):
    """Quality levels for pattern matches"""
    EXACT = 4
    SPECIFIC = 3
    GENERIC = 2
    KEYWORD = 1
    FUZZY = 0


@dataclass
class RouteResult:
    """Result of intent classification"""
    confidence: float
    function: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    is_conversation: bool = False
    match_type: str = "none"
    match_quality: MatchQuality = MatchQuality.FUZZY
    raw_command: str = ""
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    needs_code_generation: bool = False
    
    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))


class IntentRouter:
    """LLM-based intent router - understands any natural language command"""
    
    # All known tools with their descriptions and parameters
    KNOWN_TOOLS = [
        # Volume Control
        {"name": "set_system_volume", "description": "Set system volume to a specific level", "params": {"level": "int (0-100)"}},
        {"name": "mute_system_volume", "description": "Mute the system audio", "params": {}},
        {"name": "unmute_system_volume", "description": "Unmute the system audio", "params": {}},
        {"name": "increase_volume", "description": "Increase volume", "params": {"change": "int (default 10)"}},
        {"name": "decrease_volume", "description": "Decrease volume", "params": {"change": "int (default -10)"}},
        
        # Brightness Control
        {"name": "set_brightness", "description": "Set screen brightness to a level", "params": {"level": "int (0-100)"}},
        {"name": "increase_brightness", "description": "Increase screen brightness", "params": {"change": "int (default 20)"}},
        {"name": "decrease_brightness", "description": "Decrease screen brightness", "params": {"change": "int (default -20)"}},
        
        # YouTube
        {"name": "play_youtube", "description": "Open YouTube and play/search for music or videos", "params": {"query": "str (search query, empty to just open)"}},
        {"name": "play_youtube_video_ultra_direct", "description": "Play a specific YouTube video directly", "params": {"query": "str"}},
        
        # Spotify
        {"name": "play_spotify", "description": "Open Spotify and start playing music (opens web player with Top Hits if no query)", "params": {"query": "str (song/artist/playlist, optional)"}},
        
        # Email
        {"name": "open_email", "description": "Open email/Gmail inbox", "params": {}},
        {"name": "draft_email", "description": "Draft/compose an email", "params": {"recipient": "str", "instruction": "str (what the email should be about)"}},
        {"name": "compose_email", "description": "Compose email with subject", "params": {"to": "str", "subject": "str"}},
        {"name": "send_email", "description": "Send an email via SMTP", "params": {"to": "str", "subject": "str", "body": "str"}},
        
        # App Creation (Agentic - generates, tests, fixes code automatically)
        {"name": "create_app", "description": "Create a Python app/application with GUI (calculator, todo list, game, etc). Generates code, tests it, fixes errors automatically.", "params": {"description": "str (what kind of app to create)", "app_name": "str (optional)"}},
        
        # Applications
        {"name": "open_application", "description": "Open/launch an application", "params": {"app_name": "str"}},
        {"name": "close_application", "description": "Close/exit an application", "params": {"app_name": "str"}},
        
        # File Operations
        {"name": "open_file_explorer", "description": "Open file explorer/file manager", "params": {}},
        {"name": "create_folder", "description": "Create a new folder/directory", "params": {"name": "str"}},
        {"name": "create_file", "description": "Create a new file with optional content", "params": {"file_name": "str", "content": "str (optional)", "location": "str (optional, e.g., 'D' or 'D drive' or full path)"}},
        
        # System Operations
        {"name": "take_screenshot", "description": "Take a screenshot", "params": {}},
        {"name": "open_camera_app", "description": "Open camera app", "params": {}},
        {"name": "lock_workstation", "description": "Lock the computer/screen", "params": {}},
        {"name": "restart_explorer", "description": "Restart Windows Explorer", "params": {}},
        {"name": "empty_recycle_bin", "description": "Empty the recycle bin", "params": {}},
        {"name": "night_light_on", "description": "Turn on night light/blue light filter", "params": {}},
        {"name": "night_light_off", "description": "Turn off night light", "params": {}},
        {"name": "airplane_mode_on", "description": "Enable airplane mode", "params": {}},
        {"name": "airplane_mode_off", "description": "Disable airplane mode", "params": {}},
        {"name": "hide_desktop_icons", "description": "Hide desktop icons", "params": {}},
        {"name": "show_desktop_icons", "description": "Show desktop icons", "params": {}},
        {"name": "system_info", "description": "Show system info (battery, CPU, RAM)", "params": {}},
        {"name": "shutdown_computer", "description": "Shutdown the computer", "params": {}},
        {"name": "restart_computer", "description": "Restart/reboot the computer", "params": {}},
        {"name": "sleep_computer", "description": "Put computer to sleep", "params": {}},
        
        # Calculator
        {"name": "open_calculator", "description": "Open calculator app", "params": {}},
        {"name": "calculate", "description": "Calculate a math expression", "params": {"expression": "str"}},
        
        # Clipboard
        {"name": "copy_text", "description": "Copy text/selection", "params": {}},
        {"name": "paste_text", "description": "Paste text", "params": {}},
        
        # Time/Date
        {"name": "get_time", "description": "Get current time", "params": {}},
        {"name": "get_date", "description": "Get current date", "params": {}},
        
        # Web/Search
        {"name": "google_search", "description": "Search Google for something", "params": {"query": "str"}},
        {"name": "open_website", "description": "Open a website URL", "params": {"url": "str"}},
        
        # Weather
        {"name": "get_weather", "description": "Get weather information", "params": {"location": "str (optional)"}},
        
        # Timer/Reminder
        {"name": "set_timer", "description": "Set a timer", "params": {"duration": "str", "unit": "str (minutes/hours/seconds)"}},
        {"name": "set_reminder", "description": "Set a reminder", "params": {"message": "str"}},
        
        # Media Control
        {"name": "play_media", "description": "Resume/play currently paused media (press play button)", "params": {}},
        {"name": "pause_media", "description": "Pause currently playing media", "params": {}},
        {"name": "stop_media", "description": "Stop media playback", "params": {}},
        {"name": "next_track", "description": "Skip to next track/song", "params": {}},
        {"name": "previous_track", "description": "Go to previous track/song", "params": {}},
        
        # PowerPoint
        {"name": "create_powerpoint_presentation", "description": "Create a PowerPoint presentation", "params": {"topic": "str"}},
        
        # News
        {"name": "get_news", "description": "Get latest news headlines", "params": {}},
        {"name": "create_ai_news_file", "description": "Get AI/tech news", "params": {}},
        
        # Terminal
        {"name": "run_terminal_command", "description": "Run a terminal/command line command", "params": {"command": "str"}},
        {"name": "open_terminal", "description": "Open terminal/PowerShell/CMD", "params": {}},
        
        # Keyboard
        {"name": "type_text", "description": "Type text", "params": {"text": "str"}},
        {"name": "press_key", "description": "Press a keyboard key", "params": {"key": "str"}},
        {"name": "hotkey", "description": "Press keyboard shortcut/hotkey", "params": {"keys": "str"}},
        
        # Mouse
        {"name": "mouse_click", "description": "Click mouse at position", "params": {"x": "int (optional)", "y": "int (optional)"}},
        {"name": "right_click", "description": "Right click", "params": {}},
        {"name": "double_click", "description": "Double click", "params": {}},
        {"name": "scroll", "description": "Scroll up or down", "params": {"clicks": "int (positive=up, negative=down)"}},
        
        # Window Management
        {"name": "minimize_all_windows", "description": "Minimize all windows/show desktop", "params": {}},
        {"name": "switch_window", "description": "Switch to next window (Alt+Tab)", "params": {}},
        {"name": "close_window", "description": "Close current window", "params": {}},
        {"name": "maximize_window", "description": "Maximize current window", "params": {}},
        {"name": "snap_window_left", "description": "Snap window to left half", "params": {}},
        {"name": "snap_window_right", "description": "Snap window to right half", "params": {}},
        
        # Git
        {"name": "git_status", "description": "Show git status", "params": {}},
        {"name": "git_pull", "description": "Git pull latest changes", "params": {}},
        {"name": "git_commit", "description": "Git commit with message", "params": {"message": "str"}},
        {"name": "git_push", "description": "Git push changes", "params": {}},
        
        # WhatsApp
        {"name": "open_whatsapp", "description": "Open WhatsApp", "params": {}},
        {"name": "whatsapp_send_message", "description": "Send WhatsApp message", "params": {"contact": "str", "message": "str"}},
        
        # Screen Recording
        {"name": "start_screen_recording", "description": "Start screen recording", "params": {}},
        {"name": "stop_screen_recording", "description": "Stop screen recording", "params": {}},
        
        # Browser Control
        {"name": "browser_new_tab", "description": "Open new browser tab", "params": {}},
        {"name": "browser_close_tab", "description": "Close current browser tab", "params": {}},
        {"name": "browser_refresh", "description": "Refresh/reload page", "params": {}},
        {"name": "browser_back", "description": "Go back in browser", "params": {}},
        {"name": "browser_forward", "description": "Go forward in browser", "params": {}},
        
        # Shortcuts
        {"name": "select_all", "description": "Select all (Ctrl+A)", "params": {}},
        {"name": "undo", "description": "Undo (Ctrl+Z)", "params": {}},
        {"name": "redo", "description": "Redo (Ctrl+Y)", "params": {}},
        {"name": "save", "description": "Save file (Ctrl+S)", "params": {}},
        {"name": "find", "description": "Find in page", "params": {"query": "str"}},
    ]
    
    def __init__(self):
        self._ai_client = None
        self._tools_prompt = self._build_tools_prompt()
        logging.info(f"LLM Intent Router initialized with {len(self.KNOWN_TOOLS)} tools")
    
    @property
    def ai_client(self):
        """Lazy load AI client"""
        if self._ai_client is None:
            try:
                from ai_client import ai_client
                self._ai_client = ai_client
            except Exception as e:
                logging.error(f"Could not load AI client: {e}")
        return self._ai_client
    
    def _build_tools_prompt(self) -> str:
        """Build the tools list for the LLM prompt"""
        tools_text = []
        for tool in self.KNOWN_TOOLS:
            params_str = ", ".join([f"{k}: {v}" for k, v in tool["params"].items()]) if tool["params"] else "none"
            tools_text.append(f"- {tool['name']}: {tool['description']} | params: {params_str}")
        return "\n".join(tools_text)
    
    def _is_conversation(self, command: str) -> bool:
        """Quick check if this is clearly a conversation/question"""
        command_lower = command.lower().strip()
        
        # Questions that are NOT action requests
        conversation_starters = [
            "what is", "what are", "what's", "who is", "who are",
            "why is", "why are", "how does", "how do", "can you explain",
            "tell me about", "explain", "describe", "teach me",
            "compare", "difference between", "versus", "vs"
        ]
        
        for starter in conversation_starters:
            if command_lower.startswith(starter):
                # But exclude action-oriented questions
                action_exceptions = ["what time", "what date", "what's the weather", "what is the time"]
                if not any(exc in command_lower for exc in action_exceptions):
                    return True
        
        # Ends with ? and is clearly conversational
        if command_lower.endswith("?") and len(command_lower.split()) > 5:
            return True
        
        return False
    
    def classify(self, command: str, context: Optional[Any] = None) -> RouteResult:
        """Classify user command using LLM"""
        command_clean = command.strip()
        
        logging.info(f"LLM Intent Router classifying: '{command_clean}'")
        
        # Quick check for conversations
        if self._is_conversation(command_clean):
            logging.info("Detected conversation intent")
            return RouteResult(
                confidence=0.95,
                is_conversation=True,
                match_type="conversation",
                raw_command=command_clean
            )
        
        # Use LLM to understand intent
        if not self.ai_client:
            logging.error("AI client not available, falling back to code generation")
            return RouteResult(
                confidence=0.0,
                match_type="none",
                raw_command=command_clean,
                needs_code_generation=True
            )
        
        try:
            result = self._classify_with_llm(command_clean)
            return result
        except Exception as e:
            logging.error(f"LLM classification error: {e}")
            return RouteResult(
                confidence=0.0,
                match_type="none",
                raw_command=command_clean,
                needs_code_generation=True
            )
    
    def _classify_with_llm(self, command: str) -> RouteResult:
        """Use LLM to classify the command"""
        
        prompt = f"""You are an intent classifier for a voice assistant. Given a user command, determine which tool to use.

AVAILABLE TOOLS:
{self._tools_prompt}

USER COMMAND: "{command}"

INSTRUCTIONS:
1. If the command matches one of the available tools, respond with the tool name and extracted parameters
2. If the command is a general question or conversation, respond with "CONVERSATION"
3. If no tool matches and it requires generating custom code, respond with "GENERATE_CODE"

Respond ONLY with valid JSON in this exact format:
{{"action": "TOOL" or "CONVERSATION" or "GENERATE_CODE", "tool_name": "tool_name_here or null", "params": {{"param_name": "value"}} or {{}}}}

Examples:
- "set volume to 50" -> {{"action": "TOOL", "tool_name": "set_system_volume", "params": {{"level": 50}}}}
- "play despacito on youtube" -> {{"action": "TOOL", "tool_name": "play_youtube", "params": {{"query": "despacito"}}}}
- "what is machine learning" -> {{"action": "CONVERSATION", "tool_name": null, "params": {{}}}}
- "create a todo app with python" -> {{"action": "GENERATE_CODE", "tool_name": null, "params": {{}}}}

JSON RESPONSE:"""

        # Call LLM with retry
        import time
        max_retries = 3
        response_text = "{}"
        
        for attempt in range(max_retries):
            try:
                response = self.ai_client.client.models.generate_content(
                    model=self.ai_client.model,
                    contents=prompt
                )
                response_text = response.text.strip()
                break
            except Exception as e:
                error_str = str(e)
                # Check for rate limit errors
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # 2, 4 seconds
                        logging.warning(f"Rate limit hit in intent classification, waiting {wait_time}s (retry {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Intent classification error: {e}")
                # If we fail completely, return early to trigger fallback
                if attempt == max_retries - 1:
                    raise
        
        logging.debug(f"LLM classification response: {response_text}")
        
        # Parse JSON response
        try:
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            action = result.get("action", "GENERATE_CODE")
            tool_name = result.get("tool_name")
            params = result.get("params", {})
            
            if action == "CONVERSATION":
                return RouteResult(
                    confidence=0.95,
                    is_conversation=True,
                    match_type="llm_conversation",
                    raw_command=command
                )
            
            if action == "TOOL" and tool_name:
                # Validate tool exists
                valid_tools = [t["name"] for t in self.KNOWN_TOOLS]
                if tool_name in valid_tools:
                    logging.info(f"LLM matched tool: {tool_name} with params: {params}")
                    return RouteResult(
                        confidence=0.90,
                        function=tool_name,
                        args=params,
                        match_type="llm_tool",
                        match_quality=MatchQuality.SPECIFIC,
                        raw_command=command
                    )
                else:
                    logging.warning(f"LLM suggested unknown tool: {tool_name}")
            
            # Fall back to code generation
            logging.info("LLM suggests code generation")
            return RouteResult(
                confidence=0.0,
                match_type="none",
                raw_command=command,
                needs_code_generation=True
            )
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            logging.error(f"Response was: {response_text}")
            return RouteResult(
                confidence=0.0,
                match_type="none",
                raw_command=command,
                needs_code_generation=True
            )


# Global instance
_router_instance = None

def get_intent_router() -> IntentRouter:
    """Get or create the global intent router"""
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance


def classify_command(command: str) -> RouteResult:
    """Convenience function for classifying a command"""
    return get_intent_router().classify(command)