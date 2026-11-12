"""Optional MediaPipe Hands recognition with stable observations and cooldown."""
from time import monotonic

import cv2
import numpy as np


def classify_hand(landmarks):
    """Classify four fingers by tip distance to wrist vs PIP distance.

    Distance ratios avoid depending on whether the hand points up or down.
    Ambiguous/partial poses intentionally produce no command.
    """
    points = np.array([(p.x, p.y, p.z) for p in landmarks])
    extended = []
    folded = []
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        tip_distance = np.linalg.norm(points[tip] - points[0])
        pip_distance = np.linalg.norm(points[pip] - points[0])
        extended.append(tip_distance > pip_distance * 1.2)
        folded.append(tip_distance < pip_distance * 0.9)
    if all(extended):
        return 'activate'
    if all(folded):
        return 'deactivate'
    return None


class HandGesture:
    def __init__(self, cooldown=1.5):
        import mediapipe as mp
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1, min_detection_confidence=0.65,
            min_tracking_confidence=0.65)
        self.cooldown = cooldown
        self.last_trigger = float('-inf')
        self.candidate = None
        self.count = 0
        self.last_inference = float('-inf')

    def update(self, frame):
        now = monotonic()
        if now - self.last_inference < 0.1:
            return None
        self.last_inference = now
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if rgb.shape[1] > 640:
            rgb = cv2.resize(rgb, (640, round(rgb.shape[0] * 640 / rgb.shape[1])))
        result = self.hands.process(rgb)
        command = (classify_hand(result.multi_hand_landmarks[0].landmark)
                   if result.multi_hand_landmarks else None)
        self.count = self.count + 1 if command == self.candidate else 1
        self.candidate = command
        if command and self.count >= 3 and now - self.last_trigger >= self.cooldown:
            self.last_trigger = now
            return command
        return None

    def close(self):
        self.hands.close()
