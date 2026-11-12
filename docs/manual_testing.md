# Physical-device acceptance and demonstration

These checks require a physical webcam, cloth and desktop. Optional interaction
checks require visible hands, a microphone, speaker and an unpacked Vosk model.
The cloud environment supplies none of those physical inputs. Record OS, Python,
camera, actual resolution, illumination, enabled modes, average FPS and latency.

1. Start `python main.py --gui --width 640 --height 480`. Before B verify the
   missing-background message and unchanged live scene. Clear the entire view,
   capture and wait for Background locked. Enter with green cloth. Cloth pixels
   must reveal the spatially correct background; exposed skin stays visible.
2. Toggle I twice. Capture a changed empty scene and verify the new background.
   Try an invalid camera index and physically disconnect while running: expect
   an explicit error and resource release. Restart after reconnection.
3. Select red/blue and calibrate HSV. Verify wrapped red hues, white/gray/black
   mask preview and save/load persistence. Try both GUI and OpenCV interfaces.
4. Compare default refinement to `--raw-mask` and `--smoothing-ms 0`. Inspect
   speckles, large holes, edges and movement lag. Tune minimum area and kernel
   sizes for your cloth. Change presets/toggle I: old silhouettes must not linger.
5. Keep the camera fixed and move the cloth horizontally. G should make it
   translucent and shimmering. M should emit steps following movement, with none
   from a stationary cloak; older steps fade. S should emit more boundary particles
   during faster movement. Check floor mapping against measured planar corners.
6. Test P, particle palette/intensity and reveal/heatmap. Check H with O off (cloth
   bounds) and on (visible pose). Occlude the person: shield should fall back
   appropriately. Test E both ways; disable it if loose cloth is rejected.
7. T freezes only visual output. Continue moving and recapture; unfreeze and
   verify fresh camera output and responsive controls. Change replacement
   intensity 0/50/100%; test with decorative modes off for a pure blend comparison.
8. J: hold an open palm and then fist. Verify three-observation stability and
   cooldown; ambiguous gestures should not repeatedly toggle. Test several
   orientations and note classification failures.
9. Choose an offline English Vosk model, V on, and speak Invisibility/Reveal.
   Then test Lumos/Nox if the model vocabulary supports them. Check background
   noise, silence, microphone denial, missing model and disconnect. Camera must
   remain responsive. Reveal must clear modes/freeze. No audio should be uploaded.
10. Listen for distinct activation/deactivation chimes only on state changes;
    A mutes them. Check missing output device handling. A dummy audio test does
    not establish audible playback.
11. Move the camera or change lighting/background substantially: wait for the
    conservative warning, clear the scene and recapture. Large unkeyed foreground
    objects may also trigger it. It is not automatic stabilization.
12. Run for at least 60 seconds at 480p and 720p, core and combined modes. Record
    FPS/processing time separately from capture/inference/preview costs. Close the
    GUI and confirm camera light turns off and workers release resources.

Use an OS screen recorder for the hardware demonstration. Show an empty capture,
cloth entry, I comparison, HSV adjustment and G/M/S interaction, followed by
additional modes and voice/gestures. Keep the camera still. Add actual physical
screenshots to the README only after this checklist passes; the existing desktop
screenshot and headless recording are explicitly synthetic.
