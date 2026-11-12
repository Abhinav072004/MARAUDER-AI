"""Render/benchmark a labelled synthetic demo; no webcam or microphone claims."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from core.demo_camera import DemoCamera
from core.frame_processor import FrameProcessor


def render_demo(width=640, height=480, frames=180, output=None, mode="all"):
    if not 160 <= width <= 3840 or not 120 <= height <= 2160 or frames < 1:
        raise ValueError("Invalid demo dimensions or frame count")
    source = DemoCamera(width, height)
    processor = FrameProcessor(background_frames=3)
    processor.background.start()
    for _ in range(3):
        processor.process(source.background, dt=1 / 30)
    effects = processor.effects
    effects.particles.rng = np.random.default_rng(42)
    if mode == "all":
        effects.ghost = effects.footsteps = effects.sparkles = True
        effects.shield = True
    writer = None
    if output:
        codec = "mp4v" if Path(output).suffix.lower() == ".mp4" else "MJPG"
        writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*codec), 30, (width, height))
        if not writer.isOpened():
            writer.release()
            raise RuntimeError(f"Cannot create video: {output}")
    timings = []
    changed = False
    try:
        for index in range(frames + 10):
            frame = source.frame_at(2 + index / 30)
            begin = perf_counter()
            result, mask = processor.process(frame, dt=1 / 30)
            duration = perf_counter() - begin
            assert result.shape == frame.shape and result.dtype == np.uint8
            assert mask.any(), "Demo cloak was not detected"
            changed |= not np.array_equal(frame, result)
            if index >= 10:
                timings.append(duration)
                if writer:
                    cv2.putText(
                        result,
                        "SYNTHETIC DEMO - NOT A WEBCAM",
                        (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 240, 180),
                        1,
                    )
                    writer.write(result)
    finally:
        if writer:
            writer.release()
    assert changed, "Pipeline did not change the synthetic camera image"
    if output:
        capture = cv2.VideoCapture(str(output))
        count = 0
        while True:
            ok, _ = capture.read()
            if not ok:
                break
            count += 1
        capture.release()
        if count != frames:
            raise RuntimeError(f"Video contains {count} frames, expected {frames}")
    return {
        "source": "synthetic; excludes capture/display/AI inference",
        "mode": mode,
        "resolution": [width, height],
        "frames": frames,
        "mean_ms": round(np.mean(timings) * 1000, 2),
        "p95_ms": round(np.percentile(timings, 95) * 1000, 2),
        "processing_fps": round(1 / np.mean(timings), 2),
        "particles": len(effects.particles.particles),
        "footsteps": len(effects.steps.steps),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--frames", type=int, default=180)
    parser.add_argument(
        "--output", help="Optional AVI or MP4 file; decoded and checked after writing"
    )
    parser.add_argument("--mode", choices=["core", "all"], default="all")
    parser.add_argument("--opencv-threads", type=int, default=2)
    args = parser.parse_args()
    if args.opencv_threads < 1:
        parser.error("OpenCV threads must be positive")
    cv2.setNumThreads(args.opencv_threads)
    print(
        json.dumps(
            render_demo(args.width, args.height, args.frames, args.output, args.mode), indent=2
        )
    )


if __name__ == "__main__":
    main()
