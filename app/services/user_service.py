from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone, timedelta
import secrets
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, null, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.dependencies import get_settings
import logging
import secrets

from app.models.user_model import User
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.schemas.profile_schemas import ProfileUpdate, ProfessionalStatusUpdate
from app.utils.security import hash_password, verify_password, generate_verification_token, hash_verification_token, verify_token
from app.utils.nickname_gen import generate_nickname
from app.utils.rate_limiter import login_rate_limiter
from uuid import UUID
from app.services.email_service import EmailService
from app.models.user_model import UserRole
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()
            existing_user = await cls.get_by_email(session, validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                return None
            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            new_user = User(**validated_data)
            new_nickname = generate_nickname()
            while await cls.get_by_nickname(session, new_nickname):
                new_nickname = generate_nickname()
            new_user.nickname = new_nickname
            logger.info(f"User Role: {new_user.role}")
            user_count = await cls.count(session)
            new_user.role = UserRole.ADMIN if user_count == 0 else UserRole.ANONYMOUS            
            if new_user.role == UserRole.ADMIN:
                new_user.email_verified = True

            else:
                raw_token, hashed_token = generate_verification_token()
                new_user.verification_token = hashed_token
                # Store the raw token temporarily for email sending
                new_user.raw_verification_token = raw_token
                await email_service.send_verification_email(new_user)
                # Remove the raw token after sending email to prevent exposure
                new_user.raw_verification_token = None

            session.add(new_user)
            await session.commit()
            return new_user
        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None

    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            # validated_data = UserUpdate(**update_data).dict(exclude_unset=True)
            validated_data = UserUpdate(**update_data).model_dump(exclude_unset=True)

            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            query = update(User).where(User.id == user_id).values(**validated_data).execution_options(synchronize_session="fetch")
            await cls._execute_query(session, query)
            updated_user = await cls.get_by_id(session, user_id)
            if updated_user:
                session.refresh(updated_user)  # Explicitly refresh the updated user object
                logger.info(f"User {user_id} updated successfully.")
                return updated_user
            else:
                logger.error(f"User {user_id} not found after update attempt.")
            return None
        except Exception as e:  # Broad exception handling for debugging
            logger.error(f"Error during user update: {e}")
            return None

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info(f"User with ID {user_id} not found.")
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await cls._execute_query(session, query)
        return result.scalars().all() if result else []

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], get_email_service) -> Optional[User]:
        return await cls.create(session, user_data, get_email_service)
    

    @classmethod
    async def authenticate_user(cls, db: AsyncSession, username: str, password: str, ip_address: str = None) -> User:
        """Authenticate a user by username and password."""
        rate_limit_key = f"ip_{ip_address}:user_{username}" if ip_address else f"user_{username}"
        
        # First check if already rate limited
        is_limited, blocked_until = login_rate_limiter.is_rate_limited(rate_limit_key)
        if is_limited:
            print(f"Rate limit exceeded for {rate_limit_key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again after {blocked_until}",
                headers={"Retry-After": str(int((blocked_until - datetime.now()).total_seconds()))},
            )
        
        # Record this attempt and check if we've now exceeded the limit
        is_now_limited = login_rate_limiter.record_attempt(rate_limit_key)
        if is_now_limited:
            # This attempt pushed us over the limit
            _, blocked_until = login_rate_limiter.is_rate_limited(rate_limit_key)
            print(f"Rate limit now exceeded for {rate_limit_key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again after {blocked_until}",
                headers={"Retry-After": str(int((blocked_until - datetime.now()).total_seconds()))},
            )
        
        user = await cls.get_by_email(db, username)
        
        if not user:
            print(f"Authentication failed: User {username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(password, user.hashed_password):
            print(f"Authentication failed: Invalid password for user {username}")
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= get_settings().max_login_attempts:  
                user.is_locked = True
                print(f"User {username} locked due to too many failed login attempts")
            
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if user.is_locked:
            print(f"Login attempt for locked account: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Account is locked. Contact support if this is an error.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        
        login_rate_limiter.reset(rate_limit_key)
        
        return user

    @classmethod
    async def login_user(cls, session: AsyncSession, email: str, password: str, ip_address: Optional[str] = None) -> Optional[User]: 
        user = await cls.authenticate_user(session, email, password, ip_address=ip_address) 
        return user

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False


    @classmethod
    async def reset_password(cls, session: AsyncSession, user_id: UUID, new_password: str) -> bool:
        hashed_password = hash_password(new_password)
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            user.failed_login_attempts = 0  
            user.is_locked = False  
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, user_id: UUID, token: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token and verify_token(token, user.verification_token):
            user.email_verified = True
            user.verification_token = None  
            user.role = UserRole.AUTHENTICATED
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        Count the number of users in the database.

        :param session: The AsyncSession instance for database access.
        :return: The count of users.
        """
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        count = result.scalar()
        return count
    
    @classmethod
    async def unlock_user_account(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.is_locked:
            user.is_locked = False
            user.failed_login_attempts = 0  
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def update_user_profile(cls, session: AsyncSession, user_id: UUID, profile_data: dict) -> Optional[User]:
        """
        Update a user's profile fields.
        
        Args:
            session: Database session
            user_id: ID of the user to update
            profile_data: Dictionary containing profile fields to update
            
        Returns:
            Updated user object or None if user not found
        """
        try:
            user = await cls.get_by_id(session, user_id)
            if not user:
                logger.error(f"User {user_id} not found for profile update")
                return None
                
            # Update only the provided fields
            for field, value in profile_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Profile updated for user {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            await session.rollback()
            return None
    
    @classmethod
    async def update_professional_status(cls, session: AsyncSession, user_id: UUID, is_professional: bool) -> Optional[User]:
        """
        Update a user's professional status.
        
        Args:
            session: Database session
            user_id: ID of the user to update
            is_professional: New professional status
            
        Returns:
            Updated user object or None if user not found
        """
        try:
            user = await cls.get_by_id(session, user_id)
            if not user:
                logger.error(f"User {user_id} not found for professional status update")
                return None
                
            user.is_professional = is_professional
            user.professional_status_updated_at = datetime.now(timezone.utc)
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Professional status updated for user {user_id} to {is_professional}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating professional status: {str(e)}")
            await session.rollback()
            return None
