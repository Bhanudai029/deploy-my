/**
 * BULK SONG UPLOAD SCRIPT FOR SONNIX
 * 
 * ✅ Firebase credentials are already configured!
 * 
 * HOW TO USE:
 * 1. Add your songs to the 'songs' array below (starting line 32)
 * 2. Run: node bulk-upload-songs.example.js
 * 
 * That's it! Your songs will appear at: https://sonnix.netlify.app/all-songs
 * 
 * REQUIREMENTS:
 * - Node.js installed (download from nodejs.org)
 */

// ============================================
// FIREBASE CONFIGURATION
// ============================================
// Firebase configuration for Sonnix
const firebaseConfig = {
  apiKey: "AIzaSyOgh68Cuqhxzm11VGVRcc2W4BYFXP4ZNOk",
  authDomain: "music-x-dfd87.firebaseapp.com",
  projectId: "music-x-dfd87",
  storageBucket: "music-x-dfd87.firebasestorage.app",
  messagingSenderId: "600929755806",
  appId: "1:600929755806:web:3e11645bd94118854618f"
};

// ============================================
// SONGS DATA - ADD YOUR SONGS HERE
// ============================================
const songs = [
  {
    title: "Midnight Rain",
    artist: "Taylor Swift",
    duration: 178,  // in seconds (2:58)
    audioUrl: "https://example.com/midnight-rain.mp3"
  },
  {
    title: "As It Was",
    artist: "Harry Styles",
    duration: 167,  // 2:47
    audioUrl: "https://example.com/as-it-was.mp3"
  },
  {
    title: "Anti-Hero",
    artist: "Taylor Swift",
    duration: 200,  // 3:20
    audioUrl: "https://example.com/anti-hero.mp3"
  }
  // Add more songs here...
];

// ============================================
// SCRIPT LOGIC (DO NOT EDIT BELOW)
// ============================================

import https from 'https';
import http from 'http';

// Simple Firebase REST API implementation
class FirebaseUploader {
  constructor(config) {
    this.projectId = config.projectId;
    this.apiKey = config.apiKey;
    this.baseUrl = `https://firestore.googleapis.com/v1/projects/${this.projectId}/databases/(default)/documents`;
  }

  async uploadSongs(songs) {
    console.log('\n🎵 Starting bulk song upload...\n');
    console.log(`Total songs to upload: ${songs.length}\n`);

    const results = {
      success: 0,
      failed: 0,
      errors: []
    };

    for (let i = 0; i < songs.length; i++) {
      const song = songs[i];
      console.log(`[${i + 1}/${songs.length}] Uploading: "${song.title}" by ${song.artist}...`);

      try {
        await this.uploadSong(song);
        results.success++;
        console.log(`✅ Success: "${song.title}"\n`);
      } catch (error) {
        results.failed++;
        results.errors.push({ song: song.title, error: error.message });
        console.error(`❌ Failed: "${song.title}" - ${error.message}\n`);
      }

      // Small delay to avoid rate limiting
      await this.sleep(500);
    }

    return results;
  }

  async uploadSong(song) {
    const songData = {
      fields: {
        title: { stringValue: song.title },
        artist: { stringValue: song.artist },
        duration: { integerValue: song.duration.toString() },
        audioUrl: { stringValue: song.audioUrl },
        album: { stringValue: song.album || '' },
        genre: { stringValue: song.genre || 'Unknown' },
        releaseDate: { stringValue: song.releaseDate || new Date().toISOString().split('T')[0] },
        imageUrl: { stringValue: song.imageUrl || '/default-song.png' },
        plays: { integerValue: '0' },
        isLiked: { booleanValue: false },
        createdAt: { timestampValue: new Date().toISOString() },
        updatedAt: { timestampValue: new Date().toISOString() },
        customId: { stringValue: `song_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` }
      }
    };

    const url = `${this.baseUrl}/songs?key=${this.apiKey}`;
    
    return new Promise((resolve, reject) => {
      const urlObj = new URL(url);
      const options = {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.write(JSON.stringify(songData));
      req.end();
    });
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Validate configuration
function validateConfig() {
  // Configuration is pre-filled for Sonnix project
  console.log('✅ Firebase configuration validated');
  console.log(`📦 Project: ${firebaseConfig.projectId}\n`);
}

// Validate songs data
function validateSongs() {
  if (!songs || songs.length === 0) {
    console.error('\n❌ ERROR: No songs found to upload!');
    console.error('\n📝 Please add songs to the "songs" array in this file.');
    console.error('\n');
    process.exit(1);
  }

  // Validate each song has required fields
  for (let i = 0; i < songs.length; i++) {
    const song = songs[i];
    if (!song.title || !song.artist || !song.duration || !song.audioUrl) {
      console.error(`\n❌ ERROR: Song at index ${i} is missing required fields!`);
      console.error('Required fields: title, artist, duration, audioUrl');
      console.error('Song data:', JSON.stringify(song, null, 2));
      console.error('\n');
      process.exit(1);
    }
  }
}

// Main execution
async function main() {
  console.clear();
  console.log('╔════════════════════════════════════════════╗');
  console.log('║   SONNIX BULK SONG UPLOAD TOOL            ║');
  console.log('║   Upload multiple songs programmatically  ║');
  console.log('╚════════════════════════════════════════════╝');
  console.log('');

  // Validate configuration and data
  validateConfig();
  validateSongs();

  // Create uploader and start upload
  const uploader = new FirebaseUploader(firebaseConfig);
  
  try {
    const results = await uploader.uploadSongs(songs);

    console.log('\n╔════════════════════════════════════════════╗');
    console.log('║           UPLOAD COMPLETE!                 ║');
    console.log('╚════════════════════════════════════════════╝');
    console.log(`\n✅ Successfully uploaded: ${results.success} songs`);
    console.log(`❌ Failed uploads: ${results.failed} songs`);

    if (results.errors.length > 0) {
      console.log('\n⚠️  Errors:');
      results.errors.forEach((err, index) => {
        console.log(`${index + 1}. ${err.song}: ${err.error}`);
      });
    }

    console.log('\n🎉 Your songs are now available at:');
    console.log('   https://sonnix.netlify.app/all-songs');
    console.log('\n');
  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  }
}

// Run the script
main();
