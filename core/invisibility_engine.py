"""Vectorized alpha compositing, independent of camera and GUI."""

import numpy as np


def composite(frame, background, mask, intensity=1.0):
    """Replace masked pixels; a missing background leaves the frame intact."""
    if background is None:
        return frame.copy()
    if frame.shape != background.shape or mask.shape != frame.shape[:2]:
        raise ValueError("Frame, background and mask dimensions must match")
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    alpha = mask.astype(np.float32) / 255.0 * intensity
    alpha = alpha[..., None]
    return np.clip(frame * (1 - alpha) + background * alpha, 0, 255).astype(np.uint8)
