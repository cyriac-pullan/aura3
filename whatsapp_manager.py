
import os
import requests
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WhatsAppManager")

WHATSAPP_SERVICE_DIR = r"e:\agent\whatsapp_service"
WHATSAPP_BOT_SCRIPT = "whatsapp_bot.js"
API_URL = "http://localhost:3000"

class WhatsAppManager:
    def __init__(self):
        self.process = None
        self._ensure_service_running()

    def _ensure_service_running(self):
        """Checks if the Node.js service is running, otherwise starts it."""
        try:
            response = requests.get(f"{API_URL}/health", timeout=1) # Assume health check or just connect
            if response.status_code == 200:
                logger.info("WhatsApp service is already running.")
                return
        except requests.ConnectionError:
            logger.info("Starting WhatsApp service...")
            self._start_service()

    def _start_service(self):
        """Starts the Node.js WhatsApp bot service."""
        try:
            # Check if node is installed
            subprocess.run(["node", "-v"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Start the service in a new console window so user can scan QR code
            cmd = f'start cmd /k "cd /d {WHATSAPP_SERVICE_DIR} && node {WHATSAPP_BOT_SCRIPT}"'
            subprocess.Popen(cmd, shell=True)
            
            logger.info("WhatsApp service started. Please check the new window for QR code if needed.")
            # Wait for service to initialize
            time.sleep(5) 
        except FileNotFoundError:
            logger.error("Node.js is not installed or not in PATH.")
        except Exception as e:
            logger.error(f"Failed to start WhatsApp service: {e}")

    def find_file(self, filename: str, search_path: str = None) -> Optional[str]:
        """Finds a file in the given directory with robust matching."""
        if not search_path:
            search_path = str(Path.home() / "Downloads")
        
        search_path = Path(search_path)
        if not search_path.exists():
            logger.error(f"Search path does not exist: {search_path}")
            return None

        # Exact match first
        exact_match = search_path / filename
        if exact_match.exists():
            return str(exact_match)
        
        # Fuzzy match using glob
        # e.g., "resume" matches "resume.pdf", "My Resume.docx"
        patterns = [f"{filename}", f"{filename}.*", f"*{filename}*"]
        
        for pattern in patterns:
            matches = list(search_path.glob(pattern))
            # Sort by modification time (newest first)
            matches.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            if matches:
                found_file = str(matches[0])
                logger.info(f"Found file: {found_file}")
                return found_file
        
        logger.warning(f"File '{filename}' not found in {search_path}")
        return None

    def _send_request_with_retry(self, endpoint: str, payload: dict, retries: int = 20, delay: int = 2) -> bool:
        """Sends a request to the WhatsApp service with retries for readiness."""
        url = f"{API_URL}/{endpoint}"
        
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    return True
                
                elif response.status_code == 503:
                    logger.info(f"WhatsApp client not ready (attempt {attempt+1}/{retries}). Waiting...")
                    time.sleep(delay)
                    continue
                    
                else:
                    logger.error(f"Failed to send request: {response.text}")
                    return False
                    
            except requests.ConnectionError:
                logger.warning(f"WhatsApp service not reachable (attempt {attempt+1}/{retries}). Waiting...")
                time.sleep(delay)
        
        logger.error(f"Failed to send request after {retries} attempts.")
        return False

    def send_message(self, contact: str, message: str) -> bool:
        """Sends a text message via the WhatsApp service."""
        payload = {"contact": contact, "message": message}
        if self._send_request_with_retry("send-message", payload):
            logger.info(f"Message sent to {contact}")
            return True
        return False

    def send_file(self, contact: str, filename: str, location: str = "Downloads", caption: str = "") -> bool:
        """Sends a file via the WhatsApp service."""
        
        # Resolve location alias
        if location.lower() == "downloads":
            search_path = str(Path.home() / "Downloads")
        elif location.lower() == "desktop":
            search_path = str(Path.home() / "Desktop")
        elif location.lower() == "documents":
            search_path = str(Path.home() / "Documents")
        else:
            search_path = location

        file_path = self.find_file(filename, search_path)
        
        if not file_path:
            logger.error(f"Could not find file '{filename}' in '{location}'")
            return False

        payload = {
            "contact": contact, 
            "filePath": file_path,
            "caption": caption
        }
        
        if self._send_request_with_retry("send-file", payload):
            logger.info(f"File sent to {contact}")
            return True
        return False

if __name__ == "__main__":
    # Test
    wm = WhatsAppManager()
    # wm.send_message("Alex", "Hello from Python!")
