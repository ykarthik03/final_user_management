from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID

class ProfileUpdate(BaseModel):
    """Schema for updating user profile fields."""
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[str] = Field(None, example="https://github.com/johndoe")
    
    class Config:
        from_attributes = True

class ProfessionalStatusUpdate(BaseModel):
    """Schema for updating a user's professional status."""
    is_professional: bool = Field(..., example=True)
    
    class Config:
        from_attributes = True

class ProfileResponse(BaseModel):
    """Response schema for profile operations."""
    message: str
    user_id: UUID
    updated_fields: Dict[str, Any]
    
    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    """Response schema for notification operations."""
    message: str
    user_id: UUID
    notification_sent: bool
    
    class Config:
        from_attributes = True
