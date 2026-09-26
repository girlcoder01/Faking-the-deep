# Deepfake Video Checker — v1

Upload a video clip → get a REAL / LIKELY FAKE verdict with a confidence score.
Uses **MesoNet**, a small pretrained face-forgery detection model. This is the
scoped-down v1: one modality (face, from an uploaded video), one existing
pretrained model (no training required), no live-call detection yet.

## What's in here
- `mesonet_model.py` — the MesoNet (Meso4) architecture, ready to load pretrained weights
- `face_utils.py` — pulls sample frames from a video and crops out the face in each
- `detect.py` — the core loop: video in → verdict out. **Run this first, from the command line, before the app.**
- `app.py` — a simple Streamlit page that wraps `detect.py` in an upload button
- `weights/` — put the downloaded model weights file here (see below)

## Step-by-step setup

### 1. Install Python
Get Python 3.10 or 3.11 from https://python.org if you don't have it.
(Check with `python3 --version` in a terminal.)

### 2. Install the dependencies
From inside this project folder:
```bash
pip install -r requirements.txt
```
If you're on a Mac with Apple Silicon and `tensorflow` fails to install, use
`tensorflow-macos` instead — ask your coding assistant to adjust
`requirements.txt` for your machine if this happens.

### 3. Get the pretrained weights
The weights are **not included here** — you need to download them once.

1. Go to the original MesoNet repo: https://github.com/DariusAf/MesoNet
2. Inside it there's a `weights/` folder containing several `.h5` files
   (e.g. `Meso4_DF.h5`, `Meso4_F2F.h5`).
3. Download `Meso4_DF.h5` and place it in this project's `weights/` folder,
   so the path `weights/Meso4_DF.h5` exists.

If that repo has moved or the file layout has changed by the time you read
this, ask your AI coding tool (e.g. Claude Code) to search GitHub for
"MesoNet pretrained weights" or "deepfake detection pretrained h5 weights"
and adapt `WEIGHTS_PATH` in `detect.py` to match — that's a normal, expected
step, not a sign something's broken.

### 4. Prove the core loop works — command line first
Find or record one short (5-10 second) video clip with a clearly visible
face, then run:
```bash
python detect.py path/to/that_video.mp4
```
You should see output like:
```
--- Result ---
Verdict:          REAL
Confidence:       78.4%
Frames analyzed:  30
Raw mean score:   0.892 (near 1 = real, near 0 = fake)
```
**Don't move on to the app until this works.** This is the actual proof
that detection works on your machine — everything else is just UI around it.

### 5. Run the app
```bash
streamlit run app.py
```
This opens a browser page with an upload button. Upload a clip, click
Analyze, see the verdict.

## Known limitations of this v1 (by design — see the original plan)
- Face detection uses OpenCV's basic built-in detector, not a state-of-the-art one — it can miss faces at odd angles or poor lighting.
- MesoNet is a small, fairly old model (2018). It's a solid *starting point*, not the most accurate detector available — good for proving the loop, worth upgrading later.
- No live-call support. This only analyzes files you upload.
- No mobile app — this is a local web page (Streamlit) for now.

## Natural next steps, once this works
- Swap the Haar cascade for a better face detector (OpenCV DNN or MTCNN)
- Try a stronger pretrained model (e.g. a FaceForensics++-trained XceptionNet checkpoint) and compare results
- Add support for analyzing multiple faces in a frame, not just the largest one
- Package as a downloadable desktop app instead of a local Streamlit server
