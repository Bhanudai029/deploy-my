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
  for p in /usr/bin/ffmpeg /usr/local/bin/ffmpeg /nix/store/*-ffmpeg-*/bin/ffmpeg; do
    if [ -x "$p" ]; then
      export PATH="$(dirname "$p"):$PATH"
      break
    fi
  done
fi

echo "✅ Build complete!"
