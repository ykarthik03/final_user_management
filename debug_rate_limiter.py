"""
Debug script for rate limiter.
"""
from datetime import datetime, timedelta
import time

from app.utils.rate_limiter import RateLimiter

def test_mixed_timestamp_formats():
    """Test that the rate limiter correctly handles mixed timestamp formats."""
    print("Starting mixed timestamp formats test...")
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
    print(f"Added old datetime attempt: {old_time}")
    
    # Add a recent attempt (within window) as a datetime object
    recent_time = now - timedelta(seconds=100)  # Within window
    limiter._attempts[test_key][recent_time] = 1
    print(f"Added recent datetime attempt: {recent_time}")
    
    # Add a recent attempt as a string timestamp (integer)
    recent_timestamp_str = str(int(time.time() - 50))  # Within window
    limiter._attempts[test_key][recent_timestamp_str] = 1
    print(f"Added recent string timestamp (int): {recent_timestamp_str}")
    
    # Add a recent attempt as a string timestamp (float)
    recent_timestamp_float_str = str(time.time() - 150)  # Within window
    limiter._attempts[test_key][recent_timestamp_float_str] = 1
    print(f"Added recent string timestamp (float): {recent_timestamp_float_str}")
    
    # Add an invalid timestamp string that should be handled gracefully
    limiter._attempts[test_key]["invalid_timestamp"] = 1
    print("Added invalid timestamp string: 'invalid_timestamp'")
    
    # Print the attempts dictionary
    print(f"\nAttempts dictionary: {limiter._attempts[test_key]}")
    
    # Count recent attempts
    count = limiter._count_recent_attempts(test_key, now)
    print(f"\nCounted recent attempts: {count}")
    
    # Test cleanup
    print("\nRunning cleanup...")
    limiter._cleanup(test_key, now)
    
    # After cleanup, we should have only the recent attempts
    print(f"After cleanup, attempts dictionary: {limiter._attempts[test_key]}")
    print(f"Number of attempts after cleanup: {len(limiter._attempts[test_key])}")

if __name__ == "__main__":
    test_mixed_timestamp_formats()
