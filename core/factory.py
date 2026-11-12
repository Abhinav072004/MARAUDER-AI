"""Shared runtime construction for both desktop interfaces."""
import json
import math

from config.settings import Settings
from core.frame_processor import FrameProcessor
from tracking.floor_mapping import FloorMapping


def create_processor(args):
    settings = Settings(args.width, args.height, args.background_frames)
    processor = FrameProcessor(args.color, settings.background_frames,
                               refine=not args.raw_mask, mask_options={
                                   'kernel_size': args.cleanup_size,
                                   'feather_size': args.feather_size,
                                   'min_area_ratio': args.min_area_ratio,
                                   'temporal_seconds': args.smoothing_ms / 1000,
                               })
    if getattr(args, 'floor_calibration', None):
        with open(args.floor_calibration) as source:
            data = json.load(source)
        processor.effects.steps.mapping = FloorMapping(data['image_points'], data['floor_points'])
        spacing = float(data.get('spacing', 35))
        if not math.isfinite(spacing) or spacing <= 0:
            raise ValueError('Floor step spacing must be finite and positive')
        processor.effects.steps.spacing = spacing
    if args.calibration:
        processor.detector.load(args.calibration)
    return processor
