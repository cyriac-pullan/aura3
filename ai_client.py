import logging
import time
import json
from typing import Dict, List, Optional, Any
from config import config
from google import genai

class AIClient:
    """Google Gemini AI client for code generation"""

    def __init__(self):
        self.model_name = "gemini-2.5-flash"

        # Code-Generator uses its own dedicated API key.
        # Set GEMINI_API_KEY_CODEGEN in .env to isolate its quota.
        # Falls back to the shared GEMINI_API_KEY if not set.
        api_key = config.api_key_codegen

        if not api_key or len(api_key.strip()) < 20:
            logging.error("[CodeGen] No valid API key — set GEMINI_API_KEY_CODEGEN or GEMINI_API_KEY in .env")
            print("\u274c ERROR: No API key found.")
            print("   Please set GEMINI_API_KEY in your .env file")
            print("   Get your key from: https://aistudio.google.com/app/apikey")
            raise ValueError("Invalid or missing API key")

        self.api_key = api_key.strip()
        self.client = genai.Client(api_key=self.api_key)
        self.model = self.model_name

        logging.info(f"[CodeGen] API key: {self.api_key[:10]}...{self.api_key[-4:]} (len={len(self.api_key)})")
        logging.info(f"[CodeGen] Client ready — model: {self.model_name}")

    def generate_json(self, prompt: str) -> Optional[dict]:
        """Generate a JSON response from the LLM and parse it.
        Used by multi_task_handler for structured task splitting."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            logging.warning(f"[CodeGen] generate_json: invalid JSON: {e}")
            return {}
        except Exception as e:
            logging.error(f"[CodeGen] generate_json failed: {e}")
            return {}

    def generate_code(self, command: str, context: Dict[str, Any] = None) -> str:
        """Generate Python code from natural language command with retry and fallback"""
        
        system_prompt = self._build_system_prompt(context)
        
        # Try multiple times with exponential backoff
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logging.info(f"Attempting to generate code (attempt {attempt + 1}/{max_retries})")
                
                # Combine system prompt and user command for Gemini
                full_prompt = f"{system_prompt}\n\nUser command: {command}"
                
                # Generate content using google-genai SDK
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                
                # Extract text from response
                code = response.text.strip()
                
                if not code:
                    raise ValueError("No content in API response")
                
                # Clean up code formatting
                code = self._clean_code(code)
                
                logging.info(f"Generated code for command: {command[:50]}...")
                return code
                
            except Exception as e:
                error_str = str(e)
                logging.error(f"Error generating code (attempt {attempt + 1}): {e}")
                
                # Check for authentication errors
                if "401" in error_str or "Unauthorized" in error_str or "API_KEY_INVALID" in error_str or "API key not valid" in error_str:
                    logging.error("Please check your GEMINI_API_KEY in .env file")
                    logging.warning("Authentication failed, trying fallback method")
                    return self._generate_fallback_code(command, context)
                
                # Check for quota/rate limit errors
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower() or "ResourceExhausted" in error_str:
                    logging.error(f"Quota/Rate limit error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logging.info(f"Rate limited, waiting {delay:.1f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    logging.warning("Quota exceeded, trying fallback method")
                    return self._generate_fallback_code(command, context)
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logging.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    # Last attempt failed, try fallback
                    logging.warning("All API attempts failed, trying fallback method")
                    return self._generate_fallback_code(command, context)
    
    def _generate_fallback_code(self, command: str, context: Dict[str, Any] = None) -> str:
        """Generate simple fallback code when API is unavailable"""
        try:
            command_lower = command.lower()
            import re
            
            # Folder/directory creation
            if 'create' in command_lower and ('folder' in command_lower or 'directory' in command_lower):
                folder_match = re.search(r'(?:named|name|called)\s+(\w+)', command_lower)
                drive_match = re.search(r'\b([a-z]):\s*drive', command_lower)
                
                if folder_match:
                    folder_name = folder_match.group(1)
                    if drive_match:
                        drive = drive_match.group(1).upper()
                        folder_path = f"{drive}:/{folder_name}"
                    elif 'd drive' in command_lower or 'd:' in command_lower:
                        folder_path = f"D:/{folder_name}"
                    else:
                        from config import config as _cfg
                        folder_path = f"{_cfg.default_files_dir}/{folder_name}"
                    
                    return f"""import os
