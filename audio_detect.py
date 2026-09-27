import sys
import os
import tempfile
import numpy as np
import soundfile as sf
from transformers import pipeline

MODEL_NAME = "motheecreator/Deepfake-audio-detection"
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}


def _extract_audio_if_needed(input_path: str) -> str:
    ext = os.path.splitext(input_path)[1].lower()
    if ext in AUDIO_EXTENSIONS:
        return input_path

    from moviepy import VideoFileClip

    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav_path = tmp_wav.name
    tmp_wav.close()

    try:
        with VideoFileClip(input_path) as clip:
            if clip.audio is None:
                raise RuntimeError("This video file doesn't seem to have an audio track.")
            clip.audio.write_audiofile(tmp_wav_path, fps=16000, logger=None)
        return tmp_wav_path
    except Exception:
        if os.path.exists(tmp_wav_path):
            os.unlink(tmp_wav_path)
        raise


def analyze_audio(input_path: str):
    audio_path = _extract_audio_if_needed(input_path)
    is_temp = audio_path != input_path

    try:
        audio_array, sample_rate = sf.read(audio_path)
        if audio_array.ndim > 1:
            audio_array = np.mean(audio_array, axis=1)

        audio_array = audio_array.astype(np.float32)

        rms = float(np.sqrt(np.mean(audio_array ** 2)))
        silence_threshold = 0.02
        if rms < silence_threshold:
            raise RuntimeError(
                "Audio track is silent or has no clear speech -- skipping audio "
                "analysis (there's nothing meaningful to check)."
            )

        classifier = pipeline("audio-classification", model=MODEL_NAME)
        results = classifier({"array": audio_array, "sampling_rate": sample_rate})

        top = max(results, key=lambda r: r["score"])
        raw_label = top["label"].lower()
        is_fake = "fake" in raw_label or "spoof" in raw_label

        return {
            "label": "LIKELY FAKE" if is_fake else "REAL",
            "confidence": round(top["score"] * 100, 1),
            "raw_label": top["label"],
            "all_scores": results,
        }
    finally:
        if is_temp and os.path.exists(audio_path):
            os.unlink(audio_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_detect.py path/to/video_or_audio.mp4")
        sys.exit(1)

    result = analyze_audio(sys.argv[1])
    print("\n--- Audio Result ---")
    print(f"Verdict:      {result['label']}")
    print(f"Confidence:   {result['confidence']}%")
    print(f"Raw model output: {result['all_scores']}")
