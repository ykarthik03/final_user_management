# test_security.py
from builtins import RuntimeError, ValueError, isinstance, str, tuple
import pytest
from app.utils.security import hash_password, verify_password, generate_verification_token, hash_verification_token, verify_token

def test_hash_password():
    """Test that hashing password returns a bcrypt hashed string."""
    password = "secure_password"
    hashed = hash_password(password)
    assert hashed is not None
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')

def test_hash_password_with_different_rounds():
    """Test hashing with different cost factors."""
    password = "secure_password"
    rounds = 10
    hashed_10 = hash_password(password, rounds)
    rounds = 12
    hashed_12 = hash_password(password, rounds)
    assert hashed_10 != hashed_12, "Hashes should differ with different cost factors"

def test_verify_password_correct():
    """Test verifying the correct password."""
    password = "secure_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Test verifying the incorrect password."""
    password = "secure_password"
    hashed = hash_password(password)
    wrong_password = "incorrect_password"
    assert verify_password(wrong_password, hashed) is False

def test_verify_password_invalid_hash():
    """Test verifying a password against an invalid hash format."""
    with pytest.raises(ValueError):
        verify_password("secure_password", "invalid_hash_format")

@pytest.mark.parametrize("password", [
    "",
    " ",
    "a"*100  # Long password
])
def test_hash_password_edge_cases(password):
    """Test hashing various edge cases."""
    hashed = hash_password(password)
    assert isinstance(hashed, str) and hashed.startswith('$2b$'), "Should handle edge cases properly"

def test_verify_password_edge_cases():
    """Test verifying passwords with edge cases."""
    password = " "
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("not empty", hashed) is False

# This function tests the error handling when an internal error occurs in bcrypt
def test_hash_password_internal_error(monkeypatch):
    """Test proper error handling when an internal bcrypt error occurs."""
    def mock_bcrypt_gensalt(rounds):
        raise RuntimeError("Simulated internal error")

    monkeypatch.setattr("bcrypt.gensalt", mock_bcrypt_gensalt)
    with pytest.raises(ValueError):
        hash_password("test")


def test_generate_verification_token():
    """Test that generate_verification_token returns a tuple with raw and hashed tokens."""
    result = generate_verification_token()
    assert isinstance(result, tuple)
    assert len(result) == 2
    raw_token, hashed_token = result
    assert isinstance(raw_token, str)
    assert isinstance(hashed_token, str)
    assert raw_token != hashed_token
    assert hashed_token.startswith('$2b$')

def test_hash_verification_token():
    """Test that hash_verification_token returns a bcrypt hashed string."""
    token = "test_token"
    hashed = hash_verification_token(token)
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')

def test_verify_token_correct():
    """Test verifying the correct token."""
    token = "test_verification_token"
    hashed = hash_verification_token(token)
    assert verify_token(token, hashed) is True

def test_verify_token_incorrect():
    """Test verifying an incorrect token."""
    token = "test_verification_token"
    hashed = hash_verification_token(token)
    wrong_token = "incorrect_token"
    assert verify_token(wrong_token, hashed) is False

def test_verify_token_invalid_hash():
    """Test verifying a token against an invalid hash format."""
    assert verify_token("test_token", "invalid_hash_format") is False

def test_verify_token_edge_cases():
    """Test token verification with edge cases."""
    # Empty token
    empty_token = ""
    hashed_empty = hash_verification_token(empty_token)
    assert verify_token(empty_token, hashed_empty) is True
    assert verify_token("not_empty", hashed_empty) is False
    
    # Long token
    long_token = "a" * 100
    hashed_long = hash_verification_token(long_token)
    assert verify_token(long_token, hashed_long) is True
