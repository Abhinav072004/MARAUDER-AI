"""Dark purple/gold desktop interface backed by a single-owner camera worker."""
import os
import sys

from PySide6.QtCore import QLibraryInfo, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QScrollArea,
    QSplitter, QVBoxLayout, QWidget,
)

from gui.camera_widget import CameraWidget
from gui.control_panel import ControlPanel
from gui.worker import CameraWorker


STYLE = '''
QWidget { background: #101321; color: #e9e5f5; font-size: 13px; }
QMainWindow { background: #0b0e19; }
QLabel#title { color: #e8c878; font-size: 25px; font-weight: bold; }
QPushButton { background: #29223e; border: 1px solid #625180;
              border-radius: 7px; padding: 9px; text-align: left; }
QPushButton:hover { background: #49375f; border-color: #e8c878; }
QGroupBox { border: 1px solid #443456; border-radius: 8px; margin-top: 12px; padding-top: 16px; }
QGroupBox::title { color: #d5b866; subcontrol-origin: margin; left: 10px; }
QComboBox, QSpinBox { padding: 5px; background: #22273b; border: 1px solid #625180; }
QSlider::groove:horizontal { height: 5px; background: #3e3455; }
QSlider::handle:horizontal { background: #d6b96a; width: 14px; margin: -5px 0; border-radius: 6px; }
QScrollArea { border: none; }
'''


class MainWindow(QMainWindow):
    def __init__(self, args, autostart=True):
        super().__init__()
        self.setWindowTitle('MARAUDER AI • Intelligent Magical Invisibility')
        self.resize(1280, 850)
        self.setStyleSheet(STYLE)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel('MARAUDER AI  ✦  THE INVISIBILITY LAB')
        title.setObjectName('title')
        layout.addWidget(title)
        self.source = QLabel('SYNTHETIC DEMO — not a webcam' if args.demo else
                             'LIVE CAMERA • keep the camera fixed')
        layout.addWidget(self.source)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.preview = CameraWidget()
        self.mask = CameraWidget('Cloak alpha mask')
        self.mask.setMinimumSize(160, 100)
        self.mask.setMaximumHeight(150)
        left_layout.addWidget(self.preview, 1)
        self.metrics = QLabel('Camera starting…')
        self.metrics.setWordWrap(True)
        left_layout.addWidget(self.metrics)
        left_layout.addWidget(self.mask)
        split.addWidget(left)
        self.controls = ControlPanel(args.color)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls)
        scroll.setMinimumWidth(330)
        split.addWidget(scroll)
        split.setSizes([900, 340])
        layout.addWidget(split, 1)
        shortcuts = QLabel('B background · I invisibility · G ghost · M steps · S sparkles · '
                           'V voice · J gestures · T freeze · R reveal · H shield · '
                           'P particles · A sound · O pose · E person mask · C calibrate · Esc exit')
        shortcuts.setWordWrap(True)
        layout.addWidget(shortcuts)
        self.worker = CameraWorker(args)
        self.controls.command.connect(self.send)
        self.worker.failed.connect(self._failed)
        self._shortcuts = []
        for key in ('B', 'I', 'G', 'M', 'S', 'V', 'J', 'T', 'R', 'H', 'P', 'A', 'O', 'E'):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda k=key.lower(): self.send('key', k))
            self._shortcuts.append(shortcut)
        for key, callback in [('Escape', self.close), ('C', lambda: self.controls.hsv[0].setFocus())]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(33)
        if autostart:
            self.worker.start()

    def send(self, action, value=None):
        if not self.worker.send(action, value):
            self.metrics.setText('Controls busy; wait briefly and try again')

    def refresh(self):
        latest = self.worker.take_latest()
        if latest is None:
            return
        image, mask, data = latest
        self.preview.set_image(image)
        self.mask.set_image(mask)
        self.metrics.setText(
            f"{data['fps']:.1f} FPS · {data['milliseconds']:.1f} ms · Camera {data['camera']} · "
            f"{data['color']} cloak · Invisibility {'ON' if data['enabled'] else 'OFF'}\n"
            f"{data['background']} · {data['modes']}\n{data['voice']} · {data['status']}")
        for key, field in [('a', 'sound'), ('j', 'gestures'), ('o', 'pose'), ('e', 'segmentation')]:
            self.controls.checks[key].setChecked(data[field])
        self.controls.checks['v'].setChecked(data['voice'].startswith(('Voice listening', 'Voice loading')))

    def _failed(self, error):
        self.metrics.setText(f'Camera stopped: {error}. Fix the device/settings and restart.')
        self.source.setText('CAMERA ERROR')

    def closeEvent(self, event):
        self.worker.requestInterruption()
        if self.worker.isRunning() and not self.worker.wait(3000):
            self.metrics.setText('Camera is still shutting down. Wait and close again.')
            event.ignore()
            return
        self.timer.stop()
        event.accept()


def launch(args):
    # OpenCV wheels set their own Qt5 plugin paths. PySide6 must use its Qt6 plugins.
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MainWindow(args)
    window.show()
    return app.exec()
