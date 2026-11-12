"""Exercise the Phase 1 application controls without native GUI hardware."""

from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import main
from core.frame_processor import FrameProcessor


def test_application_shortcuts_and_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("DISPLAY", ":test")
    processor = FrameProcessor(background_frames=3)
    frame = np.full((32, 48, 3), (0, 255, 0), np.uint8)
    args = SimpleNamespace(
        width=640,
        height=480,
        background_frames=3,
        color="green",
        calibration=None,
        camera=0,
        raw_mask=False,
        demo=False,
        cleanup_size=3,
        feather_size=5,
        min_area_ratio=0.0005,
        smoothing_ms=45,
        save_calibration=str(tmp_path / "saved.json"),
    )
    keys = [ord(k) for k in "Biii23cqb"] + [27]
    with (
        patch.object(main, "create_processor", return_value=processor),
        patch.object(main, "Camera") as camera_class,
        patch.object(main.cv2, "namedWindow"),
        patch.object(main.cv2, "createTrackbar"),
        patch.object(main.cv2, "getTrackbarPos", side_effect=[90, 80, 50, 130, 255, 255]),
        patch.object(main.cv2, "getWindowProperty", return_value=1),
        patch.object(main.cv2, "imshow"),
        patch.object(main.cv2, "waitKey", side_effect=keys),
        patch.object(main.cv2, "destroyWindow"),
        patch.object(main.cv2, "destroyAllWindows") as destroy,
    ):
        camera_class.return_value.read.return_value = frame
        camera_class.return_value.index = 0
        main.run(args)
        camera_class.return_value.close.assert_called_once()
        destroy.assert_called_once()
    assert not processor.enabled
    assert processor.detector.color == "custom"
    assert (tmp_path / "saved.json").exists()
    assert processor.background.capturing  # final B initiates recapture
