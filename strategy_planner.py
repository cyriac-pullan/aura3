"""
AURA Goal-Driven Architecture - Strategy Planner
Human reasoning layer: Given a Goal + Context, decide how to achieve it.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from goal import Goal, GoalType, HumanActionPlan, ActionStep
from context_engine import ContextEngine, get_context_engine


class Strategy(ABC):
    """Base class for all strategies"""
    
    @abstractmethod
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        """Check if this strategy can handle the goal"""
        pass
    
    @abstractmethod
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        """Create a human action plan to achieve the goal"""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# MEDIA CONTROL STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class MediaKeyStrategy(Strategy):
    """Use OS-level media keys for play/pause/next/prev"""
    
    MEDIA_ACTIONS = {
        "play": "playpause",
        "pause": "playpause",
        "play_pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack",
        "prev": "prevtrack",
        "stop": "stop",
        "mute": "volumemute",
    }
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.CONTROL_MEDIA:
            return False
        action = goal.modifiers.get("action", "")
        return action.lower() in self.MEDIA_ACTIONS
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        action = goal.modifiers.get("action", "play_pause").lower()
        media_key = self.MEDIA_ACTIONS.get(action, "playpause")
        
        plan = HumanActionPlan(description=f"Media control: {action}")
        plan.key(media_key)
        return plan


class SpotifyStrategy(Strategy):
    """Open Spotify and play content"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.PLAY_MEDIA:
            return False
        # Use Spotify if explicitly requested or it's the preferred music app
        pref = goal.preference.lower()
        if pref == "spotify":
            return True
        if not pref and context.get_preference("music") == "spotify":
            return True
        return False
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(
            description=f"Play '{goal.content}' on Spotify",
            goal=goal
        )
        
        # Open Spotify via Start Menu
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("spotify")
        plan.wait(200)
        plan.key("enter")
        plan.wait(3000)  # Wait for Spotify to open
        
        if goal.content:
            # Search for content
            plan.hotkey("ctrl", "l")  # Focus search
            plan.wait(200)
            plan.type_text(goal.content)
            plan.wait(300)
            plan.key("enter")
            plan.wait(1000)
            plan.key("enter")  # Play first result
        
        # Update context
        context.update_preference("music", "spotify")
        
        return plan


class YouTubeStrategy(Strategy):
    """Open YouTube and play/search content"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.PLAY_MEDIA:
            return False
        pref = goal.preference.lower()
        if pref in ["youtube", "yt"]:
            return True
        # Use YouTube for video content
        if "video" in goal.modifiers.get("type", ""):
            return True
        return False
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(
            description=f"Play '{goal.content}' on YouTube",
            goal=goal
        )
        
        # Open browser and go to YouTube
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("chrome")
        plan.wait(200)
        plan.key("enter")
        plan.wait(2000)
        
        # Navigate to YouTube search
        plan.hotkey("ctrl", "l")
        plan.wait(200)
        
        if goal.content:
            plan.type_text(f"youtube.com/results?search_query={goal.content.replace(' ', '+')}")
        else:
            plan.type_text("youtube.com")
        
        plan.key("enter")
        plan.wait(2000)
        
        if goal.content:
            # Click first video result
            plan.key("tab")
            plan.wait(200)
            plan.key("enter")
        
        context.update_preference("video", "youtube")
        return plan


class NetflixStrategy(Strategy):
    """Open Netflix and search for content"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.PLAY_MEDIA:
            return False
        pref = goal.preference.lower()
        return pref == "netflix"
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(
            description=f"Play '{goal.content}' on Netflix",
            goal=goal
        )
        
        # Open browser and go to Netflix
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("chrome")
        plan.wait(200)
        plan.key("enter")
        plan.wait(2000)
        
        plan.hotkey("ctrl", "l")
        plan.wait(200)
        
        if goal.content:
            plan.type_text(f"netflix.com/search?q={goal.content.replace(' ', '%20')}")
        else:
            plan.type_text("netflix.com")
        
        plan.key("enter")
        
        return plan


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class GmailStrategy(Strategy):
    """Open Gmail"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type not in [GoalType.CHECK_EMAIL, GoalType.SEND_EMAIL]:
            return False
        pref = goal.preference.lower()
        if pref in ["gmail", "google"]:
            return True
        if not pref and context.get_preference("email") == "gmail":
            return True
        return False
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(description="Open Gmail", goal=goal)
        
        # Open browser and go to Gmail
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("chrome")
        plan.wait(200)
        plan.key("enter")
        plan.wait(2000)
        
        plan.hotkey("ctrl", "l")
        plan.wait(200)
        plan.type_text("mail.google.com")
        plan.key("enter")
        
        context.update_preference("email", "gmail")
        return plan


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CONTROL STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class VolumeStrategy(Strategy):
    """Control system volume"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.SYSTEM_CONTROL:
            return False
        control = goal.modifiers.get("control", "")
        return control in ["volume", "sound", "audio"]
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(description="Volume control", goal=goal)
        
        action = goal.modifiers.get("action", "")
        level = goal.modifiers.get("level")
        
        if action == "mute":
            plan.key("volumemute")
        elif action == "up":
            for _ in range(5):
                plan.key("volumeup")
        elif action == "down":
            for _ in range(5):
                plan.key("volumedown")
        elif level is not None:
            # Use nircmd or PowerShell for exact level
            pass
        
        return plan