try:
    os.makedirs(r'{folder_path}', exist_ok=True)
    if os.path.exists(r'{folder_path}'):
        print(f'Folder created successfully: {folder_path}')
    else:
        print(f'Failed to create folder: {folder_path}')
except Exception as e:
    print(f'Error creating folder: {{e}}')"""
            
            # Brightness commands
            if 'brightness' in command_lower:
                numbers = re.findall(r'\d+', command)
                if numbers:
                    level = max(0, min(100, int(numbers[0])))
                    return f"""import screen_brightness_control as sbc
try:
    sbc.set_brightness({level})
    print('Brightness set to {level}%')
except Exception as e:
    print(f'Error setting brightness: {{e}}')"""
            
            # Try matching existing functions
            try:
                from windows_system_utils import get_function_for_command, FUNCTION_MAPPINGS
                func = get_function_for_command(command)
                if func and callable(func):
                    func_name = getattr(func, '__name__', None)
                    if func_name and func_name != '<lambda>':
                        return f"result = {func_name}()\nprint(f'Result: {{result}}')"
            except ImportError:
                pass
            
            # Generic fallback
            return f"""try:
    print("Command received but API unavailable for code generation.")
    print("Command: {command}")
    print("Please try again once the connection is restored.")
except Exception as e:
    print(f"Error: {{e}}")"""
            
        except Exception as e:
            logging.error(f"Fallback code generation failed: {e}")
            return f"print('Unable to process command due to system issues')"
    
    def generate_function(self, task_description: str, error_context: str = None) -> str:
        """Generate a new function to handle unknown tasks"""
        
        prompt = f"""
Create a Windows-compatible Python function that can perform: "{task_description}"

Requirements:
- Use only standard libraries, ctypes, or common packages (os, sys, subprocess, winreg, etc.)
- Include comprehensive error handling with try/except blocks
- Return a boolean success status
- Add type hints for all parameters and return values
- Include a detailed docstring

{f"Previous error context: {error_context}" if error_context else ""}

