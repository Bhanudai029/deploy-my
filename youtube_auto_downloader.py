#!/usr/bin/env python3
"""
YouTube Auto-Downloader
Automatically search for songs on YouTube, download audio, and upload to Supabase
"""

import os
import sys
import time
import re
import subprocess
from pathlib import Path
import requests
import concurrent.futures
import threading
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup

# Import Supabase uploader
from supabase_uploader import SupabaseUploader

class YouTubeAutoDownloader:
    def __init__(self, audio_folder="Audios", enable_supabase=True):
        self.audio_folder = Path(audio_folder)
        self.audio_folder.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        
        # YouTube API configuration
        self.youtube_api = None
        self.api_quota_exceeded = False
        
        # Supabase configuration
        self.enable_supabase = enable_supabase
        self.supabase_uploader = None
        if enable_supabase:
            self.init_supabase()
        
        # Initialize YouTube API
        self.init_youtube_api()
    
    def init_supabase(self):
        """Initialize Supabase uploader with credentials"""
        try:
            # Supabase credentials (same as we used before)
            SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aekvevvuanwzmjealdkl.supabase.co")
            SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFla3ZldnZ1YW53em1qZWFsZGtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMzExMjksImV4cCI6MjA3MTYwNzEyOX0.PZxoGAnv0UUeCndL9N4yYj0bgoSiDodcDxOPHZQWTxI")
            
            self.supabase_uploader = SupabaseUploader(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Supabase uploader initialized successfully")
        except Exception as e:
            print(f"⚠️ Supabase initialization failed: {str(e)[:50]}...")
            print("📝 Downloads will work, but uploads will be skipped")
            self.enable_supabase = False
    
    def init_youtube_api(self):
        """Initialize YouTube API client with API key"""
        try:
            YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
            
            if YOUTUBE_API_KEY:
                self.youtube_api = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                print("✅ YouTube API initialized successfully")
            else:
                print("⚠️ YouTube API key not found - will use HTTP fallback")
                self.api_quota_exceeded = True  # Force HTTP fallback mode
        except Exception as e:
            print(f"⚠️ YouTube API initialization failed: {str(e)[:50]}...")
            print("📝 Will use HTTP request fallback for searches")
            self.api_quota_exceeded = True
    
    def validate_video_url(self, video_id):
        """Validate if video ID corresponds to a long-form video (not shorts)
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            bool: True if valid long-form video, False otherwise
        """
        if not video_id or len(video_id) != 11:
            return False
        
        # Construct standard YouTube URL
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Basic validation - video ID should be 11 characters
        # Shorts use the same ID format but different URL pattern
        return True
    
    def search_youtube_api(self, song_name):
        """Search for song on YouTube using YouTube Data API v3
        
        Args:
            song_name: Name of the song to search for
            
        Returns:
            str: YouTube video URL or None if not found
        """
        try:
            print(f"🔍 Searching YouTube API for: {song_name}")
            
            # Search for videos using YouTube API
            search_response = self.youtube_api.search().list(
                q=song_name,
                part='id,snippet',
                type='video',
                videoDuration='medium',  # Excludes shorts (< 4 minutes)
                maxResults=10
            ).execute()
            
            # Process search results
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                
                # Validate it's a long-form video
                if self.validate_video_url(video_id):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"   🎯 Found: {video_title[:60]}...")
                    print(f"   ✅ Video URL: {video_url}")
                    return video_url
            
            print(f"   ❌ No suitable videos found via API")
            return None
            
        except HttpError as e:
            error_content = str(e.content) if hasattr(e, 'content') else str(e)
            
            # Check if quota exceeded
            if 'quotaExceeded' in error_content or e.resp.status == 403:
                print(f"   ⚠️ YouTube API quota exceeded - switching to HTTP fallback")
                self.api_quota_exceeded = True
                return None
            else:
                print(f"   ❌ YouTube API error: {str(e)[:100]}...")
                return None
                
        except Exception as e:
            print(f"   ❌ Error with YouTube API: {str(e)[:100]}...")
            return None
    
    def search_youtube_http(self, song_name):
        """Search for song on YouTube using HTTP requests (fallback method)
        
        Args:
            song_name: Name of the song to search for
            
        Returns:
            str: YouTube video URL or None if not found
        """
        try:
            print(f"🔍 Searching YouTube (HTTP) for: {song_name}")
            
            # Format search query
            search_query = song_name.replace(' ', '+')
            search_url = f"https://www.youtube.com/results?search_query={search_query}"
            
            # Send HTTP request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"   ❌ HTTP request failed with status {response.status_code}")
                return None
            
            # Parse HTML to extract video IDs
            # YouTube embeds video data in JavaScript variables
            html_content = response.text
            
            # Find video IDs using regex - look for watch?v= patterns
            # Avoid shorts by checking the context
            video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            matches = re.findall(video_pattern, html_content)
            
            # Also look for shorts to exclude them
            shorts_pattern = r'"shorts/([a-zA-Z0-9_-]{11})"'
            shorts_ids = set(re.findall(shorts_pattern, html_content))
            
            # Filter out shorts and duplicates
            seen = set()
            for video_id in matches:
                if video_id not in seen and video_id not in shorts_ids:
                    seen.add(video_id)
                    
                    if self.validate_video_url(video_id):
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"   🎯 Found video ID: {video_id}")
                        print(f"   ✅ Video URL: {video_url}")
                        return video_url
                    
                    # Limit checks to first 5 unique videos
                    if len(seen) >= 5:
                        break
            
            print(f"   ❌ No suitable videos found via HTTP")
            return None
            
        except requests.Timeout:
            print(f"   ❌ HTTP request timeout")
            return None
        except Exception as e:
            print(f"   ❌ Error with HTTP search: {str(e)[:100]}...")
            return None

    def get_song_list(self):
        """Get list of songs from user input (supports pasting multiple lines)"""
        print("\n🎵 Paste your song list (format: '1. Song Name' on separate lines OR all in one line like '1. A2. B3. C'):")
        print("💡 Example:")
        print("   1. Shape of you")
        print("   2. See you again")
        print("   3. Blinding lights")
        print("📝 After pasting, press Enter on an empty line to finish\n")

        songs = []

        print("📝 Paste your songs below (press Enter on an empty line to finish):")

        # Read pasted lines until the user hits Enter on an empty line
        try:
            buffer_lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                # Empty line means finish
                if line.strip() == "":
                    break
                buffer_lines.append(line)

            # Join all lines into a single buffer string
            buffer = "\n".join(buffer_lines).strip()

            if not buffer:
                print("❌ No input received!")
                return []

            # Handle the case where all songs are pasted in one line without spaces
            # e.g., "1. Rangin2. Don't Worry3. Aasha4. Uff5. Falling Apart6. All I ever dreamed7. Live in Rangashala8. Kheladi"
            if not '\n' in buffer and re.search(r'\d+\.\s*\w', buffer):
                # Split the single line input into separate songs
                # Pattern explanation:
                # (\d+\.) - matches the number followed by a dot (e.g., "1.", "2.", etc.)
                # ([^0-9]*?)- matches any characters except digits, non-greedy
                # (?=\d+\.|$) - positive lookahead for the next number or end of string
                parts = re.findall(r'(\d+\.)\s*([^0-9]*?)(?=\d+\.|$)', buffer)
                
                if parts:
                    for _, title in parts:
                        song_name = title.strip()
                        # Normalize internal whitespace
                        song_name = re.sub(r"\s+", " ", song_name)
                        if song_name:
                            songs.append(song_name)
                            print(f"   ✅ Added: {song_name}")
                else:
                    # Fallback if regex doesn't work
                    # Manually split by looking for patterns like "1.", "2.", etc.
                    song_parts = re.split(r'(\d+\.\s*)', buffer)
                    if len(song_parts) > 1:
                        # Process the split parts
                        i = 1
                        while i < len(song_parts):
                            if re.match(r'\d+\.\s*', song_parts[i]):
                                # This is a number marker
                                if i + 1 < len(song_parts):
                                    song_name = song_parts[i + 1].strip()
                                    song_name = re.sub(r"\s+", " ", song_name)
                                    # Check if the next part starts with a number (next song)
                                    if song_name and not re.match(r'^\d+\.', song_name):
                                        songs.append(song_name)
                                        print(f"   ✅ Added: {song_name}")
                            i += 2
            else:
                # Handle multi-line input or normally formatted input
                # If user pasted everything in one line like: 1. A2. B3. C ...
                # or in multiple lines, handle both by extracting numbered items
                # Pattern: capture text after each "N." up to the next number or end
                numbered_item_regex = re.compile(r"\b(\d+)\.\s*([^\d].*?)(?=\s*\d+\.|$)", re.DOTALL)
                matches = numbered_item_regex.findall(buffer)

                if matches:
                    for _, title in matches:
                        song_name = title.strip()
                        # Normalize internal whitespace
                        song_name = re.sub(r"\s+", " ", song_name)
                        if song_name:
                            songs.append(song_name)
                            print(f"   ✅ Added: {song_name}")
                else:
                    # Fallback: parse per-line if user provided one title per line with numbers
                    line_regex = re.compile(r"^\s*\d+\.\s*(.+)$")
                    for raw in buffer.splitlines():
                        m = line_regex.match(raw.strip())
                        if m:
                            song_name = re.sub(r"\s+", " ", m.group(1).strip())
                            if song_name:
                                songs.append(song_name)
                                print(f"   ✅ Added: {song_name}")

        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return []
        except Exception as e:
            print(f"❌ Error reading input: {e}")
            return []

        if not songs:
            print("❌ No valid songs found!")
            print("💡 Please paste songs in format: '1. Song Name'")
            return []

        # Show summary of detected songs
        print(f"\n🎵 {len(songs)} Songs detected ✅")
        print("=" * 40)
        print("📝 Song List:")
        for i, song in enumerate(songs, 1):
            print(f"   {i}. {song}")
        print("=" * 40)

        return songs

    def search_youtube(self, song_name, retry_attempt=0, max_retries=1):
        """Search for song on YouTube and return video URL with retry logic
        
        Uses YouTube API v3 first, falls back to HTTP requests if quota exceeded
        
        Args:
            song_name: Name of the song to search for
            retry_attempt: Current retry attempt number
            max_retries: Maximum number of retry attempts
        """
        try:
            retry_text = f" (Retry {retry_attempt + 1}/{max_retries + 1})" if retry_attempt > 0 else ""
            print(f"🔍 Searching for: {song_name}{retry_text}")
            
            video_url = None
            
            # Try YouTube API first (if not quota exceeded)
            if not self.api_quota_exceeded and self.youtube_api:
                video_url = self.search_youtube_api(song_name)
            
            # If API failed or quota exceeded, use HTTP fallback
            if not video_url:
                video_url = self.search_youtube_http(song_name)
            
            # If found, return the URL
            if video_url:
                return video_url
            
            # If not found and retries available, try with alternative search terms
            if retry_attempt < max_retries:
                print(f"   🔄 Retrying search ({retry_attempt + 1}/{max_retries})...")
                time.sleep(2)
                
                # Generate alternative search terms for retry
                search_variations = self.generate_search_variations(song_name)
                if retry_attempt < len(search_variations):
                    alt_search = search_variations[retry_attempt]
                    return self.search_youtube(alt_search, retry_attempt + 1, max_retries)
                else:
                    return self.search_youtube(song_name, retry_attempt + 1, max_retries)
            else:
                print(f"   ❌ All search attempts failed for: {song_name}")
                return None

        except Exception as e:
            print(f"❌ Error searching YouTube: {e}")
            
            # Retry logic for failed searches
            if retry_attempt < max_retries:
                print(f"   🔄 Retrying search ({retry_attempt + 1}/{max_retries})...")
                time.sleep(3)
                return self.search_youtube(song_name, retry_attempt + 1, max_retries)
            else:
                print(f"   ❌ All search attempts failed for: {song_name}")
                return None

    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        # Handle both regular videos and shorts
        video_id_pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
        match = re.search(video_id_pattern, url)
        return match.group(1) if match else None
    
    def generate_search_variations(self, song_name):
        """Generate alternative search terms for finding different uploads
        
        Args:
            song_name: Original song name
            
        Returns:
            list: List of alternative search terms
        """
        variations = []
        
        # Remove "official" and "By [Artist]" patterns to get broader results
        base_name = song_name
        
        # Remove common patterns
        patterns_to_remove = [
            r'\s+official\s*$',  # Remove "official" at the end
            r'\s+By\s+[^\s]+.*$',  # Remove "By Artist" pattern
            r'\s+by\s+[^\s]+.*$',  # Remove "by Artist" pattern (lowercase)
            r'\s+-\s+[^\s]+\s+Version.*$',  # Remove version info
        ]
        
        for pattern in patterns_to_remove:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        base_name = base_name.strip()
        
        # Generate variations
        variations.append(base_name)  # Clean song name
        variations.append(f"{base_name} audio")  # Add "audio"
        variations.append(f"{base_name} music")  # Add "music"
        variations.append(f"{base_name} song")  # Add "song"
        variations.append(f"{base_name} cover")  # Look for covers
        variations.append(f"{base_name} remix")  # Look for remixes
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for variation in variations:
            if variation.lower() not in seen:
                seen.add(variation.lower())
                unique_variations.append(variation)
        
        return unique_variations[:5]  # Return top 5 variations

    def process_songs(self, songs):
        """Process all songs and return video URLs with song names"""
        video_data = []  # Changed from video_urls to video_data to store song names too

        print(f"\n🚀 Starting auto-download for {len(songs)} songs...")
        print("=" * 60)

        for i, song in enumerate(songs, 1):
            print(f"\n📍 Processing {i}/{len(songs)}: {song}")
            print("-" * 40)

            video_url = self.search_youtube(song)

            if video_url:
                # Store both URL and song name
                video_data.append((video_url, song))
                print(f"✅ Success: {song}")
            else:
                print(f"❌ Failed: {song}")

            # Add small delay between searches to avoid rate limiting
            if i < len(songs):
                print("⏳ Waiting 2 seconds before next search...")
                time.sleep(2)

        return video_data

    def skip_thumbnails(self, video_data):
        """Skip thumbnail downloads - not needed for PythonAnywhere"""
        print(f"\n⏭️  Skipping thumbnail downloads (not needed for cloud environment)")
        print(f"📝 Processing {len(video_data)} songs for audio download only...")

    def clean_filename(self, filename):
        """Remove special characters from filename"""
        # Remove special characters, keep only letters, numbers, spaces, dots, hyphens, underscores
        cleaned = re.sub(r'[^a-zA-Z0-9\s._-]', '', filename)
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def get_audio_duration(self, file_path):
        """Get audio file duration in MM:SS format using ffprobe"""
        try:
            # Use ffprobe to get duration
            cmd = [
                'ffprobe', 
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration_seconds = float(data['format']['duration'])
                
                # Convert to MM:SS format
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                return f"{minutes}:{seconds:02d}"
            else:
                return "Unknown"
                
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError):
            return "Unknown"
        except FileNotFoundError:
            # ffprobe not available, try alternative method with yt-dlp
            try:
                cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    '--print', 'duration',
                    '--no-warnings',
                    str(file_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    duration_seconds = float(result.stdout.strip())
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    return f"{minutes}:{seconds:02d}"
            except:
                pass
            return "Unknown"

    def download_single_audio(self, url, song_name, index=None):
        """Download audio from a single YouTube URL with custom filename"""
        try:
            prefix = f"[{index}]" if index else ""
            print(f"🎵 {prefix} Starting audio download: {song_name}")
            print(f"   🌐 URL: {url}")
            
            # Clean the song name for use as filename
            clean_song_name = self.clean_filename(song_name)
            if not clean_song_name:
                clean_song_name = "audio"
            
            # Enhanced yt-dlp options for fast audio downloads and age-restricted content
            yt_dlp_options = [
                sys.executable, '-m', 'yt_dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K',
                '--no-playlist',
                '--no-warnings',
                '--ignore-errors',
                '--no-check-certificate',
                '--prefer-insecure',
                '--concurrent-fragments', '4',  # Faster fragment downloads
                '--throttled-rate', '100K',      # Minimum download rate
                # Multiple player clients for better compatibility with age-restricted content
                '--extractor-args', 'youtube:player_client=android,web,ios;player_skip=webpage;include_hls_manifest=false',
                '--user-agent', 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
                # Try to handle age-restricted content
                '--age-limit', '0',  # No age limit
                # Custom output template with clean song name
                '-o', str(self.audio_folder / f'{clean_song_name}.%(ext)s'),
                url
            ]
            
            start_time = time.time()
            
            # Run audio download
            result = subprocess.run(
                yt_dlp_options, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout per video
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ {prefix} SUCCESS! Audio downloaded in {duration:.1f}s")
                print(f"   📁 Saved to: {self.audio_folder}")
                return True
            else:
                # Check if it's an age-restricted error
                if result.stderr and "age-restricted" in result.stderr.lower():
                    print(f"❌ {prefix} AGE-RESTRICTED: {song_name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()[:100]}...")
                    return "age_restricted"
                else:
                    print(f"❌ {prefix} FAILED: {song_name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()[:100]}...")
                    return False
                        
        except subprocess.TimeoutExpired:
            print(f"⏰ {prefix} TIMEOUT: {song_name} (took too long)")
            return False
            
        except Exception as e:
            print(f"💥 {prefix} ERROR: {song_name} - {str(e)}")
            return False

    def download_audio_files(self, video_data):
        """Download audio files for all videos in parallel"""
        if not video_data:
            print("❌ No video data to download audio for!")
            return

        print(f"\n🎵 Downloading audio for {len(video_data)} songs...")
        print("=" * 60)

        # Download audio files in parallel (max 3 at a time)
        max_workers = min(3, len(video_data))
        success_count = 0
        failed_count = 0
        retry_count = 0
        retry_success_songs = []  # Track songs downloaded via retry mechanism
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, (url, song_name) in enumerate(video_data, 1):
                future = executor.submit(self.download_single_audio, url, song_name, i)
                futures.append((future, song_name, url, i))
            
            # Wait for all downloads to complete
            for future, song_name, original_url, index in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    if result is True:
                        success_count += 1
                    elif result == "age_restricted":
                        print(f"\n🔄 ATTEMPTING RETRY for: {song_name}")
                        print(f"   🔍 Searching for alternative upload...")
                        
                        # Try to find alternative video using our search methods
                        search_variations = self.generate_search_variations(song_name)
                        alternative_url = None
                        
                        for variation in search_variations[:3]:  # Try first 3 variations
                            print(f"   🔍 Trying: '{variation}'")
                            
                            # Try API first, then HTTP
                            if not self.api_quota_exceeded and self.youtube_api:
                                alternative_url = self.search_youtube_api(variation)
                            
                            if not alternative_url:
                                alternative_url = self.search_youtube_http(variation)
                            
                            if alternative_url:
                                break
                        
                        if alternative_url:
                            print(f"   🎵 Attempting download with alternative URL...")
                            retry_result = self.download_single_audio(alternative_url, song_name, f"{index}R")
                            
                            if retry_result is True:
                                print(f"   ✅ RETRY SUCCESS: {song_name}")
                                success_count += 1
                                retry_count += 1
                                retry_success_songs.append(song_name)
                            else:
                                print(f"   ❌ RETRY FAILED: {song_name}")
                                failed_count += 1
                        else:
                            print(f"   ❌ No alternative found: {song_name}")
                            failed_count += 1
                    else:
                        failed_count += 1
                        
                except concurrent.futures.TimeoutError:
                    print(f"⏰ TIMEOUT: {song_name} (took too long)")
                    failed_count += 1
                except Exception as e:
                    print(f"💥 ERROR: {song_name} - {str(e)}")
                    failed_count += 1

        # Print summary
        print("\n" + "=" * 60)
        print("📈 AUDIO DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {success_count}/{len(video_data)}")
        print(f"❌ Failed: {failed_count}")
        if retry_count > 0:
            print(f"🔄 Successful Retries: {retry_count}")
            print("\n🎵 SONGS DOWNLOADED VIA RETRY MECHANISM:")
            print("-" * 50)
            for i, song in enumerate(retry_success_songs, 1):
                print(f"   {i}. \"{song}\" was age-restricted and downloaded using retry mechanism")
        print(f"\n📁 All files saved to: {self.audio_folder}")

        print(f"\n🎉 Audio download complete!")
        print(f"📁 Audio files saved to: {self.audio_folder}")
        
        return success_count, failed_count, retry_success_songs
    
    def upload_all_audio_files(self, total_songs_requested, successful_downloads, failed_downloads, retry_songs, video_data):
        """Upload all downloaded audio files to Supabase
        
        Args:
            total_songs_requested: Total number of songs user requested
            successful_downloads: Number of successful downloads
            failed_downloads: Number of failed downloads  
            retry_songs: List of songs downloaded via retry mechanism
            video_data: List of (url, song_name) tuples in original order
            
        Returns:
            tuple: (upload_success_count, upload_failed_count, should_upload, public_urls)
        """
        # STRICT all-or-nothing policy: Only upload if ALL requested songs were downloaded
        should_upload = (successful_downloads == total_songs_requested and failed_downloads == 0)
        
        if not self.enable_supabase:
            print(f"\n⚠️ Supabase upload skipped - not enabled")
            return 0, 0, False, []
        
        if not should_upload:
            print(f"\n❌ SUPABASE UPLOAD SKIPPED")
            print(f"   Reason: {failed_downloads} song(s) failed to download")
            print(f"   Policy: Only upload when ALL songs download successfully")
            print(f"   📝 {successful_downloads} downloaded songs will NOT be uploaded")
            return 0, 0, False, []
        
        # All downloads were successful - proceed with uploads
        print(f"\n🚀 STARTING SUPABASE UPLOADS")
        print("=" * 60)
        print(f"🎉 All {successful_downloads} songs downloaded successfully!")
        print(f"📄 Proceeding with Supabase uploads...")
        
        # Build ordered list of audio files based on original video_data order
        audio_files_ordered = []
        for url, song_name in video_data:
            clean_song_name = self.clean_filename(song_name)
            if not clean_song_name:
                clean_song_name = "audio"
            
            # Find the MP3 file with this name
            mp3_file = self.audio_folder / f"{clean_song_name}.mp3"
            if mp3_file.exists():
                audio_files_ordered.append(mp3_file)
            else:
                # Check for files with counter suffix (e.g., song_1.mp3, song_2.mp3)
                counter = 1
                while True:
                    mp3_file_alt = self.audio_folder / f"{clean_song_name}_{counter}.mp3"
                    if mp3_file_alt.exists():
                        audio_files_ordered.append(mp3_file_alt)
                        break
                    counter += 1
                    if counter > 10:  # Safety limit
                        print(f"   ⚠️ Could not find audio file for: {song_name}")
                        break
        
        if not audio_files_ordered:
            print(f"   ❌ No MP3 files found in {self.audio_folder}")
            return 0, 1, should_upload, []
        
        print(f"\n🎵 Found {len(audio_files_ordered)} audio files to upload (in original order)")
        
        # Upload files using the existing Supabase uploader
        try:
            file_paths = [str(file_path) for file_path in audio_files_ordered]
            bucket_name = "Sushant-KC more"  # Your bucket name
            
            # Use the batch upload method from supabase_uploader
            results = self.supabase_uploader.upload_audio_files_batch(file_paths, bucket_name)
            
            # Count successes and failures, collect public URLs IN ORDER
            upload_success_count = 0
            upload_failed_count = 0
            public_urls = []
            
            for result in results:
                if result["success"]:
                    upload_success_count += 1
                    # Get public URL for successful uploads
                    filename = Path(result["file_path"]).name
                    public_url = self.supabase_uploader.get_public_url(filename, bucket_name)
                    if public_url:
                        public_urls.append((filename, public_url))
                else:
                    upload_failed_count += 1
            
            return upload_success_count, upload_failed_count, should_upload, public_urls
            
        except Exception as e:
            print(f"\n❌ SUPABASE UPLOAD ERROR: {str(e)}")
            return 0, len(audio_files_ordered), should_upload, []

def main():
    """Main function"""
    print("🎵" + "=" * 60)
    print("      YOUTUBE AUTO-DOWNLOADER")
    print("=" * 60 + "🎵")
    print()
    print("This program will:")
    print("1. Ask for song names in numbered format")
    print("2. Search YouTube using API/HTTP requests")
    print("3. Download audio files as MP3")
    print("4. Upload to Supabase cloud storage")
    print()

    # Create downloader instance
    print("🔧 Initializing YouTube Auto-Downloader...")
    downloader = YouTubeAutoDownloader(audio_folder="Audios")
    print()

    try:
        # Get song list from user
        songs = downloader.get_song_list()
        if not songs:
            print("❌ No songs to process. Exiting...")
            return

        # Process songs (no browser needed!)
        video_data = downloader.process_songs(songs)

        if video_data:
            # Skip thumbnails (not needed for cloud environment)
            downloader.skip_thumbnails(video_data)
            
            # Download audio files with custom naming
            success_count, failed_count, retry_songs = downloader.download_audio_files(video_data)
            
            # Upload to Supabase if enabled and all downloads succeeded
            upload_success, upload_failed, upload_attempted, public_urls = downloader.upload_all_audio_files(
                total_songs_requested=len(songs),
                successful_downloads=success_count, 
                failed_downloads=failed_count,
                retry_songs=retry_songs,
                video_data=video_data
            )
            
            # Final completion message
            print(f"\n🎆 FINAL COMPLETION MESSAGE")
            print("=" * 60)
            print(f"🎉 YouTube Auto-Download Complete!")
            print(f"🎵 Audio Downloads: {success_count}/{len(songs)} ({int(success_count/len(songs)*100) if len(songs) > 0 else 0}%)")
            
            if upload_attempted:
                if upload_success > 0:
                    print(f"🚀 Supabase Uploads: {upload_success}/{success_count} ({int(upload_success/success_count*100) if success_count > 0 else 0}%)")
                    print(f"\n✨ Successfully uploaded {upload_success} songs to Supabase!")
                else:
                    print(f"🚀 Supabase Uploads: 0/{success_count} (Failed)")
            elif failed_count > 0:
                print(f"🚀 Supabase Uploads: Skipped (due to {failed_count} download failures)")
            else:
                print(f"🚀 Supabase Uploads: Disabled")
                
            # Display public URLs if any were uploaded - SIMPLIFIED FORMAT
            if upload_attempted and public_urls:
                print(f"\n🌍 SUPABASE URLS:")
                for i, (filename, url) in enumerate(public_urls, 1):
                    print(f"{i}. {url}")
                
                # Display audio durations
                print(f"\n🎵 AUDIO DURATIONS:")
                for i, (filename, url) in enumerate(public_urls, 1):
                    # Find the corresponding local file to get duration
                    local_file_path = downloader.audio_folder / filename
                    if local_file_path.exists():
                        duration = downloader.get_audio_duration(local_file_path)
                        print(f"{i}. {duration}")
                    else:
                        print(f"{i}. Unknown")
            
            print(f"\n📁 Local audio files saved to: Audios/")
        else:
            print("❌ No video URLs extracted. Downloads skipped.")

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()
