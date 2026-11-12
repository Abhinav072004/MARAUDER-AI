# Validation evidence — 12 November 2026

## Environment and checks

Linux cloud executor, Python 3.12.14, NumPy 1.26.4, OpenCV contrib 4.11.0.86,
MediaPipe 0.10.21, PySide6 6.8.3; complete package versions in
`requirements-lock.txt`. No physical webcam devices are exposed.

| Check | Observed result |
| --- | --- |
| Full installed stack, offscreen Qt / dummy SDL | 51 tests passed, no skips |
| Fresh core-only virtual environment | 47 passed, 2 skipped (Qt module and optional MediaPipe inference) |
| Ruff lint and formatting | Passed |
| `pip check`, core-only and full stack | Passed |
| CLI help | Passed; lists GUI, demo, refinement and optional-model flags |
| Camera discovery | Explicit no-readable-camera error, as expected in this executor |
| Real MediaPipe Hands/Pose/person mask | Initialized and ran on blank generated frames; no physical detections claimed |
| Real Pygame sound generation | Activation/deactivation buffers played through SDL dummy output; no audible-output claim |
| Real PySide6 widgets and worker | Offscreen preview, colour/capture/freeze controls, calibration load and clean shutdown passed |
| Voice worker | Controlled PCM/recognizer dispatch and failure/stop paths tested; no real Vosk-model/speech accuracy claim |
| Synthetic video | 180-frame 640×480 AVI written and fully decoded; frame count verified |
| GitHub Actions | Workflow configured; remote CI completion is not claimed here |

The core-only run skips one Qt module containing three tests and one MediaPipe
inference test. Pytest reports two skip entries; that is not a full-stack pass.
The full-stack run includes those four tests.

## Processing benchmark

Use `python -m tools.validate_demo` from the repository root. Two OpenCV threads,
10 warm-up frames, 30 FPS simulation timestep; timing covers pipeline processing,
not source generation, disk encoding, camera capture, display, microphone or AI.
The `all` preset activates ghost + footsteps + sparkles + shield; it does not mean
all optional recognition models. Measurements are samples from this executor,
not a laptop FPS guarantee. The source is a moving textured green rectangle.

| Preset | Resolution | Timed frames | Mean ms | P95 ms | Processing FPS |
| --- | --- | ---: | ---: | ---: | ---: |
| Core | 1280×720 | 90 | 13.32 | 15.84 | 75.09 |
| Combined effects | 640×480 | 180 | 22.60 | 27.63 | 44.24 |
| Combined effects | 1280×720 | 90 | 53.31 | 57.78 | 18.76 |

The equivalent pre-optimization samples measured 38.83 / 42.99 / 114.27 ms.
Changes reuse a float32 compositing buffer, avoid an overwritten base blend,
cache ghost coordinate grids and skip optical flow for inactive motion modes.
Choose 480p for combined effects; the 720p combined run misses the 25–30 FPS goal.

Reproduce:

```bash
python -m tools.validate_demo --mode core --width 1280 --height 720 --frames 90
python -m tools.validate_demo --width 640 --height 480 --frames 180 --output demo.avi
python -m tools.validate_demo --width 1280 --height 720 --frames 90
```

## Outstanding physical acceptance

Follow `manual_testing.md` on the target desktop. No physical cloth illusion,
spoken command accuracy, real-hand gesture accuracy, real-pose anchoring,
microphone input, audible sound or sustained laptop FPS is validated here. Vosk
requires a separately supplied offline model. Fictional spell words may be absent
from its vocabulary; Invisibility/Reveal are practical alternatives. A synthetic
recording and offscreen screenshot demonstrate software rendering only.
