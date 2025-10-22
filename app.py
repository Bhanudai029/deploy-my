from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import os
from pathlib import Path
from datetime import datetime, timedelta
from youtube_auto_downloader import YouTubeAutoDownloader
from supabase_uploader import SupabaseUploader

app = Flask(__name__)

# Enable CORS for Netlify frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://sonnixmusicsadder.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Global variable to track download status
download_status = {
    'running': False,
    'progress': [],
    'completed': False,
    'results': None
}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """Start download process"""
    global download_status
    
    # Check if already running
    if download_status['running']:
        return jsonify({'error': 'Download already in progress'}), 400
    
    # Get songs from request
    data = request.json
    songs_text = data.get('songs', '')
    
    if not songs_text:
        return jsonify({'error': 'No songs provided'}), 400
    
    # Parse songs (same logic as get_song_list)
    songs = []
    lines = songs_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract song name (remove numbering like "1.", "2.", etc.)
        import re
        match = re.match(r'^\d+\.\s*(.+)$', line)
        if match:
            songs.append(match.group(1).strip())
        else:
            songs.append(line)
    
    if not songs:
        return jsonify({'error': 'No valid songs found'}), 400
    
    # Reset status
    download_status = {
        'running': True,
        'progress': [],
        'completed': False,
        'results': None
    }
    
    # Start download in background thread
    thread = threading.Thread(target=download_songs, args=(songs,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': f'Started downloading {len(songs)} songs'})

@app.route('/status')
def status():
    """Get current download status"""
    return jsonify(download_status)

@app.route('/files')
def list_files():
    """List all files from local storage and Supabase (uploaded in last 24 hours)"""
    try:
        files = []
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Get local files
        audio_folder = Path("Audios")
        if audio_folder.exists():
            for file_path in audio_folder.glob("*.mp3"):
                file_stat = file_path.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time >= cutoff_time:
                    files.append({
                        'name': file_path.name,
                        'size': file_stat.st_size,
                        'uploaded_at': file_time.isoformat(),
                        'location': 'local',
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 2)
                    })
        
        # Get Supabase files
        try:
            SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aekvevvuanwzmjealdkl.supabase.co")
            SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFla3ZldnZ1YW53em1qZWFsZGtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMzExMjksImV4cCI6MjA3MTYwNzEyOX0.PZxoGAnv0UUeCndL9N4yYj0bgoSiDodcDxOPHZQWTxI")
            SUPABASE_AUDIO_BUCKET = os.getenv("SUPABASE_AUDIO_BUCKET", "Sushant-KC more")

            supabase_uploader = SupabaseUploader(SUPABASE_URL, SUPABASE_KEY)

            # List all files in the configured audio bucket (root path)
            bucket_files = supabase_uploader.supabase.storage.from_(SUPABASE_AUDIO_BUCKET).list()

            for file_obj in bucket_files:
                # Prefer created_at, fall back to updated_at/last_accessed_at
                ts = (
                    file_obj.get('created_at')
                    or file_obj.get('updated_at')
                    or file_obj.get('last_accessed_at')
                )
                if ts:
                    try:
                        file_time = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                        file_time = file_time.replace(tzinfo=None)
                    except Exception:
                        # If parsing fails, skip time filter
                        file_time = datetime.now()

                    if file_time >= cutoff_time:
                        file_name = file_obj.get('name', '')
                        public_url = supabase_uploader.get_public_url(file_name, SUPABASE_AUDIO_BUCKET)

                        size_bytes = 0
                        meta = file_obj.get('metadata') or {}
                        if isinstance(meta, dict):
                            size_bytes = meta.get('size', 0)

                        files.append({
                            'name': file_name,
                            'size': size_bytes,
                            'uploaded_at': file_time.isoformat(),
                            'location': 'supabase',
                            'url': public_url,
                            'size_mb': round((size_bytes or 0) / (1024 * 1024), 2)
                        })
        except Exception as e:
            print(f"Error fetching Supabase files: {e}")
        
        # Sort by upload time (newest first)
        files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        
        return jsonify({'files': files})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    """Delete a file from local storage or Supabase"""
    try:
     data = request.json
        file_name = data.get('name', '')
        location = data.get('location', '')
        
        if not file_name or not location:
            return jsonify({'error': 'File name and location required'}), 400
        
        if location == 'local':
            # Delete from local storage
            file_path = Path("Audios") / file_name
            if file_path.exists():
                file_path.unlink()
                return jsonify({'success': True, 'message': f'Deleted {file_name} from local storage'})
            else:
                return jsonify({'error': 'File not found'}), 404
                
        elif location == 'supabase':
            # Delete from Supabase
            try:
                SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aekvevvuanwzmjealdkl.supabase.co")
                SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFla3ZldnZ1YW53em1qZWFsZGtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMzExMjksImV4cCI6MjA3MTYwNzEyOX0.PZxoGAnv0UUeCndL9N4yYj0bgoSiDodcDxOPHZQWTxI")
                SUPABASE_AUDIO_BUCKET = os.getenv("SUPABASE_AUDIO_BUCKET", "Sushant-KC more")

                supabase_uploader = SupabaseUploader(SUPABASE_URL, SUPABASE_KEY)
                supabase_uploader.supabase.storage.from_(SUPABASE_AUDIO_BUCKET).remove([file_name])

                return jsonify({'success': True, 'message': f'Deleted {file_name} from Supabase'})
            except Exception as e:
                return jsonify({'error': f'Supabase deletion failed: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Invalid location'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_songs(songs):
    """Background task to download songs"""
    global download_status
    
    try:
        # Create downloader instance
        download_status['progress'].append('🔧 Initializing downloader...')
        downloader = YouTubeAutoDownloader(audio_folder="Audios")
        
        # Process songs
        download_status['progress'].append(f'🔍 Searching for {len(songs)} songs...')
        video_data = downloader.process_songs(songs)
        
        if video_data:
            # Skip thumbnails
            downloader.skip_thumbnails(video_data)
            
            # Download audio files
            download_status['progress'].append(f'🎵 Downloading audio files...')
            success_count, failed_count, retry_songs = downloader.download_audio_files(video_data)
            
            # Upload to Supabase
            download_status['progress'].append(f'☁️ Uploading to Supabase...')
            upload_success, upload_failed, upload_attempted, public_urls = downloader.upload_all_audio_files(
                total_songs_requested=len(songs),
                successful_downloads=success_count,
                failed_downloads=failed_count,
                retry_songs=retry_songs,
                video_data=video_data
            )
            
            # Store results
            download_status['results'] = {
                'total_songs': len(songs),
                'successful_downloads': success_count,
                'failed_downloads': failed_count,
                'successful_uploads': upload_success,
                'failed_uploads': upload_failed,
                'public_urls': public_urls
            }
            
            download_status['progress'].append('✅ All done!')
        else:
            download_status['progress'].append('❌ No video URLs found')
            download_status['results'] = {
                'error': 'No video URLs extracted'
            }
        
    except Exception as e:
        download_status['progress'].append(f'❌ Error: {str(e)}')
        download_status['results'] = {
            'error': str(e)
        }
    finally:
        download_status['completed'] = True
        download_status['running'] = False

if __name__ == '__main__':
    import os
    import subprocess
    import shutil
    
    # Debug: Check for ffmpeg at startup
    print("\n" + "="*60)
    print("🔍 FFMPEG DETECTION AT STARTUP")
    print("="*60)
    
    ffmpeg_which = shutil.which('ffmpeg')
    print(f"shutil.which('ffmpeg'): {ffmpeg_which}")
    
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        print(f"which ffmpeg: {result.stdout.strip() if result.returncode == 0 else 'NOT FOUND'}")
    except:
        print("which command failed")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"ffmpeg -version: {result.stdout.split(chr(10))[0]}")
        else:
            print("ffmpeg -version failed")
    except Exception as e:
        print(f"ffmpeg -version error: {e}")
    
    print(f"PATH: {os.environ.get('PATH', 'NOT SET')[:200]}...")
    print("="*60 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
