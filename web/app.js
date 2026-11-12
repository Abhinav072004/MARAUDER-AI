import {CloakEngine, PRESETS} from './engine.js';

const $ = id => document.getElementById(id);
const preview = $('preview'), ctx = preview.getContext('2d');
const source = document.createElement('canvas');
const sourceCtx = source.getContext('2d', {willReadFrequently: true});
const frozen = document.createElement('canvas');
const video = $('camera');
const modes = {ghost: false, steps: false, sparkles: false, reveal: false, shield: false, freeze: false};
const sliders = [];
let engine, stream = null, kind = null, animation = null, session = 0;
let previous = 0, fps = 0, started = 0, backgroundFrames = [], capturing = false, sampled = 0;
let particles = [], steps = [], lastPosition = null, distance = 0, left = true, credit = 0;
let freezeReady = false, audio = null, demoBackground = null;

function status(text) { $('status').textContent = text; }
function chime(on) {
  if (!$('sound').checked) return;
  try {
    audio ||= new (window.AudioContext || window.webkitAudioContext)();
    audio.resume();
    const oscillator = audio.createOscillator(), gain = audio.createGain(), now = audio.currentTime;
    oscillator.frequency.setValueAtTime(on ? 880 : 440, now);
    oscillator.frequency.exponentialRampToValueAtTime(on ? 1200 : 300, now + 0.25);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.12, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);
    oscillator.connect(gain).connect(audio.destination);
    oscillator.start(); oscillator.stop(now + 0.31);
  } catch { status('Audio is unavailable. Keyboard and camera controls still work.'); }
}

function applyPreset() {
  const values = PRESETS[$('color').value];
  sliders.forEach((slider, i) => { slider.value = values[i]; slider.nextElementSibling.value = values[i]; });
  engine?.setBounds(values);
  lastPosition = null;
}

['H low', 'S low', 'V low', 'H high', 'S high', 'V high'].forEach((label, i) => {
  const row = document.createElement('div'), title = document.createElement('label');
  const slider = document.createElement('input'), output = document.createElement('output');
  slider.id = `hsv-${i}`; slider.type = 'range'; slider.min = 0; slider.max = i % 3 === 0 ? 179 : 255;
  title.htmlFor = slider.id; title.textContent = label;
  row.append(title, slider, output);
  $('hsv-controls').append(row); sliders.push(slider);
  slider.addEventListener('input', () => {
    output.value = slider.value;
    try { engine?.setBounds(sliders.map(s => Number(s.value))); }
    catch (error) { status(error.message); }
  });
});
applyPreset();
$('color').addEventListener('change', applyPreset);
$('reset').addEventListener('click', applyPreset);
$('intensity').addEventListener('input', () => { $('intensity-value').value = `${$('intensity').value}%`; });
$('invisible').addEventListener('change', () => { if (engine) engine.history = false; chime($('invisible').checked); });

function toggle(name) {
  modes[name] = !modes[name];
  document.querySelector(`[data-mode="${name}"]`).setAttribute('aria-pressed', String(modes[name]));
  if (name === 'freeze') { freezeReady = false; $('freeze-label').hidden = !modes.freeze; }
}
for (const button of document.querySelectorAll('[data-mode]')) {
  button.addEventListener('click', () => toggle(button.dataset.mode));
}

function stop(message = 'Camera stopped. Choose your camera or explore the demo.') {
  session++;
  if (animation !== null) cancelAnimationFrame(animation);
  animation = null;
  if (stream) stream.getTracks().forEach(track => { track.onended = null; track.stop(); });
  stream = null; kind = null;
  video.srcObject = null;
  capturing = false; backgroundFrames = [];
  $('welcome').hidden = false; $('capture').disabled = true; $('stop').disabled = true;
  $('start').disabled = false;
  $('demo-label').hidden = true; $('freeze-label').hidden = true;
  $('source').textContent = 'LAB OFFLINE'; $('fps').textContent = '— FPS';
  document.querySelector('.live-dot').classList.remove('active');
  ctx.clearRect(0, 0, preview.width, preview.height);
  status(message);
}
$('stop').addEventListener('click', () => stop());
window.addEventListener('pagehide', () => stop());

function initialize(width, height, type) {
  for (const canvas of [preview, source, frozen]) { canvas.width = width; canvas.height = height; }
  document.querySelector('.viewport').style.aspectRatio = `${width}/${height}`;
  engine = new CloakEngine(width, height);
  engine.setBounds(sliders.map(s => Number(s.value)));
  kind = type; previous = performance.now(); started = previous; fps = 0;
  particles = []; steps = []; lastPosition = null; distance = 0; credit = 0; freezeReady = false;
  $('welcome').hidden = true; $('capture').disabled = false; $('stop').disabled = false;
  $('demo-label').hidden = type !== 'demo'; $('freeze-label').hidden = !modes.freeze;
  $('source').textContent = type === 'demo' ? 'SYNTHETIC DEMO' : 'LIVE CAMERA · LOCAL PROCESSING';
  document.querySelector('.live-dot').classList.add('active');
  if (type === 'demo') {
    drawDemo(0);
    demoBackground = sourceCtx.getImageData(0, 0, width, height).data.slice();
    engine.background = demoBackground.slice();
    status('Synthetic background locked. Try Ghost, Footsteps or Sparkles.');
  } else status('Clear the entire scene, then capture the background (B).');
  animation = requestAnimationFrame(frame);
}

