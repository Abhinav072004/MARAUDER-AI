"""Explicit synthetic source for demos/tests; never presented as webcam evidence."""
from time import monotonic

import cv2
import numpy as np


class DemoCamera:
    index = 'SYNTHETIC DEMO'

    def __init__(self, width=640, height=480):
        self.width, self.height = width, height
        self.start = monotonic()
        yy, xx = np.mgrid[:height, :width]
        self.background = np.zeros((height, width, 3), np.uint8)
        self.background[:] = (35, 22, 18)
        self.background[(xx // 60 + yy // 60) % 2 == 0] = (55, 38, 28)

    def read(self):
        frame = self.background.copy()
        t = monotonic() - self.start
        if t > 1.5:
            x = round(self.width * (0.5 + 0.25 * np.sin(t)))
            y = self.height // 3
            cv2.rectangle(frame, (x - self.width // 10, y),
                          (x + self.width // 10, self.height * 4 // 5), (0, 220, 0), -1)
            # Small saturated texture supplies flow corners on the cloth.
            for offset in range(0, self.height // 3, 18):
                cv2.circle(frame, (x, y + offset), 3, (0, 155, 0), -1)
        return frame

    def close(self):
        pass  # Source owns no device or external resources.
