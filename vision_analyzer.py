"""
vision_analyzer.py — Part 3 of 4: Vision Analysis Module
Analyzes extracted video frames using CLIP (scene classification) and
YOLO (object detection) on CPU only. Models are loaded once as singletons.
"""

import os
import glob
from collections import Counter
from PIL import Image
import torch
from transformers import CLIPModel, CLIPProcessor
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Singleton model references — loaded once per server lifetime
# ---------------------------------------------------------------------------
_clip_model = None
_clip_processor = None
_yolo_model = None

# Candidate scene labels for CLIP zero-shot classification
CANDIDATE_LABELS = [
    "person talking",
    "outdoor adventure",
    "cooking food",
    "gaming setup",
    "fitness workout",
    "music performance",
    "travel vlog",
    "technology review",
    "comedy skit",
    "animal or pet",
    "art or craft",
    "fashion or style",
    "nature landscape",
    "sports action",
    "educational content",
]

# Maximum frames to process (keeps CPU runtime reasonable)
MAX_FRAMES = 20


# ---------------------------------------------------------------------------
# FUNCTION B: load_clip_model()
# Lazily loads CLIPModel + CLIPProcessor from HuggingFace (CPU only).
# Returns the (model, processor) tuple. On subsequent calls returns cached refs.
# ---------------------------------------------------------------------------
def load_clip_model() -> tuple:
    """
    Singleton loader for CLIP.
    Uses CLIPModel + CLIPProcessor directly (NOT transformers pipeline).
    All tensors are on CPU.
    """
    global _clip_model, _clip_processor

    # Return cached models if already loaded
    if _clip_model is not None and _clip_processor is not None:
        return _clip_model, _clip_processor

    print("Loading CLIP model...")
    _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    _clip_model.eval()                # Switch to inference mode
    _clip_model = _clip_model.to("cpu")
    print("CLIP model loaded on CPU.")

    return _clip_model, _clip_processor


# ---------------------------------------------------------------------------
# FUNCTION C: load_yolo_model()
# Lazily loads YOLOv8-nano (smallest/fastest variant) on CPU.
# Returns the YOLO model instance. On subsequent calls returns cached ref.
# ---------------------------------------------------------------------------
def load_yolo_model() -> YOLO:
    """
    Singleton loader for YOLOv8 nano.
    Forces CPU device. verbose=False suppresses per-inference logging.
    """
    global _yolo_model

    # Return cached model if already loaded
    if _yolo_model is not None:
        return _yolo_model

    print("Loading YOLO model...")
    _yolo_model = YOLO("yolov8n.pt")   # Downloads yolov8n.pt if not cached
    _yolo_model.to("cpu")
    print("YOLO model loaded on CPU.")

    return _yolo_model


# ---------------------------------------------------------------------------
# INTERNAL HELPER: analyze_single_frame()
# Runs CLIP + YOLO on one image. Returns top-3 CLIP labels and YOLO detections.
# Any per-frame error is caught so the rest of the batch can continue.
# ---------------------------------------------------------------------------
def analyze_single_frame(
    image_path: str,
    clip_model: CLIPModel,
    clip_processor: CLIPProcessor,
    yolo_model: YOLO,
    candidate_labels: list[str],
) -> dict:
    """
    Analyze a single frame with CLIP and YOLO.

    Returns:
        {
            "clip_top3": [(label, score), ...],   # top-3 by softmax score
            "yolo_objects": [str, ...]             # class names with conf > 0.3
        }
    On any error returns safe empty defaults.
    """
    try:
        # --- Load image via PIL ---
        image = Image.open(image_path).convert("RGB")

        # ------------------------------------------------------------------
        # CLIP inference
        # Tokenize the candidate text labels and encode the image, then
        # compute cosine-similarity logits → softmax → pick top 3.
        # ------------------------------------------------------------------
        with torch.no_grad():
            inputs = clip_processor(
                text=candidate_labels,
                images=image,
                return_tensors="pt",
                padding=True,
            )
            # Move all input tensors to CPU (explicit, future-proof)
            inputs = {k: v.to("cpu") for k, v in inputs.items()}

            outputs = clip_model(**inputs)
            # logits_per_image shape: [1, num_labels]
            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0).tolist()

        # Pair labels with their probabilities and sort descending
        label_scores = sorted(
            zip(candidate_labels, probs), key=lambda x: x[1], reverse=True
        )
        clip_top3 = [(label, round(score, 4)) for label, score in label_scores[:3]]

        # ------------------------------------------------------------------
        # YOLO inference
        # Run detection; collect class names for boxes with conf > 0.3.
        # verbose=False keeps stdout clean.
        # ------------------------------------------------------------------
        yolo_results = yolo_model(image_path, verbose=False)
        yolo_objects = []

        for result in yolo_results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf > 0.3:
                    class_id = int(box.cls[0])
                    class_name = yolo_model.names[class_id]
                    yolo_objects.append(class_name)

        return {"clip_top3": clip_top3, "yolo_objects": yolo_objects}

    except Exception as e:
        # Skip this frame and log the error — do not crash the whole batch
        print(f"  [WARNING] Error analyzing frame {image_path}: {e}")
        return {"clip_top3": [], "yolo_objects": []}


