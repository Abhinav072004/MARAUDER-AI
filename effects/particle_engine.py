"""Bounded particle simulation with elapsed-time motion and fading glows."""
from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass
class Particle:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    lifetime: float
    particle_size: int
    color: tuple = (40, 190, 255)
    age: float = 0.0

    @property
    def opacity(self):
        return max(0.0, 1 - self.age / self.lifetime)

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.velocity_y += 15 * dt
        self.age += dt

    def draw(self, layer):
        if self.opacity <= 0:
            return
        color = tuple(int(c * self.opacity) for c in self.color)
        cv2.circle(layer, (round(self.x), round(self.y)), self.particle_size,
                   color, -1, cv2.LINE_AA)


class ParticleEngine:
    def __init__(self, capacity=400, seed=None):
        if capacity < 1:
            raise ValueError('Particle capacity must be positive')
        self.capacity = capacity
        self.particles = []
        self.rng = np.random.default_rng(seed)
        self._credit = 0.0

    def emit(self, points, rate, dt, color=(40, 190, 255)):
        if len(points) == 0 or rate <= 0:
            self._credit = 0.0
            return
        self._credit = min(self.capacity, self._credit + rate * dt)
        count = min(int(self._credit), self.capacity - len(self.particles))
        self._credit -= int(self._credit)
        for index in self.rng.integers(0, len(points), size=count):
            x, y = points[index]
            angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(12, 65)
            self.particles.append(Particle(
                float(x), float(y), math.cos(angle) * speed,
                math.sin(angle) * speed - 25, self.rng.uniform(0.4, 1.5),
                int(self.rng.integers(1, 4)), color))

    def update(self, dt, shape):
        for particle in self.particles:
            particle.update(dt)
        h, w = shape[:2]
        self.particles = [p for p in self.particles if p.opacity > 0
                          and -20 <= p.x <= w + 20 and -20 <= p.y <= h + 20]

    def draw(self, frame):
        layer = np.zeros_like(frame)
        for particle in self.particles:
            particle.draw(layer)
        glow = cv2.GaussianBlur(layer, (15, 15), 0)
        return cv2.add(frame, cv2.add(layer, glow))
