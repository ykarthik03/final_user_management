"""
Tests for nickname generation functionality.
"""
import pytest
import re
from app.utils.nickname_gen import generate_nickname, is_valid_nickname, ADJECTIVES, ANIMALS

def test_nickname_format():
    """Test that generated nicknames follow the expected format."""
    for _ in range(100):  # Test multiple times to catch potential issues
        nickname = generate_nickname()
        # Check format: adjective_animal_number
        assert is_valid_nickname(nickname), f"Generated nickname {nickname} is invalid"
        
        # Verify structure
        parts = nickname.split('_')
        assert len(parts) == 3, f"Nickname {nickname} does not have 3 parts"
        
        # Verify each part
        adjective, animal, number = parts
        assert adjective.isalpha(), f"Adjective part '{adjective}' contains non-alphabetic characters"
        assert animal.isalpha(), f"Animal part '{animal}' contains non-alphabetic characters"
        assert number.isdigit(), f"Number part '{number}' is not a number"

def test_nickname_uniqueness():
    """Test that generated nicknames are likely to be unique."""
    nicknames = [generate_nickname() for _ in range(100)]
    unique_nicknames = set(nicknames)
    # We expect most nicknames to be unique due to the random number
    assert len(unique_nicknames) > 90, f"Only {len(unique_nicknames)} out of 100 nicknames were unique"

def test_nickname_length_constraints():
    """Test that nicknames respect length constraints."""
    # Test minimum length constraint
    for min_length in [5, 10, 15]:
        for _ in range(10):
            nickname = generate_nickname(min_length=min_length)
            assert len(nickname) >= min_length, f"Nickname {nickname} is shorter than minimum length {min_length}"
    
    # Test maximum length constraint
    for max_length in [20, 15, 10]:
        for _ in range(10):
            nickname = generate_nickname(max_length=max_length)
            assert len(nickname) <= max_length, f"Nickname {nickname} is longer than maximum length {max_length}"
    
    # Test both constraints together
    for _ in range(10):
        nickname = generate_nickname(min_length=10, max_length=15)
        assert 10 <= len(nickname) <= 15, f"Nickname {nickname} is not between 10 and 15 characters"

def test_custom_word_lists():
    """Test that custom word lists are used correctly."""
    custom_adjectives = ["super", "mega", "ultra"]
    custom_animals = ["cat", "dog", "fish"]
    
    for _ in range(20):
        nickname = generate_nickname(custom_adjectives=custom_adjectives, custom_animals=custom_animals)
        parts = nickname.split('_')
        assert parts[0] in custom_adjectives, f"Adjective {parts[0]} not in custom list"
        assert parts[1] in custom_animals, f"Animal {parts[1]} not in custom list"

def test_empty_word_lists():
    """Test that empty word lists raise appropriate errors."""
    with pytest.raises(ValueError):
        generate_nickname(custom_adjectives=[])
    
    with pytest.raises(ValueError):
        generate_nickname(custom_animals=[])

def test_is_valid_nickname():
    """Test the nickname validation function."""
    # Valid nicknames
    valid_nicknames = [
        "clever_fox_123",
        "happy_dog_1",
        "super_cat_9999",
        "a_b_1"  # Minimal valid nickname
    ]
    for nickname in valid_nicknames:
        assert is_valid_nickname(nickname), f"Nickname {nickname} should be valid"
    
    # Invalid nicknames
    invalid_nicknames = [
        "clever-fox-123",  # Wrong separator
        "Clever_Fox_123",  # Uppercase letters
        "clever_fox",      # Missing number
        "clever__fox_123", # Double separator
        "clever_fox_",     # Missing number
        "_clever_fox_123", # Leading separator
        "clever_fox_abc",  # Non-numeric suffix
        "123_clever_fox",  # Wrong order
        "",                # Empty string
        "a"                # Too short
    ]
    for nickname in invalid_nicknames:
        assert not is_valid_nickname(nickname), f"Nickname {nickname} should be invalid"

def test_word_lists_content():
    """Test that the word lists contain appropriate content."""
    # Check adjectives
    assert len(ADJECTIVES) >= 10, "Adjectives list is too short"
    for adj in ADJECTIVES:
        assert adj.isalpha(), f"Adjective '{adj}' contains non-alphabetic characters"
        assert adj.islower(), f"Adjective '{adj}' is not lowercase"
    
    # Check animals
    assert len(ANIMALS) >= 10, "Animals list is too short"
    for animal in ANIMALS:
        assert animal.isalpha(), f"Animal '{animal}' contains non-alphabetic characters"
        assert animal.islower(), f"Animal '{animal}' is not lowercase"

def test_extreme_length_constraints():
    """Test nickname generation with extreme length constraints."""
    # Very short maximum length
    nickname = generate_nickname(max_length=8)
    assert len(nickname) <= 8, f"Nickname {nickname} exceeds maximum length 8"
    
    # Very long minimum length
    nickname = generate_nickname(min_length=50)
    assert len(nickname) >= 5, f"Nickname {nickname} is too short"  # Should still generate something reasonable

def test_nickname_pattern():
    """Test that generated nicknames match the expected pattern."""
    pattern = r'^[a-z]+_[a-z]+_[0-9]+$'
    for _ in range(50):
        nickname = generate_nickname()
        assert re.match(pattern, nickname), f"Nickname {nickname} does not match pattern {pattern}"
