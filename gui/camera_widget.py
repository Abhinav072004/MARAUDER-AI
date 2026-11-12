"""Aspect-preserving live preview that owns its last pixmap."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class CameraWidget(QLabel):
    def __init__(self, text='Waiting for camera…'):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self._pixmap = None

    def set_image(self, image):
        self._pixmap = QPixmap.fromImage(image)
        self._rescale()

    def _rescale(self):
        if self._pixmap is not None:
            self.setPixmap(self._pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()