class BrightnessStrategy(Strategy):
    """Control screen brightness"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        if goal.type != GoalType.SYSTEM_CONTROL:
            return False
        control = goal.modifiers.get("control", "")
        return control in ["brightness", "screen"]
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        # Brightness control typically needs PowerShell
        plan = HumanActionPlan(description="Brightness control", goal=goal)
        # Will be executed via function_executor fallback
        return plan


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAppStrategy(Strategy):
    """Open any application via Start Menu"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        return goal.type == GoalType.OPEN_APP
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        app_name = goal.content or goal.preference
        plan = HumanActionPlan(description=f"Open {app_name}", goal=goal)
        
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text(app_name)
        plan.wait(300)
        plan.key("enter")
        
        return plan


class CloseAppStrategy(Strategy):
    """Close application via Alt+F4"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        return goal.type == GoalType.CLOSE_APP
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(description=f"Close {goal.content}", goal=goal)
        plan.hotkey("alt", "f4")
        return plan


# ═══════════════════════════════════════════════════════════════════════════════
# WEB STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════════

class WebSearchStrategy(Strategy):
    """Search the web"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        return goal.type == GoalType.WEB_SEARCH
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        plan = HumanActionPlan(description=f"Search: {goal.content}", goal=goal)
        
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("chrome")
        plan.wait(200)
        plan.key("enter")
        plan.wait(2000)
        
        plan.hotkey("ctrl", "l")
        plan.wait(200)
        plan.type_text(f"google.com/search?q={goal.content.replace(' ', '+')}")
        plan.key("enter")
        
        return plan


class OpenWebsiteStrategy(Strategy):
    """Open a specific website"""
    
    def applicable(self, goal: Goal, context: ContextEngine) -> bool:
        return goal.type == GoalType.OPEN_WEBSITE
    
    def plan(self, goal: Goal, context: ContextEngine) -> HumanActionPlan:
        url = goal.content
        if not url.startswith("http"):
            url = "https://" + url
        
        plan = HumanActionPlan(description=f"Open {url}", goal=goal)
        
        plan.hotkey("win")
        plan.wait(300)
        plan.type_text("chrome")
        plan.wait(200)
        plan.key("enter")
        plan.wait(2000)
        
        plan.hotkey("ctrl", "l")
        plan.wait(200)
        plan.type_text(url)
        plan.key("enter")
        
        return plan


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY PLANNER
# ═══════════════════════════════════════════════════════════════════════════════

class StrategyPlanner:
    """
    Main strategy planner - routes goals to appropriate strategies.
    Uses the first applicable strategy.
    """
    
    def __init__(self):
        self.context = get_context_engine()
        
        # Register strategies in priority order
        self.strategies: List[Strategy] = [
            # Media control (highest priority for quick actions)
            MediaKeyStrategy(),
            
            # Specific app strategies
            SpotifyStrategy(),
            YouTubeStrategy(),
            NetflixStrategy(),
            
            # Email
            GmailStrategy(),
            
            # System control
            VolumeStrategy(),
            BrightnessStrategy(),
            
            # Generic app/web
            OpenAppStrategy(),
            CloseAppStrategy(),
            WebSearchStrategy(),
            OpenWebsiteStrategy(),
        ]
        
        logging.info(f"Strategy Planner initialized with {len(self.strategies)} strategies")
    
    def plan(self, goal: Goal) -> Optional[HumanActionPlan]:
        """Find a strategy and create a plan for the goal"""
        for strategy in self.strategies:
            if strategy.applicable(goal, self.context):
                logging.info(f"Using strategy: {strategy.__class__.__name__}")
                return strategy.plan(goal, self.context)
        
        logging.warning(f"No strategy found for goal: {goal.type}")
        return None
    
    def get_context(self) -> ContextEngine:
        """Get the context engine"""
        return self.context


# Global instance
_planner_instance = None

def get_strategy_planner() -> StrategyPlanner:
    """Get the global strategy planner"""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = StrategyPlanner()
    return _planner_instance
