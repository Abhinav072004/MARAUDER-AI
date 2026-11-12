# Phase 1 webcam acceptance checklist

Run `python main.py --camera 0 --width 1280 --height 720` on a desktop with a
physical webcam. Record OS, Python version, camera, actual resolution and FPS.

1. Before B, verify the missing-background warning and unchanged live feed.
2. Clear the scene, press B, remain out of view until capture completes. Check
   the capture counter and locked status. Enter the frame with a green cloth.
3. Confirm cloth pixels reveal the correct static background and unkeyed
   clothing/skin remain visible. Toggle I twice; compare effect on/off.
4. Test red (including a bright red fabric) with 2 and blue with 3. Press C,
   tune HSV while checking white/black regions, Q to save; restart with
   `--calibration calibration.json` and verify matching behaviour.
5. Clear the scene, change a background object, press B and confirm replacement
   uses the new scene. Move the camera and observe expected misalignment;
   recapture. Phase 1 does not detect camera/background motion automatically.
6. Close calibration using its window controls; reopen with C. Test Q saving,
   preset reset, uppercase B/I/C/Q, Escape and closing the main window.
7. Unplug the webcam while running: verify an explicit error and nonzero exit.
   Restart with an unavailable index: verify a useful error without hanging.
8. Measure at least 60 seconds of ordinary operation at 720p and 480p. Record
   FPS and processing time separately from background-capture timing. Do not
   infer a laptop performance guarantee from synthetic cloud tests.

Pass Phase 1 only when a real camera produces the intended cloak illusion,
capture/recapture and controls work, and resource cleanup succeeds. Log any
failure before starting Phase 2. Current cloud validation lacks webcam hardware.
