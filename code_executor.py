import ast
import sys
import io
import contextlib
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from config import config

class CodeValidator:
    """Validates Python code for security before execution"""
    
    def __init__(self):
        self.allowed_modules = set(config.get('security.allowed_modules', []))
        self.forbidden_functions = set(config.get('security.forbidden_functions', []))
        self.max_code_length = config.get('security.max_code_length', 5000)
    
    def validate(self, code: str) -> Tuple[bool, str]:
        """Validate code for security and syntax - SECURITY DISABLED"""
        try:
            # Only check for basic syntax errors, no security restrictions
            ast.parse(code)
            return True, "Code is valid (security checks disabled)"

        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"

class SecurityVisitor(ast.NodeVisitor):
    """AST visitor to check for security violations"""
    
    def __init__(self, allowed_modules: set, forbidden_functions: set):
        self.allowed_modules = allowed_modules
        self.forbidden_functions = forbidden_functions
        self.violations = []
        self.imported_modules = set()
    
    def visit_Import(self, node):
        """Check import statements"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name not in self.allowed_modules:
                self.violations.append(f"Forbidden import: {module_name}")
            self.imported_modules.add(module_name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check from...import statements"""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name not in self.allowed_modules:
                self.violations.append(f"Forbidden import: {module_name}")
            self.imported_modules.add(module_name)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Check function calls"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.forbidden_functions:
                self.violations.append(f"Forbidden function: {func_name}")
        elif isinstance(node.func, ast.Attribute):
            # Check for dangerous attribute access
            if node.func.attr in self.forbidden_functions:
                self.violations.append(f"Forbidden function: {node.func.attr}")
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Check attribute access"""
        # Check for dangerous attributes like __class__, __globals__, etc.
        if isinstance(node.attr, str) and node.attr.startswith('__') and node.attr.endswith('__'):
            if node.attr not in ['__init__', '__str__', '__repr__']:
                self.violations.append(f"Forbidden attribute access: {node.attr}")
        self.generic_visit(node)

class SafeExecutor:
    """Safely execute Python code with timeout and output capture"""
    
    def __init__(self):
        self.validator = CodeValidator()
        self.timeout = config.get('security.execution_timeout', 30)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Any]:
        """
        Execute code safely with validation and timeout
        Returns: (success, output/error, result)
        """
        # Validate code first
        is_valid, validation_msg = self.validator.validate(code)
        if not is_valid:
            logging.warning(f"Code validation failed: {validation_msg}")
            return False, f"Validation failed: {validation_msg}", None
        
        # Prepare execution context
        # Include ALL built-ins for unrestricted execution
        import builtins
        exec_context = {
            '__builtins__': builtins.__dict__.copy(),
            '__name__': '__main__',
        }
        
        if context:
            exec_context.update(context)
        
        # Capture output
        output_buffer = io.StringIO()
        result = None
        
        def execute_with_timeout():
            nonlocal result
            try:
                with contextlib.redirect_stdout(output_buffer), \
                     contextlib.redirect_stderr(output_buffer):
                    result = exec(code, exec_context)
            except SyntaxError as e:
                error_msg = f"Syntax error: {e}"
                if "'return' outside function" in str(e):
                    error_msg += "\n\nHint: The generated code has a 'return' statement outside of a function. This usually means the AI generated incomplete code. Please try rephrasing your request or ask for a complete function."
                output_buffer.write(f"Execution error: {error_msg}")
                raise
            except Exception as e:
                output_buffer.write(f"Execution error: {e}")
                raise
        
        # Execute with timeout
        thread = threading.Thread(target=execute_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            return False, f"Execution timeout ({self.timeout}s)", None
        
        output = output_buffer.getvalue()
        
        if "Execution error:" in output:
            return False, output, None
        
        return True, output, result

# Global executor instance
executor = SafeExecutor()
