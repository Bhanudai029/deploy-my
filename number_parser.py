"""
Number Parser Utility
Parses and extracts numbers from various formats to prevent bypass attempts
"""

import re
from word2number import w2n

def extract_number_from_text(text):
    """
    Extract and calculate numbers from text, handling:
    - Math expressions (5+5, 10+10, etc.)
    - Text numbers (five, ten, twenty, etc.)
    - Mixed formats (5 plus 5, five + 5)
    - Numbers in other languages (basic support)
    
    Returns the calculated number or 0 if no valid number found.
    Caps at 250 to prevent abuse.
    """
    try:
        text = text.lower().strip()
        
        # Check for math expressions with operators
        # Pattern: number operator number (e.g., "5+5", "10 + 10", "5 plus 5")
        math_patterns = [
            r'(\d+)\s*[\+plus]\s*(\d+)',
            r'(\d+)\s*[\-minus]\s*(\d+)',
            r'(\d+)\s*[\*×xXtimes]\s*(\d+)',
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, text)
            if match:
                num1 = int(match.group(1))
                num2 = int(match.group(2))
                
                if '+' in text or 'plus' in text:
                    result = num1 + num2
                elif '-' in text or 'minus' in text:
                    result = num1 - num2
                elif any(op in text for op in ['*', '×', 'x', 'X', 'times']):
                    result = num1 * num2
                else:
                    result = num1
                
                return min(result, 250)
        
        # Try to extract text numbers (e.g., "twenty", "fifty")
        try:
            # Replace common words with their number equivalents before parsing
            text_replaced = text.replace('and', '').strip()
            number = w2n.word_to_num(text_replaced)
            return min(number, 250)
        except:
            pass
        
        # Extract simple numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            # Sum all numbers found (handles cases like "5 and 5")
            total = sum(int(n) for n in numbers)
            return min(total, 250)
        
        return 0
        
    except Exception as e:
        print(f"Number parsing error: {e}")
        return 0


def normalize_query_for_counting(query):
    """
    Normalize a user query to extract the intended number of items.
    
    Examples:
    - "Top 5+5 songs" -> 10
    - "Best twenty songs" -> 20
    - "top fifty tracks" -> 50
    - "5 plus 5 songs" -> 10
    
    Returns: The normalized count (capped at 250)
    """
    extracted = extract_number_from_text(query)
    
    # If we found a number, cap it at 250
    if extracted > 0:
        return min(extracted, 250)
    
    # Default to 0 (no specific count requested)
    return 0
