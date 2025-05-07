# app/security.py
from builtins import Exception, ValueError, bool, int, str
import secrets
import bcrypt
from logging import getLogger

# Set up logging
logger = getLogger(__name__)

def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hashes a password using bcrypt with a specified cost factor.
    
    Args:
        password (str): The plain text password to hash.
        rounds (int): The cost factor that determines the computational cost of hashing.

    Returns:
        str: The hashed password.

    Raises:
        ValueError: If hashing the password fails.
    """
    try:
        salt = bcrypt.gensalt(rounds=rounds)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')
    except Exception as e:
        logger.error("Failed to hash password: %s", e)
        raise ValueError("Failed to hash password") from e

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a hashed password.
    
    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The bcrypt hashed password.

    Returns:
        bool: True if the password is correct, False otherwise.

    Raises:
        ValueError: If the hashed password format is incorrect or the function fails to verify.
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error("Error verifying password: %s", e)
        raise ValueError("Authentication process encountered an unexpected error") from e

def generate_verification_token():
    """Generate a secure URL-safe token for email verification.
    
    Returns:
        tuple: A tuple containing (raw_token, hashed_token) where raw_token is sent to the user
        and hashed_token is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)  # Increased from 16 to 32 bytes for better security
    hashed_token = hash_verification_token(raw_token)
    return raw_token, hashed_token

def hash_verification_token(token: str, rounds: int = 10) -> str:
    """Hash a verification token using bcrypt.
    
    Args:
        token (str): The raw verification token to hash.
        rounds (int): The cost factor for bcrypt hashing.
        
    Returns:
        str: The hashed verification token.
    """
    try:
        salt = bcrypt.gensalt(rounds=rounds)
        hashed_token = bcrypt.hashpw(token.encode('utf-8'), salt)
        return hashed_token.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to hash verification token: {e}")
        raise ValueError("Failed to hash verification token") from e

def verify_token(raw_token: str, hashed_token: str) -> bool:
    """Verify a raw verification token against its hashed version.
    
    Args:
        raw_token (str): The raw token provided by the user.
        hashed_token (str): The hashed token stored in the database.
        
    Returns:
        bool: True if the token is valid, False otherwise.
    """
    try:
        return bcrypt.checkpw(raw_token.encode('utf-8'), hashed_token.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return False