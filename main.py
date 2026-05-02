"""
main.py — Video Metadata Generator API
=======================================
Entry point for the FastAPI application.

Pipeline (per request):
  [video file | youtube_url]
        │
        ▼
  video_processor  →  {frames_path, audio_path}
        │
        ├─► audio_processor  →  transcript (str)
        │
        └─► vision_analyzer  →  visual_summary (dict)
                │
                ▼
        metadata_generator  →  final JSON metadata
"""

import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# ── Load .env before anything else touches env vars ──────────────
load_dotenv()

# ── Downstream pipeline modules (built in Parts 2 & 3) ───────────
from video_processor import download_youtube_video, process_video  # noqa: E402
from audio_processor import transcribe_audio                       # noqa: E402
from vision_analyzer import analyze_frames                         # noqa: E402
from metadata_generator import generate_metadata                   # noqa: E402


# ─────────────────────────────────────────────────────────────────
# Lifespan — runs once on startup / shutdown
# ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # ── Startup ──────────────────────────────────────────────────
    print("🚀 Video Metadata Generator API is running!")
    print("📡 Visit http://localhost:8000/docs for Swagger UI")

    # Ensure a dedicated temp directory exists for our pipeline
    temp_root = Path(os.getenv("TEMP_DIR", tempfile.gettempdir())) / "video_metadata"
    temp_root.mkdir(parents=True, exist_ok=True)
    print(f"📁 Temp directory: {temp_root}")

    yield  # ← app is live while we're here

    # ── Shutdown (graceful cleanup) ───────────────────────────────
    print("🛑 Shutting down Video Metadata Generator API.")


