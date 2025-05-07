"""
Tests for profile management API endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi import HTTPException, status
from app.models.user_model import User, UserRole
from app.services.jwt_service import decode_token
from app.services.user_service import UserService
from uuid import UUID

@pytest.mark.asyncio
async def test_update_profile_authenticated_user(async_client, verified_user, admin_token):
    """Test that an admin can update a user's profile."""
    # Prepare update data
    update_data = {
        "first_name": "Updated",
        "last_name": "User",
        "bio": "This is my updated bio"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be successful for admin
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]

@pytest.mark.asyncio
async def test_update_profile_picture_url_as_admin(async_client, verified_user, admin_token):
    """Test updating profile picture URL as admin."""
    # Prepare update data
    update_data = {
        "profile_picture_url": "https://example.com/new-profile-pic.jpg"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be successful for admin
    assert response.status_code == 200
    assert response.json()["profile_picture_url"] == update_data["profile_picture_url"]

@pytest.mark.asyncio
async def test_update_github_profile_url_as_admin(async_client, verified_user, admin_token):
    """Test updating GitHub profile URL as admin."""
    # Prepare update data
    update_data = {
        "github_profile_url": "https://github.com/updated-username"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be successful for admin
    assert response.status_code == 200
    assert response.json()["github_profile_url"] == update_data["github_profile_url"]

@pytest.mark.asyncio
async def test_update_linkedin_profile_url_as_admin(async_client, verified_user, admin_token):
    """Test updating LinkedIn profile URL as admin."""
    # Prepare update data
    update_data = {
        "linkedin_profile_url": "https://linkedin.com/in/updated-username"
    }
    
    # Set proper authorization header
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Update profile
    response = await async_client.put(
        f"/users/{verified_user.id}",
        json=update_data,
        headers=headers
    )
    
    # Check response - should be successful for admin
    assert response.status_code == 200
    assert response.json()["linkedin_profile_url"] == update_data["linkedin_profile_url"]

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

async def test_login_user_incorrect_email(db_session):
    exception_caught = False
    actual_exception = None
    try:
        await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    except HTTPException as e:
        exception_caught = True
        actual_exception = e
        print(f"\nDEBUG - CAUGHT EXCEPTION:\nStatus: {e.status_code}\nDetail: {e.detail}\nHeaders: {e.headers}\n")  # Added debug output
    except Exception as e:
        print(f"\nDEBUG - UNEXPECTED ERROR:\n{str(e)}\n{type(e)}\n")  # Catch any non-HTTPException errors
        raise
    
    assert exception_caught, "HTTPException was not raised"
    assert actual_exception.status_code == status.HTTP_401_UNAUTHORIZED
