"""Nonblocking multi-frame median background capture."""

import numpy as np


class BackgroundCapture:
    def __init__(self, frame_count=21):
        if not 3 <= frame_count <= 31:
            raise ValueError("frame_count must be between 3 and 31")
        self.frame_count = frame_count
        self.background = None
        self._frames = []
        self.capturing = False

    @property
    def progress(self):
        return len(self._frames), self.frame_count

    def start(self):
        self._frames.clear()
        self.capturing = True

    def update(self, frame):
        if not self.capturing:
            return False
        if self._frames and frame.shape != self._frames[0].shape:
            self._frames.clear()
        self._frames.append(frame.copy())
        if len(self._frames) < self.frame_count:
            return False
        # Row chunks avoid a full-resolution float64 median temporary.
        result = np.empty_like(frame)
        for row in range(0, frame.shape[0], 64):
            stack = np.stack([f[row : row + 64] for f in self._frames])
            result[row : row + 64] = np.median(stack, axis=0).astype(np.uint8)
        self.background = result
        self._frames.clear()
        self.capturing = False
        return True
