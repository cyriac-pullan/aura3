"""
API Key Pool Manager
Rotates between multiple Gemini API keys to avoid rate limits
"""
import logging
import time
from typing import List, Optional

class APIKeyPool:
    """Manages multiple API keys and rotates between them"""
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize with a list of API keys
        
        Args:
            api_keys: List of Gemini API keys
        """
        self.api_keys = api_keys
        self.current_index = 0
        self.key_usage = {key: {"requests": 0, "last_reset": time.time()} for key in api_keys}
        self.requests_per_minute_limit = 15  # Free tier limit
        
        logging.info(f"API Key Pool initialized with {len(api_keys)} keys")
    
    def get_key(self) -> str:
        """
        Get an available API key
        Automatically rotates to next key if current one is rate limited
        
        Returns:
            API key string
        """
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            current_key = self.api_keys[self.current_index]
            
            # Check if we need to reset the counter (1 minute passed)
            if time.time() - self.key_usage[current_key]["last_reset"] > 60:
                self.key_usage[current_key]["requests"] = 0
                self.key_usage[current_key]["last_reset"] = time.time()
            
            # Check if this key is still under the limit
            if self.key_usage[current_key]["requests"] < self.requests_per_minute_limit:
                self.key_usage[current_key]["requests"] += 1
                logging.debug(f"Using API key #{self.current_index + 1} ({self.key_usage[current_key]['requests']}/{self.requests_per_minute_limit} requests)")
                return current_key
            
            # This key is rate limited, try next one
            logging.warning(f"API key #{self.current_index + 1} rate limited, rotating to next key")
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            attempts += 1
        
        # All keys are rate limited, use the first one anyway (will trigger retry logic)
        logging.warning("All API keys are rate limited, using first key with retry logic")
        return self.api_keys[0]
    
    def get_status(self) -> dict:
        """Get current status of all API keys"""
        status = {}
        for i, key in enumerate(self.api_keys):
            status[f"Key {i+1}"] = {
                "requests_used": self.key_usage[key]["requests"],
                "limit": self.requests_per_minute_limit,
                "available": self.key_usage[key]["requests"] < self.requests_per_minute_limit
            }
        return status


# Global instance
_key_pool = None

def get_api_key_pool() -> Optional[APIKeyPool]:
    """Get the global API key pool instance"""
    return _key_pool

def initialize_key_pool(api_keys: List[str]):
    """Initialize the global API key pool"""
    global _key_pool
    _key_pool = APIKeyPool(api_keys)
    return _key_pool
