"""
audio_processor.py
==================
Part 2 of 4 — Audio Processing Module

Responsibilities:
  - Load faster-whisper WhisperModel once at module level (singleton pattern)
  - Transcribe a .wav audio file to a plain text string
  - Return "No speech detected" for empty/silent audio

CPU-only. device="cpu", compute_type="int8".
Uses faster-whisper==1.0.3 (NOT openai-whisper).
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level singleton: load the Whisper model ONCE when this module is
# imported. Reloading a ~150 MB model per call would be unacceptably slow.
# ---------------------------------------------------------------------------

print("[audio_processor] Loading WhisperModel (base, cpu, int8) …")

try:
    from faster_whisper import WhisperModel

    # "base" model  — good accuracy / speed balance for CPU
    # device="cpu"  — no GPU required
    # compute_type="int8" — quantized for faster CPU inference
    _whisper_model: WhisperModel = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8",
    )
    print("[audio_processor] WhisperModel loaded successfully.")

except ImportError as _import_err:
    # Surface a clear error if faster-whisper isn't installed
    raise ImportError(
        "faster-whisper is not installed. "
        "Install with: pip install faster-whisper==1.0.3"
    ) from _import_err

except Exception as _model_err:
    raise RuntimeError(
        f"Failed to initialise WhisperModel: {_model_err}"
    ) from _model_err


# ---------------------------------------------------------------------------
# A. transcribe_audio
# ---------------------------------------------------------------------------

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe a WAV audio file to plain text using faster-whisper.

    The global singleton `_whisper_model` is used — the model is NOT
    reloaded on each call.

    Parameters
    ----------
    audio_path : Path to a .wav file (16 kHz mono recommended)

    Returns
    -------
    str — full transcript joined from all Whisper segments, or
          "No speech detected" if the transcript is empty/blank.

    Raises
    ------
    FileNotFoundError – if audio_path does not exist
    RuntimeError      – if faster-whisper raises an unexpected error
    """

    # --- Input validation ---------------------------------------------------
    if not audio_path or not str(audio_path).strip():
        raise ValueError("audio_path must be a non-empty string.")

    audio_file = Path(audio_path).resolve()

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}\n"
            "Make sure process_video() ran successfully before calling transcribe_audio()."
        )

    if not audio_file.is_file():
        raise ValueError(f"audio_path is not a regular file: {audio_file}")

    file_size_kb = audio_file.stat().st_size / 1024
    print(f"[audio_processor] Transcribing: {audio_file} ({file_size_kb:.1f} KB)")

    # Guard against zero-byte files (empty audio)
    if audio_file.stat().st_size == 0:
        print("[audio_processor] Audio file is empty (0 bytes). Returning default.")
        return "No speech detected"

    # --- Transcription ------------------------------------------------------
    print("[audio_processor] Running faster-whisper inference …")

    try:
        # `transcribe` returns a generator of Segment objects + TranscriptionInfo
        # beam_size=5   — default; good accuracy on CPU
        # language=None — auto-detect language
        # vad_filter=True — Voice Activity Detection: skip silent regions
        #                   (speeds up CPU inference significantly)
        segments_generator, info = _whisper_model.transcribe(
            str(audio_file),
            beam_size=5,
            language=None,       # auto-detect
            vad_filter=True,     # skip silence — helps on CPU
        )

        print(
            f"[audio_processor] Detected language: '{info.language}' "
            f"(probability: {info.language_probability:.2f})"
        )

        # --- Collect all segment texts --------------------------------------
        # The generator is consumed lazily; join into one string.
        segment_texts = []
        for segment in segments_generator:
            text = segment.text.strip()
            if text:
                segment_texts.append(text)

        transcript = " ".join(segment_texts).strip()

    except FileNotFoundError:
        # Re-raise with a clearer message in case ffmpeg/ctranslate2 can't open the file
        raise FileNotFoundError(
            f"faster-whisper could not open the audio file: {audio_file}"
        )

    except Exception as whisper_err:
        raise RuntimeError(
            f"faster-whisper transcription failed for '{audio_file}': {whisper_err}"
        ) from whisper_err

    # --- Handle empty transcript -------------------------------------------
    if not transcript:
        print("[audio_processor] Transcript is empty — returning default string.")
        return "No speech detected"

    # --- Debug preview (first 100 chars) ------------------------------------
    preview = transcript[:100]
    print(f"[audio_processor] Transcript preview (first 100 chars): {preview!r}")
    print(f"[audio_processor] Total transcript length: {len(transcript)} chars")

    return transcript


# ---------------------------------------------------------------------------
# Quick smoke test (run directly: python audio_processor.py <path_to.wav>)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python audio_processor.py <path_to_audio.wav>")
        sys.exit(1)

    wav_path = sys.argv[1]
    print(f"=== Smoke test: transcribing {wav_path} ===")
    result = transcribe_audio(wav_path)
    print("\n=== FULL TRANSCRIPT ===")
    print(result)