"""Additional rendered modes, compositing controls and state invariants."""
import numpy as np

from core.frame_processor import FrameProcessor
from effects.magic_shield import render_shield
from effects.reveal_mode import render_reveal
from effects.time_freeze import TimeFreeze
from interaction.controller import Controller


def test_freeze_preserves_output_and_resume():
    freeze = TimeFreeze()
    a = np.zeros((30, 30, 3), np.uint8)
    b = np.full_like(a, 100)
    freeze.enabled = True
    assert not freeze.render(a).any()
    assert not freeze.render(b).any()
    freeze.enabled = False
    assert np.array_equal(freeze.render(b), b)


def test_freeze_does_not_stop_background_capture():
    processor = FrameProcessor(background_frames=3)
    processor.effects.freeze.enabled = True
    processor.background.start()
    for value in (30, 40, 50):
        processor.process(np.full((40, 40, 3), value, np.uint8))
    assert not processor.background.capturing
    assert np.all(processor.background.background == 40)


def test_reveal_and_shield_have_visible_output():
    frame = np.zeros((100, 120, 3), np.uint8)
    mask = np.zeros((100, 120), np.uint8)
    mask[30:80, 40:90] = 255
    assert render_reveal(frame, mask, 0).any()
    assert render_reveal(frame, mask, 0, heatmap=True).any()
    assert render_shield(frame, (40, 30, 50, 50), 0).any()
    assert np.array_equal(render_shield(frame, None, 0), frame)


def test_additional_shortcuts_and_intensity():
    processor = FrameProcessor(refine=False)
    controller = Controller(processor)
    controller.audio.enabled = False
    for key, field in [('r', 'reveal'), ('h', 'shield'), ('p', 'ambient')]:
        controller.key(key)
        assert getattr(processor.effects, field)
        controller.key(key)
    controller.key('t')
    assert processor.effects.freeze.enabled
    controller.key('t')
    processor.background.background = np.zeros((30, 30, 3), np.uint8)
    processor.effects.intensity = 0
    green = np.full((30, 30, 3), (0, 255, 0), np.uint8)
    assert np.array_equal(processor.process(green)[0], green)
    controller.close()