Respond ONLY with the complete function code, no explanations or markdown formatting.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            function_code = response.text.strip()
            if not function_code:
                raise ValueError("No content in API response")
            function_code = self._clean_code(function_code)
            
            logging.info(f"Generated function for task: {task_description[:50]}...")
            return function_code
            
        except Exception as e:
            logging.error(f"Error generating function: {e}")
            raise
    
    def analyze_image(self, image_data: bytes, prompt: str = "What is in this image?") -> str:
        """Analyze an image using Gemini Vision"""
        try:
            logging.info(f"Analyzing image ({len(image_data)} bytes)...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    image_data
                ]
            )
            
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"
    
    def analyze_error(self, code: str, error: str, command: str) -> Dict[str, Any]:
        """Analyze execution error and suggest improvements"""
        
        prompt = f"""
Analyze this Python code execution error and provide suggestions:

Command: {command}
Code: {code}
Error: {error}

Provide analysis in this JSON format:
{{
    "error_type": "syntax|runtime|logic|missing_capability",
    "root_cause": "brief description of the root cause",
    "suggested_fix": "specific fix suggestion",
    "needs_new_function": true/false,
    "function_description": "description of needed function if applicable"
}}

Respond ONLY with valid JSON, no explanations.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            content = response.text.strip()
            if not content:
                raise ValueError("No content in API response")
            
            # Try to extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                content = content[start:end]

            analysis = json.loads(content)
            return analysis

        except Exception as e:
            logging.error(f"Error analyzing error: {e}")
            try:
                if 'response' in locals() and hasattr(response, 'text'):
                    logging.error(f"Response content: {response.text}")
            except:
                pass
            return {
                "error_type": "missing_capability",
                "root_cause": "Function or capability not available",
                "suggested_fix": "Generate new function",
                "needs_new_function": True,
                "function_description": f"Create function to handle system information requests"
            }
    
    def _build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Build comprehensive system prompt with current capabilities"""

        # Load current capabilities
        from capability_manager import capability_manager
        capabilities = capability_manager.get_capabilities_summary()

        # Load available functions from windows_system_utils
        try:
            from windows_system_utils import get_function_for_command, list_available_functions, FUNCTION_MAPPINGS
            available_functions = list_available_functions()
            function_mappings = FUNCTION_MAPPINGS
        except ImportError:
            available_functions = {}
            function_mappings = {}

        # Resolve the default files directory at prompt-build time
        from config import config as _cfg
        default_files_dir = _cfg.default_files_dir  # also creates the dir if missing

        prompt = f"""\
You are an advanced Python code generator for a Windows system automation assistant.
Generate ONLY executable Python code. No explanations, no markdown.

CONTEXT:
- OS: Windows
- Filename: {context.get('filename') if context else 'None'}
- Available capabilities: {len(capabilities)} functions
- Available system functions: {len(available_functions)} functions
- Default files directory: {default_files_dir}

=== FILE PATH ANCHOR (CRITICAL) ===
Default save location (when user gives NO path):
  save_dir = "{default_files_dir}"

If user specifies a location, decode it:
  "in D drive" / "on D"       -> save_dir = "D:/"
  "in folder X on D"          -> save_dir = "D:/X"
  "in D:/Projects"            -> save_dir = "D:/Projects"
  "on desktop"                -> save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
  "in documents"              -> save_dir = os.path.join(os.path.expanduser("~"), "Documents")
  "in downloads"              -> save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
  Any full path               -> use as-is

ALWAYS run: os.makedirs(save_dir, exist_ok=True)
NEVER default to Desktop/Documents/CWD unless user explicitly says so.

=== WINDOWS OS RULES ===
BANNED commands (Linux-only, do NOT exist here): touch, rm, cat, ls, cp, mv, chmod, grep, sed, awk
Use Python instead:
  Create empty file:   open(path, "w").close()
  Create with content: with open(path, "w") as f: f.write(content)
  Create folders:      os.makedirs(path, exist_ok=True)
  Delete files:        os.remove(path)
  List files:          os.listdir(path)
  Copy files:          import shutil; shutil.copy(src, dst)
For terminal commands use PowerShell syntax (Get-ChildItem, not ls).

=== PATH STRING RULES ===
NEVER write: r"D:\\"  (raw strings cannot end with single backslash — syntax error)
ALWAYS use forward slashes: "D:/folder/file.txt" — Python handles this on Windows.

=== FOLDER CREATION ===
"already exists" is SUCCESS. Always use: os.makedirs(path, exist_ok=True)

=== EXECUTION RULES ===
1. Check existing functions FIRST before generating new code
2. Generate ONLY executable Python — no explanations, no markdown
3. ALL imports are allowed — use any library
4. Handle errors with try/except but ALWAYS attempt execution
5. If a package is missing, auto-install: subprocess.run(["pip", "install", pkg])
6. NEVER use input() — hardcode test values instead
7. NEVER use 'return' outside a function — use print() instead
8. Extract parameters from commands (numbers, paths, names) using regex or string parsing
9. Use subprocess, os.system, ctypes, win32api — ALL methods allowed

=== EXISTING FUNCTIONS (use before generating new code) ===
{chr(10).join([f"- {name}: {info['description']}" for name, info in available_functions.items()])}

FUNCTION MAPPINGS:
{chr(10).join([f"- '{cmd}' -> {func.__name__ if hasattr(func, '__name__') else str(func)}" for cmd, func in function_mappings.items()])}

=== DYNAMIC CAPABILITIES (pre-loaded in execution context) ===
{self._format_dynamic_capabilities(capabilities)}

All capabilities above are already loaded — call them directly by name.
If you need a function that doesn't exist, define it completely first.

=== YOUTUBE ===
For ANY YouTube command: use play_youtube_video_ultra_direct(search_term)
NEVER generate new YouTube code or use webbrowser.open() for YouTube.

Generate code that is safe, robust, and handles errors gracefully.
"""
        return prompt
    
    def _format_capabilities(self, capabilities: List[Dict[str, Any]]) -> str:
        """Format capabilities list for system prompt"""
        if not capabilities:
            return "No custom capabilities loaded yet."
        
        formatted = []
        for cap in capabilities[:20]:  # Limit to prevent prompt overflow
            formatted.append(f"- {cap['name']}(): {cap['description']}")
        
        if len(capabilities) > 20:
            formatted.append(f"... and {len(capabilities) - 20} more functions")
        
        return "\n".join(formatted)
    
    def _format_dynamic_capabilities(self, capabilities: List[Dict[str, Any]]) -> str:
        """Format dynamically generated capabilities for system prompt"""
        if not capabilities:
            return "No dynamically generated capabilities available yet."
        
        # Get the capability names and signatures from capability manager
        try:
            from capability_manager import capability_manager
            formatted = []
            for capability_name, capability_data in capability_manager.capabilities.items():
                signature = capability_data.get('signature', capability_name + '()')
                description = capability_data.get('description', 'Generated function')
                formatted.append(f"- {signature}: {description}")
            
            if formatted:
                return "\n".join(formatted[:20]) + (f"\n... and {len(formatted) - 20} more" if len(formatted) > 20 else "")
            else:
                return "No dynamically generated capabilities available yet."
        except Exception as e:
            logging.warning(f"Could not load dynamic capabilities: {e}")
            return "No dynamically generated capabilities available yet."
    
    def _clean_code(self, code: str) -> str:
        """Clean and format generated code"""
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        # Fix common issues that cause execution problems
        lines = code.split('\n')
        cleaned_lines = []
        in_function = False
        function_depth = 0
        
        for i, line in enumerate(lines):
            # Skip empty lines at start/end
            if not cleaned_lines and not line.strip():
                continue
            
            line_stripped = line.strip()
            
            # Track function definitions and indentation
            if line_stripped.startswith('def '):
                in_function = True
                function_depth = len(line) - len(line.lstrip())
                cleaned_lines.append(line)
                continue
            elif line_stripped.startswith('class '):
                in_function = True
                function_depth = len(line) - len(line.lstrip())
                cleaned_lines.append(line)
                continue
            elif line_stripped and not line.startswith(' ' * function_depth if function_depth > 0 else '') and in_function:
                in_function = False
                function_depth = 0
            
            # Check for return statements outside functions
            if line_stripped.startswith('return ') and not in_function:
                if 'return' in line_stripped and '=' in line_stripped:
                    cleaned_line = line_stripped.replace('return ', 'result = ')
                    if cleaned_line != line_stripped:
                        cleaned_lines.append(cleaned_line)
                        cleaned_lines.append('print(f"Result: {result}")')
                    else:
                        cleaned_lines.append(line)
                else:
                    return_value = line_stripped.replace('return ', '').strip()
                    if return_value:
                        cleaned_lines.append(f'print({return_value})')
                    else:
                        cleaned_lines.append('print("Operation completed")')
            elif 'input(' in line and 'def' not in line:
                # Replace input() calls with test data to prevent timeouts
                import re
                line = re.sub(r'input\(["\'][^"\']*["\']\)', '"test_input"', line)
                line = line.replace('input()', '"test_input"')
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        cleaned_code = '\n'.join(cleaned_lines)
        
        # Final validation - check for syntax errors
        try:
            import ast
            ast.parse(cleaned_code)
        except SyntaxError as e:
            logging.warning(f"Syntax error detected in cleaned code: {e}")
            if "'return' outside function" in str(e):
                if 'return ' in cleaned_code and not cleaned_code.strip().startswith('def '):
                    cleaned_code = f"def main():\n    " + cleaned_code.replace('\n', '\n    ') + "\n\nmain()"
        
        return cleaned_code

# Global AI client instance
ai_client = AIClient()
