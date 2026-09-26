"""
Core detection loop. Run this file directly first, on one test video,
before touching the app UI at all:

    python detect.py path/to/test_video.mp4

This is Step 4 from the plan: prove the core detection works on your
machine on a single video before building anything else.
"""

import sys
import numpy as np

from mesonet_model import Meso4
from face_utils import extract_face_crops

WEIGHTS_PATH = "weights/Meso4_DF.h5"  # see README for where to get this file


def analyze_video(video_path: str, weights_path: str = WEIGHTS_PATH):
    """
    Returns a dict: {
        "label": "REAL" or "LIKELY FAKE",
        "confidence": float 0-100,
        "frames_analyzed": int,
        "faces_found": int,
    }
    """
    crops = extract_face_crops(video_path)
    if len(crops) == 0:
        raise RuntimeError(
            "No faces detected in the sampled frames. Try a clip with a "
            "clearer, more front-facing view of the person."
        )

    faces = np.array([c[1] for c in crops])  # shape (N, 256, 256, 3)

    model = Meso4()
    model.load_weights(weights_path)

    per_frame_scores = model.predict(faces).flatten()  # values near 1 = real, near 0 = fake
    mean_score = float(np.mean(per_frame_scores))

    is_real = mean_score >= 0.5
    # confidence = how far the average score is from the 0.5 decision boundary,
    # rescaled to a 50-100% range
    confidence = 50 + abs(mean_score - 0.5) * 100

    return {
        "label": "REAL" if is_real else "LIKELY FAKE",
        "confidence": round(min(confidence, 99.0), 1),
        "frames_analyzed": len(crops),
        "faces_found": len(crops),
        "raw_mean_score": round(mean_score, 4),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect.py path/to/video.mp4")
        sys.exit(1)

    result = analyze_video(sys.argv[1])
    print("\n--- Result ---")
    print(f"Verdict:          {result['label']}")
    print(f"Confidence:       {result['confidence']}%")
    print(f"Frames analyzed:  {result['frames_analyzed']}")
    print(f"Raw mean score:   {result['raw_mean_score']} (near 1 = real, near 0 = fake)")

    try:
        from arduino_serial import send_to_arduino
        send_to_arduino(result["label"], result["confidence"])
    except Exception as e:
        print(f"(Arduino display update skipped: {e})")
