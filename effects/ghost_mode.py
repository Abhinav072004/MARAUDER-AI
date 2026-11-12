"""Partial background replacement with a cyan shimmering boundary."""

import cv2
import numpy as np

from core.invisibility_engine import composite


class GhostMode:
    def __init__(self):
        self._grid = None
        self._shape = None

    def render(self, frame, background, mask, time, intensity=1.0):
        if background is None:
            return frame.copy()
        h, w = mask.shape
        if self._shape != (h, w):
            self._grid = np.mgrid[:h, :w].astype(np.float32)
            self._shape = (h, w)
        yy, base_x = self._grid
        offsets = 2.5 * np.sin(yy[:, 0] * 0.06 + time * 4)
        xx = base_x + offsets[:, None]
        shimmer = cv2.remap(background, xx, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        result = composite(frame, shimmer, mask, intensity * 0.5)
        edge = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
        glow = cv2.GaussianBlur(edge, (11, 11), 0).astype(np.float32) / 255
        cyan = np.array([255, 210, 70], np.float32)
        return np.clip(
            result + glow[..., None] * cyan * (0.35 + 0.15 * np.sin(time * 5)) * intensity, 0, 255
        ).astype(np.uint8)
