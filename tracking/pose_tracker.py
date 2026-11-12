"""Optional throttled MediaPipe Pose anchor for the shield."""

from time import monotonic

import cv2
import numpy as np


class PoseTracker:
    def __init__(self):
        import mediapipe as mp

        self.pose = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.6)
        self.last = float("-inf")
        self.bounds = None

    def update(self, frame):
        now = monotonic()
        if now - self.last < 0.1:
            return self.bounds
        self.last = now
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(cv2.resize(frame, (320, round(h * 320 / w))), cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        self.bounds = None
        if result.pose_landmarks:
            visible = [
                (p.x * w, p.y * h) for p in result.pose_landmarks.landmark if p.visibility > 0.6
            ]
            if len(visible) >= 6:
                points = np.asarray(visible)
                x, y = np.maximum(points.min(axis=0), 0)
                right, bottom = np.minimum(points.max(axis=0), (w - 1, h - 1))
                self.bounds = (x, y, max(1, right - x), max(1, bottom - y))
        return self.bounds

    def close(self):
        self.pose.close()
