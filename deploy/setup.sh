#!/usr/bin/env bash
# deploy/setup.sh — One-shot setup for the Video Metadata Generator
# Run with: bash deploy/setup.sh
set -e   # Exit immediately on any error

# ─────────────────────────────────────────────────────────────────
# 1. Welcome banner
# ─────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🎬  Video Metadata Generator — Setup                  ║"
echo "║   Powered by Whisper · CLIP · YOLO · Gemini API         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────
# 2. Update apt package lists (silently)
# ─────────────────────────────────────────────────────────────────
echo "📦  Updating package lists..."
sudo apt-get update -qq

# ─────────────────────────────────────────────────────────────────
# 3. Install ffmpeg
# ─────────────────────────────────────────────────────────────────
echo "🎞️   Installing ffmpeg..."
sudo apt-get install -y ffmpeg
echo "✅  ffmpeg installed: $(ffmpeg -version 2>&1 | head -1)"
echo ""

# ─────────────────────────────────────────────────────────────────
# 4. Install Python dependencies
# ─────────────────────────────────────────────────────────────────
echo "🐍  Installing Python packages from requirements.txt..."
pip install -r requirements.txt
echo ""
echo "✅  Python packages installed."
echo ""

# ─────────────────────────────────────────────────────────────────
# 5. Configure .env
# ─────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️   Please edit .env and add your GEMINI_API_KEY before starting the server."
    else
        echo "⚠️   No .env or .env.example found."
        echo "     Create a .env file with: GEMINI_API_KEY=your_key_here"
    fi
else
    echo "✅  .env already configured."
fi
echo ""

# ─────────────────────────────────────────────────────────────────
# 6. Pre-download YOLO nano model
# ─────────────────────────────────────────────────────────────────
echo "🤖  Pre-downloading YOLO nano model (yolov8n.pt)..."
python3 -c "
from ultralytics import YOLO
YOLO('yolov8n.pt')
print('YOLO model ready.')
"
echo ""

# ─────────────────────────────────────────────────────────────────
# 7. Pre-download CLIP model
# ─────────────────────────────────────────────────────────────────
echo "🔍  Pre-downloading CLIP model (openai/clip-vit-base-patch32)..."
python3 -c "
from transformers import CLIPModel, CLIPProcessor
CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
print('CLIP model ready.')
"
echo ""

# ─────────────────────────────────────────────────────────────────
# 8. Done!
# ─────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✅  Setup complete!                                    ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║   ▶   Start server:                                      ║"
echo "║       uvicorn main:app --reload --host 0.0.0.0 --port 8000║"
echo "║                                                          ║"
echo "║   📖  Then open the Ports tab in Codespaces and click   ║"
echo "║       the link for port 8000                             ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""