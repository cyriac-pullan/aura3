"""
AURA v2.3 - Multi-Task Handler
Handles complex commands with multiple tasks, understanding dependencies.

Example: "close notepad and then open chrome and search for weather"
 → Tasks: [close notepad] → [open chrome] → [search for weather]
 → Dependencies: search depends on chrome being open
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    """Represents a single task extracted from a multi-task command"""
    command: str
    index: int
    depends_on: List[int] = field(default_factory=list)  # Indices of tasks this depends on
    executed: bool = False
    success: bool = False
    result: str = ""


class MultiTaskHandler:
    """
    Handles multi-task commands by:
    1. Detecting if command has multiple tasks
    2. Splitting into individual tasks
    3. Understanding dependencies
    4. Executing in order through the routing pipeline
    """
    
    # Separators that indicate multiple tasks
    SEPARATORS = [
        r'\s+and\s+also\s+',
        r'\s+and\s+then\s+',
        r'\s+then\s+',
        r'\s+and\s+',
        r'\s+also\s+',
        r',\s*and\s+',
        r',\s*then\s+',
        r',\s+',
    ]
    
    # Keywords that indicate dependency (task B depends on task A)
    DEPENDENCY_KEYWORDS = [
        'then', 'after that', 'next', 'afterwards', 'following that'
    ]
    
    # Keywords that indicate parallel execution (no dependency)
    PARALLEL_KEYWORDS = [
        'also', 'at the same time', 'simultaneously', 'as well'
    ]
    
    def __init__(self):
        self._intent_router = None
        self._goal_router = None
        self._bridge = None
        logging.info("MultiTaskHandler initialized")
    
    @property
    def intent_router(self):
        if self._intent_router is None:
            from intent_router import get_intent_router
            self._intent_router = get_intent_router()
        return self._intent_router
    
    @property
    def goal_router(self):
        if self._goal_router is None:
            try:
                from goal_router import get_goal_router
                self._goal_router = get_goal_router()
            except ImportError:
                pass
        return self._goal_router
    
    @property
    def bridge(self):
        if self._bridge is None:
            from aura_v2_bridge import aura_bridge
            self._bridge = aura_bridge
        return self._bridge
    
    def is_multi_task(self, command: str) -> bool:
        """Check if command contains multiple tasks"""
        command_lower = command.lower()
        
        # Commands that involve browser interaction should NOT be split
        # They are single browser_task operations
        browser_indicators = [
            'fill out', 'fill in', 'fill the form', 'extract', 'scrape',
            'find the', 'find me', 'find out', 'look up', 'look for',
            'book a', 'book the', 'sign up', 'log in', 'login',
            'browse', 'navigate', 'interact with', 'click on',
            'browser agent', 'use the browser', 'on the website',
            'on github', 'on amazon', 'on linkedin', 'on twitter',
            'tell me the', 'tell me how', 'tell me what',
        ]
        
        # If the command looks like a web interaction task, don't split it
        if any(indicator in command_lower for indicator in browser_indicators):
            # Check if it's clearly a web task (mentions going to a site + doing something)
            web_patterns = [
                r'go to .+ and (find|search|fill|click|extract|tell|get|check|look|read|scrape)',
                r'(visit|open|navigate to) .+ and (find|search|fill|click|extract|tell|get|check|look|read)',
                r'(find|search|get|extract|check) .+ (on|from|at) .+\.(com|org|net|io|dev)',
                r'use the browser',
                r'browser agent',
            ]
            for pattern in web_patterns:
                if re.search(pattern, command_lower):
                    logging.info(f"Detected browser task, not splitting: {command[:60]}")
                    return False
        
        # Check for separators
        for pattern in self.SEPARATORS:
            if re.search(pattern, command_lower):
                return True
        
        return False
    
    def split_tasks(self, command: str) -> List[Task]:
        """
        Split a multi-task command into individual tasks using LLM.
        Understands dependencies based on context.
        """
        tasks = []
        
        # Try LLM-based splitting first for better accuracy
        try:
            from ai_client import ai_client
            
            prompt = f"""Break down this multi-task command into individual, independent tasks.

USER COMMAND: "{command}"

INSTRUCTIONS:
1. Identify each distinct task/action the user wants to perform
2. Each task should be a complete, standalone instruction
3. Preserve context (e.g., "create folder X" and "create folder Y" are TWO tasks)
4. Don't split compound objects (e.g., "folders X and Y" means create BOTH folders)
5. Identify if tasks are sequential (one depends on another) or parallel

Respond with valid JSON:
{{
  "tasks": [
    {{"command": "task description", "depends_on_previous": true/false}}
  ]
}}

Examples:
- "create folders X and Y" → [{{"command": "create folder X", "depends_on_previous": false}}, {{"command": "create folder Y", "depends_on_previous": false}}]
- "open chrome and search for weather" → [{{"command": "open chrome", "depends_on_previous": false}}, {{"command": "search for weather", "depends_on_previous": true}}]
- "create folder X. Inside X, create file test.txt" → [{{"command": "create folder X", "depends_on_previous": false}}, {{"command": "create file test.txt inside folder X", "depends_on_previous": true}}]

