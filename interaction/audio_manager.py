"""Nonblocking synthesized spell chimes; no proprietary sound assets needed."""

import logging
import os

import numpy as np


class AudioManager:
    def __init__(self):
        self.enabled = True
        self._sounds = None
        self._failed = False

    def play(self, activated):
        if not self.enabled or self._failed:
            return
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame

            if self._sounds is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
                t = np.arange(6615) / 22050
                envelope = np.sin(np.pi * np.arange(len(t)) / len(t)) ** 2
                self._sounds = {}
                for state, frequency in ((True, 880), (False, 440)):
                    wave = np.sin(2 * np.pi * (frequency * t + 180 * t * t))
                    pcm = (wave * envelope * 8000).astype(np.int16)
                    self._sounds[state] = pygame.mixer.Sound(buffer=pcm.tobytes())
            self._sounds[bool(activated)].play()
        except Exception as error:
            logging.warning("Audio unavailable: %s", error)
            self._failed = True

    def close(self):
        if self._sounds is not None:
            import pygame

            pygame.mixer.quit()
