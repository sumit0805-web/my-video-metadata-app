---
title: Video Metadata Generator
emoji: 🎬
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# Video Metadata Generator

A multimodal FastAPI backend that generates rich metadata from video files.

## Models Used
- **faster-whisper** (base) — audio transcription
- **CLIP** (openai/clip-vit-base-patch32) — visual embeddings
- **YOLOv8 nano** — object detection

## API Docs
Once deployed, visit `/docs` for the interactive Swagger UI.

## Health Check
`GET /health` → `{"status": "ok", "version": "1.0.0"}`





# 🎬 Video Metadata Generator

> Upload a video (or paste a YouTube URL) and get 5 viral Shorts titles, an SEO description, tags, and hashtags — powered by Whisper, CLIP, YOLO, and Google Gemini.

---

## 🗺️ How It Works

```
  Video File / YouTube URL
           ↓
        FFmpeg
       ↙      ↘
    Audio     Frames (1 per 2s)
      ↓            ↓
   Whisper     CLIP + YOLO
      ↓            ↓
  Transcript  Visual Summary
          ↘  ↙
         Gemini API
              ↓
      JSON Metadata Output
  (5 Titles · Description · Tags · Hashtags)
```

---

## ✨ Features

- **Automatic transcription** — Whisper converts speech to text, no subtitles needed
- **Visual scene understanding** — CLIP identifies what's happening; YOLO detects objects
- **Viral title generation** — Gemini writes 5 hook-driven YouTube Shorts titles
- **SEO-optimised description** — 150-200 words, keyword-rich, ends with a call to action
- **Ready-to-paste tags & hashtags** — 10 tags + 10 hashtags, always includes #Shorts
- **YouTube URL support** — paste a link instead of uploading a file
- **100% CPU** — no GPU required, runs on any machine or cloud VM
- **Interactive Swagger UI** — test the API from a browser, no code needed

---

## 🚀 Setup Guide (GitHub Codespaces)

This guide is written for someone on a **tablet** with **no terminal experience**. Follow every step in order.

---

### Step 1 — Sign in to GitHub

