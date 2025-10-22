#!/usr/bin/env bash
# Build script for Render.com deployment

set -o errexit

echo "📦 Build script starting..."

# Create necessary directories
echo "📁 Creating download directories..."
mkdir -p thumbnails
mkdir -p Audios

# Ensure ffmpeg exists on PATH if platform didn't add it
if ! command -v ffmpeg >/dev/null 2>&1; then
  if [ -x "/usr/bin/ffmpeg" ]; then
    export PATH="/usr/bin:$PATH"
  elif [ -x "/nix/store" ]; then
    # try common nix locations
    FFMPEG_BIN=$(command -v /nix/store/*-ffmpeg-*/bin/ffmpeg 2>/dev/null | head -n1)
    if [ -n "$FFMPEG_BIN" ]; then
      export PATH="$(dirname "$FFMPEG_BIN"):$PATH"
    fi
  fi
fi

echo "✅ Build complete!"
