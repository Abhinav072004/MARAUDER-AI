"""Colour segmentation with hue wraparound and portable calibration files."""

import json
from pathlib import Path

import cv2
import numpy as np

from config.color_presets import PRESETS


class CloakDetector:
    def __init__(self, color="green"):
        self.set_preset(color)

    def set_preset(self, color):
        if color not in PRESETS:
            raise ValueError(f"Unknown cloak colour: {color}")
        self.color = color
        self.ranges = list(PRESETS[color])

    def set_bounds(self, lower, upper):
        self._validate(lower, upper)
        self.ranges = [(tuple(lower), tuple(upper))]
        self.color = "custom"

    @staticmethod
    def _validate(lower, upper):
        for bound in (lower, upper):
            if len(bound) != 3 or any(
                not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= limit
                for v, limit in zip(bound, (179, 255, 255))
            ):
                raise ValueError("HSV bounds require three integers: H 0–179, S/V 0–255")
        if lower[1] > upper[1] or lower[2] > upper[2]:
            raise ValueError("Saturation/value lower bounds must not exceed upper bounds")

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        for lower, upper in self.ranges:
            if lower[0] <= upper[0]:
                part = cv2.inRange(hsv, np.array(lower), np.array(upper))
            else:
                part = cv2.bitwise_or(
                    cv2.inRange(hsv, np.array((0, *lower[1:])), np.array(upper)),
                    cv2.inRange(hsv, np.array(lower), np.array((179, *upper[1:]))),
                )
            mask = cv2.bitwise_or(mask, part)
        return mask

    def save(self, path):
        Path(path).write_text(json.dumps({"ranges": self.ranges}, indent=2) + "\n")

    def load(self, path):
        ranges = json.loads(Path(path).read_text())["ranges"]
        if not isinstance(ranges, list) or not 1 <= len(ranges) <= 8:
            raise ValueError("Calibration requires 1–8 HSV ranges")
        for lower, upper in ranges:
            self._validate(lower, upper)
        self.ranges = [(tuple(lo), tuple(hi)) for lo, hi in ranges]
        self.color = "custom"
