"""Cloak motion from sparse Lucas–Kanade flow and observed silhouette bounds."""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Motion:
    position: tuple | None = None
    velocity: tuple = (0.0, 0.0)
    speed: float = 0.0
    bounds: tuple | None = None


class MotionTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = None
        self.points = None
        self.position = None

    def update(self, frame, mask, dt):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        binary = np.uint8(mask > 127) * 255
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self.reset()
            return Motion()
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        position = (x + w / 2, float(y + h - 1))
        displacement = None
        if (
            self.previous is not None
            and self.previous.shape == gray.shape
            and self.points is not None
            and len(self.points)
        ):
            points, status, _ = cv2.calcOpticalFlowPyrLK(
                self.previous, gray, self.points, None, winSize=(21, 21), maxLevel=2
            )
            if points is not None and status is not None:
                valid = status.ravel() == 1
                moved = points[valid].reshape(-1, 2)
                old = self.points[valid].reshape(-1, 2)
                if len(moved) >= 3:
                    # Reject tracks outside the current cloak or image.
                    ix = np.clip(moved[:, 0].astype(int), 0, gray.shape[1] - 1)
                    iy = np.clip(moved[:, 1].astype(int), 0, gray.shape[0] - 1)
                    inside = binary[iy, ix] > 0
                    if inside.sum() >= 3:
                        displacement = np.median(moved[inside] - old[inside], axis=0)
        # Textureless cloth cannot supply reliable flow: use observed bounds.
        if displacement is None and self.position is not None:
            displacement = np.subtract(position, self.position)
        velocity = (
            (0.0, 0.0) if displacement is None else tuple(np.asarray(displacement) / max(dt, 1e-6))
        )
        self.previous = gray
        self.points = cv2.goodFeaturesToTrack(
            gray, maxCorners=80, qualityLevel=0.02, minDistance=6, mask=binary
        )
        self.position = position
        return Motion(position, velocity, float(np.linalg.norm(velocity)), (x, y, w, h))
