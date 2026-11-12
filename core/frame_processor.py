"""Phase 1 pipeline: capture, colour segmentation, basic compositing."""

from core.background_capture import BackgroundCapture
from core.cloak_detector import CloakDetector
from core.invisibility_engine import composite


class FrameProcessor:
    def __init__(self, color="green", background_frames=21):
        self.detector = CloakDetector(color)
        self.background = BackgroundCapture(background_frames)
        self.enabled = True

    def process(self, frame):
        self.background.update(frame)
        mask = self.detector.detect(frame)
        background = self.background.background
        if background is not None and background.shape != frame.shape:
            # A resolution change invalidates spatial correspondence.
            self.background.background = None
            background = None
        if self.enabled and not self.background.capturing:
            return composite(frame, background, mask), mask
        return frame.copy(), mask