JSON RESPONSE:"""

            result = ai_client.generate_json(prompt)
            
            if "tasks" in result and isinstance(result["tasks"], list):
                for i, task_data in enumerate(result["tasks"]):
                    task = Task(
                        command=task_data.get("command", ""),
                        index=i,
                        depends_on=[i - 1] if i > 0 and task_data.get("depends_on_previous", False) else []
                    )
                    tasks.append(task)
                
                logging.info(f"LLM split into {len(tasks)} tasks: {[t.command for t in tasks]}")
                return tasks
        
        except Exception as e:
            logging.warning(f"LLM task splitting failed: {e}, falling back to regex")
        
        # Fallback to regex-based splitting
        parts = [command]
        original_command = command.lower()
        
        for pattern in self.SEPARATORS:
            new_parts = []
            for part in parts:
                splits = re.split(pattern, part, flags=re.IGNORECASE)
                if len(splits) > 1:
                    new_parts.extend(splits)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        # Clean up parts
        parts = [p.strip() for p in parts if p.strip()]
        
        # Determine dependencies
        has_sequential_keywords = any(kw in original_command for kw in self.DEPENDENCY_KEYWORDS)
        
        for i, part in enumerate(parts):
            task = Task(
                command=part,
                index=i,
                depends_on=[]
            )
            
            if has_sequential_keywords and i > 0:
                task.depends_on = [i - 1]
            
            # Special dependency detection
            part_lower = part.lower()
            if any(kw in part_lower for kw in ['search', 'type', 'click', 'find']):
                for j in range(i - 1, -1, -1):
                    prev = parts[j].lower()
                    if any(kw in prev for kw in ['open', 'launch', 'start']):
                        if j not in task.depends_on:
                            task.depends_on.append(j)
                        break
            
            tasks.append(task)
        
        logging.info(f"Regex split into {len(tasks)} tasks: {[t.command for t in tasks]}")
        return tasks
    
    def execute_tasks(self, tasks: List[Task]) -> Tuple[str, bool]:
        """
        Execute tasks in order, respecting dependencies.
        Returns combined result and overall success.
        """
        results = []
        all_success = True
        
        for task in tasks:
            # Check dependencies
            deps_met = all(
                tasks[dep].executed and tasks[dep].success 
                for dep in task.depends_on
            )
            
            if not deps_met:
                task.result = f"Skipped (dependency failed): {task.command}"
                task.executed = True
                task.success = False
                results.append(task.result)
                all_success = False
                continue
            
            # Execute through routing pipeline
            response, success = self._execute_single_task(task.command)
            
            task.executed = True
            task.success = success
            task.result = response
            results.append(response)
            
            if not success:
                all_success = False
        
        # Combine results
        combined = "\n".join([r for r in results if r])
        return combined, all_success
    
    def _execute_single_task(self, command: str) -> Tuple[str, bool]:
        """
        Execute a single task through the routing pipeline:
        1. Intent Router (high confidence) → Function Executor
        2. Goal Router → Strategy Executor
        3. LLM Code Generation (fallback)
        """
        logging.info(f"MultiTask: Executing '{command}'")
        
        # Step 1: Try Intent Router
        route_result = self.intent_router.classify(command)
        
        if route_result.function and route_result.confidence >= 0.70:
            logging.info(f"MultiTask: Intent matched '{route_result.function}' ({route_result.confidence:.2f})")
            
            # Execute via bridge's local executor
            result = self.bridge._execute_local(route_result)
            if result[1]:  # success
                return result[0], True
        
        # Step 2: Try Goal Router
        if self.goal_router:
            try:
                response, success = self.goal_router.route(command)
                if success:
                    logging.info(f"MultiTask: Goal router handled '{command}'")
                    return response, True
            except Exception as e:
                logging.warning(f"MultiTask: Goal router error: {e}")
        
        # Step 3: Try lower confidence Intent Router match
        if route_result.function and route_result.confidence >= 0.50:
            result = self.bridge._execute_local(route_result)
            if result[1]:
                return result[0], True
        
        # Step 4: Fallback to LLM code generation
        logging.info(f"MultiTask: Using LLM for '{command}'")
        return self.bridge._handle_gemini(command, None)[:2]  # (response, success)
    
    def process(self, command: str) -> Tuple[str, bool, bool]:
        """
        Process a potentially multi-task command.
        
        Returns:
            (response, success, used_gemini)
        """
        if not self.is_multi_task(command):
            # Single task - let the bridge handle it normally
            return None, False, False  # Signal to use normal processing
        
        logging.info(f"MultiTask: Processing multi-task command")
        
        # Split into tasks
        tasks = self.split_tasks(command)
        
        if len(tasks) <= 1:
            # Couldn't split - let normal processing handle it
            return None, False, False
        
        # Execute tasks
        result, success = self.execute_tasks(tasks)
        
        # Determine if we used Gemini
        used_gemini = any(not t.success or "gemini" in str(t.result).lower() for t in tasks)
        
        return result, success, used_gemini


# Global instance
_handler = None

def get_multi_task_handler() -> MultiTaskHandler:
    """Get or create the global multi-task handler"""
    global _handler
    if _handler is None:
        _handler = MultiTaskHandler()
    return _handler


def process_multi_task(command: str) -> Tuple[str, bool, bool]:
    """
    Process a potentially multi-task command.
    
    Returns:
        (response, success, used_gemini) or (None, False, False) if not multi-task
    """
    return get_multi_task_handler().process(command)
