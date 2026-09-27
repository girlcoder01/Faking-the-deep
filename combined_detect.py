"""
Combined video + audio deepfake detector.
 
Runs the face/video analysis (detect.py's logic) and the audio analysis
(audio_detect.py's logic) on the same file, then produces one overall
verdict. Also sends the combined result to the Arduino LCD, same as
detect.py did on its own.
 
Usage:
    python combined_detect.py human.mp4
"""
 
import sys
 
from detect import analyze_video
from audio_detect import analyze_audio
from gemini_movement import analyze_movement
 
 
def _to_raw_score(label: str, confidence: float) -> float:
    """
    Converts a (label, confidence%) pair from either modality into a
    single 0-1 scale where close to 1 = real, close to 0 = fake, so
    the two modalities can be combined on the same footing.
    """
    fraction = confidence / 100.0
    if label == "REAL":
        return 0.5 + (fraction - 0.5)  
    else:
        return 0.5 - (fraction - 0.5)  
 
 
def analyze_combined(video_path: str):
    video_result = None
    audio_result = None
    movement_result = None
    video_error = None
    audio_error = None
    movement_error = None
 
    try:
        video_result = analyze_video(video_path)
    except Exception as e:
        video_error = str(e)
 
    try:
        audio_result = analyze_audio(video_path)
    except Exception as e:
        audio_error = str(e)
 
    try:
        movement_result = analyze_movement(video_path)
    except Exception as e:
        movement_error = str(e)
 
    raw_scores = []
    if video_result is not None:
        raw_scores.append(_to_raw_score(video_result["label"], video_result["confidence"]))
    if audio_result is not None:
        raw_scores.append(_to_raw_score(audio_result["label"], audio_result["confidence"]))
    if movement_result is not None:
      
        movement_raw = _to_raw_score(movement_result["label"], movement_result["confidence"])
        raw_scores.append(0.5 + (movement_raw - 0.5) * 0.5)
 
    if not raw_scores:
        raise RuntimeError(
            f"All analyses failed. Video: {video_error}. Audio: {audio_error}. "
            f"Movement: {movement_error}."
        )
 
    combined_raw = sum(raw_scores) / len(raw_scores)
    is_real = combined_raw >= 0.5
    combined_confidence = round(min(50 + abs(combined_raw - 0.5) * 100, 99.0), 1)
 
    return {
        "label": "REAL" if is_real else "LIKELY FAKE",
        "confidence": combined_confidence,
        "video_result": video_result,
        "video_error": video_error,
        "audio_result": audio_result,
        "audio_error": audio_error,
        "movement_result": movement_result,
        "movement_error": movement_error,
    }
 
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python combined_detect.py human.mp4")
        sys.exit(1)
 
    result = analyze_combined(sys.argv[1])
 
    print("\n--- Video ---")
    if result["video_result"]:
        print(f"  Verdict: {result['video_result']['label']}  ({result['video_result']['confidence']}%)")
    else:
        print(f"  Failed: {result['video_error']}")
 
    print("\n--- Audio ---")
    if result["audio_result"]:
        print(f"  Verdict: {result['audio_result']['label']}  ({result['audio_result']['confidence']}%)")
    else:
        print(f"  Failed: {result['audio_error']}")
 
    print("\n--- Movement (Gemini) ---")
    if result["movement_result"]:
        print(f"  Verdict: {result['movement_result']['label']}  ({result['movement_result']['confidence']}%)")
        print(f"  Reasoning: {result['movement_result']['reasoning']}")
    else:
        print(f"  Failed: {result['movement_error']}")
 
    print("\n--- COMBINED ---")
    print(f"  Verdict:    {result['label']}")
    print(f"  Confidence: {result['confidence']}%")
 
    try:
        from arduino_serial import send_to_arduino
        send_to_arduino(result["label"], result["confidence"])
    except Exception as e:
        print(f"(Arduino display update skipped: {e})")
 
