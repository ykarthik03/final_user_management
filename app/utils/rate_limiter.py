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
        self._attempts: Dict[str, Dict[datetime, int]] = {}  # {key: {timestamp: count}}
        self._blocked_until: Dict[str, datetime] = {}  # {key: blocked_until_timestamp}
        self._lock = Lock()  # Thread safety for in-memory storage
        
    def is_rate_limited(self, key: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if a key is rate limited.
        
        Args:
            key: The key to check
            
        Returns:
            Tuple[bool, Optional[datetime]]: (is_limited, blocked_until)
                is_limited: True if the key is rate limited
                blocked_until: Datetime when the block expires, or None if not blocked
        """
        now = datetime.now()
        
        # Use thread lock to ensure consistent state
        with self._lock:
            # Check if key is blocked
            if key in self._blocked_until:
                if now < self._blocked_until[key]:
                    # Still blocked
                    return True, self._blocked_until[key]
                else:
                    # Block expired, remove it and its associated attempts
                    logger.debug(f"Block expired for key {key}. Clearing attempts.")
                    del self._blocked_until[key]
                    if key in self._attempts: 
                        del self._attempts[key]
            
            # If key doesn't exist in attempts dictionary (e.g., new key or block just expired and attempts cleared),
            # it's not rate limited by current ongoing attempts.
            if key not in self._attempts:
                return False, None
        
        # Clean up old attempts
        self._cleanup(key, now)
        
        # Count recent attempts
        recent_attempts = self._count_recent_attempts(key, now)
        
        # Check if over limit
        if recent_attempts >= self.max_attempts:
            # Block the key
            blocked_until = now + timedelta(seconds=self.block_seconds)
            self._blocked_until[key] = blocked_until
            return True, blocked_until
        
        return False, None
    
    def record_attempt(self, key: str) -> bool:
        """
        Record an attempt for the given key.
        
        Args:
            key: The key to record an attempt for
            
        Returns:
            bool: True if the key is now rate limited, False otherwise
        """
        now = datetime.now()
        with self._lock:
            # Ensure the key's primary dict exists if it's a completely new key
            if key not in self._attempts:
                self._attempts[key] = {}
            
            # Clean up old attempts. This might remove self._attempts[key] if all its sub-entries expire.
            self._cleanup(key, now)
            
            # If _cleanup removed the key because all its old attempts expired,
            # we need to re-initialize it for the new current attempt.
            if key not in self._attempts:
                self._attempts[key] = {}
            
            # Record new attempt
            current_minute = now.replace(second=0, microsecond=0)
            self._attempts[key][current_minute] = self._attempts[key].get(current_minute, 0) + 1
            
            # Check if we should block this key
            total_attempts = sum(self._attempts[key].values())
            if total_attempts >= self.max_attempts:
                self._blocked_until[key] = now + timedelta(seconds=self.block_seconds)
                return True
            return False
    
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
        
        # In tests, we're using timestamps as strings, but in our implementation we're using datetime objects
        # Handle both cases for backward compatibility
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Create a new dictionary with only recent attempts
        cleaned_attempts = {}
        for ts, count in self._attempts[key].items():
            # Handle both string timestamps and datetime objects
            ts_datetime = None
            
            if isinstance(ts, str):
                try:
                    # Try to convert string to timestamp
                    ts_int = int(float(ts))  # Handle both integer and float strings
                    ts_datetime = datetime.fromtimestamp(ts_int)
                except (ValueError, TypeError):
                    # If conversion fails, keep the attempt (better safe than sorry)
                    logger.warning(f"Failed to convert timestamp {ts} to datetime")
                    cleaned_attempts[ts] = count
                    continue  # Skip the datetime check
            else:
                # It's already a datetime object
                ts_datetime = ts
            
            # Now check if the timestamp is within the window
            if ts_datetime and ts_datetime >= cutoff:
                cleaned_attempts[ts] = count
                    
        self._attempts[key] = cleaned_attempts
        
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
            
        cutoff = now - timedelta(seconds=self.window_seconds)
        total_count = 0
        
        for ts, count in self._attempts[key].items():
            # Handle both string timestamps and datetime objects
            ts_datetime = None
            
            if isinstance(ts, str):
                try:
                    # Try to convert string to timestamp
                    ts_int = int(float(ts))  # Handle both integer and float strings
                    ts_datetime = datetime.fromtimestamp(ts_int)
                except (ValueError, TypeError):
                    # If conversion fails, use current time (better safe than sorry)
                    logger.warning(f"Failed to convert timestamp {ts} to datetime")
                    ts_datetime = now  # Count it as recent
            else:
                # It's already a datetime object
                ts_datetime = ts
            
            # Now check if the timestamp is within the window
            if ts_datetime and ts_datetime >= cutoff:
                total_count += count
                    
        return total_count

# Global rate limiter instance
login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
api_rate_limiter = RateLimiter(max_attempts=100, window_seconds=60, block_seconds=300)
