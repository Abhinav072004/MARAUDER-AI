"""Camera-independent colour segmentation and refined alpha compositing."""

from time import perf_counter

from core.background_capture import BackgroundCapture
from core.cloak_detector import CloakDetector
from core.invisibility_engine import composite
from core.mask_processor import MaskProcessor
from effects.scene import SceneEffects


class FrameProcessor:
    def __init__(self, color="green", background_frames=21, refine=True,
                 mask_options=None):
        self.detector = CloakDetector(color)
        self.background = BackgroundCapture(background_frames)
        self.enabled = True
        self.effects = SceneEffects()
        self.mask_processor = MaskProcessor(**(mask_options or {})) if refine else None
        self._signature = None
        self._last_time = None

    def process(self, frame):
        now = perf_counter()
        dt = 1 / 30 if self._last_time is None else max(now - self._last_time, 1e-6)
        self._last_time = now
        captured = self.background.update(frame)
        mask = self.detector.detect(frame)
        signature = (frame.shape, tuple(self.detector.ranges), self.enabled)
        if self.mask_processor is not None:
            if signature != self._signature or captured or self.background.capturing:
                self.mask_processor.reset()
            mask = self.mask_processor.process(mask, dt)
        self._signature = signature
        background = self.background.background
        if background is not None and background.shape != frame.shape:
            # A resolution change invalidates spatial correspondence.
            self.background.background = None
            background = None
        if self.enabled and not self.background.capturing:
            output = composite(frame, background, mask, self.effects.intensity)
        else:
            output = frame.copy()
        output = self.effects.render(
            frame, output, background, mask, dt,
            enabled=self.enabled and not self.background.capturing)
        return output, mask
