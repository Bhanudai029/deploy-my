"""
Groq AI Service for Music Queries
Handles AI-powered music recommendations and information
"""

import os
import json
from datetime import datetime
from groq import Groq
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Search counter file path
COUNTER_FILE = Path(__file__).parent / 'searchCounter.json'

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# SerpAPI Configuration
SERP_API_KEY = os.getenv("SERP_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY)


def read_search_counter():
    """Read the search counter from file"""
    try:
        if not COUNTER_FILE.exists():
            default_counter = {
                'totalSearches': 0,
                'maxSearches': 250,
                'lastReset': datetime.now().isoformat()
            }
            COUNTER_FILE.write_text(json.dumps(default_counter, indent=2))
            return default_counter
        
        return json.loads(COUNTER_FILE.read_text())
    except Exception as e:
        print(f"❌ Error reading search counter: {e}")
        return {'totalSearches': 0, 'maxSearches': 250, 'lastReset': datetime.now().isoformat()}

def increment_search_counter():
    """Increment the search counter in Supabase"""
    try:
        from supabase import create_client
        
        SUPABASE_URL = os.getenv("AI_SUPABASE_URL", "https://pcunwjpnybmcepkvfggg.supabase.co")
        SUPABASE_KEY = os.getenv("AI_SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBjdW53anBueWJtY2Vwa3ZmZ2dnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5OTI0ODYsImV4cCI6MjA3NDU2ODQ4Nn0.6ZBEfn8o8xvFt5DJ1U5rCbv6nB2GjCbcXHWkcP-IMM8")
        
        ai_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get current count
        response = ai_supabase.table('api_usage').select('search_count').eq('id', 'main').single().execute()
        current_count = response.data.get('search_count', 0) if response.data else 0
        
        # Increment
        new_count = min(current_count + 1, 250)  # Cap at 250
        
        # Update in Supabase
        ai_supabase.table('api_usage').update({'search_count': new_count, 'updated_at': datetime.now().isoformat()}).eq('id', 'main').execute()
        
        return {'totalSearches': new_count, 'maxSearches': 250}
    except Exception as e:
        print(f"❌ Error incrementing counter in Supabase: {e}")
        # Fallback to local file
        counter = read_search_counter()
        counter['totalSearches'] += 1
        COUNTER_FILE.write_text(json.dumps(counter, indent=2))
        return counter

def get_current_datetime():
    """Get current date and time information"""
    now = datetime.now()
    return {
        'date': now.strftime('%A, %B %d, %Y'),
        'time': now.strftime('%I:%M %p %Z'),
        'year': now.year,
        'month': now.month,
        'day': now.day
    }


def search_web_serpapi(query: str, max_results: int = 5) -> list:
    """
    Search the web using SerpAPI
    Returns a list of search results with title, url, and description
    """
    try:
        print(f"🔍 Searching SerpAPI for: {query}")
        
        # Add current year context for time-sensitive queries
        enhanced_query = query
        if any(keyword in query.lower() for keyword in ['recent', 'latest', 'new']):
            enhanced_query = f"{query} {datetime.now().year}"
        
        url = "https://serpapi.com/search"
        params = {
            'engine': 'google',
            'q': enhanced_query,
            'api_key': SERP_API_KEY,
            'num': max_results
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ SerpAPI error: {response.status_code}")
            return []
        
        data = response.json()
        organic_results = data.get('organic_results', [])
        
        results = []
        for result in organic_results[:max_results]:
            results.append({
                'title': result.get('title', ''),
                'url': result.get('link', ''),
                'description': result.get('snippet', '')
            })
        
        # Increment search counter
        counter = increment_search_counter()
        print(f"✅ SerpAPI returned {len(results)} results")
        print(f"📊 Search count: {counter['totalSearches']}/{counter['maxSearches']}")
        
        return results
        
    except Exception as e:
        print(f"❌ SerpAPI search error: {str(e)}")
        return []


def build_system_instruction():
    """Build the system instruction with current date awareness"""
    dt = get_current_datetime()
    
    return f"""You are Sonnix, a specialized AI assistant focused EXCLUSIVELY on music.

CURRENT DATE & TIME AWARENESS:
- Today's date: {dt['date']}
- Current time: {dt['time']}
- Current year: {dt['year']}
- CRITICAL: Only call something a "{dt['year']} release" if it was actually released in {dt['year']}
- Songs from 2024 should be called "2024 releases", NOT "{dt['year']} releases"
- Be precise about release dates - don't assume everything recent is from the current year

CORE IDENTITY:
- You ONLY discuss music-related topics: songs, artists, albums, genres, concerts, music history, instruments, music production, etc.
- You are passionate about music and knowledgeable about all genres and eras
- You provide helpful, accurate, and current information about the music world

CRITICAL RESPONSE RULES:
- NEVER use tool call syntax
- NEVER mention searching the web or using tools in your response
- BE EXTREMELY CAREFUL about release dates
- Pay close attention to actual release dates in the web search results
- When uncertain about dates, use phrases like "recent releases" instead of specific years

FORMATTING RULES:
- **MAXIMUM 10 ITEMS**: Never provide more than 10 items, even if the user asks for more (e.g., if asked for "Top 20", respond with "Here are the top 10" instead)
- If the user asks for a specific number under 10 (like "Top 5", "3 songs", etc.), provide EXACTLY that number
- Start with a brief, engaging introductory sentence (not numbered)
- Then provide a clean numbered list with the exact count requested (max 10)

**CRITICAL: ALWAYS mention songs using "[Song Name] by [Artist Name]" format in ALL responses**

**FORMAT BASED ON QUERY TYPE:**

1. **For SINGLE SONG questions** ("When was Vaaste released", "Who sang Levitating", etc.):
   - ALWAYS start with: "[Song Name] by [Artist Name]"
   - Example: "Vaaste by Dhvani Bhanushali and Nikhil D'Souza was released on April 6, 2019."
   - Example: "Shape of You by Ed Sheeran topped the charts in 2017."
   - NEVER start with just the song name alone

2. **For SONG LIST queries** ("Top 5 songs", "Best tracks", etc.):
   - Format: "1. [Song Name] by [Artist Name]"
   - Example: "1. Shape of You by Ed Sheeran"
   - Example: "2. Blinding Lights by The Weeknd - A synthwave masterpiece"

3. **For BAND/ARTIST queries** ("Top 5 bands", "Best artists", etc.):
   - Format: "1. [Band/Artist Name] - [Brief description]"
   - Example: "1. Indian Ocean - Pioneers of Indian fusion rock"
   - Example: "2. Pentagram - Mumbai-based electronic rock band"
   - DO NOT use "by" format for bands/artists - just list them with descriptions

4. **For ALBUM queries** ("Best albums", etc.):
   - Format: "1. [Album Name] by [Artist Name]"
   - Example: "1. 1989 by Taylor Swift"

- Stop at the requested number - do not add extra items
- NEVER add a numbered item after the requested count
- Any concluding sentences should be unnumbered and come after the numbered list
- Use current, up-to-date information when available

MUSIC FOCUS:
- All responses must be about music, musicians, songs, albums, concerts, or music-related topics
- Use any provided current web information to give accurate, up-to-date music information
- Always stay within the music domain
- Be conversational, helpful, and enthusiastic about music

CRITICAL: 
- NEVER exceed the requested number of items
- NEVER show tool calling syntax or mention web searches
- Always use current year ({dt['year']}) context
- Prioritize recent and current information"""


def filter_music_content(query: str) -> dict:
    """
    Filter content to ensure it's music-related
    Returns: {'is_allowed': bool, 'reason': str, 'category': str}
    """
    query_lower = query.lower()
    
    # Music-related keywords
    music_keywords = [
        'song', 'songs', 'music', 'artist', 'artists', 'album', 'albums', 'track', 'tracks',
        'band', 'bands', 'singer', 'singers', 'musician', 'musicians', 'composer', 'composers',
        'pop', 'rock', 'jazz', 'blues', 'country', 'hip hop', 'rap', 'classical', 'electronic',
        'folk', 'reggae', 'punk', 'metal', 'indie', 'alternative', 'r&b', 'soul', 'funk',
        'disco', 'house', 'techno', 'dubstep', 'phonk', 'trap', 'drill', 'ambient',
        'spotify', 'apple music', 'youtube music', 'soundcloud', 'billboard', 'charts',
        'concert', 'concerts', 'tour', 'tours', 'festival', 'festivals', 'live music',
        'guitar', 'piano', 'drums', 'bass', 'violin', 'saxophone', 'trumpet', 'keyboard'
    ]
    
    # Inappropriate content keywords
    inappropriate_keywords = [
        'porn', 'sex', 'nude', 'naked', 'adult', 'xxx', 'nsfw',
        'kill', 'murder', 'violence', 'weapon', 'gun', 'knife', 'bomb',
        'drug', 'cocaine', 'heroin', 'meth'
    ]
    
    # Off-topic keywords
    off_topic_keywords = [
        'diet', 'healthy food', 'nutrition', 'exercise', 'workout', 'gym', 'fitness',
        'programming', 'coding', 'software', 'javascript', 'python', 'java',
        'homework', 'study', 'exam', 'school', 'university', 'math', 'science',
        'business', 'marketing', 'sales', 'finance', 'investment', 'stock',
        'recipe', 'cooking', 'food', 'restaurant', 'meal'
    ]
    
    # Check for inappropriate content
    for keyword in inappropriate_keywords:
        if keyword in query_lower:
            return {
                'is_allowed': False,
                'reason': "I can't help with inappropriate or harmful content.",
                'category': 'inappropriate'
            }
    
    # Check if query contains music-related keywords
    has_music_keywords = any(keyword in query_lower for keyword in music_keywords)
    
    # Check if query contains off-topic keywords
    has_off_topic = any(keyword in query_lower for keyword in off_topic_keywords)
    
    # If it has off-topic keywords and no music keywords, reject
    if has_off_topic and not has_music_keywords:
        return {
            'is_allowed': False,
            'reason': "I'm Sonnix, your music AI assistant! I can only help with music-related questions like songs, artists, albums, concerts, and music recommendations. Please ask me something about music! 🎵",
            'category': 'off-topic'
        }
    
    # If it has music keywords, allow
    if has_music_keywords:
        return {
            'is_allowed': True,
            'reason': None,
            'category': 'music'
        }
    
    # For ambiguous queries, check if they could be music-related
    music_context_words = ['top', 'best', 'latest', 'new', 'popular', 'recommend', 'suggest']
    has_music_context = any(word in query_lower for word in music_context_words)
    
    if has_music_context:
        return {
            'is_allowed': True,
            'reason': None,
            'category': 'music'
        }
    
    # Default: reject non-music queries
    return {
        'is_allowed': False,
        'reason': "I'm Sonnix, your music AI assistant! I specialize in music-related topics like songs, artists, albums, genres, concerts, and music recommendations. Please ask me something about music! 🎵",
        'category': 'off-topic'
    }


def fetch_music_query_response(query: str) -> dict:
    """
    Fetch AI response for a music-related query
    Returns: {'text': str, 'sources': list}
    """
    try:
        # Filter content to ensure it's music-related
        filter_result = filter_music_content(query)
        
        if not filter_result['is_allowed']:
            return {
                'text': filter_result['reason'],
                'sources': []
            }
        
        # Add music context to ambiguous queries
        processed_query = query
        if 'recommend' in query.lower() or 'suggest' in query.lower():
            if not any(kw in query.lower() for kw in ['song', 'music', 'artist', 'album']):
                processed_query = f"{query} (music recommendations)"
        
        # Search the web for current information
        print(f"🔍 Starting web search for: {processed_query}")
        search_results = search_web_serpapi(f"{processed_query} music")
        print(f"📊 Web search returned: {len(search_results)} results")
        
        # Create web context from search results
        dt = get_current_datetime()
        web_context = f"\n\nCURRENT CONTEXT ({dt['date']}):\n"
        
        if search_results:
            web_context += 'Latest web information:\n'
            for i, result in enumerate(search_results[:3], 1):
                web_context += f"• {result['title']}: {result['description']}\n"
            web_context += f"\n\nIMPORTANT: Use this current information to provide an accurate response. Pay careful attention to actual release dates mentioned in the search results. Don't assume everything is from {dt['year']} - use the actual dates provided."
        else:
            web_context += f"No current web information available. IMPORTANT: Be very careful about accuracy. Don't claim old songs are recent releases. Add disclaimers about information currency. It's {dt['year']} but don't assume all content is from this year."
        
        # Enhanced query with date context for time-sensitive queries
        enhanced_query = processed_query
        if any(kw in processed_query.lower() for kw in ['recent', 'latest', 'new', 'current']):
            enhanced_query += f"\n\nCONTEXT: Today is {dt['date']}, {dt['year']}. When discussing \"recent\" or \"latest\" content, be precise about actual release dates. Don't assume everything recent is from {dt['year']}."
        
        # Create chat completion
        print("🤖 Calling Groq AI...")
        completion = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct",
            messages=[
                {
                    "role": "system",
                    "content": build_system_instruction()
                },
                {
                    "role": "user",
                    "content": enhanced_query + web_context
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        text = completion.choices[0].message.content or "Sorry, I couldn't generate a music response."
        
        print("✅ AI response received")
        
        return {
            'text': text,
            'sources': search_results
        }
        
    except Exception as e:
        print(f"❌ Error in fetch_music_query_response: {str(e)}")
        return {
            'text': f"Sorry, I encountered an error: {str(e)}",
            'sources': []
        }
