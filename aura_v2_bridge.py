"""
AURA v2 - Widget Integration Bridge
Integrates the new AURA v2 architecture with the existing floating widget.
Drop-in replacement for the current processing pipeline.

v2.2: Added goal-driven architecture with human-like keyboard/mouse execution.
v2.3: Added multi-task handler for complex commands with dependencies.
"""

import logging
from typing import Optional, Dict, Any, Tuple

# AURA v2 Components
from local_context import get_context, AuraState, AuraMode
from response_generator import get_response_generator
from intent_router import get_intent_router, RouteResult
from function_executor import get_function_executor
from wake_word_detector import check_wake_word, extract_command_after_wake
from capability_manager import capability_manager

# Goal-driven architecture (v2.2)
try:
    from goal_router import get_goal_router
    from goal import GoalType
    GOAL_DRIVEN_ENABLED = True
except ImportError as e:
    logging.warning(f"Goal-driven architecture not available: {e}")
    GOAL_DRIVEN_ENABLED = False

# Multi-task handler (v2.3)
try:
    from multi_task_handler import get_multi_task_handler
    MULTI_TASK_ENABLED = True
except ImportError as e:
    logging.warning(f"Multi-task handler not available: {e}")
    MULTI_TASK_ENABLED = False


class AuraV2Bridge:
    """
    Bridge between AURA v2 and the existing floating widget.
    
    This allows the widget to use the new intelligent routing
    while maintaining backward compatibility.
    
    Usage in aura_widget.py:
        from aura_v2_bridge import aura_bridge
        
        # In ProcessingThread.run():
        response, success, used_gemini = aura_bridge.process(message, context)
    """
    
    def __init__(self):
        self.context = get_context()
        self.response_gen = get_response_generator()
        self.intent_router = get_intent_router()
        self.executor = get_function_executor()
        self.capability_mgr = capability_manager  # Track learned capabilities
        
        # Goal-driven router (v2.2)
        self._goal_router = None
        if GOAL_DRIVEN_ENABLED:
            try:
                self._goal_router = get_goal_router()
                logging.info("Goal-driven router enabled")
            except Exception as e:
                logging.warning(f"Could not initialize goal router: {e}")
        
        # Multi-task handler (v2.3)
        self._multi_task_handler = None
        if MULTI_TASK_ENABLED:
            try:
                self._multi_task_handler = get_multi_task_handler()
                logging.info("Multi-task handler enabled")
            except Exception as e:
                logging.warning(f"Could not initialize multi-task handler: {e}")
        
        # Gemini client (lazy load)
        self._ai_client = None
        
        # Conversation memory for butler mode
        self.conversation_history = []
        self.max_history = 20  # Keep last 20 exchanges
        
        # Confirmation state for email
        self.pending_confirmation = None  # {type: 'email', data: {...}}
        
        # Stats
        self.stats = {
            "local_commands": 0,
            "multi_task": 0,         # v2.3: Multi-task commands
            "goal_driven": 0,        # v2.2: Human-like keyboard/mouse execution
            "gemini_intent": 0,
            "gemini_full": 0,
            "gemini_chat": 0,
            "tokens_saved": 0,
            "capabilities_learned": 0,
        }
        
        logging.info("AuraV2Bridge initialized with goal-driven architecture v2.3")
    
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
    
    def process(self, command: str, context: Dict[str, Any] = None) -> Tuple[str, bool, bool]:
        """
        Process a command using AURA v2 intelligent routing.
        
        v2.1: Always fallback to LLM if local execution fails (like v1 behavior)
        
        Args:
            command: The user's voice command
            context: Optional context dict (filename, etc.)
            
        Returns:
            Tuple of (response_text, success, used_gemini)
        """
        command = command.strip()
        if not command:
            return "", False, False
        
        logging.info(f"AuraV2Bridge processing: {command}")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 0: Check Pending Confirmation
        # ═══════════════════════════════════════════════════════════════
        if self.pending_confirmation:
            return self._handle_confirmation(command)
        
        # ═══════════════════════════════════════════════════════════════
        # v2.3 MULTI-TASK HANDLER: Split complex commands with dependencies
        # ═══════════════════════════════════════════════════════════════
        if self._multi_task_handler and MULTI_TASK_ENABLED:
            if self._multi_task_handler.is_multi_task(command):
                logging.info(f"Detected multi-task command: {command}")
                try:
                    result, success, used_gemini = self._multi_task_handler.process(command)
                    if result is not None:  # Multi-task handler handled it
                        self.stats["multi_task"] += 1
                        return result, success, used_gemini
                except Exception as e:
                    logging.warning(f"Multi-task handler error: {e}")
                    # Fall through to normal processing
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: Local Intent Classification (FREE)
        # ═══════════════════════════════════════════════════════════════
        route_result = self.intent_router.classify(command, self.context)
        
        logging.info(f"Route result: {route_result.match_type}, conf={route_result.confidence:.2f}")
        
        # ═══════════════════════════════════════════════════════════════
        # ROUTE A: Conversation → Gemini Chat
        # ═══════════════════════════════════════════════════════════════
        if route_result.is_conversation:
            self.stats["gemini_chat"] += 1
            return self._handle_conversation(command)
        
        # ═══════════════════════════════════════════════════════════════
        # v2.1 FUNCTION EXECUTOR: Try Intent Router match FIRST
        # If we have a high-confidence tool match, execute it immediately
        # ═══════════════════════════════════════════════════════════════
        
        # If we have a function match from Intent Router, try local first
        if route_result.function and route_result.confidence >= 0.70:
            logging.info(f"Trying local execution: {route_result.function}")
            
            # Special interception for email drafting
            if route_result.function == "draft_email":
                return self._intercept_email_draft(route_result)
                
            result = self._execute_local(route_result)
            if result[1]:  # success
                self.stats["local_commands"] += 1
                self.stats["tokens_saved"] += 500
                return result
            else:
                logging.info(f"Local execution failed, trying goal router")
        
        # ═══════════════════════════════════════════════════════════════
        # v2.2 GOAL-DRIVEN ROUTING (Human-like keyboard/mouse execution)
        # For media, apps, web - uses strategies + keyboard/mouse
        # ═══════════════════════════════════════════════════════════════
        if self._goal_router and GOAL_DRIVEN_ENABLED:
            try:
                response, success = self._goal_router.route(command)
                
                # If goal router handled it successfully
                if success:
                    self.stats["goal_driven"] += 1
                    self.stats["tokens_saved"] += 300  # Saved LLM call
                    logging.info(f"Goal-driven: {response}")
                    return response, True, False
                
                # Check if it needs fallback
                if response == "NEEDS_FUNCTION_EXECUTOR":
                    logging.info("Goal-driven: falling back to function executor")
                    # Continue to function executor below
                elif response == "NEEDS_CODE_GENERATION":
                    logging.info("Goal-driven: falling back to code generation")
                    self.stats["gemini_full"] += 1
                    return self._handle_gemini(command, context)
                    
            except Exception as e:
                logging.warning(f"Goal-driven routing error: {e}")
                # Fall through to function executor
        
        # ═══════════════════════════════════════════════════════════════
        # FALLBACK: Try lower-confidence function matches
        # ═══════════════════════════════════════════════════════════════
        if route_result.function and route_result.confidence >= 0.50:
            logging.info(f"Trying lower-confidence execution: {route_result.function}")
            result = self._execute_local(route_result)
            if result[1]:  # success
                self.stats["local_commands"] += 1
                self.stats["tokens_saved"] += 500
                return result
        
        # ═══════════════════════════════════════════════════════════════
        # FALLBACK: Use LLM to generate and execute code (v1 behavior)
        # This handles ANY command that local routing can't handle
        # ═══════════════════════════════════════════════════════════════
        logging.info(f"Using LLM fallback for: {command}")
        self.stats["gemini_full"] += 1
        return self._handle_gemini(command, context)

    def _intercept_email_draft(self, route_result: RouteResult) -> Tuple[str, bool, bool]:
        """Intercept draft_email to ask for confirmation"""
        try:
            from email_assistant import email_assistant
            
            instruction = route_result.args.get("instruction", "")
            recipient = route_result.args.get("recipient", "")
            
            success, msg, email_data = email_assistant.generate_draft(
                instruction=instruction,
                recipient=recipient
            )
            
            if success:
                # Store confirmation state
                self.pending_confirmation = {
                    "type": "email",
                    "data": email_data
                }
                
                # Create preview message
                subject = email_data.get("subject", "")
                body = email_data.get("body", "")
                preview = body[:100] + "..." if len(body) > 100 else body
                
                response = (f"Draft ready:\n\n"
                           f"Subject: {subject}\n"
                           f"Body: {preview}\n\n"
                           f"Say 'Send' to confirm or 'Cancel' to discard.")
                return response, True, False
            else:
                return f"Failed to draft email: {msg}", False, False
                
        except Exception as e:
            logging.error(f"Email intercept error: {e}")
            return f"Error drafting email: {e}", False, False

    def _handle_confirmation(self, command: str) -> Tuple[str, bool, bool]:
        """Handle user response to confirmation request"""
        import os
        cmd_lower = command.lower()
        affirmative = ["yes", "send", "confirm", "send it", "okay", "ok", "go ahead"]
        negative = ["no", "cancel", "don't", "discard", "stop"]
        
        # Check affirmative
        if any(w in cmd_lower for w in affirmative):
            if self.pending_confirmation and self.pending_confirmation["type"] == "email":
                try:
                    from email_assistant import email_assistant
                    email_data = self.pending_confirmation["data"]
                    
                    # Auto-detect SMTP config
                    action = "clipboard"
                    if os.environ.get("SMTP_EMAIL") and os.environ.get("SMTP_PASSWORD"):
                        action = "smtp"
                        logging.info("SMTP config detected - creating action=smtp")
                    
                    # Execute execution
                    success, msg = email_assistant.execute_email_action(email_data, action)
                    
                    if not success and action == "smtp":
                         # Fallback to clipboard if SMTP fails
                         success, msg = email_assistant.execute_email_action(email_data, "clipboard")
                         msg = "SMTP sending failed. Copied to clipboard instead. " + msg

                    self.pending_confirmation = None # Clear state
                    return msg, True, False
                except Exception as e:
                    self.pending_confirmation = None
                    return f"Error executing action: {e}", False, False
        
        # Check negative
        elif any(w in cmd_lower for w in negative):
            self.pending_confirmation = None
            return "Cancelled. Draft discarded.", True, False
            
        # Unclear response
        else:
            return "Please say 'Send' to confirm or 'Cancel' to discard.", False, False
    
    def _execute_local(self, route_result: RouteResult) -> Tuple[str, bool, bool]:
        """Execute command locally (0 tokens)"""
        logging.info(f"LOCAL EXEC: {route_result.function}")
        
        result = self.executor.execute(
            function_name=route_result.function,
            args=route_result.args
        )
        
        # Update context
        self.context.record_command(
            command=route_result.raw_command,
            function=route_result.function,
            success=result.success
        )
        
        # Track in capability manager for learning
        self.capability_mgr.record_execution(
            command=route_result.raw_command,
            success=result.success,
            function_name=route_result.function
        )
        
        # Generate response
        response = self.response_gen.confirmation(
            result=result.success,
            context={
                "function": route_result.function,
                "value": route_result.args.get("level"),
                "app": route_result.args.get("app_name"),
            }
        )
        
        return response, result.success, False  # False = didn't use Gemini
    
    def _handle_gemini(self, command: str, context: Dict = None) -> Tuple[str, bool, bool]:
        """Handle command with Gemini AI"""
        logging.info(f"GEMINI: {command}")
        
        if not self.ai_client:
            return "I'm having trouble connecting to my AI systems.", False, False
        
        try:
            # Use existing AI client for code generation
            code = self.ai_client.generate_code(command, context=context or {})
            
            if code:
                # Execute the generated code
                result = self.executor.execute_raw(code)
                
                self.context.record_command(
                    command=command,
                    function="generated_code",
                    success=result.success
                )
                
                # Track execution in capability manager
                self.capability_mgr.record_execution(
                    command=command,
                    success=result.success,
                    function_name="generated_code"
                )
                
                # If successful, save as new capability for future reuse
                if result.success and self._is_reusable_function(code):
                    try:
                        self.capability_mgr.add_capability(code, command, success=True)
                        self.stats["capabilities_learned"] += 1
                        logging.info(f"Learned new capability from: {command}")
                    except Exception as e:
                        logging.warning(f"Could not save capability: {e}")
                
                # For conversational responses, return the actual result text
                # For function executions, return a confirmation
                if result.result and isinstance(result.result, str) and len(result.result) > 10:
                    # AI generated a conversational response - return it!
                    return result.result, result.success, True
                else:
                    # Function execution - return confirmation
                    response = self.response_gen.confirmation(result.success)
                    return response, result.success, True

            
            return self.response_gen.failure(), False, True
            
        except Exception as e:
            logging.error(f"Gemini error: {e}")
            return self.response_gen.failure(), False, True
    
    def _handle_conversation(self, message: str) -> Tuple[str, bool, bool]:
        """Handle conversational message with memory and butler personality"""
        logging.info(f"BUTLER CONVERSATION: {message}")
        
        if not self.ai_client:
            return "I apologize, but I'm experiencing connectivity difficulties at the moment, sir.", False, False
        
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Add user message to history
                if attempt == 0:  # Only add on first attempt
                    self.conversation_history.append({"role": "user", "content": message})
                
                # Keep only recent history
                if len(self.conversation_history) > self.max_history:
                    self.conversation_history = self.conversation_history[-self.max_history:]
                
                # Build conversation context
                conversation_context = "\n".join([
                    f"{'User' if msg['role'] == 'user' else 'AURA'}: {msg['content']}"
                    for msg in self.conversation_history[-10:]  # Last 10 messages for context
                ])
                
                # Detect user intent for response length
                brief_keywords = ["briefly", "short", "quick", "tl;dr", "in a nutshell", "summarize", "one sentence", "keep it short"]
                detailed_keywords = ["in detail", "detailed", "explain fully", "elaborate", "comprehensive", "thorough", "tell me everything"]
                
                wants_brief = any(kw in message.lower() for kw in brief_keywords)
                wants_detailed = any(kw in message.lower() for kw in detailed_keywords)
                
                length_instruction = ""
                if wants_brief:
                    length_instruction = "\n\nRESPONSE LENGTH: User wants a BRIEF answer. Keep it to 1-3 sentences maximum. Be concise."
                elif wants_detailed:
                    length_instruction = "\n\nRESPONSE LENGTH: User wants a DETAILED answer. Provide comprehensive information with examples if relevant."
                else:
                    length_instruction = "\n\nRESPONSE LENGTH: Provide a balanced response - informative but not overly long. 3-5 sentences for simple questions, more for complex topics."
                
                # Enhanced butler personality prompt
                prompt = f"""You are AURA, an sophisticated AI butler assistant with these characteristics:

PERSONALITY:
- Polite, refined, and attentive like a traditional British butler
- Warm and engaging, making conversation feel natural
- Knowledgeable and well-informed across many topics
- Proactive in offering help and suggestions
- Uses phrases like "Certainly, sir/madam", "I'd be delighted to assist"
- Remembers context from previous messages in the conversation

CONVERSATION STYLE:
- Be conversational and engaging, not robotic
- Provide detailed, informative responses when appropriate
- Ask follow-up questions to continue the dialogue when relevant
- Show genuine interest in the user's inquiries
- Use natural language, avoid being too formal or stiff
{length_instruction}

MEMORY & CONTEXT:
You remember this conversation:
{conversation_context}

Current user message: {message}

Respond as AURA, the helpful AI butler. Be informative, engaging, and conversational. Remember what was discussed before."""

                # Use the same google-genai client pattern as the main AI client.
                # Note: current client API does not accept generation_config here,
                # so we rely on the model's defaults for now.
                response = self.ai_client.client.models.generate_content(
                    model=self.ai_client.model,
                    contents=prompt,
                )
                
                response_text = response.text.strip()
                
                # Truncate very long responses for better UX (keep first 500 words)
                words = response_text.split()
                if len(words) > 500:
                    truncated = ' '.join(words[:500]) + "\n\n[Response truncated - full answer available in conversation history]"
                    logging.info(f"BUTLER RESPONSE (truncated from {len(words)} words): {truncated[:160]}...")
                else:
                    logging.info(f"BUTLER RESPONSE: {response_text[:160]}{'...' if len(response_text) > 160 else ''}")
                
                # Store full response in history, but return truncated version for display
                full_response = response_text
                display_response = truncated if len(words) > 500 else response_text
                
                # Add assistant response to history (full version)
                self.conversation_history.append({"role": "assistant", "content": full_response})
                
                return display_response, True, True
                
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # 2, 4 seconds
                        logging.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                logging.error(f"Conversation error: {e}")
                
        return "I apologize, but I'm experiencing a momentary difficulty. Could you please repeat that?", False, True
    
    def get_acknowledgment(self) -> str:
        """Get a wake word acknowledgment"""
        return self.response_gen.acknowledgment()
    
    def get_greeting(self) -> str:
        """Get a time-appropriate greeting"""
        return self.response_gen.greeting()
    
    def _is_reusable_function(self, code: str) -> bool:
        """Determine if code is a reusable function worth saving"""
        # Only save if it contains a function definition
        return "def " in code and code.count("def ") <= 2  # Avoid very complex code
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total = sum([
            self.stats["local_commands"],
            self.stats["gemini_intent"],
            self.stats["gemini_full"],
            self.stats["gemini_chat"],
        ])
        
        return {
            **self.stats,
            "total_commands": total,
            "local_percentage": (self.stats["local_commands"] / total * 100) if total > 0 else 0,
        }
    
    def check_wake_word(self, text: str) -> bool:
        """Check if text contains wake word"""
        return check_wake_word(text)
    
    def extract_command(self, text: str) -> str:
        """Extract command after wake word"""
        return extract_command_after_wake(text)
    
    def clear_conversation_history(self) -> None:
        """Clear conversation memory - useful for starting fresh"""
        self.conversation_history = []
        logging.info("Conversation history cleared")
    
    def get_conversation_length(self) -> int:
        """Get number of messages in conversation history"""
        return len(self.conversation_history)


# Global bridge instance
aura_bridge = AuraV2Bridge()


def process_command(command: str, context: Dict = None) -> Tuple[str, bool, bool]:
    """
    Process a command using AURA v2.
    
    Returns:
        (response, success, used_gemini)
    """
    return aura_bridge.process(command, context)


def get_acknowledgment() -> str:
    """Get a wake word acknowledgment"""
    return aura_bridge.get_acknowledgment()


def get_greeting() -> str:
    """Get a greeting"""
    return aura_bridge.get_greeting()


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE IN WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
"""
To integrate AURA v2 into the existing widget, modify ProcessingThread.run() in aura_widget.py:

from aura_v2_bridge import aura_bridge

class ProcessingThread(QThread):
    def run(self):
        try:
            # Use AURA v2 for intelligent routing
            response, success, used_gemini = aura_bridge.process(
                self.message, 
                self.context
            )
            
            self.finished.emit(response, self.message, success)
            
            # Log stats periodically
            stats = aura_bridge.get_stats()
            logging.info(f"AURA v2 Stats: Local={stats['local_commands']}, Saved={stats['tokens_saved']} tokens")
            
        except Exception as e:
            logging.error(f"Processing error: {e}")
            self.finished.emit(str(e), self.message, False)
"""
