"""
Sonnix Firebase Uploader
Uploads songs to Sonnix website (Firebase) after successful Supabase upload
"""

import requests
import json
from datetime import datetime
from pathlib import Path
from mutagen.mp3 import MP3
from song_parser import parse_songs_from_ai_response
import re


# Firebase Configuration for Sonnix
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyOgh68Cuqhxzm11VGVRcc2W4BYFXP4ZNOk",
    "projectId": "music-x-dfd87",
    "baseUrl": "https://firestore.googleapis.com/v1/projects/music-x-dfd87/databases/(default)/documents"
}


def extract_artist_and_song_from_filename(filename: str) -> dict:
    """
    Extract artist and song name from filename
    Expected formats:
    - "Song Name by Artist Name.mp3"
    - "Artist Name - Song Name.mp3"
    - "Song Name.mp3" (artist = Unknown)
    
    Returns: {'song': str, 'artist': str}
    """
    # Remove .mp3 extension
    name = filename.replace('.mp3', '').strip()
    
    # Pattern 1: "Song by Artist"
    match = re.match(r'^(.+?)\s+by\s+(.+?)$', name, re.IGNORECASE)
    if match:
        return {
            'song': match.group(1).strip(),
            'artist': match.group(2).strip()
        }
    
    # Pattern 2: "Artist - Song"
    if ' - ' in name:
        parts = name.split(' - ', 1)
        # Try to guess which is artist and which is song
        # Usually artist comes first in downloads
        return {
            'artist': parts[0].strip(),
            'song': parts[1].strip()
        }
    
    # Pattern 3: Just song name (no artist)
    return {
        'song': name,
        'artist': 'Unknown Artist'
    }


def get_audio_duration(file_path: str) -> int:
    """
    Get duration of MP3 file in seconds
    
    Args:
        file_path: Path to MP3 file
        
    Returns:
        Duration in seconds (integer)
    """
    try:
        audio = MP3(file_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"⚠️ Could not read duration for {file_path}: {e}")
        return 180  # Default 3 minutes


def upload_song_to_sonnix(song_data: dict) -> dict:
    """
    Upload a single song to Sonnix Firebase
    
    Args:
        song_data: Dict with keys: title, artist, duration, audioUrl
        
    Returns:
        {'success': bool, 'message': str, 'firebase_id': str}
    """
    try:
        # Prepare Firebase document structure
        firebase_document = {
            "fields": {
                "title": {"stringValue": song_data['title']},
                "artist": {"stringValue": song_data['artist']},
                "duration": {"integerValue": str(song_data['duration'])},
                "audioUrl": {"stringValue": song_data['audioUrl']},
                "album": {"stringValue": song_data.get('album', '')},
                "genre": {"stringValue": song_data.get('genre', 'Unknown')},
                "releaseDate": {"stringValue": song_data.get('releaseDate', datetime.now().strftime('%Y-%m-%d'))},
                "imageUrl": {"stringValue": song_data.get('imageUrl', '/default-song.png')},
                "plays": {"integerValue": "0"},
                "isLiked": {"booleanValue": False},
                "createdAt": {"timestampValue": datetime.now().isoformat()},
                "updatedAt": {"timestampValue": datetime.now().isoformat()},
                "customId": {"stringValue": f"song_{int(datetime.now().timestamp())}_{song_data['title'][:10].replace(' ', '_')}"}
            }
        }
        
        # Firebase REST API endpoint
        url = f"{FIREBASE_CONFIG['baseUrl']}/songs?key={FIREBASE_CONFIG['apiKey']}"
        
        # Make POST request
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=firebase_document,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            firebase_id = response.json().get('name', '').split('/')[-1]
            print(f"✅ Uploaded to Sonnix: \"{song_data['title']}\" by {song_data['artist']}")
            return {
                'success': True,
                'message': 'Uploaded to Sonnix successfully',
                'firebase_id': firebase_id
            }
        else:
            print(f"❌ Sonnix upload failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {
                'success': False,
                'message': f'HTTP {response.status_code}: {response.text[:100]}'
            }
            
    except Exception as e:
        print(f"❌ Sonnix upload error: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


def upload_batch_to_sonnix(audio_files: list, public_urls: list, progress_callback=None) -> dict:
    """
    Upload multiple audio files to Sonnix after Supabase upload
    
    Args:
        audio_files: List of local file paths
        public_urls: List of tuples [(filename, supabase_url), ...]
        progress_callback: Optional function to call with progress updates
        
    Returns:
        {'successful': int, 'failed': int, 'details': list}
    """
    def log(message):
        print(message)
        if progress_callback:
            progress_callback(message)
    
    log("🎸 Uploading to Sonnix...")
    
    results = {
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    # Create a mapping of filename to Supabase URL
    url_map = {filename: url for filename, url in public_urls}
    
    log(f"🎵 Uploading {len(audio_files)} songs to Sonnix Firebase...")
    
    for i, audio_file in enumerate(audio_files, 1):
        try:
            file_path = Path(audio_file)
            filename = file_path.name
            
            # Check if we have a Supabase URL for this file
            if filename not in url_map:
                log(f"⚠️ Skipping {filename}: No Supabase URL found")
                results['failed'] += 1
                results['details'].append({
                    'filename': filename,
                    'success': False,
                    'error': 'No Supabase URL'
                })
                continue
            
            supabase_url = url_map[filename]
            
            # Extract artist and song from filename
            metadata = extract_artist_and_song_from_filename(filename)
            
            # Get audio duration
            duration = get_audio_duration(str(file_path))
            
            # Prepare song data for Sonnix
            song_data = {
                'title': metadata['song'],
                'artist': metadata['artist'],
                'duration': duration,
                'audioUrl': supabase_url,
                'genre': 'Music',  # Default genre
                'album': '',
                'imageUrl': '/default-song.png'
            }
            
            # Upload to Sonnix
            log(f"📤 [{i}/{len(audio_files)}] {metadata['song']} by {metadata['artist']}")
            result = upload_song_to_sonnix(song_data)
            
            if result['success']:
                results['successful'] += 1
                log(f"✅ [{i}/{len(audio_files)}] Success")
            else:
                results['failed'] += 1
                log(f"❌ [{i}/{len(audio_files)}] Failed")
            
            results['details'].append({
                'filename': filename,
                'song': metadata['song'],
                'artist': metadata['artist'],
                'duration': duration,
                'supabase_url': supabase_url,
                'success': result['success'],
                'message': result.get('message', ''),
                'firebase_id': result.get('firebase_id', '')
            })
            
        except Exception as e:
            log(f"❌ Error processing {audio_file}: {str(e)}")
            results['failed'] += 1
            results['details'].append({
                'filename': Path(audio_file).name,
                'success': False,
                'error': str(e)
            })
    
    log(f"✅ Sonnix complete: {results['successful']}/{len(audio_files)} uploaded")
    if results['successful'] > 0:
        log(f"🎉 View at: https://sonnix.netlify.app/all-songs")
    
    return results


# Test function
if __name__ == "__main__":
    # Test artist/song extraction
    test_filenames = [
        "Shape of You by Ed Sheeran.mp3",
        "Taylor Swift - Anti-Hero.mp3",
        "Blinding Lights.mp3"
    ]
    
    print("Testing filename parsing:")
    for filename in test_filenames:
        result = extract_artist_and_song_from_filename(filename)
        print(f"  {filename}")
        print(f"    → Song: {result['song']}, Artist: {result['artist']}")
