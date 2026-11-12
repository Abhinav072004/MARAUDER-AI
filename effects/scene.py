"""Composable effects orchestrator; motion comes from the original camera frame."""
import cv2
import numpy as np

from effects.footsteps import Footsteps
from effects.ghost_mode import GhostMode
from effects.particle_engine import ParticleEngine
from tracking.motion_tracker import MotionTracker


class SceneEffects:
    def __init__(self, floor_mapping=None):
        self.ghost = False
        self.footsteps = False
        self.sparkles = False
        self.intensity = 1.0
        self.particle_intensity = 1.0
        self.tracker = MotionTracker()
        self.steps = Footsteps(floor_mapping)
        self.particles = ParticleEngine()
        self.ghost_effect = GhostMode()
        self.time = 0.0
        self._shape = None
        self.motion = None

    def render(self, frame, output, background, mask, dt, enabled=True):
        dt = min(dt, 0.2)
        self.time += dt
        if self._shape != frame.shape:
            self.tracker.reset()
            self.steps.steps.clear()
            self.steps.last = None
            self.particles.particles.clear()
            self._shape = frame.shape
        motion = self.tracker.update(frame, mask, dt)
        self.motion = motion
        if self.ghost and enabled:
            output = self.ghost_effect.render(frame, background, mask,
                                               self.time, self.intensity)
        if self.footsteps:
            self.steps.update(motion, dt)
            output = self.steps.draw(output)
        else:
            self.steps.steps.clear()
            self.steps.last = None
            self.steps.distance = 0
        points = np.empty((0, 2))
        if self.sparkles and motion.speed > 8:
            contours, _ = cv2.findContours(np.uint8(mask > 127) * 255,
                                          cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if contours:
                points = np.concatenate(contours).reshape(-1, 2)
        rate = min(240, motion.speed) * self.particle_intensity
        self.particles.emit(points, rate, dt)
        self.particles.update(dt, frame.shape)
        if self.particles.particles:
            output = self.particles.draw(output)
        return output
