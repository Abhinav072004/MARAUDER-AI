"""Shared state/commands for keyboard, GUI, offline voice and hand gestures."""
import logging

from interaction.audio_manager import AudioManager
from interaction.voice_controller import VoiceController


class Controller:
    def __init__(self, processor, voice_model=None):
        self.processor = processor
        self.voice = VoiceController(voice_model)
        self.audio = AudioManager()
        self.gesture = None
        self.pose = None
        self.status = ''

    def activate(self, active):
        if self.processor.enabled != active:
            self.processor.enabled = active
            self.audio.play(active)

    def toggle_gestures(self):
        if self.gesture is not None:
            self.gesture.close()
            self.gesture = None
            self.status = 'Gestures off'
        else:
            try:
                from tracking.hand_gesture import HandGesture
                self.gesture = HandGesture()
                self.status = 'Gestures on: open palm / fist'
            except Exception as error:
                self.status = f'Gestures unavailable: {error}'
                logging.warning(self.status)

    def toggle_pose(self):
        if self.pose is not None:
            self.pose.close()
            self.pose = None
            self.processor.effects.pose_bounds = None
        else:
            try:
                from tracking.pose_tracker import PoseTracker
                self.pose = PoseTracker()
            except Exception as error:
                self.status = f"Pose unavailable: {error}"
                logging.warning(self.status)

    def toggle_segmentation(self):
        model = self.processor.person_segmentation
        if model is not None:
            model.close()
            self.processor.person_segmentation = None
        else:
            try:
                from core.person_segmentation import PersonSegmentation
                self.processor.person_segmentation = PersonSegmentation()
            except Exception as error:
                self.status = f"Segmentation unavailable: {error}"
                logging.warning(self.status)
        if self.processor.mask_processor:
            self.processor.mask_processor.reset()

    def toggle_voice(self):
        if self.voice.running:
            self.voice.stop()
        else:
            try:
                self.voice.start()
            except Exception as error:
                self.status = f'Voice unavailable: {error}'
                logging.warning(self.status)

    def update(self, frame):
        commands = self.voice.poll()
        if self.pose is not None:
            try:
                self.processor.effects.pose_bounds = self.pose.update(frame)
            except Exception as error:
                self.status = f"Pose tracking failed: {error}"
                self.pose.close()
                self.pose = None
                self.processor.effects.pose_bounds = None
        if self.gesture is not None:
            try:
                command = self.gesture.update(frame)
                if command:
                    commands.append(command)
            except Exception as error:
                self.status = f'Gesture tracking failed: {error}'
                self.gesture.close()
                self.gesture = None
        for command in commands:
            self.activate(command == 'activate')

    def key(self, key):
        if isinstance(key, int):
            key = chr(key).lower() if 0 <= key <= 255 else ''
        key = key.lower()
        if key == 'b':
            self.processor.background.start()
        elif key == 'i':
            self.activate(not self.processor.enabled)
        elif key in ('g', 'm', 's', 'r', 'h', 'p'):
            name = {'g': 'ghost', 'm': 'footsteps', 's': 'sparkles',
                    'r': 'reveal', 'h': 'shield', 'p': 'ambient'}[key]
            effects = self.processor.effects
            setattr(effects, name, not getattr(effects, name))
        elif key == 't':
            freeze = self.processor.effects.freeze
            freeze.enabled = not freeze.enabled
        elif key == 'o':
            self.toggle_pose()
        elif key == 'e':
            self.toggle_segmentation()
        elif key == 'v':
            self.toggle_voice()
        elif key == 'j':
            self.toggle_gestures()
        elif key == 'a':
            self.audio.enabled = not self.audio.enabled
        else:
            return False
        return True

    def close(self):
        self.voice.stop()
        if self.gesture is not None:
            self.gesture.close()
        if self.pose is not None:
            self.pose.close()
        if self.processor.person_segmentation is not None:
            self.processor.person_segmentation.close()
        self.audio.close()
