"""Spatial mask cleanup and bounded, time-aware temporal filtering."""

import math

import cv2
import numpy as np


class MaskProcessor:
    """Remove small regions, close holes, feather edges and reduce flicker.

    Area is a fraction of the frame, so filtering scales with resolution.
    Temporal filtering uses a short time constant rather than a fixed FPS.
    """

    def __init__(self, kernel_size=3, feather_size=5,
                 min_area_ratio=0.0005, temporal_seconds=0.045):
        for value in (kernel_size, feather_size):
            if not isinstance(value, int) or value < 1 or value % 2 != 1:
                raise ValueError("Kernel sizes must be positive odd integers")
        if not 0 <= min_area_ratio <= 1:
            raise ValueError("Minimum area ratio must be between 0 and 1")
        if not math.isfinite(temporal_seconds) or temporal_seconds < 0:
            raise ValueError("Temporal time constant must be finite and nonnegative")
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
        self.feather_size = feather_size
        self.min_area_ratio = min_area_ratio
        self.temporal_seconds = temporal_seconds
        self._previous = None

    def reset(self):
        """Discard history after a capture, colour or resolution change."""
        self._previous = None

    def process(self, mask, dt=1 / 30):
        if mask.ndim != 2 or mask.dtype != np.uint8:
            raise ValueError("Mask must be a two-dimensional uint8 array")
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("Frame duration must be finite and positive")
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, self.kernel)
        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        regions = np.zeros_like(mask)
        min_area = mask.size * self.min_area_ratio
        for contour in contours:
            if cv2.contourArea(contour) >= min_area:
                cv2.drawContours(regions, [contour], -1, 255, cv2.FILLED)
        # Intersect to preserve real holes instead of filling all interiors.
        cleaned = cv2.bitwise_and(cleaned, regions)
        spatial = cv2.GaussianBlur(
            cleaned, (self.feather_size, self.feather_size), 0
        ).astype(np.float32)
        if self._previous is not None and self._previous.shape == mask.shape:
            weight = (1.0 if self.temporal_seconds == 0 else
                      -math.expm1(-dt / self.temporal_seconds))
            spatial = self._previous + weight * (spatial - self._previous)
        self._previous = spatial
        return np.clip(np.rint(spatial), 0, 255).astype(np.uint8)
