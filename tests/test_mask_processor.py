"""Noise, edges, temporal response and integration regression tests."""

import numpy as np
import pytest

from core.frame_processor import FrameProcessor
from core.mask_processor import MaskProcessor


def test_cleanup_noise_holes_and_small_regions():
    mask = np.zeros((200, 200), np.uint8)
    mask[40:140, 40:140] = 255
    mask[80, 80] = 0
    mask[10, 10] = 255
    mask[170:175, 170:175] = 255
    result = MaskProcessor(feather_size=1, min_area_ratio=0.001).process(mask)
    assert result[80, 80] == 255
    assert result[10, 10] == 0
    assert result[172, 172] == 0
    assert result[100, 100] == 255


def test_feather_preserves_interiors_and_real_holes():
    mask = np.zeros((80, 80), np.uint8)
    mask[10:70, 10:70] = 255
    mask[30:50, 30:50] = 0
    result = MaskProcessor().process(mask)
    assert 0 < result[10, 20] < 255
    assert result[20, 20] == 255
    assert result[40, 40] == 0
    assert result[0, 0] == 0


def test_temporal_flicker_decay_reset_and_resolution():
    processor = MaskProcessor(kernel_size=1, feather_size=1)
    full = np.full((20, 20), 255, np.uint8)
    empty = np.zeros_like(full)
    processor.process(full)
    first = processor.process(empty, dt=1 / 30)
    assert 0 < first[10, 10] < 255
    last = first
    for _ in range(20):
        last = processor.process(empty, dt=1 / 30)
    assert last.max() == 0
    processor.reset()
    assert processor.process(full).min() == 255
    assert processor.process(np.zeros((10, 10), np.uint8)).max() == 0


def test_temporal_response_is_frame_rate_independent():
    results = []
    for fps in (30, 60):
        processor = MaskProcessor(kernel_size=1, feather_size=1)
        processor.process(np.zeros((10, 10), np.uint8))
        for _ in range(fps // 10):
            result = processor.process(np.full((10, 10), 255, np.uint8), 1 / fps)
        results.append(result)
    assert np.array_equal(*results)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kernel_size": 2},
        {"feather_size": 0},
        {"min_area_ratio": -1},
        {"temporal_seconds": float("nan")},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        MaskProcessor(**kwargs)


def test_refined_pipeline_and_preset_change():
    engine = FrameProcessor(background_frames=3)
    background = np.full((100, 100, 3), 30, np.uint8)
    engine.background.start()
    for _ in range(3):
        engine.process(background)
    scene = background.copy()
    scene[20:80, 20:80] = (0, 255, 0)
    scene[5, 5] = (0, 255, 0)
    engine.mask_processor.reset()
    output, mask = engine.process(scene)
    assert np.array_equal(output[50, 50], background[50, 50])
    assert 0 < mask[20, 40] < 255
    assert np.array_equal(output[5, 5], scene[5, 5])
    engine.detector.set_preset("blue")
    output, mask = engine.process(scene)
    assert not mask.any()  # no stale green silhouette after colour change
    assert np.array_equal(output, scene)


def test_toggle_resets_temporal_history():
    engine = FrameProcessor(mask_options={"temporal_seconds": 100})
    green = np.full((40, 40, 3), (0, 255, 0), np.uint8)
    engine.process(green)
    engine.enabled = False
    blank = np.zeros_like(green)
    engine.process(blank)
    engine.enabled = True
    _, mask = engine.process(blank)
    assert not mask.any()


def test_capture_completion_resets_history():
    engine = FrameProcessor(background_frames=3, mask_options={"temporal_seconds": 100})
    engine.process(np.full((40, 40, 3), (0, 255, 0), np.uint8))
    engine.background.start()
    for _ in range(3):
        output, mask = engine.process(np.zeros((40, 40, 3), np.uint8))
    assert not mask.any()
    assert not output.any()
    assert not engine.background.capturing


def test_temporal_disabled_responds_immediately():
    processor = MaskProcessor(temporal_seconds=0)
    processor.process(np.full((40, 40), 255, np.uint8))
    assert not processor.process(np.zeros((40, 40), np.uint8)).any()
