"""Composable effects orchestrator; motion comes from the original camera frame."""

import cv2
import numpy as np

from effects.footsteps import Footsteps
from effects.ghost_mode import GhostMode
from effects.particle_engine import ParticleEngine
from tracking.motion_tracker import Motion, MotionTracker
from effects.reveal_mode import render_reveal
from effects.magic_shield import render_shield
from effects.time_freeze import TimeFreeze


class SceneEffects:
    def __init__(self, floor_mapping=None):
        self.reveal = False
        self.heatmap = False
        self.shield = False
        self.ambient = False
        self.particle_color = (40, 190, 255)
        self.pose_bounds = None
        self.person_mask = None
        self.freeze = TimeFreeze()
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
        if self.footsteps or self.sparkles or self.ambient or self.shield:
            motion = self.tracker.update(frame, mask, dt)
        else:
            self.tracker.reset()
            motion = Motion()
        self.motion = motion
        if self.ghost and enabled:
            output = self.ghost_effect.render(frame, background, mask, self.time, self.intensity)
        if self.reveal:
            silhouette = self.person_mask if self.person_mask is not None else mask
            output = render_reveal(frame, silhouette, self.time, self.heatmap)
        if self.shield:
            output = render_shield(output, self.pose_bounds or motion.bounds, self.time)
        if self.footsteps:
            self.steps.update(motion, dt)
            output = self.steps.draw(output)
        else:
            self.steps.steps.clear()
            self.steps.last = None
            self.steps.distance = 0
        points = np.empty((0, 2))
        if self.sparkles and motion.speed > 8:
            contours, _ = cv2.findContours(
                np.uint8(mask > 127) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            if contours:
                points = np.concatenate(contours).reshape(-1, 2)
        if self.ambient and motion.bounds is not None:
            x, y, w, h = motion.bounds
            points = np.array([(x, y), (x + w, y), (x, y + h), (x + w, y + h)])
        rate = (min(240, motion.speed) + (50 if self.ambient else 0)) * self.particle_intensity
        self.particles.emit(points, rate, dt, self.particle_color)
        self.particles.update(dt, frame.shape)
        if self.particles.particles:
            output = self.particles.draw(output)
        return self.freeze.render(output)
