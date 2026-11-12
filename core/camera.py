"""Camera lifecycle with bounded discovery and explicit read failures."""

import cv2


class CameraError(RuntimeError):
    """The camera cannot be opened or read."""


class Camera:
    def __init__(self, index=None, width=1280, height=720):
        self.capture = None
        candidates = range(4) if index is None else [index]
        for candidate in candidates:
            cap = cv2.VideoCapture(candidate)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ok, frame = cap.read()
                if ok and frame is not None:
                    self.capture = cap
                    self.index = candidate
                    self._first_frame = frame
                    break
            cap.release()
        if self.capture is None:
            raise CameraError(
                "No readable webcam found. Check connection, camera permissions, "
                "other camera applications, or pass --camera INDEX."
            )

    def read(self):
        if self._first_frame is not None:
            frame, self._first_frame = self._first_frame, None
            return frame
        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise CameraError("Camera disconnected or failed to deliver a frame")
        return frame

    def close(self):
        if self.capture is not None:
            self.capture.release()
