"""
AURA Goal-Driven Architecture - Goal Object
Semantic, app-agnostic representation of user intent.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class GoalType(str, Enum):
    """Types of goals AURA can understand"""
    # Media
    PLAY_MEDIA = "PLAY_MEDIA"
    CONTROL_MEDIA = "CONTROL_MEDIA"
    
    # Communication
    CHECK_EMAIL = "CHECK_EMAIL"
    SEND_EMAIL = "SEND_EMAIL"
    SEND_MESSAGE = "SEND_MESSAGE"
    
    # Applications
    OPEN_APP = "OPEN_APP"
    CLOSE_APP = "CLOSE_APP"
    
    # System
    SYSTEM_CONTROL = "SYSTEM_CONTROL"  # volume, brightness, etc.
    FILE_OPERATION = "FILE_OPERATION"
    
    # Web
    WEB_SEARCH = "WEB_SEARCH"
    OPEN_WEBSITE = "OPEN_WEBSITE"
    
    # Productivity
    CREATE_CONTENT = "CREATE_CONTENT"  # apps, docs, presentations
    
    # Conversation (no action needed)
    CONVERSATION = "CONVERSATION"
    
    # Unknown - needs code generation
    UNKNOWN = "UNKNOWN"


@dataclass
class Goal:
    """
    Semantic representation of what the user wants.
    App-agnostic - does not specify HOW to do it.
    
    Examples:
    - "play some jazz" → Goal(type=PLAY_MEDIA, content="jazz")
    - "pause" → Goal(type=CONTROL_MEDIA, modifiers={"action": "pause"})
    - "open netflix and play stranger things" → Goal(type=PLAY_MEDIA, content="stranger things", preference="netflix")
    """
    type: GoalType
    content: str = ""           # What to play/search/send
    preference: str = ""        # Which app/service (spotify, netflix, gmail)
    modifiers: Dict[str, Any] = field(default_factory=dict)
    raw_command: str = ""       # Original user command
    
    # Confidence from LLM
    confidence: float = 0.9
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = GoalType(self.type)


@dataclass
class ActionStep:
    """
    Single atomic action in a human action plan.
    These are the building blocks of execution.
    """
    type: str  # KEY, HOTKEY, TYPE, CLICK, WAIT, SCROLL
    
    # For KEY/HOTKEY actions
    keys: List[str] = field(default_factory=list)
    
    # For TYPE action
    text: str = ""
    
    # For WAIT action
    ms: int = 500
    
    # For CLICK action
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"
    
    # For SCROLL action
    clicks: int = 3


@dataclass
class HumanActionPlan:
    """
    A sequence of atomic actions that achieve a goal.
    This is what a human would do step by step.
    
    Example for "play jazz on spotify":
    1. Press Win key
    2. Type "spotify"
    3. Press Enter
    4. Wait 3000ms
    5. Press Ctrl+L
    6. Type "jazz"
    7. Press Enter
    """
    steps: List[ActionStep] = field(default_factory=list)
    description: str = ""
    goal: Optional[Goal] = None
    
    # For recovery
    fallback_plan: Optional['HumanActionPlan'] = None
    
    def add_step(self, step_type: str, **kwargs) -> 'HumanActionPlan':
        """Fluent interface for building plans"""
        self.steps.append(ActionStep(type=step_type, **kwargs))
        return self
    
    def key(self, *keys) -> 'HumanActionPlan':
        """Add a key press"""
        return self.add_step("KEY", keys=list(keys))
    
    def hotkey(self, *keys) -> 'HumanActionPlan':
        """Add a hotkey combination"""
        return self.add_step("HOTKEY", keys=list(keys))
    
    def type_text(self, text: str) -> 'HumanActionPlan':
        """Add typing action"""
        return self.add_step("TYPE", text=text)
    
    def wait(self, ms: int = 500) -> 'HumanActionPlan':
        """Add wait action"""
        return self.add_step("WAIT", ms=ms)
    
    def click(self, x: int = None, y: int = None, button: str = "left") -> 'HumanActionPlan':
        """Add click action"""
        return self.add_step("CLICK", x=x, y=y, button=button)


# Convenience factory functions
def create_goal(goal_type: str, content: str = "", preference: str = "", **modifiers) -> Goal:
    """Create a goal from LLM output"""
    return Goal(
        type=GoalType(goal_type) if isinstance(goal_type, str) else goal_type,
        content=content,
        preference=preference,
        modifiers=modifiers
    )
