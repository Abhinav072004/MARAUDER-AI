"""Deterministic effects and measured-motion tests without physical devices."""
import cv2
import numpy as np
import pytest

from effects.footsteps import Footsteps
from effects.ghost_mode import GhostMode
from effects.particle_engine import Particle, ParticleEngine
from tracking.floor_mapping import FloorMapping
from tracking.motion_tracker import Motion, MotionTracker


def test_particle_capacity_motion_and_expiration():
    engine = ParticleEngine(capacity=10, seed=42)
    engine.emit([(50, 50)], 1000, 1)
    assert len(engine.particles) == 10
    particle = engine.particles[0]
    old = (particle.x, particle.y)
    engine.update(0.1, (100, 100, 3))
    assert (particle.x, particle.y) != old
    assert 0 < particle.opacity < 1
    assert engine.draw(np.zeros((100, 100, 3), np.uint8)).any()
    engine.update(5, (100, 100, 3))
    assert not engine.particles
    p = Particle(0, 0, 1, 1, 0.5, 2)
    p.update(1)
    assert p.opacity == 0


def test_footsteps_require_actual_displacement_and_fade():
    steps = Footsteps(spacing=20)
    for _ in range(20):
        steps.update(Motion((50, 80), (0, 0), 0), 1 / 30)
    assert not steps.steps
    for x in range(55, 140, 5):
        steps.update(Motion((x, 80), (150, 0), 150), 1 / 30)
    assert len(steps.steps) == 4
    assert all(50 <= p[0] <= 140 for p, *_ in steps.steps)
    assert steps.draw(np.zeros((120, 160, 3), np.uint8)).any()
    steps.update(Motion(), 4)
    assert not steps.steps


def test_optical_flow_follows_translated_texture():
    rng = np.random.default_rng(1)
    frame = np.zeros((160, 200, 3), np.uint8)
    frame[30:120, 30:120] = rng.integers(0, 256, (90, 90, 3), dtype=np.uint8)
    mask = np.zeros((160, 200), np.uint8)
    mask[30:120, 30:120] = 255
    tracker = MotionTracker()
    tracker.update(frame, mask, 0.1)
    transform = np.float32([[1, 0, 5], [0, 1, 0]])
    moved = tracker.update(cv2.warpAffine(frame, transform, (200, 160)),
                           cv2.warpAffine(mask, transform, (200, 160)), 0.1)
    assert moved.velocity[0] == pytest.approx(50, abs=3)
    assert abs(moved.velocity[1]) < 3
    assert moved.position == (80.0, 119.0)
    assert tracker.update(frame, np.zeros_like(mask), 0.1).position is None


def test_floor_mapping_round_trip_and_invalid_input():
    mapping = FloorMapping([(0, 0), (100, 0), (80, 100), (20, 100)],
                           [(0, 0), (100, 0), (100, 100), (0, 100)])
    point = (40, 60)
    assert mapping.to_image(mapping.to_floor(point)) == pytest.approx(point)
    with pytest.raises(ValueError):
        FloorMapping([(0, 0)] * 4, [(0, 0)] * 4)


def test_ghost_only_changes_cloak_and_requires_background():
    frame = np.full((80, 100, 3), 200, np.uint8)
    background = np.full_like(frame, 40)
    mask = np.zeros((80, 100), np.uint8)
    mask[20:60, 20:80] = 255
    ghost = GhostMode()
    assert np.array_equal(ghost.render(frame, None, mask, 0), frame)
    output = ghost.render(frame, background, mask, 0)
    assert np.all(output[40, 50] == 120)
    assert np.array_equal(output[0, 0], frame[0, 0])
