"""Alternating, fading steps emitted only along observed movement paths."""
import math

import cv2
import numpy as np


class Footsteps:
    def __init__(self, floor_mapping=None, spacing=35):
        self.mapping = floor_mapping
        self.spacing = spacing
        self.steps = []
        self.last = None
        self.left = True
        self.heading = 0.0
        self.distance = 0.0

    def update(self, motion, dt):
        self.steps = [(p, age + dt, angle, left)
                      for p, age, angle, left in self.steps if age + dt < 3.0]
        if motion.position is None:
            self.last = None
            self.distance = 0
            return
        point = (self.mapping.to_floor(motion.position) if self.mapping
                 else motion.position)
        if self.last is not None:
            delta = np.subtract(point, self.last)
            distance = float(np.linalg.norm(delta))
            # Guard large re-acquisition jumps; no invented intervening steps.
            if motion.speed > 8 and 0 < distance < self.spacing * 5:
                heading = math.atan2(delta[1], delta[0])
                walked = self.spacing - self.distance
                while walked <= distance:
                    sample = np.asarray(self.last) + delta * (walked / distance)
                    normal = np.array([-math.sin(heading), math.cos(heading)])
                    sample += normal * (7 if self.left else -7)
                    image = self.mapping.to_image(sample) if self.mapping else sample
                    self.steps.append((tuple(image), 0.0, math.degrees(heading), self.left))
                    self.left = not self.left
                    walked += self.spacing
                self.distance = (self.distance + distance) % self.spacing
            elif distance >= self.spacing * 5:
                self.distance = 0
        self.last = point
        self.steps = self.steps[-80:]

    def draw(self, frame):
        layer = np.zeros_like(frame)
        for (x, y), age, angle, _ in self.steps:
            # Image-space fallback approximates perspective by vertical position.
            scale = np.clip(y / frame.shape[0], 0.3, 1.0)
            color = tuple(int(c * (1 - age / 3)) for c in (255, 125, 160))
            cv2.ellipse(layer, (round(x), round(y)),
                        (max(2, int(13 * scale)), max(2, int(5 * scale))),
                        angle, 0, 360, color, -1, cv2.LINE_AA)
        return cv2.add(frame, cv2.add(layer, cv2.GaussianBlur(layer, (17, 17), 0)))