Go to [github.com](https://github.com) and sign in. If you don't have an account, create one (it's free).

---

### Step 2 — Open the Repository in Codespaces

1. Open this repository in your browser.
2. Click the big green **"Code"** button near the top right of the page.
3. Click the **"Codespaces"** tab.
4. Click **"Create codespace on main"**.
5. Wait about 60 seconds — Codespaces will open a full VS Code editor inside your browser tab.

> 💡 You don't need to install anything on your tablet. Everything runs in the cloud.

---

### Step 3 — Open the Terminal

In the Codespaces editor:

- Click **Terminal** in the top menu bar.
- Click **New Terminal**.

A black panel will appear at the bottom of the screen. This is where you type commands.

---

### Step 4 — Run the Setup Script

Type or paste this into the terminal, then press **Enter**:

```bash
bash deploy/setup.sh
```

This will:
- Install ffmpeg
- Install all Python packages
- Download the YOLO and CLIP models (~200 MB total)

It takes **3–8 minutes** depending on internet speed. You'll see progress messages. Wait until you see **"✅ Setup complete!"** before moving on.

---

### Step 5 — Add Your Gemini API Key

You need a free Google Gemini API key.

**Get your key:**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account.
3. Click **"Get API key"** → **"Create API key"**.
4. Copy the key (it starts with `AIza...`).

**Add the key to the project:**
1. In the left sidebar of Codespaces, find and click the file named **`.env`**.
2. You'll see a line that looks like: `GEMINI_API_KEY=your_key_here`
3. Replace `your_key_here` with the key you just copied.
4. Save the file: press **Ctrl+S** (Windows/Linux) or **Cmd+S** (Mac/iPad).

> ⚠️ Never share your `.env` file or commit it to GitHub. It contains your private key.

---

### Step 6 — Start the Server

In the terminal, type:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You'll see output ending with:

```
INFO:     Application startup complete.
```

The server is now running. **Leave this terminal open** — closing it stops the server.

---

### Step 7 — Open the API in Your Browser

1. Look at the bottom of the Codespaces window for a **"Ports"** tab.
2. Click it.
3. Find the row with port **8000**.
4. Click the **globe icon** 🌐 on that row.

A new browser tab opens showing `{"status": "running"}`. The API is live!

---

### Step 8 — Test with Swagger UI

In the browser tab that just opened, add `/docs` to the end of the URL:

```
https://your-codespace-url.app.github.dev/docs
```

This opens **Swagger UI** — a visual interface to test the API without writing any code.

**To test a video upload:**
1. Click **POST /process-video**.
2. Click **"Try it out"** (top right of that section).
3. Either upload a video file, **or** paste a YouTube URL into the `youtube_url` box.
4. Click the blue **"Execute"** button.
5. Scroll down to see the JSON response — your titles, description, tags, and hashtags!

---

## 📡 API Reference

### `POST /process-video`

Processes a video and returns full YouTube Shorts metadata.

**Inputs (use one or the other):**

| Field | Type | Description |
|---|---|---|
| `file` | multipart file | Upload an `.mp4`, `.mov`, `.avi`, or `.mkv` file |
| `youtube_url` | query param | Paste a full YouTube URL instead of uploading |

**Output:**

```json
{
  "titles": ["...", "...", "...", "...", "..."],
  "description": "...",
  "tags": ["...", "..."],
  "hashtags": ["#...", "#..."]
}
```

**Example curl command:**

```bash
# Upload a local file
curl -X POST "http://localhost:8000/process-video" \
  -F "file=@my_video.mp4"

# Use a YouTube URL
curl -X POST "http://localhost:8000/process-video?youtube_url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

### `GET /`

Health check — confirms the server is running.

**Response:**

```json
{"status": "running"}
```

---

## 📄 Example Output

**Scenario:** a 60-second video of someone making pasta carbonara at home.

```json
{
  "titles": [
    "I Made Carbonara in 60 Seconds (No Cream!)",
    "The Secret Pasta Chefs Don't Want You to Know 🍝",
    "3 Ingredients, Perfect Carbonara Every Time",
    "Why Your Carbonara Always Fails (Fix THIS)",
    "Roman Chef Taught Me This Trick at 2AM"
  ],
  "description": "Think carbonara needs cream? Think again. In this Short I'll show you the authentic Roman technique that takes only 60 seconds and three pantry staples — eggs, guanciale, and Pecorino Romano. The secret is all in the temperature: pull the pan off the heat before adding the egg mixture so you get silky sauce, not scrambled eggs. This is the method home cooks get wrong 90% of the time, and once you see it you can't unsee it. Perfect for a weeknight dinner when you want something impressive without the effort. Save this video so you never forget the ratio: 1 egg yolk per person, plus one whole egg for the pan. Drop your pasta shape of choice in the comments — I test them all. Like for more Italian cooking secrets and subscribe to never miss a recipe. #pasta #carbonara #italianfood",
  "tags": [
    "carbonara recipe",
    "pasta carbonara",
    "italian cooking",
    "easy pasta recipe",
    "quick dinner ideas",
    "authentic carbonara",
    "pasta without cream",
    "weeknight dinner",
    "cooking tips",
    "roman cuisine"
  ],
  "hashtags": [
    "#Carbonara",
    "#PastaRecipe",
    "#ItalianFood",
    "#CookingTips",
    "#EasyRecipes",
    "#QuickDinner",
    "#HomeCooking",
    "#FoodShorts",
    "#Shorts",
    "#YouTubeShorts"
  ]
}
```

---

## 🛠️ Troubleshooting

### `ModuleNotFoundError: No module named 'faster_whisper'`

The Python packages didn't install correctly. Run:

```bash
pip install -r requirements.txt
```

If it still fails, try:

```bash
pip install faster-whisper==1.0.3
```

---

### Whisper transcription takes more than 5 minutes

This is normal for long videos on CPU — Whisper is doing heavy computation.

- Try a shorter clip (under 3 minutes) for testing.
- Make sure you're using the `tiny` or `base` Whisper model in your config (the larger models are much slower on CPU).
- Codespaces free tier has limited CPU; consider upgrading if speed is critical.

---

### YOLO or CLIP model fails to download

These models are downloaded from the internet the first time. If the download fails:

1. Check your internet connection.
2. Re-run the download step manually:

```bash
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
python3 -c "from transformers import CLIPModel; CLIPModel.from_pretrained('openai/clip-vit-base-patch32')"
```

If Hugging Face is blocked in your region, set a mirror:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

### Gemini returns invalid JSON / parsing error

The API will automatically fall back to a default response rather than crashing. You'll see this in the server logs:

```
[generate_metadata] ERROR: ...
```

To fix it:
- Check that your `GEMINI_API_KEY` is correct (see below).
- The Gemini model occasionally returns markdown-formatted responses. The parser strips code fences automatically, but if it persists, file an issue.

---

### GEMINI_API_KEY not found / 401 Unauthorized

This means the API key is missing or wrong.

1. Open `.env` in the sidebar.
2. Make sure the line reads exactly: `GEMINI_API_KEY=AIzaYourActualKeyHere` (no spaces, no quotes).
3. Save the file, then **restart the server** (press Ctrl+C in the terminal, then run the uvicorn command again).

Get a free key at [aistudio.google.com](https://aistudio.google.com).

---

### Port 8000 not appearing in the Ports tab

1. Make sure the server is actually running (you should see `Application startup complete.` in the terminal).
2. Click the **refresh icon** inside the Ports tab.
3. If it still doesn't appear, manually add it: click **"Add Port"**, type `8000`, press Enter.

---

### "ffmpeg not found" error

FFmpeg wasn't installed. Run:

```bash
sudo apt-get install -y ffmpeg
```

Then verify it works:

```bash
ffmpeg -version
```

---

## 🧰 Tech Stack

| Component | Tool | Why |
|---|---|---|
| API framework | FastAPI | Fast, async, auto Swagger docs |
| Video processing | FFmpeg | Industry-standard audio/frame extraction |
| Speech-to-text | faster-whisper 1.0.3 | CPU-friendly Whisper, 4× faster than original |
| Scene understanding | CLIP (ViT-B/32) | Zero-shot visual labelling, no fine-tuning needed |
| Object detection | YOLOv8 nano | Fast, lightweight, CPU-capable |
| Metadata generation | Gemini 1.5 Flash | Best instruction-following LLM for structured JSON |
| YouTube download | yt-dlp | Reliable, maintained YouTube downloader |
| Server | Uvicorn | ASGI server, works great with FastAPI |
| Environment | GitHub Codespaces | Zero-install cloud dev environment |

---

## 📁 Project Structure

```
video-metadata-generator/
├── main.py                  # FastAPI app — routes and orchestration
├── video_processor.py       # Downloads YouTube URLs, splits video via FFmpeg
├── audio_processor.py       # Extracts audio and transcribes with faster-whisper
├── vision_analyzer.py       # Frame analysis with CLIP + YOLOv8
├── metadata_generator.py    # Gemini API integration → JSON metadata
├── requirements.txt         # Python dependencies
├── .env                     # Your secrets (GEMINI_API_KEY) — never commit this
├── .env.example             # Template .env — safe to commit
├── .gitignore               # Excludes .env, models, temp files
└── deploy/
    └── setup.sh             # One-command setup script
```

---

## 📝 Notes

- **Free tier limits:** Gemini 1.5 Flash has a generous free quota (15 req/min, 1 million tokens/day as of mid-2024). Check [ai.google.dev](https://ai.google.dev) for current limits.
- **Video length:** Works best on clips under 10 minutes. Longer videos are processed but transcription will take proportionally longer on CPU.
- **Supported formats:** mp4, mov, avi, mkv, webm (anything FFmpeg can decode).
- **Data privacy:** Video files are processed locally and deleted after analysis. Nothing is stored permanently.
