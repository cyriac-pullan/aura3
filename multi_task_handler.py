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
        
        # Check for separators
        for pattern in self.SEPARATORS:
            if re.search(pattern, command_lower):
                return True
        
        return False
    
    def split_tasks(self, command: str) -> List[Task]:
        """
        Split a multi-task command into individual tasks.
        Understands dependencies based on keywords.
        """
        tasks = []
        
        # Try to split using separators (in order of specificity)
        parts = [command]
        original_command = command.lower()
        
        for pattern in self.SEPARATORS:
            new_parts = []
            for part in parts:
                # Track what separator was used
                splits = re.split(pattern, part, flags=re.IGNORECASE)
                if len(splits) > 1:
                    new_parts.extend(splits)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        # Clean up parts
        parts = [p.strip() for p in parts if p.strip()]
        
        # Determine dependencies
        # Check if original command had dependency keywords
        has_sequential_keywords = any(kw in original_command for kw in self.DEPENDENCY_KEYWORDS)
        
        for i, part in enumerate(parts):
            task = Task(
                command=part,
                index=i,
                depends_on=[]
            )
            
            # If command had "then" or similar, each task depends on previous
            if has_sequential_keywords and i > 0:
                task.depends_on = [i - 1]
            
            # Special dependency detection
            # "search X" usually depends on a browser/app being open
            part_lower = part.lower()
            if any(kw in part_lower for kw in ['search', 'type', 'click', 'find']):
                # Look for a previous task that opens something
                for j in range(i - 1, -1, -1):
                    prev = parts[j].lower()
                    if any(kw in prev for kw in ['open', 'launch', 'start']):
                        if j not in task.depends_on:
                            task.depends_on.append(j)
                        break
            
            tasks.append(task)
        
        logging.info(f"Split into {len(tasks)} tasks: {[t.command for t in tasks]}")
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
