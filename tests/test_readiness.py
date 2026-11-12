"""Scene warnings, real optional inference, voice worker and video validation."""

from queue import Empty
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from core.scene_monitor import SceneMonitor
from interaction.voice_controller import VoiceController
from tools.validate_demo import render_demo


def test_scene_warning_requires_persistent_visible_background_change():
    monitor = SceneMonitor()
    background = np.zeros((90, 160, 3), np.uint8)
    mask = np.zeros((90, 160), np.uint8)
    assert not monitor.update(background, background, mask, 0.1)
    changed = np.full_like(background, 120)
    assert not monitor.update(changed, background, mask, 0.1)
    for _ in range(8):
        monitor.update(changed, background, mask, 0.1)
    assert monitor.warning
    monitor.reset()
    mask[:] = 255  # Too little visible background is not evidence of movement.
    for _ in range(10):
        monitor.update(changed, background, mask, 0.1)
    assert not monitor.warning


def test_cloak_motion_does_not_raise_scene_warning():
    monitor = SceneMonitor()
    background = np.zeros((90, 160, 3), np.uint8)
    frame = background.copy()
    frame[20:70, 40:100] = (0, 255, 0)
    mask = np.zeros((90, 160), np.uint8)
    mask[20:70, 40:100] = 255
    for _ in range(20):
        assert not monitor.update(frame, background, mask, 1 / 30)


def test_synthetic_recording_is_decodable_and_complete(tmp_path):
    result = render_demo(320, 240, 6, tmp_path / "demo.avi", mode="all")
    assert result["frames"] == 6
    assert result["processing_fps"] > 0
    assert result["particles"] <= 400


def test_voice_worker_emits_command_and_stops(tmp_path):
    class Recognizer:
        def __init__(self, *args):
            pass

        def AcceptWaveform(self, data):
            return True

        def Result(self):
            return '{"text":"lumos"}'

    class Stream:
        def __init__(self, **kwargs):
            self.callback = kwargs["callback"]

        def __enter__(self):
            self.callback(b"pcm audio", 1, None, None)
            return self

        def __exit__(self, *args):
            return False

    voice = VoiceController(str(tmp_path))
    modules = {
        "sounddevice": SimpleNamespace(RawInputStream=Stream),
        "vosk": SimpleNamespace(Model=lambda path: object(), KaldiRecognizer=Recognizer),
    }
    try:
        with patch.dict("sys.modules", modules):
            voice.start()
            try:
                assert voice.commands.get(timeout=2) == "activate"
            except Empty:
                pytest.fail(voice.status)
            voice.stop()
            assert not voice.running
    finally:
        voice.stop()


def test_real_optional_mediapipe_models_on_blank_frame(monkeypatch):
    pytest.importorskip("mediapipe")
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/marauder-mpl")
    from tracking.hand_gesture import HandGesture
    from tracking.pose_tracker import PoseTracker
    from core.person_segmentation import PersonSegmentation

    frame = np.zeros((120, 160, 3), np.uint8)
    hands = HandGesture()
    pose = PoseTracker()
    person = PersonSegmentation()
    try:
        assert hands.update(frame) is None
        assert pose.update(frame) is None
        assert not person.refine(frame, np.zeros((120, 160), np.uint8)).any()
        assert person.last_mask.shape == (120, 160)
        assert person.last_mask.dtype == np.uint8
    finally:
        hands.close()
        pose.close()
        person.close()
