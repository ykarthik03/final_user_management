"""
URL validation utilities for the User Management System.
These functions validate profile URLs to ensure they are properly formatted and point to valid domains.
"""
from builtins import str
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

def validate_github_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a GitHub profile URL.
    
    Args:
        url: The URL to validate, can be None.
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing (is_valid, error_message).
        If the URL is valid, is_valid will be True and error_message will be None.
        If the URL is invalid, is_valid will be False and error_message will contain the reason.
    """
    if url is None or url.strip() == "":
        return True, None  # Empty URLs are allowed
        
    # Basic URL structure validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format. Must include scheme (http:// or https://) and domain."
    
    # Ensure the scheme is http or https
    if parsed.scheme not in ["http", "https"]:
        return False, "URL must use http or https protocol."
    
    # Check if it's a GitHub URL
    if not parsed.netloc.lower() in ["github.com", "www.github.com"]:
        return False, "URL must be from github.com domain."
    
    # Validate the path format (should be /username)
    path_pattern = r"^/[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
    if not re.match(path_pattern, parsed.path):
        return False, "Invalid GitHub username format in URL."
    
    return True, None

def validate_linkedin_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a LinkedIn profile URL.
    
    Args:
        url: The URL to validate, can be None.
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing (is_valid, error_message).
        If the URL is valid, is_valid will be True and error_message will be None.
        If the URL is invalid, is_valid will be False and error_message will contain the reason.
    """
    if url is None or url.strip() == "":
        return True, None  # Empty URLs are allowed
        
    # Basic URL structure validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format. Must include scheme (http:// or https://) and domain."
    
    # Ensure the scheme is http or https
    if parsed.scheme not in ["http", "https"]:
        return False, "URL must use http or https protocol."
    
    # Check if it's a LinkedIn URL
    valid_domains = ["linkedin.com", "www.linkedin.com"]
    if not any(parsed.netloc.lower() == domain for domain in valid_domains):
        return False, "URL must be from linkedin.com domain."
    
    # Validate the path format (should start with /in/ or /company/)
    if not (parsed.path.startswith("/in/") or parsed.path.startswith("/company/")):
        return False, "Invalid LinkedIn profile format. Must start with /in/ or /company/."
    
    return True, None

def validate_profile_picture_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a profile picture URL.
    
    Args:
        url: The URL to validate, can be None.
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing (is_valid, error_message).
        If the URL is valid, is_valid will be True and error_message will be None.
        If the URL is invalid, is_valid will be False and error_message will contain the reason.
    """
    if url is None or url.strip() == "":
        return True, None  # Empty URLs are allowed
        
    # Basic URL structure validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL format. Must include scheme (http:// or https://) and domain."
    
    # Ensure the scheme is http or https
    if parsed.scheme not in ["http", "https"]:
        return False, "URL must use http or https protocol."
    
    # Check if the URL points to an image file
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    if not any(parsed.path.lower().endswith(ext) for ext in image_extensions):
        return False, "URL must point to an image file (jpg, jpeg, png, gif, bmp, webp)."
    
    return True, None
