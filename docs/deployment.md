# Browser deployment on GitHub Pages

The desktop application cannot run inside GitHub Pages. The `web/` companion
implements the cloak illusion directly in the browser and accesses the visitor's
camera only after permission. It has no backend, accounts, secrets, analytics or
third-party runtime dependencies. Webcam frames and captured backgrounds remain
in memory in the visitor's page and are discarded on reload/stop. It has no
microphone feature; the optional desktop voice model is not hosted.

## Publish

1. In this repository's **Settings → Pages → Build and deployment**, set
   **Source: GitHub Actions**. Administrative repository access may be required.
2. Push changes to `web/` on `main`, or open **Actions → Deploy browser edition
   to GitHub Pages → Run workflow**.
3. The test job installs pinned Playwright, runs seven engine tests and a real
   Chromium integration check, including synthetic camera capture and denied
   permission handling. Deployment runs only if that job passes.
4. The deployment job publishes only `index.html`, `style.css`, `app.js`,
   `engine.js` and `.nojekyll`, never development dependencies or test artifacts.
5. Read the actual URL from the successful workflow's `github-pages` environment
   and verify its page/assets and camera/demo controls. Do not treat the expected
   URL as deployed until GitHub reports success and it responds over HTTPS.

For this repository, GitHub's default project-site URL is expected to be
`https://abhinav072004.github.io/MARAUDER-AI/`. This is a target, not a deployment
success claim. GitHub Pages settings may override the hostname.

## Local validation

From the repository root:

```bash
node --test web/tests/*.test.js
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

In a second terminal:

```bash
cd web
npm ci
npx playwright install chromium
npm run test:browser
```

If a compatible Chromium is already installed, set `CHROMIUM_PATH` to its path.
The integration runner uses a browser test camera, not physical hardware. It
checks start/stop, a median background capture, effect toggles/keyboard, rendered
freeze, permission denial recovery, mobile overflow and the absence of page
requests to third-party services. Screenshots go to ignored `web/test-results/`.
The cloud check used system Chromium and passed; real visitor cameras remain
subject to browser/device permissions and cloth/lighting quality.

## Browser controls and limitations

Start camera, clear the view, capture B and wait for seven samples. Wear a green,
red or blue cloth; I toggles replacement. G/M/S/R/H/T control effects, C opens
HSV calibration, 1/2/3 select presets, Escape stops and releases the device.
Fine-tuning includes mask view, edge smoothing and optional WebAudio tones.
Camera access requires HTTPS (or local development) and user permission. The
synthetic demo works without a camera. A fixed camera and captured empty scene
are still essential. Edge quality and FPS depend on browser/device performance.
This edition does not claim offline speech, MediaPipe inference, homography or
Python optical flow. Use the desktop edition for those features.

## Environment access

This cloud environment initially denied `api.github.com` and the project Pages
host. Draft domain additions were saved for those destinations. They must be
applied through environment settings before the agent can configure Pages using
the existing GitHub binding and independently verify the public deployment.
Git pushes use the existing Git proxy and remain available. No additional token
value should be pasted into chat; insufficient GitHub admin permissions require
the repository owner to enable Pages in Settings instead.
