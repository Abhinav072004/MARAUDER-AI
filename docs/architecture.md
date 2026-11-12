# Architecture and implementation phases

The project uses absolute imports from the repository root; run commands there.
`main.py` launches either the OpenCV interface or the optional PySide6 desktop.
`core/factory.py` constructs the same configured `FrameProcessor` for both.

## Modules

| Package | Responsibilities |
| --- | --- |
| `config/` | Validated capture settings and wrapped HSV presets |
| `core/` | Camera lifecycle, median background, HSV masks, optional person gate, mask refinement, compositing, scene monitoring and explicit synthetic source |
| `tracking/` | Sparse optical flow with silhouette fallback, planar floor mapping, optional MediaPipe hands/pose |
| `effects/` | Bounded particles/footsteps, ghost remap, reveal, shield, freeze and composable scene renderer |
| `interaction/` | Shared commands, offline voice worker and synthesized audio |
| `gui/` | PySide6 controls/preview and single-owner camera thread |
| `tools/` | Reproducible synthetic profiling/video recording |
| `tests/` | Mathematical, state/lifecycle, inference and Qt integration checks |

## Image pipeline

1. Request webcam resolution and acquire a BGR frame; fail explicitly if unreadable.
2. Collect an empty-scene sequence when B is pressed; compute a per-pixel median
   in row chunks. Lock the result until a successful recapture replaces it.
3. HSV `inRange` keys green/blue or red's two intervals. Wrapped calibration hues
   are supported. The optional person confidence gate only removes keyed pixels;
   it never makes unkeyed body parts invisible.
4. Open/close a binary mask, filter external contours by frame-relative area while
   preserving large holes, Gaussian-feather edges and apply a 45 ms exponential
   temporal filter. Reset history on capture, bounds/resolution or toggle changes.
5. Normalize alpha to [0,1]. Evaluate `live + alpha*(background-live)` in a reused
   float32 buffer; output uint8. Skip this base blend when a mode replaces it.
6. Track original cloth movement when required by active effects. Textureless
   cloth uses observed bounding-box displacement; footsteps never follow a random
   path. Floor homography maps observed path coordinates into/out of a plane.
7. Render effects; reveal overrides ghost, then shield, footsteps and particles
   overlay. Freeze stores rendered output while upstream capture remains active.
8. Monitor sustained differences outside a dilated cloth mask against the locked
   background. This warning is a heuristic, not a camera-motion classifier.

The single largest cloak is the tracked target. The bottom-centre is a proxy for
floor contact; it does not detect feet or estimate a physical gait. Particle
motion is stochastic around observed contours; footprint path is measured.
Particle capacity (400), footprint count (80), audio queue and frame delivery are
bounded. Ghost coordinate grids are cached; inactive optical flow is skipped.

## Thread ownership

OpenCV mode owns capture, inference and GUI calls on its main thread. PySide6 mode
owns all camera/processor/controller state in `CameraWorker`. The UI sends bounded
commands and polls a lock-protected latest QImage pair, preventing queued video
backlog. QImage buffers are copied before NumPy storage is released. UI widgets
are updated only on the GUI thread. Shutdown requests interruption and waits for
worker cleanup; it never destroys a running QThread or forcibly terminates one.
A driver stuck in a blocking read can require another close attempt.

Voice uses an independent daemon thread for Vosk/model loading and PortAudio;
bounded callbacks feed PCM and exact recognized commands feed a queue. Model
loading/voice never blocks camera processing. Missing resources become status
errors. Pygame chimes play asynchronously on actual state changes. MediaPipe
hands/pose are optional and throttled; the person gate is optional per frame.
Models may still reduce camera FPS and must be measured on target hardware.

## Phase record

1. **Core:** camera, capture, HSV, compositing, controls, tests and setup docs.
2. **Refinement:** cleanup, feathering, time-aware smoothing and tunable parameters.
3. **Effects:** ghost, measured-motion footsteps, boundary particles and floor mapping.
4. **Interaction:** optional hands, asynchronous offline voice, state-change audio.
5. **Desktop/modes:** threaded PySide6, sliders, reveal/freeze/shield/ambient effects,
   optional pose/person masks and explicit synthetic desktop demonstration.
6. **Validation:** buffer/performance work, scene warnings, lint/CI, full-stack tests,
   reproducible recording/profiling, dependency lock and consolidated docs.

Each phase is committed separately. Physical-device acceptance remains outstanding
and is kept distinct from synthetic/software validation in `validation.md`.
