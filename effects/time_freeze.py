"""Freeze only rendered output; callers continue camera capture and processing."""


class TimeFreeze:
    def __init__(self):
        self.enabled = False
        self._frame = None

    def render(self, frame):
        if not self.enabled:
            self._frame = None
            return frame
        if self._frame is None or self._frame.shape != frame.shape:
            self._frame = frame.copy()
        return self._frame.copy()
