"""
Rate limiting utilities for the User Management System.
Implements a simple in-memory rate limiter to prevent brute force attacks.
"""
from builtins import dict, int, str
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A simple in-memory rate limiter to prevent brute force attacks.
    
    This implementation uses a dictionary to store the number of attempts and timestamps
    for each key (e.g., IP address or username). It supports both per-key and global rate limiting.
    
    Note: This is a simple implementation suitable for single-instance deployments.
    For production use with multiple instances, consider using Redis or another distributed cache.
    """
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, block_seconds: int = 3600):
        """
        Initialize the rate limiter.
        
        Args:
            max_attempts: Maximum number of attempts allowed within the time window
            window_seconds: Time window in seconds for counting attempts
            block_seconds: Time in seconds to block after max_attempts is reached
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self._attempts: Dict[str, Dict[str, int]] = {}  # {key: {timestamp: count}}
        self._blocked_until: Dict[str, datetime] = {}  # {key: blocked_until_timestamp}
        self._lock = Lock()  # Thread safety for in-memory storage
        
    def is_rate_limited(self, key: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if a key is rate limited.
        
        Args:
            key: The key to check (e.g., IP address, username, or combination)
            
        Returns:
            Tuple[bool, Optional[datetime]]: (is_limited, blocked_until)
            - is_limited: True if the key is rate limited, False otherwise
            - blocked_until: Datetime until which the key is blocked, or None if not blocked
        """
        with self._lock:
            now = datetime.now()
            
            # Check if key is blocked
            if key in self._blocked_until:
                blocked_until = self._blocked_until[key]
                if now < blocked_until:
                    # Still blocked
                    return True, blocked_until
                else:
                    # Block expired, remove from blocked list
                    del self._blocked_until[key]
            
            # Clean up old attempts
            self._cleanup(key, now)
            
            # Count recent attempts
            recent_attempts = self._count_recent_attempts(key, now)
            
            # Check if max attempts reached
            if recent_attempts >= self.max_attempts:
                # Block the key
                blocked_until = now + timedelta(seconds=self.block_seconds)
                self._blocked_until[key] = blocked_until
                logger.warning(f"Rate limit exceeded for {key}. Blocked until {blocked_until}")
                return True, blocked_until
            
            return False, None
    
    def record_attempt(self, key: str) -> None:
        """
        Record an attempt for a key.
        
        Args:
            key: The key to record an attempt for
        """
        with self._lock:
            now = datetime.now()
            timestamp = int(now.timestamp())
            
            # Initialize key if not exists
            if key not in self._attempts:
                self._attempts[key] = {}
            
            # Record attempt
            if timestamp in self._attempts[key]:
                self._attempts[key][timestamp] += 1
            else:
                self._attempts[key][timestamp] = 1
    
    def reset(self, key: str) -> None:
        """
        Reset attempts and unblock a key.
        
        Args:
            key: The key to reset
        """
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]
            if key in self._blocked_until:
                del self._blocked_until[key]
    
    def _cleanup(self, key: str, now: datetime) -> None:
        """
        Clean up old attempts for a key.
        
        Args:
            key: The key to clean up
            now: Current datetime
        """
        if key not in self._attempts:
            return
        
        cutoff = int((now - timedelta(seconds=self.window_seconds)).timestamp())
        self._attempts[key] = {ts: count for ts, count in self._attempts[key].items() if int(ts) >= cutoff}
        
        # Remove empty entries
        if not self._attempts[key]:
            del self._attempts[key]
    
    def _count_recent_attempts(self, key: str, now: datetime) -> int:
        """
        Count recent attempts for a key.
        
        Args:
            key: The key to count attempts for
            now: Current datetime
            
        Returns:
            int: Number of recent attempts
        """
        if key not in self._attempts:
            return 0
        
        cutoff = int((now - timedelta(seconds=self.window_seconds)).timestamp())
        return sum(count for ts, count in self._attempts[key].items() if int(ts) >= cutoff)

# Global rate limiter instance
login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
api_rate_limiter = RateLimiter(max_attempts=100, window_seconds=60, block_seconds=300)
