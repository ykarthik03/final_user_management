"""
Unit tests for rate limiting functionality without database dependencies.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.utils.rate_limiter import RateLimiter


def test_rate_limiter_initialization():
    """Test that the rate limiter initializes with correct values."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    assert limiter.max_attempts == 5
    assert limiter.window_seconds == 300
    assert limiter.block_seconds == 3600


def test_is_rate_limited_under_limit():
    """Test that is_rate_limited returns False when under the limit."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Make fewer attempts than the limit
    for _ in range(4):
        limiter.record_attempt("test_key")
    
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited


def test_is_rate_limited_at_limit():
    """Test that is_rate_limited returns True when at the limit."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Make exactly the maximum number of attempts
    for _ in range(5):
        limiter.record_attempt("test_key")
    
    is_limited, blocked_until = limiter.is_rate_limited("test_key")
    assert is_limited
    assert blocked_until > datetime.now()


def test_is_rate_limited_over_limit():
    """Test that is_rate_limited returns True when over the limit."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Make more than the maximum number of attempts
    for _ in range(6):
        limiter.record_attempt("test_key")
    
    is_limited, blocked_until = limiter.is_rate_limited("test_key")
    assert is_limited
    assert blocked_until > datetime.now()


def test_reset_clears_attempts():
    """Test that reset clears all attempts for a key."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Make some attempts
    for _ in range(3):
        limiter.record_attempt("test_key")
    
    # Reset the key
    limiter.reset("test_key")
    
    # Check that the key is no longer rate limited
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert not is_limited
    
    # Check that the attempts were cleared
    assert limiter._count_recent_attempts("test_key", datetime.now()) == 0


def test_cleanup_removes_old_attempts():
    """Test that _cleanup removes old attempts."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Add some attempts
    now = datetime.now()
    
    with patch('app.utils.rate_limiter.datetime') as mock_datetime:
        # Old attempt (outside window)
        mock_datetime.now.return_value = now - timedelta(seconds=400)
        limiter.record_attempt("test_key")
        
        # Recent attempts (within window)
        mock_datetime.now.return_value = now - timedelta(seconds=200)
        limiter.record_attempt("test_key")
        
        mock_datetime.now.return_value = now
        limiter.record_attempt("test_key")
    
    # Clean up old attempts
    limiter._cleanup("test_key", now)
    
    # Check that only recent attempts remain
    assert limiter._count_recent_attempts("test_key", now) == 2  # Only the two recent ones


def test_block_expiration():
    """Test that blocks expire after the configured time."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=10)  # Short block time
    
    # Exceed the limit
    for _ in range(6):
        limiter.record_attempt("test_key")
    
    # Verify blocked
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert is_limited
    
    # Check after block expires
    with patch('app.utils.rate_limiter.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime.now() + timedelta(seconds=11)  # After block time
        is_limited, _ = limiter.is_rate_limited("test_key")
        assert not is_limited


def test_different_keys_separate_limits():
    """Test that different keys have separate rate limits."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Exceed limit for key1
    for _ in range(6):
        limiter.record_attempt("key1")
    
    # Make some attempts for key2
    for _ in range(3):
        limiter.record_attempt("key2")
    
    # Check that key1 is limited but key2 is not
    is_limited_1, _ = limiter.is_rate_limited("key1")
    is_limited_2, _ = limiter.is_rate_limited("key2")
    
    assert is_limited_1
    assert not is_limited_2


def test_count_recent_attempts():
    """Test that _count_recent_attempts correctly counts attempts within the window."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Add some attempts at different times
    now = datetime.now()
    
    with patch('app.utils.rate_limiter.datetime') as mock_datetime:
        # Old attempt (outside window)
        mock_datetime.now.return_value = now - timedelta(seconds=400)
        limiter.record_attempt("test_key")
        
        # Recent attempts (within window)
        mock_datetime.now.return_value = now - timedelta(seconds=200)
        limiter.record_attempt("test_key")
        
        mock_datetime.now.return_value = now - timedelta(seconds=100)
        limiter.record_attempt("test_key")
        
        mock_datetime.now.return_value = now
        limiter.record_attempt("test_key")
    
    # Count recent attempts
    count = limiter._count_recent_attempts("test_key", now)
    
    # Should only count the 3 recent attempts, not the old one
    assert count == 3


def test_rate_limiter_with_ip_and_username():
    """Test rate limiting with combined IP and username keys."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Create rate limiting keys that combine IP and username
    key1 = f"ip_127.0.0.1:user_test@example.com"
    key2 = f"ip_192.168.1.1:user_test@example.com"  # Same user, different IP
    key3 = f"ip_127.0.0.1:user_other@example.com"  # Same IP, different user
    
    # Exceed limit for key1
    for _ in range(6):
        limiter.record_attempt(key1)
    
    # Make some attempts for key2 and key3
    for _ in range(3):
        limiter.record_attempt(key2)
        limiter.record_attempt(key3)
    
    # Check that key1 is limited but key2 and key3 are not
    is_limited_1, _ = limiter.is_rate_limited(key1)
    is_limited_2, _ = limiter.is_rate_limited(key2)
    is_limited_3, _ = limiter.is_rate_limited(key3)
    
    assert is_limited_1  # key1 should be limited
    assert not is_limited_2  # key2 should not be limited
    assert not is_limited_3  # key3 should not be limited


def test_rate_limiter_login_flow():
    """Test the complete login flow with rate limiting."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Simulate login flow for a specific user and IP
    key = "ip_127.0.0.1:user_test@example.com"
    
    # First check if rate limited (should not be initially)
    is_limited, _ = limiter.is_rate_limited(key)
    assert not is_limited
    
    # Record failed login attempts
    for i in range(3):
        limiter.record_attempt(key)
        is_limited, _ = limiter.is_rate_limited(key)
        if i < 2:  # First two attempts should not be limited
            assert not is_limited
    
    # After 3 attempts, should be rate limited
    is_limited, blocked_until = limiter.is_rate_limited(key)
    assert is_limited
    assert blocked_until > datetime.now()
    
    # Simulate successful login by resetting
    limiter.reset(key)
    
    # Should no longer be rate limited
    is_limited, _ = limiter.is_rate_limited(key)
    assert not is_limited
