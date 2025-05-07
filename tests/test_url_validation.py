"""
Tests for URL validation utilities.
"""
import pytest
from app.utils.url_validation import (
    validate_github_url,
    validate_linkedin_url,
    validate_profile_picture_url
)

class TestGitHubURLValidation:
    def test_valid_github_urls(self):
        valid_urls = [
            "https://github.com/username",
            "http://github.com/username-with-dash",
            "https://www.github.com/username123",
            "https://github.com/a"  # Minimum length username
        ]
        for url in valid_urls:
            is_valid, error_msg = validate_github_url(url)
            assert is_valid, f"URL {url} should be valid, but got error: {error_msg}"
            assert error_msg is None

    def test_invalid_github_urls(self):
        invalid_urls = [
            "github.com/username",  # Missing scheme
            "https://gitlab.com/username",  # Wrong domain
            "https://github.com/",  # Missing username
            "https://github.com/invalid_username!",  # Invalid character in username
            "https://github.com/username/repo",  # Should be just username
            "ftp://github.com/username",  # Invalid scheme
        ]
        for url in invalid_urls:
            is_valid, error_msg = validate_github_url(url)
            assert not is_valid, f"URL {url} should be invalid"
            assert error_msg is not None

    def test_empty_github_url(self):
        is_valid, error_msg = validate_github_url(None)
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_github_url("")
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_github_url("   ")
        assert is_valid
        assert error_msg is None

class TestLinkedInURLValidation:
    def test_valid_linkedin_urls(self):
        valid_urls = [
            "https://linkedin.com/in/username",
            "http://www.linkedin.com/in/username-with-dash",
            "https://linkedin.com/in/username123",
            "https://www.linkedin.com/company/company-name",
        ]
        for url in valid_urls:
            is_valid, error_msg = validate_linkedin_url(url)
            assert is_valid, f"URL {url} should be valid, but got error: {error_msg}"
            assert error_msg is None

    def test_invalid_linkedin_urls(self):
        invalid_urls = [
            "linkedin.com/in/username",  # Missing scheme
            "https://facebook.com/username",  # Wrong domain
            "https://linkedin.com/profile/username",  # Invalid path format
            "https://linkedin.com/",  # Missing path
            "ftp://linkedin.com/in/username",  # Invalid scheme
        ]
        for url in invalid_urls:
            is_valid, error_msg = validate_linkedin_url(url)
            assert not is_valid, f"URL {url} should be invalid"
            assert error_msg is not None

    def test_empty_linkedin_url(self):
        is_valid, error_msg = validate_linkedin_url(None)
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_linkedin_url("")
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_linkedin_url("   ")
        assert is_valid
        assert error_msg is None

class TestProfilePictureURLValidation:
    def test_valid_profile_picture_urls(self):
        valid_urls = [
            "https://example.com/image.jpg",
            "http://example.com/path/to/image.png",
            "https://cdn.example.com/user/profile.jpeg",
            "https://example.com/image.gif",
            "https://example.com/image.webp",
            "https://example.com/image.bmp",
        ]
        for url in valid_urls:
            is_valid, error_msg = validate_profile_picture_url(url)
            assert is_valid, f"URL {url} should be valid, but got error: {error_msg}"
            assert error_msg is None

    def test_invalid_profile_picture_urls(self):
        invalid_urls = [
            "example.com/image.jpg",  # Missing scheme
            "https://example.com/image.txt",  # Not an image file
            "https://example.com/image",  # Missing extension
            "ftp://example.com/image.jpg",  # Invalid scheme
        ]
        for url in invalid_urls:
            is_valid, error_msg = validate_profile_picture_url(url)
            assert not is_valid, f"URL {url} should be invalid"
            assert error_msg is not None

    def test_empty_profile_picture_url(self):
        is_valid, error_msg = validate_profile_picture_url(None)
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_profile_picture_url("")
        assert is_valid
        assert error_msg is None

        is_valid, error_msg = validate_profile_picture_url("   ")
        assert is_valid
        assert error_msg is None
