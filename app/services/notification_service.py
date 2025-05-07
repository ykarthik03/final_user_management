import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to users."""
    
    @classmethod
    async def send_professional_status_notification(
        cls, 
        db: AsyncSession, 
        user_id: UUID, 
        email_service: EmailService,
        is_professional: bool
    ) -> bool:
        """
        Send a notification to a user about their professional status change.
        
        Args:
            db: Database session
            user_id: ID of the user to notify
            email_service: Email service for sending notifications
            is_professional: New professional status
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Get the user
            user = await UserService.get_by_id(db, user_id)
            if not user:
                logger.error(f"User {user_id} not found for notification")
                return False
                
            # Prepare the email content
            subject = "Your Professional Status Has Been Updated"
            status_text = "upgraded to professional" if is_professional else "changed from professional"
            content = f"""
            <h2>Professional Status Update</h2>
            <p>Dear {user.first_name or user.nickname},</p>
            <p>Your account has been {status_text} status.</p>
            <p>As a professional user, you now have access to additional features and benefits.</p>
            <p>If you have any questions about your new status, please contact our support team.</p>
            <p>Thank you for being a valued member of our community!</p>
            """
            
            # Send the email
            await email_service.send_email(
                to_email=user.email,
                subject=subject,
                content=content
            )
            
            logger.info(f"Professional status notification sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending professional status notification: {str(e)}")
            return False
