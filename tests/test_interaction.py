"""Spell parsing, state transitions, gesture geometry and async failure paths."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pytest

from core.frame_processor import FrameProcessor
from interaction.controller import Controller
from interaction.voice_controller import VoiceController, parse_spell
from tracking.hand_gesture import classify_hand


@pytest.mark.parametrize('text,expected', [
    (' Lumos ', 'activate'), ('invisibility', 'activate'),
    ('NOX', 'deactivate'), ('reveal', 'deactivate'),
    ('please say lumos now', None), ('', None),
])
def test_spell_parsing(text, expected):
    assert parse_spell(text) == expected


def test_transition_audio_only_once_and_shortcuts():
    processor = FrameProcessor()
    controller = Controller(processor)
    controller.audio = Mock()
    controller.activate(True)
    controller.audio.play.assert_not_called()
    controller.activate(False)
    controller.activate(False)
    controller.audio.play.assert_called_once_with(False)
    for key, field in [('g', 'ghost'), ('m', 'footsteps'), ('s', 'sparkles')]:
        assert controller.key(ord(key.upper()))
        assert getattr(processor.effects, field)
    controller.key('b')
    assert processor.background.capturing
    assert not controller.key('z')
    controller.voice.commands.put('activate')
    controller.update(np.zeros((10, 10, 3), np.uint8))
    assert processor.enabled
    controller.close()


def test_gesture_geometry():
    points = [SimpleNamespace(x=0., y=0., z=0.) for _ in range(21)]
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        points[pip].y = 0.5
        points[tip].y = 1.0
    assert classify_hand(points) == 'activate'
    for tip in (8, 12, 16, 20):
        points[tip].y = 0.2
    assert classify_hand(points) == 'deactivate'
    points[8].y = 1
    assert classify_hand(points) is None


def test_missing_voice_model_is_explicit():
    voice = VoiceController('/does/not/exist')
    with pytest.raises(ValueError, match='offline Vosk model'):
        voice.start()
    assert not voice.running


def test_voice_failure_does_not_crash_camera_thread(tmp_path):
    voice = VoiceController(str(tmp_path))
    with patch.dict('sys.modules', {'sounddevice': None}):
        voice.start()
        voice._thread.join(timeout=2)
    assert not voice.running
    assert 'unavailable' in voice.status
    voice.stop()
