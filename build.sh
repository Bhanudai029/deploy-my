#!/usr/bin/env bash
# Build script for Render.com deployment

set -o errexit

echo "📦 Build script starting..."

# Create necessary directories
echo "📁 Creating download directories..."
mkdir -p thumbnails
mkdir -p Audios

echo "✅ Build complete!"