$('start').addEventListener('click', async () => {
  stop();
  const request = session;
  $('start').disabled = true;
  status('Waiting for camera permission…');
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('Webcam access needs HTTPS and a supported browser.');
    const incoming = await navigator.mediaDevices.getUserMedia({audio: false,
      video: {width: {ideal: 640}, height: {ideal: 480}, facingMode: 'user'}});
    if (request !== session) { incoming.getTracks().forEach(track => track.stop()); return; }
    stream = incoming; video.srcObject = stream; await video.play();
    if (request !== session) return;
    stream.getVideoTracks()[0].onended = () => stop('Camera disconnected. Reconnect and start again.');
    initialize(640, Math.max(120, Math.round(640 * video.videoHeight / video.videoWidth)), 'camera');
  } catch (error) {
    if (request !== session) return;
    const reason = error.name === 'NotAllowedError' ? 'Camera permission denied. Allow access in your browser or try the demo.' :
      error.name === 'NotFoundError' ? 'No webcam found. Connect one or try the demo.' : `Camera unavailable: ${error.message}`;
    stop(reason);
  } finally { if (request === session) $('start').disabled = false; }
});
$('demo').addEventListener('click', () => { stop(); initialize(480, 360, 'demo'); });

function drawDemo(time, empty = false) {
  const w = source.width, h = source.height;
  sourceCtx.fillStyle = '#1a2033'; sourceCtx.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 48) for (let x = 0; x < w; x += 48) {
    if ((x / 48 + y / 48) % 2 === 0) { sourceCtx.fillStyle = '#273147'; sourceCtx.fillRect(x, y, 48, 48); }
  }
  if (time > 0 && !empty) {
    const x = w * (0.5 + 0.23 * Math.sin(time * 0.8)), y = h * 0.23;
    sourceCtx.fillStyle = '#00d800'; sourceCtx.fillRect(x - w * 0.12, y, w * 0.24, h * 0.6);
    sourceCtx.fillStyle = '#00a500';
    for (let dy = 16; dy < h * 0.57; dy += 20) sourceCtx.fillRect(x - 3, y + dy, 6, 6);
  }
}

function capture() {
  if (!engine || !kind) return;
  capturing = true; backgroundFrames = []; sampled = 0;
  $('capture').disabled = true;
  status('Capturing empty scene: 0/7. Stay out of view.');
}
$('capture').addEventListener('click', capture);

