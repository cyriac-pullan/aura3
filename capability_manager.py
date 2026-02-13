import ast
import json
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from config import config

class CapabilityManager:
    """Manages dynamic capabilities and self-improvement"""
    
    def __init__(self):
        self.capabilities_file = Path(config.capabilities_file)
        self.learning_file = Path(config.learning_file)
        self.utils_module_path = Path(__file__).parent / "windows_system_utils.py"
        
        # Load existing capabilities and learning data
        self.capabilities = self._load_capabilities()
        self.learning_data = self._load_learning_data()
        
        # Track success/failure rates
        self.execution_stats = {}
        
        logging.info(f"Capability Manager initialized with {len(self.capabilities)} capabilities")
    
    def _load_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Load capabilities from file"""
        if self.capabilities_file.exists():
            try:
                with open(self.capabilities_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading capabilities: {e}")
        return {}
    
    def _save_capabilities(self):
        """Save capabilities to file"""
        try:
            with open(self.capabilities_file, 'w') as f:
                json.dump(self.capabilities, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving capabilities: {e}")
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """Load learning data from file"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading learning data: {e}")
        
        return {
            "successful_commands": [],
            "failed_commands": [],
            "generated_functions": [],
            "improvement_history": []
        }
    
    def _save_learning_data(self):
        """Save learning data to file"""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving learning data: {e}")
    
    def add_capability(self, function_code: str, command: str, success: bool = True) -> bool:
        """Add a new capability from generated function code"""
        try:
            # Parse the function
            tree = ast.parse(function_code)
            func_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            if not func_nodes:
                logging.error("No function definition found in code")
                return False
            
            func_node = func_nodes[0]
            func_name = func_node.name
            
            # Extract function metadata
            docstring = ast.get_docstring(func_node) or "Auto-generated function"
            
            # Get function signature
            signature = self._extract_signature(func_node)
            
            # Add to capabilities
            capability = {
                "name": func_name,
                "description": docstring.split('\n')[0],  # First line of docstring
                "signature": signature,
                "code": function_code,
                "created_date": datetime.now().isoformat(),
                "created_for_command": command,
                "success_count": 1 if success else 0,
                "failure_count": 0 if success else 1,
                "last_used": datetime.now().isoformat() if success else None
            }
            
            self.capabilities[func_name] = capability
            self._save_capabilities()
            
            # Add to utils module
            self._add_to_utils_module(function_code, command)
            
            # Record in learning data
            self.learning_data["generated_functions"].append({
                "function_name": func_name,
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "success": success
            })
            self._save_learning_data()
            
            logging.info(f"Added new capability: {func_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding capability: {e}")
            return False
    
    def _extract_signature(self, func_node: ast.FunctionDef) -> str:
        """Extract function signature from AST node"""
        args = []
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                # Try to get annotation string
                if isinstance(arg.annotation, ast.Name):
                    arg_str += f": {arg.annotation.id}"
                elif isinstance(arg.annotation, ast.Constant):
                    arg_str += f": {arg.annotation.value}"
            args.append(arg_str)
        
        # Handle return annotation
        returns = ""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                returns = f" -> {func_node.returns.id}"
            elif isinstance(func_node.returns, ast.Constant):
                returns = f" -> {func_node.returns.value}"
        
        return f"{func_node.name}({', '.join(args)}){returns}"
    
    def _add_to_utils_module(self, function_code: str, command: str):
        """Add function to windows_system_utils.py"""
        try:
            # Read current utils module
            if self.utils_module_path.exists():
                with open(self.utils_module_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            else:
                current_content = ""
            
            # Add new function
            new_content = current_content + f"\n\n# Auto-generated for: {command}\n{function_code}\n"
            
            with open(self.utils_module_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Reload the module to make function available
            self._reload_utils_module()
            
        except Exception as e:
            logging.error(f"Error adding to utils module: {e}")
    
    def _reload_utils_module(self):
        """Reload the utils module to pick up new functions"""
        try:
            import sys
            if 'windows_system_utils' in sys.modules:
                importlib.reload(sys.modules['windows_system_utils'])
            else:
                import windows_system_utils
        except Exception as e:
            logging.error(f"Error reloading utils module: {e}")
    
    def record_execution(self, command: str, success: bool, function_name: str = None):
        """Record execution results for learning"""
        timestamp = datetime.now().isoformat()
        
        execution_record = {
            "command": command,
            "success": success,
            "timestamp": timestamp,
            "function_name": function_name
        }
        
        if success:
            self.learning_data["successful_commands"].append(execution_record)
        else:
            self.learning_data["failed_commands"].append(execution_record)
        
        # Update capability stats
        if function_name and function_name in self.capabilities:
            if success:
                self.capabilities[function_name]["success_count"] += 1
                self.capabilities[function_name]["last_used"] = timestamp
            else:
                self.capabilities[function_name]["failure_count"] += 1
        
        # Limit history size
        max_history = config.get('learning.max_learning_history', 1000)
        if len(self.learning_data["successful_commands"]) > max_history:
            self.learning_data["successful_commands"] = self.learning_data["successful_commands"][-max_history:]
        if len(self.learning_data["failed_commands"]) > max_history:
            self.learning_data["failed_commands"] = self.learning_data["failed_commands"][-max_history:]
        
        self._save_capabilities()
        self._save_learning_data()
    
    def get_capabilities_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all capabilities"""
        summary = []
        for name, cap in self.capabilities.items():
            summary.append({
                "name": name,
                "description": cap["description"],
                "signature": cap["signature"],
                "success_rate": self._calculate_success_rate(cap),
                "last_used": cap.get("last_used")
            })
        return summary
    
    def _calculate_success_rate(self, capability: Dict[str, Any]) -> float:
        """Calculate success rate for a capability"""
        total = capability["success_count"] + capability["failure_count"]
        if total == 0:
            return 0.0
        return capability["success_count"] / total
    
    def find_similar_commands(self, command: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar successful commands for learning"""
        successful_commands = self.learning_data["successful_commands"]
        
        # Simple similarity based on word overlap
        command_words = set(command.lower().split())
        similarities = []
        
        for record in successful_commands:
            record_words = set(record["command"].lower().split())
            overlap = len(command_words.intersection(record_words))
            if overlap > 0:
                similarities.append({
                    "command": record["command"],
                    "similarity": overlap / len(command_words.union(record_words)),
                    "function_name": record.get("function_name"),
                    "timestamp": record["timestamp"]
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]
    
    def should_attempt_improvement(self, command: str, error: str) -> bool:
        """Determine if we should attempt to improve capabilities - ALWAYS ENABLED"""
        # Always attempt improvement for any failure
        return True

# Global capability manager instance
capability_manager = CapabilityManager()
