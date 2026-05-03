FROM python:3.12-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs as user 1000 — set this up early
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models at BUILD time so they're baked into the image
# This avoids cold-start timeouts when requests arrive
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && \
    python3 -c "
from transformers import CLIPModel, CLIPProcessor
CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
print('CLIP downloaded successfully')
" && \
    python3 -c "
from faster_whisper import WhisperModel
WhisperModel('base', device='cpu', compute_type='int8')
print('Whisper downloaded successfully')
"

# Copy app source code
COPY . .

# Fix ownership so appuser can write to cache dirs
RUN chown -R appuser:appuser /app /root/.cache 2>/dev/null || true

USER appuser

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Start FastAPI on port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]