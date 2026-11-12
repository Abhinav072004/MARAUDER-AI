"""Single-owner camera worker with bounded commands and latest-frame delivery."""

from queue import Empty, Full, Queue
from threading import Lock
from time import perf_counter

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from core.camera import Camera
from core.demo_camera import DemoCamera
from core.factory import create_processor
from interaction.controller import Controller


class CameraWorker(QThread):
    failed = Signal(str)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.commands = Queue(maxsize=64)
        self.lock = Lock()
        self.latest = None
        self.loaded_ranges = None
        self.calibration_revision = 0

    def send(self, action, value=None):
        try:
            self.commands.put_nowait((action, value))
            return True
        except Full:
            return False

    def take_latest(self):
        with self.lock:
            latest, self.latest = self.latest, None
        return latest

    def _command(self, controller, action, value):
        processor = controller.processor
        if action == "key":
            controller.key(value)
        elif action == "color":
            processor.detector.set_preset(value)
        elif action == "hsv":
            processor.detector.set_bounds(value[:3], value[3:])
        elif action == "intensity":
            processor.effects.intensity = value / 100
        elif action == "particles":
            processor.effects.particle_intensity = value / 100
        elif action == "particle_color":
            processor.effects.particle_color = value
        elif action == "heatmap":
            processor.effects.heatmap = value
        elif action == "voice_model":
            controller.voice.stop()
            controller.voice.model_path = value
        elif action == "save":
            processor.detector.save(value)
            controller.status = f"Calibration saved: {value}"
        elif action == "load":
            processor.detector.load(value)
            self.loaded_ranges = list(processor.detector.ranges)
            self.calibration_revision += 1
            controller.status = f"Calibration loaded: {value}"

    def run(self):
        camera = None
        controller = None
        try:
            processor = create_processor(self.args)
            self.loaded_ranges = list(processor.detector.ranges)
            self.calibration_revision += 1
            controller = Controller(processor, self.args.voice_model)
            camera = (
                DemoCamera(self.args.width, self.args.height)
                if self.args.demo
                else Camera(self.args.camera, self.args.width, self.args.height)
            )
            if self.args.demo:
                processor.background.start()
            previous = perf_counter()
            fps = 0.0
            while not self.isInterruptionRequested():
                begin = perf_counter()
                for _ in range(64):
                    try:
                        action, value = self.commands.get_nowait()
                    except Empty:
                        break
                    try:
                        self._command(controller, action, value)
                    except Exception as error:
                        controller.status = f"Control error: {error}"
                frame = camera.read()
                controller.update(frame)
                output, mask = processor.process(frame)
                milliseconds = (perf_counter() - begin) * 1000
                now = perf_counter()
                instant = 1 / max(now - previous, 1e-6)
                fps = instant if fps == 0 else fps * 0.9 + instant * 0.1
                previous = now
                rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
                image = QImage(
                    rgb.data,
                    rgb.shape[1],
                    rgb.shape[0],
                    rgb.strides[0],
                    QImage.Format.Format_RGB888,
                ).copy()
                mask_image = QImage(
                    mask.data,
                    mask.shape[1],
                    mask.shape[0],
                    mask.strides[0],
                    QImage.Format.Format_Grayscale8,
                ).copy()
                bg = processor.background
                effects = processor.effects
                modes = [
                    name
                    for name in ("ghost", "footsteps", "sparkles", "reveal", "shield", "ambient")
                    if getattr(effects, name)
                ]
                if effects.freeze.enabled:
                    modes.append("frozen")
                metadata = {
                    "loaded_ranges": self.loaded_ranges,
                    "calibration_revision": self.calibration_revision,
                    "fps": fps,
                    "milliseconds": milliseconds,
                    "camera": str(camera.index),
                    "color": processor.detector.color,
                    "enabled": processor.enabled,
                    "modes": ", ".join(modes) or "Invisibility",
                    "background": (
                        f"Capturing {bg.progress[0]}/{bg.progress[1]} - stay out"
                        if bg.capturing
                        else "Background locked"
                        if bg.background is not None
                        else "Clear scene and capture background"
                    ),
                    "status": processor.warning or controller.status,
                    "voice": controller.voice.status,
                    "sound": controller.audio.enabled,
                    "gestures": controller.gesture is not None,
                    "pose": controller.pose is not None,
                    "segmentation": processor.person_segmentation is not None,
                }
                with self.lock:
                    self.latest = (image, mask_image, metadata)
                # Backpressure: only one latest frame survives; never queue video signals.
                delay = max(1, round(1000 / 30 - (perf_counter() - begin) * 1000))
                self.msleep(delay)
        except Exception as error:
            import logging

            logging.exception("Camera worker stopped")
            self.failed.emit(str(error))
        finally:
            if controller:
                controller.close()
            if camera:
                camera.close()
