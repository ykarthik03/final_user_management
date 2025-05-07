"""
Tests for rate limiting functionality.
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
    # Create a fresh limiter for this test with a small number of max attempts
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    test_key = "under_limit_test_key"
    
    # Record attempts but stay under the limit
    for i in range(4):
        is_blocked = limiter.record_attempt(test_key)
        assert not is_blocked, f"Should not be blocked after {i+1} attempts"
    
    # Verify not rate limited
    is_limited, _ = limiter.is_rate_limited(test_key)
    assert not is_limited, "Should not be rate limited under the maximum attempts"


def test_is_rate_limited_at_limit():
    """Test that is_rate_limited returns True when at the limit."""
    # Create a fresh limiter with exactly 3 max attempts
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    test_key = "at_limit_test_key"
    
    # Make attempts up to the limit
    for i in range(3):
        is_blocked = limiter.record_attempt(test_key)
        if i < 2:
            assert not is_blocked, f"Should not be blocked after {i+1} attempts"
        else:
            assert is_blocked, f"Should be blocked after {i+1} attempts (at limit)"
    
    # Verify rate limited
    try:
        is_limited, blocked_until = limiter.is_rate_limited(test_key)
        assert is_limited, "Should be rate limited at the maximum attempts"
        assert blocked_until is not None, "Block expiration time should be set"
    except KeyError:
        assert False, "KeyError should not occur"


def test_is_rate_limited_over_limit():
    """Test that is_rate_limited returns True when over the limit."""
    # Create a fresh limiter with a small number of max attempts
    limiter = RateLimiter(max_attempts=2, window_seconds=300, block_seconds=3600)
    test_key = "over_limit_test_key"
    
    # First attempt - should not be blocked
    is_blocked = limiter.record_attempt(test_key)
    assert not is_blocked, "First attempt should not trigger blocking"
    
    # Second attempt - should trigger blocking (at limit)
    is_blocked = limiter.record_attempt(test_key)
    assert is_blocked, "Second attempt should trigger blocking (at limit)"
    
    # Third attempt - should already be blocked
    is_blocked = limiter.record_attempt(test_key)
    assert is_blocked, "Third attempt should show as blocked (over limit)"
    
    # Verify rate limited status
    is_limited, blocked_until = limiter.is_rate_limited(test_key)
    assert is_limited, "Should be rate limited over the maximum attempts"
    assert blocked_until is not None, "Block expiration time should be set"


def test_reset_clears_attempts():
    """Test that reset clears all attempts for a key."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    test_key = "reset_test_key"
    
    # Make enough attempts to trigger rate limiting
    for _ in range(3):
        limiter.record_attempt(test_key)
    
    # Verify rate limited before reset
    is_limited_before, _ = limiter.is_rate_limited(test_key)
    assert is_limited_before, "Should be rate limited before reset"
    
    # Reset the key
    limiter.reset(test_key)
    
    # Verify not rate limited after reset
    is_limited_after, _ = limiter.is_rate_limited(test_key)
    assert not is_limited_after, "Should not be rate limited after reset"
    
    # Verify can make new attempts after reset
    is_blocked = limiter.record_attempt(test_key)
    assert not is_blocked, "Should be able to make new attempts after reset"


def test_cleanup_with_time_passage():
    """Test that old attempts are automatically cleaned up after time passes."""
    # Create a limiter with a very short window
    limiter = RateLimiter(max_attempts=5, window_seconds=2, block_seconds=10)
    test_key = "cleanup_test_key"
    
    # Record some attempts
    for _ in range(3):
        limiter.record_attempt(test_key)
    
    # Verify not rate limited yet
    is_limited_before, _ = limiter.is_rate_limited(test_key)
    assert not is_limited_before, "Should not be rate limited with only 3 attempts"
    
    # Wait for the window to expire
    import time
    time.sleep(3)  # Sleep longer than the window_seconds
    
    # Make more attempts - should start from 0 since old ones expired
    for i in range(3):
        is_blocked = limiter.record_attempt(test_key)
        assert not is_blocked, f"Should not be blocked after {i+1} new attempts"
    
    # Verify still not rate limited
    is_limited_after, _ = limiter.is_rate_limited(test_key)
    assert not is_limited_after, "Should not be rate limited after window expiration"


