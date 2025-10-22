from flask import Flask, render_template, request, jsonify
import threading
from youtube_auto_downloader import YouTubeAutoDownloader

app = Flask(__name__)

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
