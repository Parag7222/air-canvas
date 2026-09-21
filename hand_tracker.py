import os
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

# Landmark connection definitions for hand skeleton
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (9, 10), (10, 11), (11, 12),
    # Ring finger
    (13, 14), (14, 15), (15, 16),
    # Pinky finger
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm base connections
    (5, 9), (9, 13), (13, 17)
]

class HandTracker:
    def __init__(self, model_path=MODEL_PATH, min_detection_confidence=0.6, min_tracking_confidence=0.5):
        # Automatically download model asset if missing
        if not os.path.exists(model_path):
            print(f"[HandTracker] Downloading model to {model_path}...")
            urllib.request.urlretrieve(MODEL_URL, model_path)
            print("[HandTracker] Model downloaded successfully.")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.latest_landmarks = []

    def process_frame(self, frame_bgr):
        """Processes a BGR OpenCV frame and returns a list of (x, y) pixel coordinates."""
        h, w, _ = frame_bgr.shape
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        result = self.detector.detect(mp_image)
        self.latest_landmarks = []

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            hand = result.hand_landmarks[0]
            for lm in hand:
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                self.latest_landmarks.append((cx, cy))

        return self.latest_landmarks

    def get_fingers_up(self, landmarks=None):
        """
        Determines which fingers are extended: [thumb, index, middle, ring, pinky].
        A finger is considered UP if its tip (id 8, 12, 16, 20) is higher (smaller y)
        than its PIP joint (id 6, 10, 14, 18).
        """
        lm = landmarks if landmarks is not None else self.latest_landmarks
        if not lm or len(lm) < 21:
            return [False, False, False, False, False]

        fingers = []

        # Thumb: compare tip (4) with IP joint (3) and MCP (2)
        # Check vertical height or horizontal spread
        thumb_is_up = lm[4][1] < lm[3][1] or abs(lm[4][0] - lm[2][0]) > 40
        fingers.append(thumb_is_up)

        # Index, Middle, Ring, Pinky: tip Y < PIP joint Y
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]

        for tip, pip in zip(tip_ids, pip_ids):
            fingers.append(lm[tip][1] < lm[pip][1])

        return fingers

    def draw_skeleton(self, frame, landmarks=None, color=(56, 189, 248), radius=5):
        """Draws aesthetic glowing joints and bones on the given frame."""
        lm = landmarks if landmarks is not None else self.latest_landmarks
        if not lm or len(lm) < 21:
            return frame

        # Draw bones
        for start_idx, end_idx in HAND_CONNECTIONS:
            pt1 = lm[start_idx]
            pt2 = lm[end_idx]
            cv2.line(frame, pt1, pt2, (100, 100, 100), 2, cv2.LINE_AA)

        # Draw joints
        for idx, (x, y) in enumerate(lm):
            # Highlight index tip and middle tip
            if idx == 8:
                cv2.circle(frame, (x, y), radius + 4, (0, 255, 255), -1, cv2.LINE_AA)
            elif idx == 12:
                cv2.circle(frame, (x, y), radius + 2, (255, 200, 0), -1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (x, y), radius, color, -1, cv2.LINE_AA)

        return frame
