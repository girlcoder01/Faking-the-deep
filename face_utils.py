"""
Frame + face extraction from a video file, using only OpenCV's built-in
Haar cascade face detector (ships inside opencv-python, no separate
download). It's less accurate than a modern DNN face detector, but it's
zero-setup, which matters for a first working v1.

Upgrade path (later): swap `_get_face_detector` for OpenCV's DNN
face detector or MTCNN for better accuracy on angled/low-light faces.
"""

import cv2
import numpy as np

FACE_SIZE = 256  # must match mesonet_model.IMG_WIDTH


def _get_face_detector():
    """
    Returns an OpenCV Haar cascade face detector, or None if this
    particular OpenCV build doesn't include it (this can happen on
    very new/unsupported Python versions where only a partial OpenCV
    build is available). Callers must handle the None case.
    """
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        if detector.empty():
            return None
        return detector
    except AttributeError:
        return None


def _center_crop(frame):
    """
    Fallback when no face detector is available: just take a centered
    square region of the frame. Works fine for typical talking-head
    clips where the face is roughly centered, but is less robust than
    real face detection.
    """
    h, w = frame.shape[:2]
    side = min(h, w)
    y0 = (h - side) // 2
    x0 = (w - side) // 2
    return frame[y0:y0 + side, x0:x0 + side]


def extract_face_crops(video_path: str, max_frames: int = 30, frame_stride: int = 10):
    """
    Reads a video, samples frames, finds the largest face in each sampled
    frame, and returns a list of (frame_index, face_crop) where face_crop
    is a 256x256x3 float32 array scaled to [0, 1].

    max_frames: cap on how many sampled frames we actually process
    frame_stride: take every Nth frame when sampling (keeps this fast)
    """
    detector = _get_face_detector()
    if detector is None:
        print(
            "Note: this OpenCV build doesn't include face detection "
            "(CascadeClassifier). Falling back to using the center of "
            "each frame instead. For best results, film with your face "
            "centered in the frame."
        )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    crops = []
    frame_idx = 0
    sampled = 0

    while sampled < max_frames:
        ret, frame = cap.read()
        if not ret:
            break  # end of video

        if frame_idx % frame_stride == 0:
            face = None

            if detector is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
                )
                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    face = frame[y:y + h, x:x + w]

            if face is None and detector is None:
                face = _center_crop(frame)

            if face is not None:
                face = cv2.resize(face, (FACE_SIZE, FACE_SIZE))
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                crops.append((frame_idx, face))
            sampled += 1

        frame_idx += 1

    cap.release()
    return crops
