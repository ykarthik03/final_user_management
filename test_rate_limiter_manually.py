"""
Simple script to test the rate limiter functionality directly without pytest.
"""
from datetime import datetime, timedelta
import time
from app.utils.rate_limiter import RateLimiter

def run_tests():
    print("Testing Rate Limiter functionality...")
    
    # Test initialization
    limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    print(f"Initialized with max_attempts={limiter.max_attempts}, window_seconds={limiter.window_seconds}, block_seconds={limiter.block_seconds}")
    
    # Test under limit
    print("\nTesting under limit...")
    for i in range(4):
        limiter.record_attempt("test_key")
        print(f"Recorded attempt {i+1}")
    
    is_limited, _ = limiter.is_rate_limited("test_key")
    print(f"Is rate limited after 4 attempts: {is_limited} (Expected: False)")
    
    # Test at limit
    print("\nTesting at limit...")
    limiter.record_attempt("test_key")
    print("Recorded 5th attempt")
    
    is_limited, blocked_until = limiter.is_rate_limited("test_key")
    print(f"Is rate limited after 5 attempts: {is_limited} (Expected: True)")
    print(f"Blocked until: {blocked_until}")
    
    # Test reset
    print("\nTesting reset...")
    limiter.reset("test_key")
    print("Reset key")
    
    is_limited, _ = limiter.is_rate_limited("test_key")
    print(f"Is rate limited after reset: {is_limited} (Expected: False)")
    
    # Test different keys
    print("\nTesting different keys...")
    for i in range(6):
        limiter.record_attempt("key1")
    print("Recorded 6 attempts for key1")
    
    for i in range(3):
        limiter.record_attempt("key2")
    print("Recorded 3 attempts for key2")
    
    is_limited_1, _ = limiter.is_rate_limited("key1")
    is_limited_2, _ = limiter.is_rate_limited("key2")
    
    print(f"Is key1 rate limited: {is_limited_1} (Expected: True)")
    print(f"Is key2 rate limited: {is_limited_2} (Expected: False)")
    
    # Test IP and username combinations
    print("\nTesting IP and username combinations...")
    key1 = "ip_127.0.0.1:user_test@example.com"
    key2 = "ip_192.168.1.1:user_test@example.com"  # Same user, different IP
    key3 = "ip_127.0.0.1:user_other@example.com"  # Same IP, different user
    
    for i in range(6):
        limiter.record_attempt(key1)
    print("Recorded 6 attempts for IP1+User1")
    
    for i in range(3):
        limiter.record_attempt(key2)
        limiter.record_attempt(key3)
    print("Recorded 3 attempts each for IP2+User1 and IP1+User2")
    
    is_limited_1, _ = limiter.is_rate_limited(key1)
    is_limited_2, _ = limiter.is_rate_limited(key2)
    is_limited_3, _ = limiter.is_rate_limited(key3)
    
    print(f"Is IP1+User1 rate limited: {is_limited_1} (Expected: True)")
    print(f"Is IP2+User1 rate limited: {is_limited_2} (Expected: False)")
    print(f"Is IP1+User2 rate limited: {is_limited_3} (Expected: False)")
    
    # Test block expiration
    print("\nTesting block expiration...")
    # Use a very short block time for testing
    short_limiter = RateLimiter(max_attempts=3, window_seconds=1, block_seconds=2)
    
    for i in range(4):
        short_limiter.record_attempt("expire_test")
    print("Recorded 4 attempts for expire_test")
    
    is_limited, blocked_until = short_limiter.is_rate_limited("expire_test")
    print(f"Is rate limited initially: {is_limited} (Expected: True)")
    print(f"Blocked until: {blocked_until}")
    
    print("Waiting for block to expire (3 seconds)...")
    time.sleep(3)
    
    is_limited, _ = short_limiter.is_rate_limited("expire_test")
    print(f"Is rate limited after waiting: {is_limited} (Expected: False)")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_tests()
