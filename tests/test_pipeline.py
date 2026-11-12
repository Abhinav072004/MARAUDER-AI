"""Deterministic Phase 1 tests without a webcam or desktop."""

import cv2
import numpy as np
import pytest

from core.background_capture import BackgroundCapture
from core.cloak_detector import CloakDetector
from core.frame_processor import FrameProcessor
from core.invisibility_engine import composite


@pytest.mark.parametrize("color,hues", [
    ("green", [60]), ("blue", [110]), ("red", [0, 179]),
])
def test_presets(color, hues):
    detector = CloakDetector(color)
    for hue in hues:
        hsv = np.array([[[hue, 255, 255], [30, 0, 100]]], np.uint8)
        mask = detector.detect(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
        assert mask.tolist() == [[255, 0]]


def test_calibration_wraparound_and_roundtrip(tmp_path):
    detector = CloakDetector()
    detector.set_bounds([170, 100, 50], [10, 255, 255])
    path = tmp_path / "calibration.json"
    detector.save(path)
    loaded = CloakDetector()
    loaded.load(path)
    hsv = np.array([[[179, 255, 255], [0, 255, 255], [60, 255, 255]]], np.uint8)
    assert loaded.detect(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)).tolist() == [[255, 255, 0]]


def test_invalid_color_and_bounds():
    with pytest.raises(ValueError):
        CloakDetector("purple")
    with pytest.raises(ValueError):
        CloakDetector().set_bounds([180, 0, 0], [179, 255, 255])
    with pytest.raises(ValueError):
        CloakDetector().set_bounds([0, 200, 0], [179, 100, 255])


def test_background_median_lock_and_recapture():
    capture = BackgroundCapture(3)
    capture.start()
    for value in (20, 255, 20):
        capture.update(np.full((4, 4, 3), value, np.uint8))
    assert np.all(capture.background == 20)
    assert not capture.capturing
    capture.update(np.zeros((4, 4, 3), np.uint8))
    assert np.all(capture.background == 20)
    capture.start()
    for _ in range(3):
        capture.update(np.full((4, 4, 3), 40, np.uint8))
    assert np.all(capture.background == 40)


def test_alpha_compositing_and_missing_background():
    frame = np.full((2, 2, 3), 200, np.uint8)
    background = np.full_like(frame, 100)
    mask = np.array([[255, 0], [128, 255]], np.uint8)
    result = composite(frame, background, mask)
    assert result[0, 0].tolist() == [100] * 3
    assert result[0, 1].tolist() == [200] * 3
    assert result[1, 0].tolist() == [149] * 3
    assert np.array_equal(composite(frame, None, mask), frame)
    assert np.array_equal(composite(frame, background, mask, 0), frame)
    with pytest.raises(ValueError):
        composite(frame, background[:1], mask)


def test_complete_pipeline_and_toggle():
    engine = FrameProcessor(background_frames=3)
    background = np.full((48, 64, 3), (50, 40, 30), np.uint8)
    engine.background.start()
    for _ in range(3):
        engine.process(background)
    scene = background.copy()
    scene[10:40, 20:50] = (0, 255, 0)
    scene[0:5, 0:5] = (255, 0, 0)
    output, mask = engine.process(scene)
    assert np.array_equal(output[10:40, 20:50], background[10:40, 20:50])
    assert np.array_equal(output[0:5, 0:5], scene[0:5, 0:5])
    assert np.count_nonzero(mask) == 900
    engine.enabled = False
    assert np.array_equal(engine.process(scene)[0], scene)
    engine.enabled = True
    engine.process(scene[:24])
    assert engine.background.background is None
