from builtins import str
import random
import re
from typing import List, Optional

# Lists of adjectives and animals for nickname generation
ADJECTIVES = ['happy', 'clever', 'brave', 'mighty', 'smart', 'tall', 'short', 'swift', 'calm', 'wild', 'gentle', 'bold', 'quiet', 'loud', 'wise', 'funny', 'kind', 'proud', 'silly', 'fancy']
ANIMALS = ['lion', 'tiger', 'bear', 'wolf', 'fox', 'eagle', 'hawk', 'dolphin', 'whale', 'shark', 'koala', 'panda', 'zebra', 'giraffe', 'elephant', 'monkey', 'owl', 'penguin', 'turtle', 'rabbit']

def generate_nickname(min_length: int = 0, max_length: int = 50, 
                     custom_adjectives: Optional[List[str]] = None, 
                     custom_animals: Optional[List[str]] = None) -> str:
    """Generate a URL-safe nickname in the format adjective_animal_number
    
    Args:
        min_length: Minimum length of the nickname (default: 0, no minimum)
        max_length: Maximum length of the nickname (default: 50)
        custom_adjectives: Optional list of custom adjectives to use
        custom_animals: Optional list of custom animals to use
        
    Returns:
        A URL-safe nickname string in the format adjective_animal_number
        
    Raises:
        ValueError: If custom_adjectives or custom_animals is empty
    """
    # Use custom lists if provided, otherwise use defaults
    if custom_adjectives is not None:
        if not custom_adjectives:
            raise ValueError("Custom adjectives list cannot be empty")
        adjectives = custom_adjectives
    else:
        adjectives = ADJECTIVES
        
    if custom_animals is not None:
        if not custom_animals:
            raise ValueError("Custom animals list cannot be empty")
        animals = custom_animals
    else:
        animals = ANIMALS
    
    # Handle extreme length constraints
    if max_length <= 8:
        # For very short max lengths, find the shortest possible combination
        # Sort adjectives and animals by length
        sorted_adjectives = sorted(adjectives, key=len)
        sorted_animals = sorted(animals, key=len)
        
        # Try combinations until we find one that fits
        for adj in sorted_adjectives:
            for anim in sorted_animals:
                # Check if this combination will fit within max_length
                # Format: adj_anim_1 (need at least one digit)
                if len(adj) + len(anim) + 3 <= max_length:  # +3 for underscores and digit
                    adjective = adj
                    animal = anim
                    break
            else:
                # Continue outer loop if inner loop didn't break
                continue
            # Break outer loop if inner loop broke
            break
        else:
            # If no combination fits, use the shortest possible
            adjective = sorted_adjectives[0][:1]  # Take just first letter if needed
            animal = sorted_animals[0][:1]  # Take just first letter if needed
    else:
        # Normal case
        adjective = random.choice(adjectives)
        animal = random.choice(animals)
    
    # Calculate how much space we have left for the number
    # Format: adjective_animal_number
    base_length = len(adjective) + len(animal) + 2  # +2 for the underscores
    
    # Determine number range based on length constraints
    if max_length < base_length + 1:  # Need at least 1 digit
        # For extreme constraints, use single digit
        max_length = base_length + 1
        
    max_number_length = max_length - base_length
    max_number = 10 ** max_number_length - 1
    
    # Generate a random number
    number = random.randint(1, min(9999, max_number))
    
    # Create the nickname
    nickname = f"{adjective}_{animal}_{number}"
    
    # Check if it meets the minimum length requirement
    if min_length > 0 and len(nickname) < min_length:
        # If too short, use a longer number
        digits_needed = min_length - base_length
        if digits_needed > 0:
            # Ensure number has at least digits_needed digits
            min_number = max(10 ** (digits_needed - 1), 1)
            number = random.randint(min_number, 10 ** digits_needed - 1)
            nickname = f"{adjective}_{animal}_{number}"
    
    return nickname

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
    if len(adjective) < 1 or len(animal) < 1 or len(number) < 1:
        return False
        
    # Check if number is actually a number
    try:
        int(number)
    except ValueError:
        return False
        
    return True