# ─────────────────────────────────────────────────────────────────
# App initialisation
# ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Video Metadata Generator",
    description=(
        "Multimodal pipeline: video → Whisper transcript + CLIP/YOLO frame analysis "
        "→ GPT-4o YouTube Shorts titles, SEO description, tags & hashtags."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow all origins (tighten in production) ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────
# Helper: resolve a unique temp working directory for this request
# ─────────────────────────────────────────────────────────────────
def _make_request_tempdir() -> Path:
    """
    Creates a fresh, isolated temp sub-directory for a single request.
    The caller is responsible for deleting it after use.
    """
    temp_root = Path(os.getenv("TEMP_DIR", tempfile.gettempdir())) / "video_metadata"
    request_dir = Path(tempfile.mkdtemp(dir=temp_root))
    return request_dir


# ─────────────────────────────────────────────────────────────────
# GET /  —  health check
# ─────────────────────────────────────────────────────────────────
@app.get(
    "/",
    summary="Health check",
    tags=["System"],
)
async def health_check() -> dict:
    """Returns a simple liveness signal."""
    return {"status": "running"}


# ─────────────────────────────────────────────────────────────────
# POST /process-video  —  main pipeline endpoint
# ─────────────────────────────────────────────────────────────────
@app.post(
    "/process-video",
    summary="Generate metadata from a video file or YouTube URL",
    tags=["Pipeline"],
    response_description=(
        "JSON containing viral titles, SEO description, tags, hashtags, "
        "transcript excerpt, and visual summary."
    ),
)
async def process_video_endpoint(
    file: UploadFile = File(
        default=None,
        description="Video file to upload (mp4, mov, avi, mkv, …)",
    ),
    youtube_url: str = Query(
        default=None,
        description="Public YouTube URL (used instead of a file upload).",
    ),
) -> dict:
    """
    Full multimodal metadata-generation pipeline.

    Accepts **either** a video file upload **or** a YouTube URL (not both).

    Returns a JSON object with:
    - ``titles``          — 5 viral YouTube Shorts title suggestions
    - ``description``     — SEO-optimised video description
    - ``tags``            — list of relevant keyword tags
    - ``hashtags``        — list of trending hashtags
    - ``transcript``      — full Whisper-generated transcript
    - ``visual_summary``  — CLIP/YOLO scene & object analysis
    """

    # ── 0. Validate input ─────────────────────────────────────────
    if not youtube_url and (file is None or file.filename == ""):
        raise HTTPException(
            status_code=422,
            detail="Provide either a 'file' upload or a 'youtube_url' query parameter.",
        )
    if youtube_url and file and file.filename:
        raise HTTPException(
            status_code=422,
            detail="Provide only one input source: 'file' OR 'youtube_url', not both.",
        )

    # ── Create an isolated temp directory for this request ────────
    request_dir: Path = _make_request_tempdir()
    video_path: Path | None = None

    try:
        # ── STEP 1: Obtain the video file ─────────────────────────
        if youtube_url:
            print(f"[Step 1] 🌐 Downloading YouTube video: {youtube_url}")
            video_path = await _run_sync(download_youtube_video, youtube_url, request_dir)
            print(f"[Step 1] ✅ Downloaded to: {video_path}")
        else:
            print(f"[Step 1] 📤 Saving uploaded file: {file.filename}")
            video_path = request_dir / file.filename
            with video_path.open("wb") as f_out:
                content = await file.read()
                f_out.write(content)
            print(f"[Step 1] ✅ Saved to: {video_path}")

        # ── STEP 2: Extract audio + frames ───────────────────────
        print("[Step 2] 🎬 Processing video (frame & audio extraction)…")
        processing_result: dict = await _run_sync(process_video, video_path)
        frames_path: Path = Path(processing_result["frames_path"])
        audio_path: Path = Path(processing_result["audio_path"])
        print(f"[Step 2] ✅ Frames dir: {frames_path} | Audio: {audio_path}")

        # ── STEP 3: Transcribe audio with Whisper ─────────────────
        print("[Step 3] 🎙️  Transcribing audio with Whisper…")
        transcript: str = await _run_sync(transcribe_audio, audio_path)
        print(f"[Step 3] ✅ Transcript length: {len(transcript)} characters")
        print(f"[Step 3]    Preview: {transcript[:120].strip()}…")

        # ── STEP 4: Analyse frames with CLIP + YOLO ───────────────
        print("[Step 4] 👁️  Analysing frames with CLIP + YOLO…")
        visual_summary: dict = await _run_sync(analyze_frames, frames_path)
        print(f"[Step 4] ✅ Visual summary keys: {list(visual_summary.keys())}")

        # ── STEP 5: Generate metadata with GPT-4o ─────────────────
        print("[Step 5] 🤖 Generating metadata with GPT-4o…")
        metadata: dict = await _run_sync(generate_metadata, transcript, visual_summary)
        print("[Step 5] ✅ Metadata generated successfully.")

        # ── Build final response ───────────────────────────────────
        response = {
            "status": "success",
            **metadata,                          # titles, description, tags, hashtags
            "transcript": transcript,
            "visual_summary": visual_summary,
        }
        print("[Done] 🎉 Pipeline complete — returning response.")
        return response

    # ── Structured error handling ──────────────────────────────────
    except HTTPException:
        raise  # re-raise FastAPI exceptions as-is

    except FileNotFoundError as exc:
        print(f"[Error] ❌ File not found: {exc}")
        raise HTTPException(status_code=500, detail=f"File not found during processing: {exc}")

    except ValueError as exc:
        print(f"[Error] ❌ Value error: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))

    except Exception as exc:  # noqa: BLE001
        print(f"[Error] ❌ Unexpected error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal pipeline error: {type(exc).__name__}: {exc}",
        )

    finally:
        # ── CLEANUP: always remove the request temp dir ───────────
        if request_dir.exists():
            shutil.rmtree(request_dir, ignore_errors=True)
            print(f"[Cleanup] 🗑️  Removed temp directory: {request_dir}")


# ─────────────────────────────────────────────────────────────────
# Async helper — run blocking (CPU-bound) functions in a thread pool
# so they don't block the event loop.
# ─────────────────────────────────────────────────────────────────
import asyncio
import functools


async def _run_sync(func, *args, **kwargs):
    """
    Execute a synchronous (blocking) function inside FastAPI's default
    thread-pool executor so the async event loop stays responsive.

    Usage:
        result = await _run_sync(some_blocking_fn, arg1, arg2)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # uses the default ThreadPoolExecutor
        functools.partial(func, *args, **kwargs),
    )


# ─────────────────────────────────────────────────────────────────
# Dev entrypoint  (python main.py)
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,   # auto-reload on code changes (dev mode)
        log_level="info",
    )
