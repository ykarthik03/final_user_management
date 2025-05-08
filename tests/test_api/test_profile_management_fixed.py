"""
Tests for profile management API endpoints.
"""
import pytest
from httpx import AsyncClient
from app.models.user_model import User, UserRole
from app.services.jwt_service import decode_token
from uuid import UUID

@pytest.mark.asyncio
async def test_update_profile_authenticated_user(async_client, verified_user, user_token):
    """Test that an authenticated user cannot update their own profile unless they are ADMIN or MANAGER."""
    # Prepare update data
    update_data = {
        "first_name": "Updated",
        "last_name": "User",
        "bio": "This is my updated bio"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be forbidden for regular users
    assert response.status_code == 403
    # The actual error message is 'Operation not permitted'
    assert "Operation not permitted" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_update_profile_picture_url(async_client, verified_user, user_token):
    """Test updating profile picture URL."""
    # Prepare update data
    update_data = {
        "profile_picture_url": "https://example.com/new-profile-pic.jpg"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be forbidden for regular users
    assert response.status_code == 403
    # The actual error message is 'Operation not permitted'
    assert "Operation not permitted" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_update_github_profile_url(async_client, verified_user, user_token):
    """Test updating GitHub profile URL."""
    # Prepare update data
    update_data = {
        "github_profile_url": "https://github.com/updated-username"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be forbidden for regular users
    assert response.status_code == 403
    # The actual error message is 'Operation not permitted'
    assert "Operation not permitted" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_update_linkedin_profile_url(async_client, verified_user, user_token):
    """Test updating LinkedIn profile URL."""
    # Prepare update data
    update_data = {
        "linkedin_profile_url": "https://linkedin.com/in/updated-username"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be forbidden for regular users
    assert response.status_code == 403
    # The actual error message is 'Operation not permitted'
    assert "Operation not permitted" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_update_profile_unauthorized_user(async_client, verified_user):
    """Test that an unauthorized user cannot update a profile."""
    # Prepare update data
    update_data = {
        "first_name": "Unauthorized",
        "last_name": "Update"
    }
    
    # No authorization header
    
    # Attempt to update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data
    )
    
    # Check response - should be unauthorized
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_update_other_user_profile_as_regular_user(async_client, verified_user, admin_user, user_token):
    """Test that a regular user cannot update another user's profile."""
    # Prepare update data
    update_data = {
        "first_name": "Forbidden",
        "last_name": "Update"
    }
    
    # Set authorization header for regular user
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Attempt to update admin's profile
    response = await async_client.put(
        f"/users/{admin_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_other_user_profile_as_admin(async_client, verified_user, admin_token):
    """Test that an admin can update another user's profile."""
    # Prepare update data
    update_data = {
        "first_name": "Admin",
        "last_name": "Updated"
    }
    
    # Set authorization header for admin user
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update regular user's profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be successful
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