# ---------------------------------------------------------------------------
# FUNCTION A: analyze_frames()  ← the only public entry point
# Loads models (singletons), iterates over frames, aggregates results.
# ---------------------------------------------------------------------------
def analyze_frames(frames_path: str) -> dict:
    """
    Main public function. Analyzes up to MAX_FRAMES JPEG frames from
    frames_path using CLIP + YOLO and returns aggregated metadata.

    Args:
        frames_path: Directory containing .jpg / .jpeg frame files.

    Returns:
        {
            "dominant_scene": str,
            "top_clip_labels": [str, ...],
            "top_yolo_objects": [str, ...],
            "avg_confidence": float,
            "frames_analyzed": int,
        }
    """

    # --- Safe defaults in case of early exit ---
    safe_defaults = {
        "dominant_scene": "unknown",
        "top_clip_labels": [],
        "top_yolo_objects": [],
        "avg_confidence": 0.0,
        "frames_analyzed": 0,
    }

    # ------------------------------------------------------------------
    # Validate frames directory
    # ------------------------------------------------------------------
    if not frames_path or not os.path.isdir(frames_path):
        print(f"[ERROR] frames_path does not exist or is not a directory: {frames_path}")
        return safe_defaults

    # Collect and sort frame files
    jpg_files = sorted(
        glob.glob(os.path.join(frames_path, "*.jpg"))
        + glob.glob(os.path.join(frames_path, "*.jpeg"))
    )

    if not jpg_files:
        print(f"[WARNING] No JPEG frames found in: {frames_path}")
        return safe_defaults

    # Cap to MAX_FRAMES for CPU performance
    if len(jpg_files) > MAX_FRAMES:
        print(f"[INFO] Capping frames from {len(jpg_files)} → {MAX_FRAMES}")
        jpg_files = jpg_files[:MAX_FRAMES]

    print(f"[INFO] Analyzing {len(jpg_files)} frame(s) from: {frames_path}")

    # ------------------------------------------------------------------
    # Load models (singleton — no-op if already loaded)
    # ------------------------------------------------------------------
    clip_model, clip_processor = load_clip_model()
    yolo_model = load_yolo_model()

    # ------------------------------------------------------------------
    # Per-frame analysis
    # ------------------------------------------------------------------
    clip_label_counts: Counter = Counter()   # label → number of frames in top-3
    yolo_object_counts: Counter = Counter()  # object class → total detections

    # Track per-frame scores of the eventual dominant label for avg_confidence
    dominant_label_scores: dict[str, list[float]] = {}

    frames_analyzed = 0

    for idx, frame_path in enumerate(jpg_files):
        print(f"  Processing frame {idx + 1}/{len(jpg_files)}: {os.path.basename(frame_path)}")

        result = analyze_single_frame(
            frame_path, clip_model, clip_processor, yolo_model, CANDIDATE_LABELS
        )

        # Only count frames that returned something useful
        if result["clip_top3"] or result["yolo_objects"]:
            frames_analyzed += 1

        # Accumulate CLIP top-3 label counts
        for label, score in result["clip_top3"]:
            clip_label_counts[label] += 1
            # Store score for average confidence calculation later
            if label not in dominant_label_scores:
                dominant_label_scores[label] = []
            dominant_label_scores[label].append(score)

        # Accumulate YOLO object counts
        for obj in result["yolo_objects"]:
            yolo_object_counts[obj] += 1

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    # Dominant scene: CLIP label with highest frame-count
    if clip_label_counts:
        dominant_scene = clip_label_counts.most_common(1)[0][0]
    else:
        dominant_scene = "unknown"

    # Top 5 CLIP labels by frame count
    top_clip_labels = [label for label, _ in clip_label_counts.most_common(5)]

    # Top 5 YOLO objects by detection frequency
    top_yolo_objects = [obj for obj, _ in yolo_object_counts.most_common(5)]

    # Average CLIP confidence for the dominant scene across all frames it appeared
    if dominant_scene != "unknown" and dominant_scene in dominant_label_scores:
        scores = dominant_label_scores[dominant_scene]
        avg_confidence = round(sum(scores) / len(scores), 2)
    else:
        avg_confidence = 0.0

    # ------------------------------------------------------------------
    # Print summary for debugging
    # ------------------------------------------------------------------
    print("\n========== Vision Analysis Summary ==========")
    print(f"  Dominant scene   : {dominant_scene}")
    print(f"  Top CLIP labels  : {top_clip_labels}")
    print(f"  Top YOLO objects : {top_yolo_objects}")
    print(f"  Avg confidence   : {avg_confidence}")
    print(f"  Frames analyzed  : {frames_analyzed}")
    print("=============================================\n")

    return {
        "dominant_scene": dominant_scene,
        "top_clip_labels": top_clip_labels,
        "top_yolo_objects": top_yolo_objects,
        "avg_confidence": avg_confidence,
        "frames_analyzed": frames_analyzed,
    }