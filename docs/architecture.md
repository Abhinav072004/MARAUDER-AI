# Architecture and incremental development

Phase 1 separates device lifecycle (`core/camera.py`), multi-frame background
state (`background_capture.py`), HSV thresholding (`cloak_detector.py`), and
normalized alpha blending (`invisibility_engine.py`). `FrameProcessor` coordinates
these operations without importing UI code; `main.py` owns desktop interaction,
timing and cleanup. Presets/settings live in `config/`. Tests exercise the core
without opening a display or accessing a camera.

HSV separates hue from brightness, allowing a saturated cloth to be keyed under
moderate illumination differences. Red straddles hue zero, requiring two ranges
or a wrapped interval. `inRange` produces a byte mask; compositing converts it
to float alpha in [0,1], then calculates `(1-alpha)*live + alpha*background`.
Phase 1 has binary boundaries; Phase 2 feeds feathered byte masks to the same
compositor. `MaskProcessor` opens/closes the binary mask, removes contours below
a frame-relative area threshold while preserving large holes, and applies a
Gaussian edge blur. An exponential temporal filter with a 45 ms time constant
reduces flicker independently of frame rate. Short motion trails are a tradeoff.
Capture, toggling invisibility, colour-bound and resolution changes reset history.
`--raw-mask` bypasses refinement for an explicit comparison. Cleanup/feather
sizes, minimum area ratio and temporal time constant are configurable CLI options.
Median background capture suppresses intermittent outliers,
but requires an unobscured static scene. Background stays locked after capture.

The capture loop gathers frames incrementally rather than blocking on a nested
capture loop. Median calculation uses row chunks to bound temporary memory.
It remains synchronous and may cause a brief pause at capture completion.
Frame resolution changes invalidate the background to preserve alignment.

## Phase completion and next phases

1. **Core:** implemented. Run `python main.py`, clear the scene and press B.
   Verify with `python -m pytest -q` and the physical webcam checklist. Cloud
   tests cover the math and lifecycle; physical validation is still required.
2. **Refinement:** implemented at the user’s request to continue. Noise, edge,
   temporal and refined-pipeline tests pass; physical acceptance remains
   outstanding. Run `python main.py` and compare with `--raw-mask`.
3. **Effects:** future independent modules under `effects/`; motion tracking
   under `tracking/`. Footsteps must follow observed movement, not randomness.
4. **Interaction:** future MediaPipe and asynchronous speech under `interaction/`
   and `tracking/`, with cooldowns, graceful optional-dependency failure and audio.
5. **Desktop and modes:** future PySide6 under `gui/` after core stability.
6. **Validation:** profile actual hardware, test all implemented features and
   document demonstration results rather than claiming unmeasured performance.

Reserved packages contain only package docstrings. There are no placeholder
core functions or pretend effects. Dependencies for future phases will be
selected and pinned when those phases begin.