function drawEffects(result, dt) {
  const bounds = result.bounds;
  let position = null, speed = 0;
  if (bounds) position = {x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height - 1};
  if (position && lastPosition) {
    const dx = position.x - lastPosition.x, dy = position.y - lastPosition.y, moved = Math.hypot(dx, dy);
    speed = moved / dt;
    if (modes.steps && moved > 0 && moved < 120 && speed > 8) {
      const angle = Math.atan2(dy, dx);
      let next = 30 - distance;
      while (next <= moved) {
        steps.push({x: lastPosition.x + dx * next / moved - Math.sin(angle) * (left ? 7 : -7),
          y: lastPosition.y + dy * next / moved + Math.cos(angle) * (left ? 7 : -7), angle, age: 0});
        left = !left; next += 30;
      }
      distance = (distance + moved) % 30;
    }
  }
  if (!position || !modes.steps) distance = 0;
  lastPosition = position;
  steps = modes.steps ? steps.filter(step => (step.age += dt) < 3).slice(-80) : [];
  ctx.save();
  for (const step of steps) {
    ctx.fillStyle = `rgba(173,133,255,${1 - step.age / 3})`;
    ctx.shadowColor = '#b29bff'; ctx.shadowBlur = 10;
    ctx.beginPath(); ctx.ellipse(step.x, step.y, Math.max(4, step.y / preview.height * 12),
      Math.max(2, step.y / preview.height * 5), step.angle, 0, Math.PI * 2); ctx.fill();
  }
  if (modes.sparkles && bounds && speed > 8) {
    credit += Math.min(160, speed) * dt;
    const count = Math.min(Math.floor(credit), 400 - particles.length);
    credit -= Math.floor(credit);
    for (let i = 0; i < count; i++) {
      // Rejection-sample actual mask boundaries, not arbitrary body positions.
      let point = null;
      for (let attempt = 0; attempt < 100; attempt++) {
        const horizontal = Math.random() < 0.5;
        const x = Math.floor(bounds.x + Math.random() * bounds.width);
        const y = Math.floor(bounds.y + Math.random() * bounds.height);
        let p = y * engine.width + x;
        if (horizontal) {
          const dir = Math.random() < 0.5 ? 1 : -1;
          for (let j = 0; j < bounds.width; j++) {
            const nx = x + j * dir;
            if (nx < 1 || nx >= engine.width - 1) break;
            p = y * engine.width + nx;
            if (result.mask[p] && (!result.mask[p - 1] || !result.mask[p + 1])) { point = {x: nx, y}; break; }
          }
        } else if (result.mask[p] && (!result.mask[p - engine.width] || !result.mask[p + engine.width])) point = {x, y};
        if (point) break;
      }
      if (point) particles.push({...point, vx: (Math.random() - 0.5) * 70,
        vy: -15 - Math.random() * 45, age: 0, life: 0.5 + Math.random(), radius: 1 + Math.random() * 2});
    }
  } else credit = 0;
  particles = particles.filter(p => (p.age += dt) < p.life && p.y < preview.height + 20);
  for (const p of particles) {
    p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 20 * dt;
    ctx.shadowColor = '#ffcb62'; ctx.shadowBlur = 10;
    ctx.fillStyle = `rgba(255,205,93,${1 - p.age / p.life})`;
    ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2); ctx.fill();
  }
  if (modes.shield && bounds) {
    const x = bounds.x + bounds.width / 2, y = bounds.y + bounds.height / 2;
    const radius = Math.max(bounds.width, bounds.height) * 0.6;
    ctx.shadowColor = '#a3c9ff'; ctx.shadowBlur = 12;
    ctx.strokeStyle = '#8fbaffaa'; ctx.lineWidth = 2;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath(); ctx.arc(x, y, radius * (0.85 + i * 0.06), performance.now() / 1000 + i * 2,
        performance.now() / 1000 + i * 2 + Math.PI * 1.5); ctx.stroke();
    }
    ctx.fillStyle = '#75acff0d'; ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

function frame(now) {
  if (!kind) return;
  try {
    const dt = Math.max(0.001, Math.min(0.2, (now - previous) / 1000)); previous = now;
    fps = fps ? fps * 0.9 + 0.1 / dt : 1 / dt;
    const time = (now - started) / 1000;
    if (kind === 'demo') drawDemo(time, capturing);
    else sourceCtx.drawImage(video, 0, 0, source.width, source.height);
    const input = sourceCtx.getImageData(0, 0, source.width, source.height);
    if (capturing && now - sampled >= 90) {
      backgroundFrames.push(input.data.slice()); sampled = now;
      status(`Capturing empty scene: ${backgroundFrames.length}/7. Stay out of view.`);
      if (backgroundFrames.length === 7) {
        engine.capture(backgroundFrames); backgroundFrames = []; capturing = false;
        $('capture').disabled = false;
        status('Background locked. Enter wearing the selected cloth. Keep the camera fixed.');
      }
    }
    const result = engine.render(input.data, {dt, time, intensity: Number($('intensity').value) / 100,
      enabled: $('invisible').checked && !capturing, smooth: $('smooth').checked,
      ghost: modes.ghost, reveal: modes.reveal, maskView: $('mask-view').checked});
    ctx.putImageData(new ImageData(result.pixels, engine.width, engine.height), 0, 0);
    if (!$('mask-view').checked) drawEffects(result, dt);
    if (modes.freeze) {
      if (!freezeReady) { frozen.getContext('2d').drawImage(preview, 0, 0); freezeReady = true; }
      ctx.drawImage(frozen, 0, 0);
    }
    $('fps').textContent = `${fps.toFixed(0)} FPS`;
    animation = requestAnimationFrame(frame);
  } catch (error) { stop(`Preview stopped: ${error.message}. Restart the camera or demo.`); }
}

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') { stop(); return; }
  if (event.ctrlKey || event.metaKey || event.altKey || event.repeat ||
      ['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName)) return;
  const key = event.key.toLowerCase();
  if (key === 'escape') stop();
  else if (key === 'b') capture();
  else if (key === 'i') { $('invisible').checked = !$('invisible').checked; $('invisible').dispatchEvent(new Event('change')); }
  else if (key === 'c') { $('calibration').open = !$('calibration').open; }
  else if (['1', '2', '3'].includes(key)) { $('color').value = ['green', 'red', 'blue'][Number(key) - 1]; applyPreset(); }
  else {
    const name = {g: 'ghost', m: 'steps', s: 'sparkles', r: 'reveal', h: 'shield', t: 'freeze'}[key];
    if (name) toggle(name);
  }
});
