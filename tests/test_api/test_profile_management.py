import pytest
from fastapi import status
import uuid
from unittest.mock import patch, MagicMock
from app.models.user_model import User, UserRole
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

# Test data
test_profile_data = {
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Test bio for profile management",
    "profile_picture_url": "https://example.com/profile.jpg",
    "linkedin_profile_url": "https://linkedin.com/in/johndoe",
    "github_profile_url": "https://github.com/johndoe"
}

test_professional_status = {
    "is_professional": True
}

# Use existing fixtures from conftest.py
pytestmark = pytest.mark.asyncio

# Create a mock for the notification service
@pytest.fixture
def mock_notification_service():
    with patch.object(NotificationService, 'send_professional_status_notification', return_value=True) as mock:
        yield mock

async def test_get_user_profile(async_client, verified_user, verified_user_token):
    """Test getting a user's own profile."""
    # Verify token first
    from app.dependencies import decode_token
    token_data = decode_token(verified_user_token)
    assert str(verified_user.id) == token_data["sub"]
    
    response = await async_client.get(
        f"/users/{verified_user.id}/profile",
        headers={"Authorization": f"Bearer {verified_user_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["email"] == verified_user.email
    assert data["id"] == str(verified_user.id)

async def test_update_user_profile(async_client, verified_user, verified_user_token):
    """Test updating a user's own profile."""
    # Verify token first
    from app.dependencies import decode_token
    token_data = decode_token(verified_user_token)
    assert str(verified_user.id) == token_data["sub"]
    
    update_data = {"first_name": "Updated", "last_name": "Name"}
    response = await async_client.put(
        f"/users/{verified_user.id}/profile",
        json=update_data,
        headers={"Authorization": f"Bearer {verified_user_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["updated_fields"]["first_name"] == "Updated"
    assert data["updated_fields"]["last_name"] == "Name"

async def test_update_other_user_profile_forbidden(async_client, verified_user, admin_user, user_token):
    """Test that a user cannot update another user's profile."""
    response = await async_client.put(
        f"/users/{admin_user.id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_admin_update_other_user_profile(async_client, verified_user, admin_token):
    """Test that an admin can update another user's profile."""
    response = await async_client.put(
        f"/users/{verified_user.id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Profile updated successfully"
    assert data["user_id"] == str(verified_user.id)

async def test_update_professional_status(async_client, verified_user, admin_token, mock_notification_service):
    """Test updating a user's professional status as admin."""
    response = await async_client.put(
        f"/users/{verified_user.id}/professional-status",
        json=test_professional_status,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Professional status updated successfully"
    assert data["user_id"] == str(verified_user.id)
    assert data["notification_sent"] == True
    
    # Verify professional status was updated
    profile_response = await async_client.get(
        f"/users/{verified_user.id}/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    profile_data = profile_response.json()
    
    assert profile_data["is_professional"] == test_professional_status["is_professional"]

async def test_user_cannot_update_professional_status(async_client, verified_user, user_token):
    """Test that a regular user cannot update professional status."""
    response = await async_client.put(
        f"/users/{verified_user.id}/professional-status",
        json=test_professional_status,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_get_nonexistent_profile(async_client, admin_token):
    """Test getting a profile that doesn't exist."""
    nonexistent_id = str(uuid.uuid4())
    response = await async_client.get(
        f"/users/{nonexistent_id}/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_update_nonexistent_profile(async_client, admin_token):
    """Test updating a profile that doesn't exist."""
    nonexistent_id = str(uuid.uuid4())
    response = await async_client.put(
        f"/users/{nonexistent_id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_professional_status_notification_failure(async_client, verified_user, admin_token):
    """Test handling of notification failure when updating professional status."""
    with patch.object(NotificationService, 'send_professional_status_notification', return_value=False):
        response = await async_client.put(
            f"/users/{verified_user.id}/professional-status",
            json=test_professional_status,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Professional status updated successfully"
        assert data["notification_sent"] == False