def test_block_expiration():
    """Test that blocks expire after the configured time."""
    # Create a limiter with a very short block time for testing
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=1)  # 1 second block
    test_key = "block_expiration_test_key"
    
    # Make enough attempts to trigger blocking
    for _ in range(3):
        limiter.record_attempt(test_key)
    
    # Verify blocked
    is_limited_before, blocked_until = limiter.is_rate_limited(test_key)
    assert is_limited_before, "Should be rate limited immediately after max attempts"
    
    # Wait for the block to expire
    import time
    time.sleep(1.5)  # Sleep longer than block_seconds
    
    # Check that the block has expired
    is_limited_after, _ = limiter.is_rate_limited(test_key)
    assert not is_limited_after, "Should not be rate limited after block expires"


def test_different_keys_separate_limits():
    """Test that different keys have separate rate limits."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    key1 = "separate_limits_key1"
    key2 = "separate_limits_key2"
    
    # Exceed limit for key1
    for _ in range(3):
        limiter.record_attempt(key1)
    
    # Make some attempts for key2 but stay under limit
    for _ in range(2):
        limiter.record_attempt(key2)
    
    # Verify key1 is limited but key2 is not
    is_limited_1, _ = limiter.is_rate_limited(key1)
    is_limited_2, _ = limiter.is_rate_limited(key2)
    
    assert is_limited_1, "Key1 should be rate limited after max attempts"
    assert not is_limited_2, "Key2 should not be rate limited"


def test_gradual_attempt_counting():
    """Test that attempts are correctly counted as they're added."""
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    test_key = "counting_test_key"
    
    # Make attempts one by one and verify behavior
    for i in range(1, 6):
        # Record attempt
        is_blocked = limiter.record_attempt(test_key)
        
        # Check if should be blocked based on attempt count
        if i < 5:
            assert not is_blocked, f"Should not be blocked after {i} attempts"
        else:
            assert is_blocked, f"Should be blocked after {i} attempts"


def test_rate_limiter_with_ip_and_username():
    """Test rate limiting with combined IP and username keys."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Create rate limiting keys that combine IP and username
    key1 = "ip_127.0.0.1:user_test@example.com"
    key2 = "ip_192.168.1.1:user_test@example.com"  # Same user, different IP
    key3 = "ip_127.0.0.1:user_other@example.com"  # Same IP, different user
    
    # Exceed limit for key1
    for _ in range(3):
        limiter.record_attempt(key1)
    
    # Make some attempts for key2 and key3 but stay under limit
    for _ in range(2):
        limiter.record_attempt(key2)
        limiter.record_attempt(key3)
    
    # Verify key1 is limited but key2 and key3 are not
    is_limited_1, _ = limiter.is_rate_limited(key1)
    is_limited_2, _ = limiter.is_rate_limited(key2)
    is_limited_3, _ = limiter.is_rate_limited(key3)
    
    assert is_limited_1, "Key1 should be rate limited"
    assert not is_limited_2, "Key2 should not be rate limited"
    assert not is_limited_3, "Key3 should not be rate limited"


def test_rate_limiter_login_flow():
    """Test the complete login flow with rate limiting."""
    limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    login_key = "login_flow_test_key"
    
    # First check if rate limited (should not be initially)
    is_limited, _ = limiter.is_rate_limited(login_key)
    assert not is_limited, "New key should not be rate limited initially"
    
    # Record failed login attempts
    for i in range(3):
        is_blocked = limiter.record_attempt(login_key)
        
        # Check expected behavior based on attempt count
        if i < 2:
            assert not is_blocked, f"Should not be blocked after {i+1} attempts"
        else:
            assert is_blocked, f"Should be blocked after {i+1} attempts"
    
    # Verify rate limited after max attempts
    is_limited, blocked_until = limiter.is_rate_limited(login_key)
    assert is_limited, "Should be rate limited after max attempts"
    assert blocked_until is not None, "Block expiration time should be set"
    
    # Simulate successful login by resetting
    limiter.reset(login_key)
    
    # Verify no longer rate limited after reset
    is_limited, _ = limiter.is_rate_limited(login_key)
    assert not is_limited, "Should not be rate limited after reset"
    
    # Verify can make new attempts after reset
    is_blocked = limiter.record_attempt(login_key)
    assert not is_blocked, "Should be able to make new attempts after reset"
