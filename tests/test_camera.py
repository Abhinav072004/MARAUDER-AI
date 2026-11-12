"""Camera error and ownership tests using a controlled device double."""

from unittest.mock import patch

import numpy as np
import pytest

from core.camera import Camera, CameraError


class Device:
    def __init__(self, opened=True):
        self.opened = opened
        self.released = False
        self.good_read = True

    def isOpened(self):
        return self.opened

    def set(self, *_):
        return True

    def read(self):
        return (True, np.zeros((8, 8, 3), np.uint8)) if self.good_read else (False, None)

    def release(self):
        self.released = True


def test_missing_camera_releases_devices():
    device = Device(False)
    with patch("core.camera.cv2.VideoCapture", return_value=device):
        with pytest.raises(CameraError, match="No readable webcam"):
            Camera(index=0)
    assert device.released


def test_disconnection_and_release():
    device = Device()
    with patch("core.camera.cv2.VideoCapture", return_value=device):
        camera = Camera(index=0)
        assert camera.read().shape == (8, 8, 3)
        device.good_read = False
        with pytest.raises(CameraError, match="disconnected"):
            camera.read()
        camera.close()
    assert device.released
