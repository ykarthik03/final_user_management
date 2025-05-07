import pytest
from fastapi import status
from httpx import AsyncClient
import uuid
from unittest.mock import patch, MagicMock
from app.models.user_model import User, UserRole
from app.services.notification_service import NotificationService

# Test data
test_user_data = {
    "email": "test_profile@example.com",
    "password": "TestPassword123!",
    "role": UserRole.AUTHENTICATED
}

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

@pytest.fixture
async def test_user(client, db_session):
    """Create a test user for profile management tests."""
    from app.services.user_service import UserService
    from app.utils.security import hash_password
    
    # Create a user directly in the database
    user = User(
        email=test_user_data["email"],
        hashed_password=hash_password(test_user_data["password"]),
        nickname="test_profile_user",
        role=UserRole.AUTHENTICATED,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest.fixture
async def admin_user(client, db_session):
    """Create an admin user for testing."""
    from app.services.user_service import UserService
    from app.utils.security import hash_password
    
    # Create an admin user directly in the database
    user = User(
        email="admin_profile@example.com",
        hashed_password=hash_password(test_user_data["password"]),
        nickname="admin_profile_user",
        role=UserRole.ADMIN,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest.fixture
async def user_token(client, test_user):
    """Get a token for the test user."""
    response = await client.post(
        "/login",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    return response.json()["access_token"]

@pytest.fixture
async def admin_token(client, admin_user):
    """Get a token for the admin user."""
    response = await client.post(
        "/login",
        data={"username": "admin_profile@example.com", "password": test_user_data["password"]}
    )
    return response.json()["access_token"]

async def test_get_user_profile(client, test_user, user_token):
    """Test getting a user's own profile."""
    response = await client.get(
        f"/users/{test_user.id}/profile",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["id"] == str(test_user.id)

async def test_update_user_profile(client, test_user, user_token):
    """Test updating a user's own profile."""
    response = await client.put(
        f"/users/{test_user.id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Profile updated successfully"
    assert data["user_id"] == str(test_user.id)
    
    # Verify profile was updated
    profile_response = await client.get(
        f"/users/{test_user.id}/profile",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    profile_data = profile_response.json()
    
    assert profile_data["first_name"] == test_profile_data["first_name"]
    assert profile_data["last_name"] == test_profile_data["last_name"]
    assert profile_data["bio"] == test_profile_data["bio"]
    assert profile_data["profile_picture_url"] == test_profile_data["profile_picture_url"]
    assert profile_data["linkedin_profile_url"] == test_profile_data["linkedin_profile_url"]
    assert profile_data["github_profile_url"] == test_profile_data["github_profile_url"]

async def test_update_other_user_profile_forbidden(client, test_user, admin_user, user_token):
    """Test that a user cannot update another user's profile."""
    response = await client.put(
        f"/users/{admin_user.id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_admin_update_other_user_profile(client, test_user, admin_token):
    """Test that an admin can update another user's profile."""
    response = await client.put(
        f"/users/{test_user.id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Profile updated successfully"
    assert data["user_id"] == str(test_user.id)

@patch.object(NotificationService, 'send_professional_status_notification', return_value=True)
async def test_update_professional_status(mock_notification, client, test_user, admin_token):
    """Test updating a user's professional status as admin."""
    response = await client.put(
        f"/users/{test_user.id}/professional-status",
        json=test_professional_status,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Professional status updated successfully"
    assert data["user_id"] == str(test_user.id)
    assert data["notification_sent"] == True
    
    # Verify professional status was updated
    profile_response = await client.get(
        f"/users/{test_user.id}/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    profile_data = profile_response.json()
    
    assert profile_data["is_professional"] == test_professional_status["is_professional"]

async def test_user_cannot_update_professional_status(client, test_user, user_token):
    """Test that a regular user cannot update professional status."""
    response = await client.put(
        f"/users/{test_user.id}/professional-status",
        json=test_professional_status,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_get_nonexistent_profile(client, admin_token):
    """Test getting a profile that doesn't exist."""
    nonexistent_id = str(uuid.uuid4())
    response = await client.get(
        f"/users/{nonexistent_id}/profile",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_update_nonexistent_profile(client, admin_token):
    """Test updating a profile that doesn't exist."""
    nonexistent_id = str(uuid.uuid4())
    response = await client.put(
        f"/users/{nonexistent_id}/profile",
        json=test_profile_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@patch.object(NotificationService, 'send_professional_status_notification', return_value=False)
async def test_professional_status_notification_failure(mock_notification, client, test_user, admin_token):
    """Test handling of notification failure when updating professional status."""
    response = await client.put(
        f"/users/{test_user.id}/professional-status",
        json=test_professional_status,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Professional status updated successfully"
    assert data["notification_sent"] == False
