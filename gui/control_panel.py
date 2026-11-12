"""Explicit desktop controls; all mutations are queued to the camera owner."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.color_presets import PRESETS


class ControlPanel(QWidget):
    command = Signal(str, object)

    def __init__(self, color="green"):
        super().__init__()
        layout = QVBoxLayout(self)
        self.checks = {}
        self.capture_button = QPushButton("Capture empty background  [B]")
        self.capture_button.clicked.connect(lambda: self.command.emit("key", "b"))
        layout.addWidget(self.capture_button)
        invisibility = QPushButton("Toggle invisibility  [I]")
        invisibility.clicked.connect(lambda: self.command.emit("key", "i"))
        layout.addWidget(invisibility)
        self.color = QComboBox()
        self.color.addItems(["green", "red", "blue"])
        self.color.setCurrentText(color)
        self.color.currentTextChanged.connect(self._preset)
        layout.addWidget(QLabel("Cloak colour"))
        layout.addWidget(self.color)
        reset = QPushButton("Reset selected colour preset")
        reset.clicked.connect(lambda: self._preset(self.color.currentText()))
        layout.addWidget(reset)
        self._slider(layout, "Invisibility intensity", "intensity", 100, 100)
        self._slider(layout, "Particle intensity", "particles", 100, 300)
        palette = QComboBox()
        palette.addItems(["Gold particles", "Purple particles", "Blue particles"])
        palette.currentIndexChanged.connect(
            lambda i: self.command.emit(
                "particle_color", [(40, 190, 255), (255, 60, 180), (255, 160, 70)][i]
            )
        )
        layout.addWidget(palette)
        modes = QGroupBox("Magical modes")
        mode_layout = QVBoxLayout(modes)
        for label, key in [
            ("Ghost / Predator [G]", "g"),
            ("Marauder footsteps [M]", "m"),
            ("Golden sparkle trail [S]", "s"),
            ("Reveal silhouette [R]", "r"),
            ("Time freeze [T]", "t"),
            ("Energy shield [H]", "h"),
            ("Ambient particles [P]", "p"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, k=key: self.command.emit("key", k))
            mode_layout.addWidget(button)
        layout.addWidget(modes)
        for label, key, state in [
            ("Sound [A]", "a", True),
            ("Hand gestures [J]", "j", False),
            ("Offline voice [V]", "v", False),
            ("Pose tracking [O]", "o", False),
            ("Person mask gate [E]", "e", False),
        ]:
            check = QCheckBox(label)
            check.setChecked(state)
            check.clicked.connect(lambda checked=False, k=key: self.command.emit("key", k))
            self.checks[key] = check
            layout.addWidget(check)
        heatmap = QCheckBox("Heatmap reveal")
        heatmap.toggled.connect(lambda v: self.command.emit("heatmap", v))
        layout.addWidget(heatmap)
        model = QPushButton("Choose offline voice model…")
        model.clicked.connect(self._voice_model)
        layout.addWidget(model)
        self.calibration = QGroupBox("HSV calibration [C]")
        form = QFormLayout(self.calibration)
        self.hsv = []
        for label, maximum in [
            ("H low", 179),
            ("S low", 255),
            ("V low", 255),
            ("H high", 179),
            ("S high", 255),
            ("V high", 255),
        ]:
            spin = QSpinBox()
            spin.setRange(0, maximum)
            spin.valueChanged.connect(self._bounds)
            self.hsv.append(spin)
            form.addRow(label, spin)
        self._set_hsv(color)
        row = QHBoxLayout()
        for label, method in [("Save…", self._save), ("Load…", self._load)]:
            button = QPushButton(label)
            button.clicked.connect(method)
            row.addWidget(button)
        form.addRow(row)
        layout.addWidget(self.calibration)
        layout.addStretch()

    def _slider(self, layout, text, action, value, maximum):
        label = QLabel(f"{text}: {value}%")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(value)
        slider.valueChanged.connect(lambda v: label.setText(f"{text}: {v}%"))
        slider.valueChanged.connect(lambda v: self.command.emit(action, v))
        layout.addWidget(label)
        layout.addWidget(slider)

    def _set_hsv(self, color):
        lower, upper = PRESETS[color][0]
        if color == "red":
            lower, upper = (170, 100, 50), (10, 255, 255)
        self.set_loaded_ranges([(lower, upper)])

    def set_loaded_ranges(self, ranges):
        lower, upper = ranges[0]
        if len(ranges) == 2 and ranges[0][0][0] == 0 and ranges[-1][1][0] == 179:
            lower, upper = ranges[-1][0], ranges[0][1]
        self.calibration.setToolTip(
            "Multiple ranges loaded; editing replaces them with one interval"
            if len(ranges) > 1
            else "HSV bounds for the active cloak"
        )
        for spin, value in zip(self.hsv, (*lower, *upper)):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)

    def select_preset(self, color):
        if self.color.currentText() == color:
            self._preset(color)
        else:
            self.color.setCurrentText(color)

    def _preset(self, color):
        self._set_hsv(color)
        self.command.emit("color", color)

    def _bounds(self):
        values = [s.value() for s in self.hsv]
        if values[1] <= values[4] and values[2] <= values[5]:
            self.command.emit("hsv", values)

    def _voice_model(self):
        path = QFileDialog.getExistingDirectory(self, "Select unpacked Vosk model")
        if path:
            self.command.emit("voice_model", path)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save HSV calibration", "calibration.json", "*.json"
        )
        if path:
            self.command.emit("save", path)

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load HSV calibration", "", "*.json")
        if path:
            self.command.emit("load", path)
