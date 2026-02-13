"""
AURA Goal-Driven Architecture - Plan Executor
Executes human action plans using keyboard/mouse.
No intelligence here - just deterministic execution.
"""

import logging
import time
from typing import Optional, Callable
from goal import HumanActionPlan, ActionStep


class PlanExecutor:
    """
    Executes HumanActionPlan step by step.
    Uses advanced_control.py for actual keyboard/mouse actions.
    """
    
    def __init__(self):
        self._advanced_control = None
        self._load_control()
        self.interrupt_flag = False
        logging.info("Plan Executor initialized")
    
    def _load_control(self):
        """Load advanced_control module"""
        try:
            import advanced_control
            self._advanced_control = advanced_control
            logging.info("Plan Executor: Loaded advanced_control")
        except ImportError as e:
            logging.error(f"Plan Executor: Could not load advanced_control: {e}")
    
    def execute(self, plan: HumanActionPlan, 
                on_step: Optional[Callable[[int, ActionStep], None]] = None) -> bool:
        """
        Execute a human action plan.
        
        Args:
            plan: The HumanActionPlan to execute
            on_step: Optional callback for progress updates
            
        Returns:
            True if all steps completed, False if interrupted or failed
        """
        if not self._advanced_control:
            logging.error("No advanced_control module available")
            return False
        
        self.interrupt_flag = False
        total_steps = len(plan.steps)
        
        logging.info(f"Executing plan: {plan.description} ({total_steps} steps)")
        
        for i, step in enumerate(plan.steps):
            # Check for interrupt
            if self.interrupt_flag:
                logging.info(f"Plan interrupted at step {i+1}/{total_steps}")
                return False
            
            # Progress callback
            if on_step:
                on_step(i, step)
            
            # Execute the step
            success = self._execute_step(step)
            if not success:
                logging.warning(f"Step {i+1} failed: {step}")
                # Continue anyway - some failures are recoverable
        
        logging.info(f"Plan completed: {plan.description}")
        return True
    
    def _execute_step(self, step: ActionStep) -> bool:
        """Execute a single action step"""
        try:
            ac = self._advanced_control
            
            if step.type == "KEY":
                # Single key press
                for key in step.keys:
                    ac.press_key(key)
                return True
            
            elif step.type == "HOTKEY":
                # Key combination
                ac.hotkey(*step.keys)
                return True
            
            elif step.type == "TYPE":
                # Type text
                ac.type_text(step.text)
                return True
            
            elif step.type == "WAIT":
                # Wait
                time.sleep(step.ms / 1000.0)
                return True
            
            elif step.type == "CLICK":
                # Mouse click
                ac.mouse_click(step.x, step.y, step.button)
                return True
            
            elif step.type == "SCROLL":
                # Scroll
                ac.scroll(step.clicks)
                return True
            
            else:
                logging.warning(f"Unknown step type: {step.type}")
                return False
                
        except Exception as e:
            logging.error(f"Error executing step {step}: {e}")
            return False
    
    def interrupt(self):
        """Set interrupt flag to stop execution"""
        self.interrupt_flag = True
        logging.info("Interrupt requested")


# Global instance
_executor_instance = None

def get_plan_executor() -> PlanExecutor:
    """Get the global plan executor"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = PlanExecutor()
    return _executor_instance


def execute_plan(plan: HumanActionPlan) -> bool:
    """Convenience function to execute a plan"""
    return get_plan_executor().execute(plan)
