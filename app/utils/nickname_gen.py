from builtins import str
import random
import re
from typing import List, Optional

# Expanded lists for more diverse nickname generation
ADJECTIVES = [
    "clever", "jolly", "brave", "sly", "gentle", "swift", "calm", "wise", 
    "happy", "mighty", "noble", "proud", "fierce", "kind", "quick", "bright", 
    "bold", "eager", "fair", "grand", "keen", "lively", "merry", "nice", 
    "polite", "quiet", "rapid", "smart", "strong", "tall", "witty", "zealous"
]

ANIMALS = [
    "panda", "fox", "raccoon", "koala", "lion", "tiger", "eagle", "wolf", 
    "bear", "hawk", "dolphin", "shark", "whale", "zebra", "elephant", "giraffe", 
    "monkey", "gorilla", "penguin", "turtle", "rabbit", "squirrel", "deer", 
    "moose", "owl", "falcon", "swan", "duck", "goose", "horse", "unicorn"
]

def generate_nickname(min_length: int = 5, max_length: int = 30, 
                     custom_adjectives: Optional[List[str]] = None, 
                     custom_animals: Optional[List[str]] = None) -> str:
    """Generate a URL-safe nickname using adjectives and animal names.
    
    Args:
        min_length: Minimum length of the generated nickname
        max_length: Maximum length of the generated nickname
        custom_adjectives: Optional list of custom adjectives to use
        custom_animals: Optional list of custom animals to use
        
    Returns:
        A URL-safe nickname string in the format adjective_animal_number
    """
    # Use custom lists if provided, otherwise use defaults
    adjectives = custom_adjectives if custom_adjectives else ADJECTIVES
    animals = custom_animals if custom_animals else ANIMALS
    
    # Ensure we have at least one adjective and animal
    if not adjectives or not animals:
        raise ValueError("Adjectives and animals lists cannot be empty")
    
    # Try to generate a nickname within the length constraints
    attempts = 0
    max_attempts = 10  # Prevent infinite loops
    
    while attempts < max_attempts:
        # Generate a random number with variable digits
        number = random.randint(1, 9999)
        
        # Create the nickname
        nickname = f"{random.choice(adjectives)}_{random.choice(animals)}_{number}"
        
        # Check if it meets the length requirements
        if min_length <= len(nickname) <= max_length:
            return nickname
            
        attempts += 1
    
    # If we couldn't generate a suitable nickname within constraints, adjust and try once more
    adj = random.choice(adjectives)
    animal = random.choice(animals)
    
    # Truncate if needed to fit within max_length
    if len(f"{adj}_{animal}_123") > max_length:
        adj = adj[:max(3, max_length // 3)]
        animal = animal[:max(3, max_length // 3)]
    
    number = random.randint(1, 999)
    return f"{adj}_{animal}_{number}"

def is_valid_nickname(nickname: str) -> bool:
    """Check if a nickname follows the required format and constraints.
    
    Args:
        nickname: The nickname to validate
        
    Returns:
        True if the nickname is valid, False otherwise
    """
    # Check basic pattern: word_word_number
    pattern = r'^[a-z]+_[a-z]+_[0-9]+$'
    if not re.match(pattern, nickname):
        return False
        
    # Check if parts are reasonable
    parts = nickname.split('_')
    if len(parts) != 3:
        return False
        
    adjective, animal, number = parts
    
    # Check reasonable lengths for each part
    if len(adjective) < 2 or len(animal) < 2 or len(number) < 1:
        return False
        
    # Check if number is actually a number
    try:
        int(number)
    except ValueError:
        return False
        
    return True
