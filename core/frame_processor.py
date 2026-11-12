"""Camera-independent colour segmentation and refined alpha compositing."""

import logging
import math
from time import perf_counter

from core.background_capture import BackgroundCapture
from core.cloak_detector import CloakDetector
from core.invisibility_engine import composite
from core.mask_processor import MaskProcessor
from effects.scene import SceneEffects
from core.scene_monitor import SceneMonitor


class FrameProcessor:
    def __init__(self, color="green", background_frames=21, refine=True, mask_options=None):
        self.detector = CloakDetector(color)
        self.background = BackgroundCapture(background_frames)
        self.enabled = True
        self.effects = SceneEffects()
        self.person_segmentation = None
        self.monitor = SceneMonitor()
        self.warning = ""
        self.mask_processor = MaskProcessor(**(mask_options or {})) if refine else None
        self._signature = None
        self._last_time = None

    def process(self, frame, dt=None):
        now = perf_counter()
        if dt is None:
            dt = 1 / 30 if self._last_time is None else max(now - self._last_time, 1e-6)
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("Frame duration must be finite and positive")
        self._last_time = now
        captured = self.background.update(frame)
        mask = self.detector.detect(frame)
        self.effects.person_mask = None
        if self.person_segmentation is not None:
            try:
                mask = self.person_segmentation.refine(frame, mask)
                self.effects.person_mask = self.person_segmentation.last_mask
            except Exception as error:
                logging.warning("Person segmentation disabled: %s", error)
                self.person_segmentation.close()
                self.person_segmentation = None
                self.warning = f"Person segmentation disabled: {error}"
        signature = (frame.shape, tuple(self.detector.ranges), self.enabled)
        if self.mask_processor is not None:
            if signature != self._signature or captured or self.background.capturing:
                self.mask_processor.reset()
            mask = self.mask_processor.process(mask, dt)
        self._signature = signature
        if captured or self.background.capturing:
            self.monitor.reset()
        background = self.background.background
        if background is not None and background.shape != frame.shape:
            # A resolution change invalidates spatial correspondence.
            self.background.background = None
            background = None
            self.monitor.reset()
        if self.monitor.update(frame, background, mask, dt):
            self.warning = "Scene changed or camera moved: clear scene and recapture B"
        elif self.warning.startswith("Scene changed"):
            self.warning = ""
        if (
            self.enabled
            and not self.background.capturing
            and not self.effects.ghost
            and not self.effects.reveal
        ):
            output = composite(frame, background, mask, self.effects.intensity)
        else:
            output = frame.copy()
        output = self.effects.render(
            frame,
            output,
            background,
            mask,
            dt,
            enabled=self.enabled and not self.background.capturing,
        )
        return output, mask
