"""
Tests for rate limiting functionality.
"""
import pytest
import time
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
    
    # Reset the attempts dictionary to start fresh
    limiter._attempts = {}
    
    # Add some attempts with specific timestamps
    now = datetime.now()
    
    # Manually add attempts to the dictionary with timestamps
    limiter._attempts["test_key"] = {}
    
    # Add an old attempt (outside the window)
    old_time = now - timedelta(seconds=400)  # Older than window
    limiter._attempts["test_key"][old_time] = 1
    
    # Add two recent attempts (within window)
    recent_time1 = now - timedelta(seconds=200)  # Within window
    recent_time2 = now - timedelta(seconds=100)  # Within window
    limiter._attempts["test_key"][recent_time1] = 1
    limiter._attempts["test_key"][recent_time2] = 1
    
    # Clean up old attempts
    limiter._cleanup("test_key", now)
    
    # Check that only recent attempts remain
    assert len(limiter._attempts["test_key"]) == 2  # Only the two recent ones should remain


def test_block_expiration():
    """Test that blocks expire after the configured time."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=10)  # Short block time
    
    # Reset the limiter's state
    limiter._attempts = {}
    limiter._blocked_until = {}
    
    # Set up a blocked key that's about to expire
    now = datetime.now()
    
    # Manually set up the blocked state
    limiter._attempts["test_key"] = {now: 6}  # More than max_attempts
    
    # First test that it's blocked
    limiter._blocked_until["test_key"] = now + timedelta(seconds=5)  # Blocked for 5 more seconds
    is_limited, _ = limiter.is_rate_limited("test_key")
    assert is_limited, "Key should be rate limited when block is active"
    
    # Now test with expired block
    # Create a future time after the block expires
    future_time = now + timedelta(seconds=15)  # 15 seconds later, after the 10-second block
    
    # Test with mocked time
    with patch('app.utils.rate_limiter.datetime') as mock_datetime:
        mock_datetime.now.return_value = future_time
        is_limited, _ = limiter.is_rate_limited("test_key")
        assert not is_limited, "Key should not be rate limited after block expires"


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
    
    # Reset the attempts dictionary to start fresh
    limiter._attempts = {}
    
    # Add some attempts with specific timestamps
    now = datetime.now()
    
    # Manually add attempts to the dictionary with timestamps
    limiter._attempts["test_key"] = {}
    
    # Add an old attempt (outside the window)
    old_time = now - timedelta(seconds=400)  # Older than window
    limiter._attempts["test_key"][old_time] = 1
    
    # Add three recent attempts (within window)
    recent_time1 = now - timedelta(seconds=200)  # Within window
    recent_time2 = now - timedelta(seconds=100)  # Within window
    recent_time3 = now - timedelta(seconds=50)   # Within window
    limiter._attempts["test_key"][recent_time1] = 1
    limiter._attempts["test_key"][recent_time2] = 1
    limiter._attempts["test_key"][recent_time3] = 1
    
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


def test_mixed_timestamp_formats():
    """Test that the rate limiter correctly handles mixed timestamp formats.
    This test verifies handling of different timestamp formats including datetime objects and string timestamps.
    """
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Reset the attempts dictionary to start fresh
    limiter._attempts = {}
    
    # Add some attempts with specific timestamps
    now = datetime.now()
    test_key = "mixed_timestamp_test"
    
    # Manually add attempts to the dictionary with different timestamp formats
    limiter._attempts[test_key] = {}
    
    # Add an old attempt (outside the window) as a datetime object
    old_time = now - timedelta(seconds=400)  # Older than window
    limiter._attempts[test_key][old_time] = 1
    
    # Add a recent attempt (within window) as a datetime object
    recent_time = now - timedelta(seconds=100)  # Within window
    limiter._attempts[test_key][recent_time] = 1
    
    # Add a recent attempt as a string timestamp (integer)
    recent_timestamp_str = str(int(time.time() - 50))  # Within window
    limiter._attempts[test_key][recent_timestamp_str] = 1
    
    # Add a recent attempt as a string timestamp (float)
    recent_timestamp_float_str = str(time.time() - 150)  # Within window
    limiter._attempts[test_key][recent_timestamp_float_str] = 1
    
    # Add an invalid timestamp string that should be handled gracefully
    limiter._attempts[test_key]["invalid_timestamp"] = 1
    
    # Count recent attempts
    count = limiter._count_recent_attempts(test_key, now)
    
    # Should count the 3 recent attempts (1 datetime, 2 valid string timestamps)
    # plus the invalid timestamp (which is counted as recent for safety)
    assert count == 4
    
    # Test cleanup
    limiter._cleanup(test_key, now)
    
    # After cleanup, we should have only the recent attempts
    # The old datetime attempt should be removed
    assert len(limiter._attempts[test_key]) == 4
