"""
AURA Agentic App Creator
Autonomous app generation with self-correcting error loop.

Like Antigravity - generates code, runs it, catches errors, fixes with Gemini, retries.
"""

import os
import sys
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
from google import genai
from config import config

# App output directory
APPS_DIR = Path.home() / "Desktop" / "AURA_Apps"


class AgenticAppCreator:
    """
    Autonomous app creator that generates, tests, and fixes code iteratively.
    
    Flow:
    1. User: "Create a calculator app"
    2. Generate code with Gemini
    3. Run the code to test it
    4. If error → Send error back to Gemini for fix
    5. Retry up to MAX_RETRIES times
    6. If success → Save and launch
    """
    
    MAX_RETRIES = 3
    
    def __init__(self):
        # Ensure apps directory exists
        APPS_DIR.mkdir(exist_ok=True)

        # --- App Creator uses its own dedicated API key ---
        # Set GEMINI_API_KEY_APPCREATOR in .env to isolate its quota.
        appcreator_key = config.api_key_appcreator
        if appcreator_key:
            self._client = genai.Client(api_key=appcreator_key)
            self._model = "gemini-2.5-flash"
            print(f"[AppCreator] Client ready. Key: {appcreator_key[:10]}...{appcreator_key[-4:]} (GEMINI_API_KEY_APPCREATOR)")
        else:
            self._client = None
            self._model = None
            print("[AppCreator] ⚠️  No API key — set GEMINI_API_KEY_APPCREATOR or GEMINI_API_KEY in .env")
    
    def create_app(self, description: str, app_name: str = None) -> Tuple[bool, str, str]:
        """
        Create an app from description with auto-fix loop.
        
        Args:
            description: What kind of app to create (e.g., "a calculator app")
            app_name: Optional name for the app file
            
        Returns:
            (success, message, file_path)
        """
        if not self._client:
            return False, "AI client not available — check GEMINI_API_KEY_APPCREATOR in .env", ""
        
        # Generate app name from description if not provided
        if not app_name:
            app_name = self._generate_app_name(description)
        
        print(f"\n{'='*60}")
        print(f"🚀 AURA Agentic App Creator")
        print(f"{'='*60}")
        print(f"📝 Request: {description}")
        print(f"📁 Output: {APPS_DIR / app_name}")
        print(f"{'='*60}\n")
        
        # Initial code generation
        code = self._generate_app_code(description)
        if not code:
            return False, "Failed to generate initial code.", ""
        
        # Iterative fix loop
        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"\n🔄 Attempt {attempt}/{self.MAX_RETRIES}")
            
            # Test the code
            success, error_msg = self._test_code(code)
            
            if success:
                # Save and launch
                file_path = self._save_app(code, app_name)
                print(f"\n✅ App created successfully!")
                print(f"📍 Saved to: {file_path}")
                
                # Launch the app
                self._launch_app(file_path)
                
                return True, f"Created {app_name} on your Desktop!", str(file_path)
            
            # Handle missing packages
            if "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                package = self._extract_package_name(error_msg)
                if package:
                    print(f"📦 Missing package: {package}")
                    if self._install_package(package):
                        print(f"✅ Installed {package}")
                        continue  # Retry same code after install
                    else:
                        print(f"❌ Failed to install {package}")
            
            # Try to fix the code with Gemini
            if attempt < self.MAX_RETRIES:
                print(f"❌ Error: {error_msg[:100]}...")
                print(f"🔧 Asking Gemini to fix...")
                code = self._fix_code(code, error_msg, description)
                if not code:
                    return False, "Failed to fix the code.", ""
        
        return False, f"Could not create app after {self.MAX_RETRIES} attempts.", ""
    
    def _generate_app_code(self, description: str) -> Optional[str]:
        """Generate initial app code from description."""
        prompt = f"""Create a complete, working Python GUI application based on this description:
"{description}"

REQUIREMENTS:
1. Use tkinter (it's built-in, no install needed)
2. Include ALL necessary imports at the top
3. Make it visually appealing with proper layout
4. Add a title bar with the app name
5. Handle common errors gracefully
6. The code must be COMPLETE and RUNNABLE as-is
7. End with: if __name__ == "__main__": followed by the main code

IMPORTANT: Return ONLY the Python code, no explanations or markdown.
Start directly with 'import' and end with the mainloop or equivalent."""

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            code = response.text.strip()
            
            # Clean up code (remove markdown if present)
            code = self._clean_code(code)
            
            print(f"📝 Generated {len(code)} characters of code")
            return code
            
        except Exception as e:
            print(f"❌ Code generation failed: {e}")
            return None
    
    def _fix_code(self, code: str, error_msg: str, original_description: str) -> Optional[str]:
        """Ask Gemini to fix the code based on the error."""
        prompt = f"""Fix this Python code that has an error.

ORIGINAL REQUEST: {original_description}

ERROR MESSAGE:
{error_msg}

CURRENT CODE:
```python
{code}
```

INSTRUCTIONS:
1. Fix the error shown above
2. Keep the same functionality
3. Make sure all imports are correct
4. Return ONLY the fixed Python code, no explanations
5. Start directly with 'import'"""

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            fixed_code = response.text.strip()
            fixed_code = self._clean_code(fixed_code)
            
            print(f"🔧 Generated fix ({len(fixed_code)} chars)")
            return fixed_code
            
        except Exception as e:
            print(f"❌ Fix generation failed: {e}")
            return None
    
    def _test_code(self, code: str) -> Tuple[bool, str]:
        """
        Test the code by running it briefly.
        For GUI apps, we just check for syntax/import errors.
        """
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # First, check syntax by compiling
            compile(code, temp_path, 'exec')
            
            # Run with timeout to check imports work
            # We use a wrapper that exits after imports succeed
            test_wrapper = f'''
import sys
import threading

def timeout_exit():
    import time
    time.sleep(2)
    # If we got here, imports worked and GUI started
    import os
    os._exit(0)

# Start timeout thread
t = threading.Thread(target=timeout_exit, daemon=True)
t.start()

# Run the actual code
try:
    exec(open(r"{temp_path}").read())
except SystemExit:
    pass
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as wrapper_f:
                wrapper_f.write(test_wrapper)
                wrapper_path = wrapper_f.name
            
            result = subprocess.run(
                [sys.executable, wrapper_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            os.unlink(wrapper_path)
            
            if result.returncode == 0:
                return True, ""
            else:
                error = result.stderr or result.stdout or "Unknown error"
                return False, error
                
        except subprocess.TimeoutExpired:
            # Timeout means the app started successfully (GUI is running)
            return True, ""
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"
        except Exception as e:
            return False, str(e)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _save_app(self, code: str, app_name: str) -> Path:
        """Save the app to the apps directory."""
        file_path = APPS_DIR / app_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return file_path
    
    def _launch_app(self, file_path: Path):
        """Launch the created app in a new process."""
        try:
            subprocess.Popen(
                [sys.executable, str(file_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            print(f"🚀 Launched: {file_path.name}")
        except Exception as e:
            print(f"⚠️ Could not launch app: {e}")
    
    def _install_package(self, package: str) -> bool:
        """Install a missing package."""
        try:
            print(f"📦 Installing {package}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Install failed: {e}")
            return False
    
    def _extract_package_name(self, error_msg: str) -> Optional[str]:
        """Extract package name from ModuleNotFoundError."""
        import re
        
        # Match: No module named 'xyz' or ModuleNotFoundError: No module named 'xyz'
        match = re.search(r"No module named ['\"](\w+)['\"]", error_msg)
        if match:
            return match.group(1)
        return None
    
    def _generate_app_name(self, description: str) -> str:
        """Generate a filename from description."""
        # Extract key words
        words = description.lower()
        words = words.replace("create", "").replace("make", "").replace("build", "")
        words = words.replace("a ", "").replace("an ", "").replace("app", "")
        words = words.strip().split()[:3]  # First 3 meaningful words
        
        if words:
            name = "_".join(words)
        else:
            name = "aura_app"
        
        # Clean up
        name = "".join(c if c.isalnum() or c == '_' else '_' for c in name)
        name = name.strip('_')
        
        return f"{name}.py"
    
    def _clean_code(self, code: str) -> str:
        """Clean up code - remove markdown formatting if present."""
        # Remove markdown code blocks
        if code.startswith("```"):
            lines = code.split('\n')
            # Remove first line (```python) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            code = '\n'.join(lines)
        
        return code.strip()


# Global instance
app_creator = AgenticAppCreator()


def create_app(description: str, app_name: str = None) -> Tuple[bool, str, str]:
    """Create an app from description."""
    return app_creator.create_app(description, app_name)


# Test
if __name__ == "__main__":
    print("Testing Agentic App Creator...")
    success, msg, path = create_app("a simple calculator with buttons for +, -, *, /")
    print(f"\nResult: {msg}")
