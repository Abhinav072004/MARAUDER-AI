"""Validated runtime settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    width: int = 1280
    height: int = 720
    background_frames: int = 21

    def __post_init__(self):
        if not (160 <= self.width <= 3840 and 120 <= self.height <= 2160):
            raise ValueError("Resolution must be within 160x120 and 3840x2160")
        if not 3 <= self.background_frames <= 31:
            raise ValueError("Background frame count must be between 3 and 31")
