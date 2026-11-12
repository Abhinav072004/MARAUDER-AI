"""MARAUDER AI desktop entry point."""

import argparse
import logging
import os
import sys
from time import perf_counter

import cv2

from config.settings import Settings
from core.camera import Camera
from core.frame_processor import FrameProcessor

WINDOW = "MARAUDER AI | Cloak preview"
CALIBRATION = "HSV calibration | Q to save and close"
SLIDERS = ("H low", "S low", "V low", "H high", "S high", "V high")


def open_calibration(detector):
    cv2.namedWindow(CALIBRATION, cv2.WINDOW_NORMAL)
    lower, upper = detector.ranges[0]
    # Red's two preset intervals become one wrapped interval for editing.
    if detector.color == "red":
        lower, upper = (170, 100, 50), (10, 255, 255)
    for name, value, maximum in zip(
        SLIDERS, (*lower, *upper), (179, 255, 255, 179, 255, 255)
    ):
        cv2.createTrackbar(name, CALIBRATION, value, maximum, lambda _: None)


def run(args):
    settings = Settings(args.width, args.height, args.background_frames)
    if sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        raise RuntimeError("No desktop display. Run locally in a graphical session.")
    processor = FrameProcessor(args.color, settings.background_frames,
                               refine=not args.raw_mask, mask_options={
                                   "kernel_size": args.cleanup_size,
                                   "feather_size": args.feather_size,
                                   "min_area_ratio": args.min_area_ratio,
                                   "temporal_seconds": args.smoothing_ms / 1000,
                               })
    if args.calibration:
        processor.detector.load(args.calibration)
    camera = None
    calibrating = False
    fps = 0.0
    previous = perf_counter()
    try:
        camera = Camera(args.camera, settings.width, settings.height)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        logging.info("Camera %s opened. Clear scene, then press B.", camera.index)
        while True:
            frame = camera.read()
            begin = perf_counter()
            if calibrating:
                if cv2.getWindowProperty(CALIBRATION, cv2.WND_PROP_VISIBLE) < 1:
                    calibrating = False
                else:
                    values = [cv2.getTrackbarPos(n, CALIBRATION) for n in SLIDERS]
                    # Keep intermediate slider states valid without interrupting preview.
                    values[4] = max(values[1], values[4])
                    values[5] = max(values[2], values[5])
                    processor.detector.set_bounds(values[:3], values[3:])
            output, mask = processor.process(frame)
            elapsed_ms = (perf_counter() - begin) * 1000
            now = perf_counter()
            instantaneous = 1 / max(now - previous, 1e-6)
            fps = instantaneous if fps == 0 else 0.9 * fps + 0.1 * instantaneous
            previous = now
            bg = processor.background
            if bg.capturing:
                captured, total = bg.progress
                status = f"Capturing empty scene {captured}/{total} - stay out!"
            elif bg.background is None:
                status = "BACKGROUND MISSING: clear scene and press B"
            else:
                status = "Background locked | keep camera and lighting fixed"
            lines = [
                f"{fps:.1f} FPS | {elapsed_ms:.1f} ms processing | "
                f"{frame.shape[1]}x{frame.shape[0]} | camera {camera.index}",
                f"Cloak: {processor.detector.color} | "
                f"Invisibility: {'ON' if processor.enabled else 'OFF'}",
                status,
                "B capture | I toggle | 1 green 2 red 3 blue | C calibrate | ESC exit",
            ]
            for i, line in enumerate(lines):
                position = (12, 28 + i * 28)
                cv2.putText(output, line, position, cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(output, line, position, cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (100, 230, 255), 1, cv2.LINE_AA)
            cv2.imshow(WINDOW, output)
            if calibrating:
                cv2.imshow(CALIBRATION, mask)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key in (ord("b"), ord("B")):
                bg.start()
            elif key in (ord("i"), ord("I")):
                processor.enabled = not processor.enabled
            elif key in (ord("1"), ord("2"), ord("3")):
                processor.detector.set_preset({49: "green", 50: "red", 51: "blue"}[key])
                if calibrating:
                    cv2.destroyWindow(CALIBRATION)
                    calibrating = False
            elif key in (ord("c"), ord("C")) and not calibrating:
                open_calibration(processor.detector)
                calibrating = True
            elif key in (ord("q"), ord("Q")) and calibrating:
                processor.detector.save(args.save_calibration)
                logging.info("Saved calibration to %s", args.save_calibration)
                cv2.destroyWindow(CALIBRATION)
                calibrating = False
    finally:
        if camera is not None:
            camera.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, help="Device index; default probes 0–3")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--background-frames", type=int, default=21)
    parser.add_argument("--color", choices=("green", "red", "blue"), default="green")
    parser.add_argument("--calibration", help="Load an HSV calibration JSON file")
    parser.add_argument("--save-calibration", default="calibration.json")
    parser.add_argument("--raw-mask", action="store_true",
                        help="Disable Phase 2 refinement for comparison")
    parser.add_argument("--cleanup-size", type=int, default=3,
                        help="Opening/closing kernel width; positive odd integer")
    parser.add_argument("--feather-size", type=int, default=5,
                        help="Gaussian edge width; positive odd integer")
    parser.add_argument("--min-area-ratio", type=float, default=0.0005,
                        help="Minimum cloak contour area / frame area (0–1)")
    parser.add_argument("--smoothing-ms", type=float, default=45,
                        help="Temporal filter time constant in ms; 0 disables")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        run(args)
    except KeyboardInterrupt:
        return 0
    except Exception:
        logging.exception("MARAUDER AI stopped. See README troubleshooting.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
