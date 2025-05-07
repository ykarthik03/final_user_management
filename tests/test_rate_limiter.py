"""
Tests for rate limiting functionality.
"""
import pytest
from datetime import datetime, timedelta
from app.utils.rate_limiter import RateLimiter
import time

def test_rate_limiter_initialization():
    """Test that the rate limiter initializes correctly."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    assert limiter.max_attempts == 5
    assert limiter.window_seconds == 300
    assert limiter.block_seconds == 3600
    assert limiter._attempts == {}
    assert limiter._blocked_until == {}

def test_record_attempt():
    """Test recording attempts."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Record a single attempt
    limiter.record_attempt("test_key")
    
    # Verify attempt was recorded
    assert "test_key" in limiter._attempts
    assert len(limiter._attempts["test_key"]) == 1
    
    # Record multiple attempts
    limiter.record_attempt("test_key")
    limiter.record_attempt("test_key")
    
    # Verify attempts were recorded
    timestamp = next(iter(limiter._attempts["test_key"].keys()))
    assert limiter._attempts["test_key"][timestamp] == 3

def test_is_rate_limited():
    """Test rate limiting functionality."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Record attempts up to limit
    for _ in range(3):
        limiter.record_attempt("test_key")
    
    # Should not be rate limited yet
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited
    
    # Record one more attempt to exceed limit
    limiter.record_attempt("test_key")
    
    # Should now be rate limited
    is_limited, blocked_until = limiter.is_rate_limited("test_key")
    assert is_limited
    assert blocked_until > datetime.now()
    assert blocked_until <= datetime.now() + timedelta(seconds=3600)

def test_reset():
    """Test resetting rate limits."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Record attempts and trigger blocking
    for _ in range(4):
        limiter.record_attempt("test_key")
    
    # Verify key is blocked
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert is_limited
    
    # Reset the key
    limiter.reset("test_key")
    
    # Verify key is no longer blocked
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited
    assert "test_key" not in limiter._attempts
    assert "test_key" not in limiter._blocked_until

def test_cleanup():
    """Test cleanup of old attempts."""
    limiter = RateLimiter(max_attempts=5, window_seconds=1, block_seconds=3600)
    
    # Record attempts
    limiter.record_attempt("test_key")
    
    # Wait for window to expire
    time.sleep(2)
    
    # Check if attempts were cleaned up
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited
    assert "test_key" not in limiter._attempts

def test_multiple_keys():
    """Test rate limiting with multiple keys."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Record attempts for different keys
    for _ in range(4):
        limiter.record_attempt("key1")
    
    for _ in range(2):
        limiter.record_attempt("key2")
    
    # Check rate limits
    is_limited_1, _ = limiter.is_rate_limited("key1")
    is_limited_2, _ = limiter.is_rate_limited("key2")
    
    assert is_limited_1  # key1 should be limited
    assert not is_limited_2  # key2 should not be limited

def test_block_expiration():
    """Test that blocks expire after the specified time."""
    # Use a very short block time for testing
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=1)
    
    # Record attempts to trigger blocking
    for _ in range(4):
        limiter.record_attempt("test_key")
    
    # Verify key is blocked
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert is_limited
    
    # Wait for block to expire
    time.sleep(1.5)
    
    # Verify key is no longer blocked
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited

def test_combined_keys():
    """Test using combined keys for more specific rate limiting."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Create combined keys (e.g., IP + username)
    key1 = "ip_127.0.0.1:user_john"
    key2 = "ip_127.0.0.1:user_jane"
    
    # Record attempts for different combined keys
    for _ in range(4):
        limiter.record_attempt(key1)
    
    for _ in range(2):
        limiter.record_attempt(key2)
    
    # Check rate limits
    is_limited_1, _ = limiter.is_rate_limited(key1)
    is_limited_2, _ = limiter.is_rate_limited(key2)
    
    assert is_limited_1  # key1 should be limited
    assert not is_limited_2  # key2 should not be limited
