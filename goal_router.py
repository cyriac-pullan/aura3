"""
AURA Goal-Driven Architecture - Goal Router
Replaces intent_router for the goal-driven flow.
Uses LLM to extract Goal objects, then routes to strategies.
"""

import json
import logging
import re
import time
from typing import Optional, Tuple
from dataclasses import asdict

from goal import Goal, GoalType, HumanActionPlan
from context_engine import get_context_engine
from strategy_planner import get_strategy_planner
from plan_executor import get_plan_executor


class GoalRouter:
    """
    Routes user commands through the goal-driven pipeline:
    1. LLM extracts Goal from command
    2. Strategy Planner creates HumanActionPlan
    3. Plan Executor executes with keyboard/mouse
    """
    
    # Prompt for goal extraction
    GOAL_EXTRACTION_PROMPT = """You are a goal-understanding module for a desktop AI assistant.
Convert the user's command into a GOAL object.

GOAL TYPES:
- PLAY_MEDIA: Play music, video, movie, song, playlist
- CONTROL_MEDIA: Pause, play, next, previous, stop, mute
- CHECK_EMAIL: Open/check email
- SEND_EMAIL: Compose/send email
- OPEN_APP: Open/launch an application
- CLOSE_APP: Close/exit an application
- SYSTEM_CONTROL: Volume, brightness, settings
- WEB_SEARCH: Search Google/web
- OPEN_WEBSITE: Open a specific website
- CREATE_CONTENT: Create an app, document, presentation
- CONVERSATION: Just chatting, questions
- UNKNOWN: Can't determine

RULES:
1. Do NOT mention specific apps unless user explicitly does
2. Infer reasonable preferences from context
3. Output ONLY valid JSON

OUTPUT FORMAT:
{
  "goal_type": "PLAY_MEDIA",
  "content": "what to play/search/do",
  "preference": "app/service if specified (spotify, netflix, gmail, etc)",
  "modifiers": {
    "action": "pause/next/up/down etc for control actions",
    "level": 50 for volume/brightness levels
  }
}

EXAMPLES:
User: "play some jazz" → {"goal_type": "PLAY_MEDIA", "content": "jazz", "preference": "", "modifiers": {}}
User: "pause" → {"goal_type": "CONTROL_MEDIA", "content": "", "preference": "", "modifiers": {"action": "pause"}}
User: "open netflix and play stranger things" → {"goal_type": "PLAY_MEDIA", "content": "stranger things", "preference": "netflix", "modifiers": {}}
User: "set volume to 50" → {"goal_type": "SYSTEM_CONTROL", "content": "", "preference": "", "modifiers": {"control": "volume", "action": "set", "level": 50}}
User: "check my email" → {"goal_type": "CHECK_EMAIL", "content": "", "preference": "", "modifiers": {}}
User: "what's the weather" → {"goal_type": "CONVERSATION", "content": "what's the weather", "preference": "", "modifiers": {}}

USER COMMAND: "{command}"

JSON RESPONSE:"""
    
    def __init__(self):
        self._ai_client = None
        self.planner = get_strategy_planner()
        self.executor = get_plan_executor()
        logging.info("Goal Router initialized")
    
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
    
    def extract_goal(self, command: str) -> Goal:
        """Use LLM to extract a Goal from the user's command - with retry for rate limits"""
        import time
        
        # Clean command (strip quotes, whitespace)
        command = self._clean_command(command)
        
        if not self.ai_client:
            logging.error("AI client not available")
            return Goal(type=GoalType.UNKNOWN, raw_command=command)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                prompt = self.GOAL_EXTRACTION_PROMPT.format(command=command)
                logging.info(f"Goal Router: Calling LLM for '{command}'... (attempt {attempt + 1})")
                
                response = self.ai_client.client.models.generate_content(
                    model=self.ai_client.model,
                    contents=prompt
                )
                
                logging.info(f"Goal Router: Got LLM response")
                response_text = response.text.strip()
                logging.info(f"Goal LLM raw: {response_text[:300]}")
                
                # Parse JSON
                goal_data = self._parse_json_response(response_text)
                
                goal = Goal(
                    type=GoalType(goal_data.get("goal_type", "UNKNOWN")),
                    content=goal_data.get("content", ""),
                    preference=goal_data.get("preference", ""),
                    modifiers=goal_data.get("modifiers", {}),
                    raw_command=command
                )
                
                logging.info(f"LLM Goal: {goal.type} content='{goal.content}' pref='{goal.preference}'")
                return goal
                
            except Exception as e:
                error_str = str(e)
                # Check for rate limit errors
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # 2, 4 seconds
                        logging.warning(f"Rate limit hit in goal extraction, waiting {wait_time}s (retry {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Goal extraction error: {e}")
        
        return Goal(type=GoalType.UNKNOWN, raw_command=command)
    
    def extract_goals_batch(self, commands: list) -> list:
        """
        Extract goals for multiple commands in ONE LLM call
        This reduces API calls from N to 1, avoiding rate limits
        
        Args:
            commands: List of command strings
            
        Returns:
            List of Goal objects (same order as input)
        """
        if not commands:
            return []
        
        if not self.ai_client:
            logging.error("AI client not available")
            return [Goal(type=GoalType.UNKNOWN, raw_command=cmd) for cmd in commands]
        
        # Build batch prompt
        commands_text = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(commands)])
        
        batch_prompt = f"""You are a goal extraction AI. Extract goals for ALL commands below in ONE response.

GOAL TYPES: PLAY_MEDIA, CONTROL_MEDIA, OPEN_APP, OPEN_WEBSITE, WEB_SEARCH, CHECK_EMAIL, SEND_EMAIL, SYSTEM_CONTROL, CREATE_CONTENT, CONVERSATION, UNKNOWN

OUTPUT: Return a JSON array with one object per command, in the SAME ORDER.

FORMAT:
[
  {{"goal_type": "...", "content": "...", "preference": "", "modifiers": {{}}}},
  {{"goal_type": "...", "content": "...", "preference": "", "modifiers": {{}}}}
]

COMMANDS:
{commands_text}

JSON ARRAY:"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.ai_client.client.models.generate_content(
                    model=self.ai_client.model,
                    contents=batch_prompt
                )
                
                response_text = response.text.strip()
                logging.info(f"Batch goal extraction response: {response_text[:200]}")
                
                # Parse JSON array
                goals_data = self._parse_json_response(response_text)
                
                # Handle both array and object responses
                if isinstance(goals_data, list):
                    goals_list = goals_data
                elif isinstance(goals_data, dict) and "goals" in goals_data:
                    goals_list = goals_data["goals"]
                else:
                    raise ValueError("Response is not a list or dict with 'goals' key")
                
                # Convert to Goal objects
                goals = []
                for i, (cmd, goal_data) in enumerate(zip(commands, goals_list)):
                    try:
                        goal = Goal(
                            type=GoalType(goal_data.get("goal_type", "UNKNOWN")),
                            content=goal_data.get("content", ""),
                            preference=goal_data.get("preference", ""),
                            modifiers=goal_data.get("modifiers", {}),
                            raw_command=cmd
                        )
                        goals.append(goal)
                    except Exception as e:
                        logging.error(f"Error parsing goal {i+1}: {e}")
                        goals.append(Goal(type=GoalType.UNKNOWN, raw_command=cmd))
                
                logging.info(f"Batch extracted {len(goals)} goals successfully")
                return goals
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        logging.warning(f"Rate limit in batch extraction, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Batch goal extraction error: {e}")
        
        # Fallback: return UNKNOWN for all
        return [Goal(type=GoalType.UNKNOWN, raw_command=cmd) for cmd in commands]
    
    def _clean_command(self, command: str) -> str:
        """Clean command text - strip quotes and whitespace"""
        cmd = command.strip()
        # Strip surrounding quotes
        if (cmd.startswith('"') and cmd.endswith('"')) or (cmd.startswith("'") and cmd.endswith("'")):
            cmd = cmd[1:-1].strip()
        return cmd
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response - robust parsing with fallback"""
        original = response
        
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            parts = response.split("```")
            if len(parts) >= 2:
                response = parts[1]
                if response.lower().startswith("json"):
                    response = response[4:]
        
        # Find JSON object in response
        response = response.strip()
        
        # Try to find JSON object between braces
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logging.warning(f"JSON parse error: {e}")
            logging.debug(f"Raw LLM response: {original[:500]}")
            
            # Fallback: try to extract goal_type using regex
            import re
            goal_type_match = re.search(r'"goal_type"\s*:\s*"([^"]+)"', original)
            content_match = re.search(r'"content"\s*:\s*"([^"]*)"', original)
            preference_match = re.search(r'"preference"\s*:\s*"([^"]*)"', original)
            
            if goal_type_match:
                logging.info(f"Recovered goal_type via regex: {goal_type_match.group(1)}")
                return {
                    "goal_type": goal_type_match.group(1),
                    "content": content_match.group(1) if content_match else "",
                    "preference": preference_match.group(1) if preference_match else "",
                    "modifiers": {}
                }
            
            # Return unknown if parsing completely fails
            logging.error(f"Could not parse goal from LLM response")
            return {"goal_type": "UNKNOWN", "content": "", "preference": "", "modifiers": {}}
    
    def route(self, command: str) -> Tuple[str, bool]:
        """
        Main routing function - extracts goal, plans, and executes.
        
        Returns:
            (response_message, success)
        """
        # Step 1: Extract goal
        goal = self.extract_goal(command)
        
        # Handle conversation/unknown
        if goal.type == GoalType.CONVERSATION:
            return self._handle_conversation(command)
        
        if goal.type == GoalType.UNKNOWN:
            return self._handle_unknown(command)
        
        # Step 2: Get action plan from strategy
        plan = self.planner.plan(goal)
        
        if not plan:
            logging.warning(f"No plan for goal: {goal}")
            return self._handle_fallback(goal)
        
        # Step 3: Execute the plan
        logging.info(f"Executing plan: {plan.description}")
        success = self.executor.execute(plan)
        
        if success:
            return f"Done: {plan.description}", True
        else:
            return f"Attempted: {plan.description}", False
    
    def _handle_conversation(self, command: str) -> Tuple[str, bool]:
        """Handle conversational commands"""
        if self.ai_client:
            try:
                response = self.ai_client.client.models.generate_content(
                    model=self.ai_client.model,
                    contents=command
                )
                return response.text.strip(), True
            except Exception as e:
                logging.error(f"Conversation error: {e}")
        return "I'm not sure how to respond to that.", False
    
    def _handle_unknown(self, command: str) -> Tuple[str, bool]:
        """Handle unknown commands - fall back to code generation"""
        logging.info(f"Unknown goal, falling back to code generation: {command}")
        # This will be handled by aura_v2_bridge's existing LLM fallback
        return ("NEEDS_CODE_GENERATION", False)
    
    def _handle_fallback(self, goal: Goal) -> Tuple[str, bool]:
        """Handle goals with no strategy - use existing function executor"""
        logging.info(f"No strategy for {goal.type}, using function executor fallback")
        return ("NEEDS_FUNCTION_EXECUTOR", False)


# Global instance
_router_instance = None

def get_goal_router() -> GoalRouter:
    """Get the global goal router"""
    global _router_instance
    if _router_instance is None:
        _router_instance = GoalRouter()
    return _router_instance
