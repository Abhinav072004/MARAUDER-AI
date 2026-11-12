"""Conservative locked-background change warning; not a camera-motion classifier."""

import cv2
import numpy as np


class SceneMonitor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.elapsed = 0.0
        self.changed_fraction = 0.0
        self.warning = False
        self._reference = None

    def update(self, frame, background, cloak_mask, dt):
        if background is None:
            self.reset()
            return False
        size = (160, 90)
        if self._reference is None:
            reference = cv2.resize(background, size)
            self._reference = cv2.GaussianBlur(reference, (5, 5), 0)
        current = cv2.GaussianBlur(cv2.resize(frame, size), (5, 5), 0)
        visible = cv2.resize(cloak_mask, size, interpolation=cv2.INTER_NEAREST) < 16
        # Exclude a margin around the keyed cloth to reduce edge-motion alarms.
        visible = cv2.erode(visible.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        count = int(visible.sum())
        if count < visible.size * 0.25:
            self.elapsed = 0
            self.warning = False
            return False
        difference = cv2.absdiff(current, self._reference).max(axis=2)
        self.changed_fraction = float(np.count_nonzero((difference > 35) & visible) / count)
        self.elapsed = self.elapsed + min(dt, 0.2) if self.changed_fraction > 0.3 else 0
        self.warning = self.elapsed >= 0.7
        return self.warning
