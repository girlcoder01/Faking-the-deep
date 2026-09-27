
"""
Standalone movement-naturalness check using Gemini.
 
Unlike MesoNet (video/face) and the Hugging Face audio model, there is
no pretrained "movement deepfake detector" model to download -- nobody
has published a clean one. Instead, this uploads the video to Gemini
and asks it to reason directly about whether the body/face movement
looks natural, since Gemini can watch and understand video content.
 
Because this is a judgment call from a general-purpose model rather
than a trained classifier's probability score, treat its output as a
qualitative second opinion, not a precise percentage the way the other
two modalities are.
 
Setup required before running:
    1. Get a free API key from https://aistudio.google.com/apikey
    2. Set it as an environment variable:
         Mac/Linux:   export GEMINI_API_KEY="your-key-here"
         Windows:     set GEMINI_API_KEY=your-key-here
       (Run that in the same terminal window before running this script,
       or add it to your shell's profile so it's always set.)
 
Usage:
    python gemini_movement.py human.mp4
"""
 
import sys
import os
import time
import json
import re
 
from google import genai
 
 
def analyze_movement(video_path: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "See the instructions at the top of this file."
        )
 
    client = genai.Client(api_key=api_key)
 
    print("Uploading video to Gemini...")
    video_file = client.files.upload(file=video_path)

    while video_file.state.name == "PROCESSING":
        print("  still processing...")
        time.sleep(3)
        video_file = client.files.get(name=video_file.name)
 
    if video_file.state.name != "ACTIVE":
        raise RuntimeError(f"Video upload failed to process (state: {video_file.state.name})")
 
    prompt = """
You are analyzing a video clip to judge whether the movement of the
person's face and body looks NATURAL (consistent with a real human
recording) or UNNATURAL (showing signs of AI generation/deepfake
manipulation, such as jittery motion, inconsistent lighting on moving
parts, warping around the edges of the face during movement, or
physically implausible motion).
 
Respond with ONLY a JSON object in this exact format, no other text:
{"verdict": "NATURAL" or "UNNATURAL", "confidence": <integer 0-100>, "reasoning": "<one sentence>"}
 
IMPORTANT: "confidence" means how confident YOU are that your verdict is
correct -- NOT the likelihood that the video is fake. For example, if
you conclude NATURAL and you are very sure about that, confidence
should be high (e.g. 90). If you conclude UNNATURAL and you are very
sure about that, confidence should also be high (e.g. 90). Only use a
low confidence number when you are genuinely unsure which verdict is
correct.
"""
 
    print("Analyzing movement...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[video_file, prompt],
    )
 
    raw_text = response.text.strip()
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text, flags=re.MULTILINE).strip()
 
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse Gemini's response as JSON. Raw response: {raw_text}")
 
    is_natural = parsed["verdict"].upper() == "NATURAL"
 
    return {
        "label": "REAL" if is_natural else "LIKELY FAKE",
        "confidence": float(parsed["confidence"]),
        "reasoning": parsed.get("reasoning", ""),
    }
 
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gemini_movement.py human.mp4")
        sys.exit(1)
 
    result = analyze_movement(sys.argv[1])
    print("\n--- Movement Result (Gemini) ---")
    print(f"Verdict:    {result['label']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Reasoning:  {result['reasoning']}")
 
