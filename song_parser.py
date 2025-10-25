"""
Song Pattern Parser
Extracts song names and artists from AI responses
"""

import re
from typing import List, Dict


def parse_songs_from_ai_response(text: str) -> List[Dict[str, str]]:
    """
    Parse songs from AI response text
    Detects patterns like:
    - "1. Song Name by Artist Name"
    - "1. Song Name - Artist Name"
    - "Song Name by Artist Name"
    
    Returns: List of {'song': str, 'artist': str, 'full_query': str}
    """
    songs = []
    
    # Pattern 1: "1. Song Name by Artist Name"
    # This is the primary format the AI is instructed to use
    pattern1 = r'^\s*\d+\.\s*(.+?)\s+by\s+(.+?)(?:\s*[-–—]\s*.*)?$'
    
    # Pattern 2: "Song Name by Artist Name" (without number)
    pattern2 = r'^(.+?)\s+by\s+(.+?)(?:\s*[-–—]\s*.*)?$'
    
    # Pattern 3: "1. Song Name - Artist Name"
    pattern3 = r'^\s*\d+\.\s*(.+?)\s*[-–—]\s*(.+?)(?:\s*[-–—]\s*.*)?$'
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try pattern 1 first (numbered "by" format - primary)
        match = re.match(pattern1, line)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            
            # Remove any trailing description after hyphen
            if ' - ' in artist_name:
                artist_name = artist_name.split(' - ')[0].strip()
            
            songs.append({
                'song': song_name,
                'artist': artist_name,
                'full_query': f"{song_name} by {artist_name}"
            })
            continue
        
        # Try pattern 2 (unnumbered "by" format)
        match = re.match(pattern2, line)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            
            # Skip if this looks like a sentence rather than a song
            if len(song_name.split()) > 8:
                continue
            
            # Remove any trailing description
            if ' - ' in artist_name:
                artist_name = artist_name.split(' - ')[0].strip()
            
            songs.append({
                'song': song_name,
                'artist': artist_name,
                'full_query': f"{song_name} by {artist_name}"
            })
            continue
        
        # Pattern 3 (hyphen format) - DISABLED for artist queries
        # Only parse if the line contains 'by' keyword
        # This prevents artist-only responses from being parsed as songs
        # Example of what we DON'T want to parse:
        # "1. Swoopna Suman - One of Nepal's most popular singers"
        # 
        # We only want lines like:
        # "1. Song Name by Artist Name - description"
        
        # Skip pattern 3 to avoid false positives with artist descriptions
    
    return songs


def format_songs_for_search(songs: List[Dict[str, str]]) -> str:
    """
    Format parsed songs into numbered list for search API
    Returns: "1. Song Name Artist Name\n2. Song Name Artist Name..."
    """
    result = []
    for i, song in enumerate(songs, 1):
        result.append(f"{i}. {song['full_query']}")
    return '\n'.join(result)


# Test function
if __name__ == "__main__":
    # Test with sample AI response
    test_response = """Here are the top 5 phonk songs trending right now:

1. SICKOTOY x Minelli - I Did by SICKOTOY - A powerful phonk track
2. Hora fetelor by Irina Rimes - Romanian phonk anthem
3. Ma by STEFANIA x FAYDEE - High-energy phonk
4. Acceptance [N°160] by Various Artists - Dark phonk vibes
5. Inner Peace [N°158] by Various Artists - Chill phonk beat

These songs are dominating the phonk scene."""
    
    songs = parse_songs_from_ai_response(test_response)
    print(f"Found {len(songs)} songs:")
    for song in songs:
        print(f"  - Song: {song['song']}")
        print(f"    Artist: {song['artist']}")
        print(f"    Full query: {song['full_query']}")
        print()
    
    print("\nFormatted for search API:")
    print(format_songs_for_search(songs))
