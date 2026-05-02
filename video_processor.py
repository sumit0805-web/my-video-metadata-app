"""
video_processor.py
==================
Part 2 of 4 — Video Processing Module

Responsibilities:
  - Download videos from YouTube URLs via yt-dlp
  - Extract audio (.wav, 16kHz mono) from local video files via ffmpeg
  - Extract JPEG frames (1 per 2 seconds) from local video files via ffmpeg

CPU-only. No GPU acceleration flags used anywhere.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# A. download_youtube_video
# ---------------------------------------------------------------------------

def download_youtube_video(url: str, dest_dir: str) -> Path:
    """
    Download a YouTube video using yt-dlp into dest_dir.

    Format strategy:
      1. Best mp4 video under 50 MB + best audio
      2. Fallback: best single mp4 file under 50 MB
      3. Last resort: best available (may exceed size hint)

    Parameters
    ----------
    url      : YouTube video URL (must be a non-empty string)
    dest_dir : Directory where the video file will be saved

    Returns
    -------
    pathlib.Path pointing to the downloaded video file

    Raises
    ------
    ValueError  – if url or dest_dir are empty/None
    FileNotFoundError – if yt-dlp is not installed
    RuntimeError – if the download fails or no file is produced
    """

    # --- Input validation ---------------------------------------------------
    if not url or not url.strip():
        raise ValueError("url must be a non-empty string.")

    if not dest_dir or not dest_dir.strip():
        raise ValueError("dest_dir must be a non-empty string.")

    dest_path = Path(dest_dir)

    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)
    print(f"[video_processor] Download destination: {dest_path.resolve()}")

    # --- Check yt-dlp availability -----------------------------------------
    if shutil.which("yt-dlp") is None:
        raise FileNotFoundError(
            "yt-dlp is not installed or not on PATH. "
            "Install it with: pip install yt-dlp"
        )

    # --- Build yt-dlp command -----------------------------------------------
    # Format string: prefer mp4 under 50 MB, fall back gracefully
    format_str = (
        "bestvideo[ext=mp4][filesize<50M]+bestaudio/best[ext=mp4][filesize<50M]/best"
    )

    # Output template: save as video.mp4 (or yt-dlp's detected extension)
    output_template = str(dest_path / "%(title).60s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--format", format_str,
        "--output", output_template,
        "--merge-output-format", "mp4",   # merge audio+video into mp4
        "--no-playlist",                  # only download the single video
        "--print", "after_move:filepath", # print final path after moving
        url,
    ]

    print(f"[video_processor] Running yt-dlp for URL: {url}")
    print(f"[video_processor] Command: {' '.join(cmd)}")

    # --- Execute yt-dlp -----------------------------------------------------
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,       # raises CalledProcessError on non-zero exit
        )
    except subprocess.CalledProcessError as e:
        stderr_snippet = e.stderr.strip()[-500:] if e.stderr else "(no stderr)"
        raise RuntimeError(
            f"yt-dlp failed for URL '{url}'.\n"
            f"Exit code: {e.returncode}\n"
            f"stderr (last 500 chars):\n{stderr_snippet}"
        ) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "yt-dlp binary not found. Install with: pip install yt-dlp"
        ) from e

    # --- Resolve the downloaded file path -----------------------------------
    # yt-dlp prints the final filepath to stdout when using --print filepath
    stdout_lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]

    downloaded_file: Path | None = None

    # Try to use the printed path first
    for line in stdout_lines:
        candidate = Path(line)
        if candidate.exists() and candidate.is_file():
            downloaded_file = candidate
            break

    # Fallback: scan dest_dir for any new video file
    if downloaded_file is None:
        video_extensions = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
        candidates = [
            p for p in dest_path.iterdir()
            if p.is_file() and p.suffix.lower() in video_extensions
        ]
        if candidates:
            # Pick the most recently modified one
            downloaded_file = max(candidates, key=lambda p: p.stat().st_mtime)

    if downloaded_file is None or not downloaded_file.exists():
        raise RuntimeError(
            f"yt-dlp reported success but no video file found in '{dest_path}'. "
            f"stdout was:\n{result.stdout}"
        )

    file_size_mb = downloaded_file.stat().st_size / (1024 * 1024)
    print(f"[video_processor] Downloaded: {downloaded_file.name} ({file_size_mb:.1f} MB)")
    return downloaded_file


# ---------------------------------------------------------------------------
# B. process_video
# ---------------------------------------------------------------------------

def process_video(video_path: str) -> dict:
    """
    Extract audio and frames from a local video file using ffmpeg (CPU only).

    Audio extraction:
      - Format : WAV, 16 kHz sample rate, mono (required by faster-whisper)
      - Saved to a temp directory alongside the frames

    Frame extraction:
      - Rate   : 1 frame every 2 seconds  (fps=0.5)
      - Format : JPEG
      - Saved to a temp directory as frame_0001.jpg, frame_0002.jpg, …

    Parameters
    ----------
    video_path : Absolute or relative path to the video file (str)

    Returns
    -------
    dict with EXACTLY these keys:
      {
        "frames_path" : str,   # absolute path to folder containing JPEG frames
        "audio_path"  : str,   # absolute path to the .wav file
        "frame_count" : int    # number of JPEG frames extracted
      }

    Raises
    ------
    FileNotFoundError – if video_path does not exist
    RuntimeError      – if ffmpeg fails or produces no output
    """

    # --- Input validation ---------------------------------------------------
    if not video_path or not str(video_path).strip():
        raise ValueError("video_path must be a non-empty string.")

    source = Path(video_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f"Video file not found: {source}")

    if not source.is_file():
        raise ValueError(f"video_path is not a regular file: {source}")

    print(f"[video_processor] Processing video: {source}")

    # --- Check ffmpeg availability ------------------------------------------
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError(
            "ffmpeg is not installed or not on PATH. "
            "Install with: sudo apt install ffmpeg"
        )

    # --- Create a persistent temp directory for outputs --------------------
    # We use a named temp dir (not auto-deleted) so callers can use the files.
    # Callers are responsible for cleanup if needed.
    tmp_dir = Path(tempfile.mkdtemp(prefix="video_proc_"))
    frames_dir = tmp_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    audio_path = tmp_dir / "audio.wav"

    print(f"[video_processor] Temp working directory: {tmp_dir}")

    # -----------------------------------------------------------------------
    # Step 1 — Extract audio as WAV (16kHz, mono)
    # -----------------------------------------------------------------------
    print("[video_processor] Extracting audio …")

    audio_cmd = [
        "ffmpeg",
        "-y",                      # overwrite output without prompting
        "-i", str(source),         # input video
        # No -hwaccel flag → CPU only
        "-vn",                     # disable video stream (audio only)
        "-ar", "16000",            # sample rate: 16 kHz (faster-whisper requirement)
        "-ac", "1",                # mono channel
        "-acodec", "pcm_s16le",    # uncompressed 16-bit PCM (standard WAV)
        str(audio_path),
    ]

    try:
        audio_result = subprocess.run(
            audio_cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"[video_processor] Audio saved to: {audio_path}")
    except subprocess.CalledProcessError as e:
        stderr_snippet = e.stderr.strip()[-800:] if e.stderr else "(no stderr)"
        raise RuntimeError(
            f"ffmpeg failed during audio extraction.\n"
            f"Exit code: {e.returncode}\n"
            f"stderr (last 800 chars):\n{stderr_snippet}"
        ) from e

    # Verify audio file was actually created
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise RuntimeError(
            f"ffmpeg audio extraction produced no output at: {audio_path}"
        )

    audio_size_kb = audio_path.stat().st_size / 1024
    print(f"[video_processor] Audio file size: {audio_size_kb:.1f} KB")

    # -----------------------------------------------------------------------
    # Step 2 — Extract frames at 1 frame per 2 seconds (fps=0.5)
    # -----------------------------------------------------------------------
    print("[video_processor] Extracting frames (1 per 2 seconds) …")

    frame_pattern = str(frames_dir / "frame_%04d.jpg")

    frame_cmd = [
        "ffmpeg",
        "-y",                      # overwrite without prompting
        "-i", str(source),         # input video
        # No -hwaccel flag → CPU only
        "-vf", "fps=0.5",          # 0.5 frames/sec = 1 frame every 2 seconds
        "-q:v", "2",               # JPEG quality (2 = high quality, range 1–31)
        frame_pattern,
    ]

    try:
        frame_result = subprocess.run(
            frame_cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        stderr_snippet = e.stderr.strip()[-800:] if e.stderr else "(no stderr)"
        raise RuntimeError(
            f"ffmpeg failed during frame extraction.\n"
            f"Exit code: {e.returncode}\n"
            f"stderr (last 800 chars):\n{stderr_snippet}"
        ) from e

    # -----------------------------------------------------------------------
    # Step 3 — Count extracted frames
    # -----------------------------------------------------------------------
    jpeg_files = sorted(frames_dir.glob("frame_*.jpg"))
    frame_count = len(jpeg_files)

    if frame_count == 0:
        raise RuntimeError(
            f"ffmpeg frame extraction produced no JPEG files in: {frames_dir}\n"
            "The video may be corrupt, have no video stream, or be too short."
        )

    print(f"[video_processor] Frames extracted: {frame_count}")
    print(f"[video_processor] Frames saved to : {frames_dir}")

    # -----------------------------------------------------------------------
    # Return the canonical result dict (key names must match exactly)
    # -----------------------------------------------------------------------
    return {
        "frames_path": str(frames_dir),   # path to folder containing JPEG frames
        "audio_path":  str(audio_path),   # path to .wav file
        "frame_count": frame_count,       # number of frames extracted
    }


# ---------------------------------------------------------------------------
# Quick smoke test (run directly: python video_processor.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg.startswith("http"):
            print("=== Testing download_youtube_video ===")
            out = download_youtube_video(arg, "/tmp/yt_test")
            print(f"Downloaded to: {out}")
        else:
            print("=== Testing process_video ===")
            result = process_video(arg)
            print("Result dict:", result)
    else:
        print("Usage:")
        print("  python video_processor.py <youtube_url>    # test download")
        print("  python video_processor.py <local_video>    # test processing")