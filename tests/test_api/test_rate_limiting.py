"""
Tests for rate limiting functionality in the API.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.utils.rate_limiter import RateLimiter

client = TestClient(app)

def test_login_rate_limiting():
    """Test that login attempts are rate limited."""
    # Create a mock rate limiter that will block after 3 attempts
    mock_limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Test user credentials
    login_data = {
        "username": "test@example.com",
        "password": "wrongpassword"
    }
    
    # Patch the login_rate_limiter in the user service
    with patch('app.services.user_service.login_rate_limiter', mock_limiter):
        # Make 3 failed login attempts (these should be allowed)
        for _ in range(3):
            response = client.post("/api/users/login", data=login_data)
            assert response.status_code in [401, 422]  # Either unauthorized or validation error
        
        # The 4th attempt should be rate limited
        response = client.post("/api/users/login", data=login_data)
        assert response.status_code == 429
        assert "Too many login attempts" in response.text
        assert "Retry-After" in response.headers

def test_ip_specific_rate_limiting():
    """Test that rate limiting is specific to IP addresses."""
    # Create a mock rate limiter
    mock_limiter = RateLimiter(max_attempts=3, window_seconds=300, block_seconds=3600)
    
    # Test user credentials
    login_data = {
        "username": "test@example.com",
        "password": "wrongpassword"
    }
    
    # Patch the login_rate_limiter and the client IP detection
    with patch('app.services.user_service.login_rate_limiter', mock_limiter):
        # Make 3 failed login attempts from IP 1
        for _ in range(3):
            with patch('app.routers.user_routes.request.client.host', return_value="192.168.1.1"):
                response = client.post("/api/users/login", data=login_data)
                assert response.status_code in [401, 422]
        
        # The 4th attempt from IP 1 should be rate limited
        with patch('app.routers.user_routes.request.client.host', return_value="192.168.1.1"):
            response = client.post("/api/users/login", data=login_data)
            assert response.status_code == 429
        
        # But attempts from IP 2 should still be allowed
        with patch('app.routers.user_routes.request.client.host', return_value="192.168.1.2"):
            response = client.post("/api/users/login", data=login_data)
            assert response.status_code in [401, 422]

def test_successful_login_resets_rate_limit():
    """Test that a successful login resets the rate limit."""
    # Create a mock rate limiter
    mock_limiter = RateLimiter(max_attempts=5, window_seconds=300, block_seconds=3600)
    
    # Mock the authenticate_user method to return a valid user after 2 failed attempts
    mock_user = MagicMock()
    mock_user.id = "test-id"
    mock_user.role.value = "AUTHENTICATED"
    
    # Patch dependencies
    with patch('app.services.user_service.login_rate_limiter', mock_limiter), \
         patch('app.services.user_service.UserService.authenticate_user', side_effect=[
             # First 2 calls raise 401
             pytest.raises(Exception("Invalid credentials")),
             pytest.raises(Exception("Invalid credentials")),
             # Third call succeeds
             mock_user
         ]):
        
        login_data = {
            "username": "test@example.com",
            "password": "password"
        }
        
        # Make 2 failed login attempts
        for _ in range(2):
            response = client.post("/api/users/login", data=login_data)
            assert response.status_code in [401, 422]
        
        # The 3rd attempt should succeed and reset the rate limit
        response = client.post("/api/users/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Verify the rate limiter was reset by checking we can make more attempts
        for _ in range(3):  # Should be able to make 3 more attempts
            response = client.post("/api/users/login", data=login_data)
            assert response.status_code != 429  # Not rate limited

def test_rate_limit_expiration():
    """Test that rate limits expire after the configured time."""
    # Create a mock rate limiter with a very short block time
    mock_limiter = RateLimiter(max_attempts=3, window_seconds=1, block_seconds=2)
    
    login_data = {
        "username": "test@example.com",
        "password": "wrongpassword"
    }
    
    # Patch the login_rate_limiter
    with patch('app.services.user_service.login_rate_limiter', mock_limiter):
        # Make enough failed login attempts to trigger rate limiting
        for _ in range(4):
            response = client.post("/api/users/login", data=login_data)
        
        # Verify we're rate limited
        assert response.status_code == 429
        
        # Wait for the rate limit to expire
        import time
        time.sleep(3)  # Wait longer than block_seconds
        
        # Try again, should be allowed
        response = client.post("/api/users/login", data=login_data)
        assert response.status_code != 429
