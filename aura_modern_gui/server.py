#!/usr/bin/env python3
"""
AURA Modern GUI - Python Backend Server
Bridges the beautiful web interface with AURA's powerful AI backend

This server:
- Serves the modern web GUI
- Provides WebSocket connection for real-time communication
- Handles AI requests and code execution
- Manages voice synthesis (optional fallback)
"""

import asyncio
import json
import logging
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory for AURA imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from aiohttp import web
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️  aiohttp not found. Install with: pip install aiohttp")

# Import AURA components
try:
    from ai_client import ai_client
    from code_executor import executor
    from capability_manager import capability_manager
    from self_improvement import improvement_engine
    from aura_responses import aura
    import windows_system_utils
    AURA_AVAILABLE = True
except ImportError as e:
    AURA_AVAILABLE = False
    print(f"⚠️  AURA components not fully available: {e}")


class AuraBackendServer:
    """Backend server for AURA Modern GUI"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.static_dir = Path(__file__).parent
        self.websockets = set()
        self.context = {
            "filename": None,
            "last_text": "",
            "session_start": datetime.now(),
            "command_count": 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("AuraServer")
        
    async def index_handler(self, request):
        """Serve the main HTML page"""
        index_path = self.static_dir / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        return web.Response(text="AURA GUI not found", status=404)
    
    async def static_handler(self, request):
        """Serve static files (CSS, JS)"""
        filename = request.match_info['filename']
        filepath = self.static_dir / filename
        
        if filepath.exists() and filepath.is_file():
            return web.FileResponse(filepath)
        return web.Response(text=f"File not found: {filename}", status=404)
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time communication"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        self.logger.info(f"New WebSocket connection. Total: {len(self.websockets)}")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        response = await self.handle_message(data)
                        await ws.send_json(response)
                    except json.JSONDecodeError:
                        await ws.send_json({
                            "type": "error",
                            "message": "Invalid JSON format"
                        })
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.websockets.discard(ws)
            self.logger.info(f"WebSocket disconnected. Total: {len(self.websockets)}")
        
        return ws
    
    async def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages from the web GUI"""
        msg_type = data.get("type", "")
        content = data.get("content", "")
        
        if msg_type == "command":
            return await self.process_command(content)
        elif msg_type == "status":
            return self.get_status()
        elif msg_type == "capabilities":
            return self.get_capabilities()
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            }
    
    async def process_command(self, message: str) -> Dict[str, Any]:
        """Process a command through AURA's AI engine"""
        self.context["command_count"] += 1
        
        if not AURA_AVAILABLE:
            return {
                "type": "error",
                "message": "AURA AI components not available. Please check installation."
            }
        
        try:
            # Generate code using AI
            code = ai_client.generate_code(message, self.context)
            
            if not code:
                return {
                    "type": "error",
                    "message": "Neural processing failed. Please rephrase your request."
                }
            
            # Execute the code
            execution_context = self.get_execution_context()
            success, output, result = executor.execute(code, execution_context)
            
            if success:
                # Check for execution errors in output
                has_errors = output and any(err in output for err in [
                    "Error:", "Traceback", "Exception", "Failed"
                ])
                
                if has_errors:
                    # Attempt self-improvement
                    improved, improvement_msg, exec_output = improvement_engine.handle_execution_failure(
                        message, code, output
                    )
                    
                    if improved:
                        return {
                            "type": "success",
                            "message": f"Neural adaptation successful: {improvement_msg}",
                            "output": exec_output,
                            "code": code
                        }
                    else:
                        return {
                            "type": "error",
                            "message": f"Execution produced errors: {output}",
                            "code": code
                        }
                else:
                    # Record success
                    capability_manager.record_execution(message, True)
                    
                    return {
                        "type": "success",
                        "message": aura.get_success_message(),
                        "output": output if output else "Command executed successfully.",
                        "code": code
                    }
            else:
                # Execution failed - attempt self-improvement
                improved, improvement_msg, exec_output = improvement_engine.handle_execution_failure(
                    message, code, output
                )
                
                if improved:
                    return {
                        "type": "success",
                        "message": f"Neural adaptation successful: {improvement_msg}",
                        "output": exec_output,
                        "code": code
                    }
                else:
                    return {
                        "type": "error",
                        "message": f"Execution failed: {output}",
                        "code": code
                    }
                    
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {
                "type": "error",
                "message": f"Neural processing error: {str(e)}"
            }
    
    def get_execution_context(self) -> Dict[str, Any]:
        """Build execution context with all available utilities"""
        context = {
            'context': self.context,
            'print': print,
        }
        
        # Add Windows system utilities
        if AURA_AVAILABLE:
            for attr_name in dir(windows_system_utils):
                if not attr_name.startswith('_'):
                    context[attr_name] = getattr(windows_system_utils, attr_name)
        
        return context
    
    def get_status(self) -> Dict[str, Any]:
        """Return system status"""
        return {
            "type": "status",
            "data": {
                "ai_client": AURA_AVAILABLE and ai_client is not None,
                "executor": AURA_AVAILABLE and executor is not None,
                "capability_manager": AURA_AVAILABLE and capability_manager is not None,
                "improvement_engine": AURA_AVAILABLE and improvement_engine is not None,
                "session_start": self.context["session_start"].isoformat(),
                "command_count": self.context["command_count"]
            }
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return available capabilities"""
        if not AURA_AVAILABLE:
            return {
                "type": "capabilities",
                "data": []
            }
        
        caps = list(capability_manager.capabilities.keys()) if capability_manager else []
        return {
            "type": "capabilities",
            "data": caps
        }
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients"""
        if self.websockets:
            await asyncio.gather(
                *[ws.send_json(message) for ws in self.websockets if not ws.closed]
            )
    
    def create_app(self) -> web.Application:
        """Create the aiohttp application"""
        app = web.Application()
        
        # Routes
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/ws', self.websocket_handler)
        app.router.add_get('/{filename}', self.static_handler)
        
        return app
    
    def run(self, open_browser: bool = True):
        """Start the server"""
        if not AIOHTTP_AVAILABLE:
            print("❌ Cannot start server: aiohttp is required")
            print("   Install with: pip install aiohttp")
            return
        
        app = self.create_app()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██╗   ██╗██████╗  █████╗                         ║
║    ██╔══██╗██║   ██║██╔══██╗██╔══██╗                        ║
║    ███████║██║   ██║██████╔╝███████║                        ║
║    ██╔══██║██║   ██║██╔══██╗██╔══██║                        ║
║    ██║  ██║╚██████╔╝██║  ██║██║  ██║                        ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                        ║
║                                                              ║
║         Advanced Neural Network Interface                   ║
║         Modern GUI with Floating Voice Animation            ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   🌐 Server running at: http://{self.host}:{self.port}               ║
║   📡 WebSocket endpoint: ws://{self.host}:{self.port}/ws             ║
║                                                              ║
║   Press Ctrl+C to stop the server                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        # Open browser
        if open_browser:
            webbrowser.open(f"http://{self.host}:{self.port}")
        
        # Run server
        web.run_app(app, host=self.host, port=self.port, print=None)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AURA Modern GUI Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    
    args = parser.parse_args()
    
    server = AuraBackendServer(host=args.host, port=args.port)
    server.run(open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
