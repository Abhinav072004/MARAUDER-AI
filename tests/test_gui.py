"""Real offscreen Qt widgets and threaded synthetic-camera integration."""
import os
import time
from types import SimpleNamespace

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def args():
    return SimpleNamespace(width=640, height=480, background_frames=3,
                           raw_mask=False, cleanup_size=3, feather_size=5,
                           min_area_ratio=0.0005, smoothing_ms=45,
                           calibration=None, color='green', demo=True,
                           voice_model=None, camera=None)


def pump(app, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_desktop_demo_controls_frames_and_clean_shutdown():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(args())
    window.show()
    try:
        assert pump(app, lambda: window.preview._pixmap is not None)
        assert 'SYNTHETIC DEMO' in window.source.text()
        window.send('key', 'g')
        assert pump(app, lambda: 'ghost' in window.metrics.text())
        window.controls.color.setCurrentText('blue')
        assert pump(app, lambda: 'blue cloak' in window.metrics.text())
        window.controls.capture_button.click()
        assert pump(app, lambda: 'Background locked' in window.metrics.text())
        window.send('intensity', 50)
        window.send('key', 't')
        assert pump(app, lambda: 'frozen' in window.metrics.text())
        window.send('key', 't')
    finally:
        window.close()
        app.processEvents()
    assert not window.worker.isRunning()


def test_calibration_bounds_validation_and_failure_message():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(args(), autostart=False)
    commands = []
    window.controls.command.connect(lambda a, v: commands.append((a, v)))
    window.controls.hsv[0].setValue(45)
    assert commands[-1][0] == 'hsv'
    window._failed('test camera disconnected')
    assert 'test camera disconnected' in window.metrics.text()
    assert window.close()
    app.processEvents()
