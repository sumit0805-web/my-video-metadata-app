"""
metadata_generator.py
─────────────────────
Calls the Gemini API to generate YouTube Shorts metadata from a transcript
and a visual summary produced by vision_analyzer.py.

Dependencies:
    google-generativeai==0.5.4
    GEMINI_API_KEY environment variable
"""

import json
import os
import re

import google.generativeai as genai

# ──────────────────────────────────────────────
# Singleton model loader
# ──────────────────────────────────────────────

_gemini_model = None


def load_gemini_model():
    """Load (or return the already-loaded) Gemini 1.5 Flash model."""
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is not set. "
                "Add it to your .env file and restart the server."
            )
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("Gemini model loaded.")
    return _gemini_model


# ──────────────────────────────────────────────
# Prompt builder
# ──────────────────────────────────────────────

def _build_prompt(transcript: str, visual_summary: dict) -> str:
    """
    Combine transcript + visual analysis into a structured Gemini prompt.

    Args:
        transcript:     Raw speech-to-text string from Whisper.
        visual_summary: Dict returned by vision_analyzer.analyze_frames().

    Returns:
        A prompt string ready to send to Gemini.
    """
    truncated_transcript = transcript[:1000] if len(transcript) > 1000 else transcript

    dominant_scene   = visual_summary.get("dominant_scene", "unknown")
    clip_labels      = visual_summary.get("top_clip_labels", [])
    yolo_objects     = visual_summary.get("top_yolo_objects", [])
    avg_confidence   = visual_summary.get("avg_confidence", 0.0)
    frames_analyzed  = visual_summary.get("frames_analyzed", 0)

    prompt = f"""You are an expert YouTube Shorts content strategist and SEO copywriter.

Below is data extracted from a video. Use it to generate viral metadata for a YouTube Shorts upload.

─── TRANSCRIPT (first 1000 chars) ───
{truncated_transcript}

─── VISUAL ANALYSIS ───
Dominant scene      : {dominant_scene}
CLIP scene labels   : {', '.join(clip_labels) if clip_labels else 'N/A'}
Detected objects    : {', '.join(yolo_objects) if yolo_objects else 'N/A'}
Avg CLIP confidence : {avg_confidence:.2f}
Frames analyzed     : {frames_analyzed}

─── INSTRUCTIONS ───
Return ONLY a valid JSON object — no markdown, no code fences, no explanation, no preamble.

The JSON must follow this EXACT structure:
{{
  "titles": [
    "Title 1 (viral hook, curiosity gap, or number)",
    "Title 2",
    "Title 3",
    "Title 4",
    "Title 5"
  ],
  "description": "150-200 word SEO-optimized YouTube Shorts description. Keyword-rich. End with a clear call to action. Keep sentences short for mobile readability.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
  "hashtags": ["#hash1", "#hash2", "#hash3", "#hash4", "#hash5", "#hash6", "#hash7", "#hash8", "#Shorts", "#YouTubeShorts"]
}}

Strict rules:
- titles   : exactly 5 items. Use viral YouTube Shorts styles — emotional hooks, numbers, "you won't believe", curiosity gaps, "how to in X seconds", etc.
- description: 150-200 words, keyword-rich, mobile-friendly, ends with call-to-action.
- tags     : exactly 10 items, NO # prefix, mix of broad and niche keywords.
- hashtags : exactly 10 items, each starts with #, MUST include #Shorts and #YouTubeShorts.

Output the raw JSON now:"""

    return prompt


# ──────────────────────────────────────────────
# Fallback response
# ──────────────────────────────────────────────

_FALLBACK = {
    "titles": ["Check out this amazing video!"],
    "description": "Watch this incredible content. Don't forget to like and subscribe!",
    "tags": ["video", "shorts", "viral"],
    "hashtags": ["#Shorts", "#YouTubeShorts", "#Viral"],
}


# ──────────────────────────────────────────────
# Main public function
# ──────────────────────────────────────────────

def generate_metadata(transcript: str, visual_summary: dict) -> dict:
    """
    Generate YouTube Shorts metadata via the Gemini 1.5 Flash API.

    Args:
        transcript    : Full speech transcript from Whisper (str).
        visual_summary: Dict from vision_analyzer.analyze_frames() with keys:
                        dominant_scene, top_clip_labels, top_yolo_objects,
                        avg_confidence, frames_analyzed.

    Returns:
        dict with keys: titles (list[str]), description (str),
                        tags (list[str]), hashtags (list[str]).
        Falls back to _FALLBACK dict if Gemini call or JSON parsing fails.
    """
    try:
        model = load_gemini_model()
        prompt = _build_prompt(transcript, visual_summary)

        print("Calling Gemini API...")
        response = model.generate_content(prompt)
        raw_text = response.text

        # Debug: show first 200 chars of raw response
        print(f"Gemini raw response (first 200 chars): {raw_text[:200]}")

        # Strip accidental markdown fences  ```json ... ``` or ``` ... ```
        cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()
        # Also strip any trailing fence
        cleaned = cleaned.rstrip("`").strip()

        metadata = json.loads(cleaned)

        # Light validation — ensure expected keys exist
        for key in ("titles", "description", "tags", "hashtags"):
            if key not in metadata:
                raise ValueError(f"Gemini response missing key: '{key}'")

        print("Metadata generated successfully.")
        return metadata

    except Exception as exc:
        print(f"[generate_metadata] ERROR: {exc}")
        return _FALLBACK