"""
Standalone audio deepfake detector. Run this on its own first, before
wiring it into the main app -- same lesson as detect.py: prove it works
before building anything on top of it.

Usage:
    python audio_detect.py path/to/video_or_audio_file.mp4

Works on video files (it extracts the audio track first) or on audio
files directly (.wav, .mp3).

Uses a pretrained model from Hugging Face (motheecreator/Deepfake-audio-detection),
downloaded automatically the first time you run this -- no manual weight
file hunting needed this time.
"""

import sys
import os
import tempfile

from transformers import pipeline

MODEL_NAME = "motheecreator/Deepfake-audio-detection"

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}


def _extract_audio_if_needed(input_path: str) -> str:
    """
    If input_path is a video file, extract its audio track to a temp
    .wav file and return that path. If it's already an audio file,
    return it unchanged.
    """
    ext = os.path.splitext(input_path)[1].lower()
    if ext in AUDIO_EXTENSIONS:
        return input_path

    from moviepy import VideoFileClip

    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav_path = tmp_wav.name
    tmp_wav.close()

    with VideoFileClip(input_path) as clip:
        if clip.audio is None:
            raise RuntimeError(
                "This video file doesn't seem to have an audio track."
            )
        
        clip.audio.write_audiofile(tmp_wav_path, fps=16000, logger=None)

    return tmp_wav_path


def analyze_audio(input_path: str):
    """
    Returns a dict: {
        "label": "REAL" or "LIKELY FAKE",
        "confidence": float 0-100,
        "raw_label": the model's raw class label,
    }
    """
    audio_path = _extract_audio_if_needed(input_path)

    import soundfile as sf
    import numpy as np

    audio_array, sample_rate = sf.read(audio_path)
    if audio_array.ndim > 1:
        # convert stereo to mono by averaging channels
        audio_array = np.mean(audio_array, axis=1)

    
    rms = float(np.sqrt(np.mean(audio_array ** 2)))
    print(f"(debug) audio RMS level: {rms}")
    SILENCE_THRESHOLD = 0.02  
    if rms < SILENCE_THRESHOLD:
        raise RuntimeError(
            "Audio track is silent or has no clear speech -- skipping audio "
            "analysis (there's nothing meaningful to check)."
        )

    classifier = pipeline("audio-classification", model=MODEL_NAME)
    results = classifier({"array": audio_array, "sampling_rate": sample_rate})
  ]

    top = max(results, key=lambda r: r["score"])
    raw_label = top["label"].lower()
    is_fake = "fake" in raw_label or "spoof" in raw_label

    return {
        "label": "LIKELY FAKE" if is_fake else "REAL",
        "confidence": round(top["score"] * 100, 1),
        "raw_label": top["label"],
        "all_scores": results,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_detect.py path/to/video_or_audio.mp4")
        sys.exit(1)

    result = analyze_audio(sys.argv[1])
    print("\n--- Audio Result ---")
    print(f"Verdict:      {result['label']}")
    print(f"Confidence:   {result['confidence']}%")
    print(f"Raw model output: {result['all_scores']}")
