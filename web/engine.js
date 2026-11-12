/** Pure browser colour-key pipeline. Pixels are RGBA; HSV uses OpenCV units. */
export const PRESETS = {
  green: [35, 70, 50, 85, 255, 255],
  red: [170, 100, 50, 10, 255, 255],
  blue: [90, 80, 50, 130, 255, 255],
};

export function medianBackground(frames) {
  if (frames.length < 3 || frames.length % 2 !== 1) {
    throw new Error('Capture requires an odd number of at least three frames.');
  }
  const length = frames[0].length;
  if (!frames.every(frame => frame.length === length)) {
    throw new Error('Background frames must have the same dimensions.');
  }
  const result = new Uint8ClampedArray(length);
  const samples = new Uint8Array(frames.length);
  for (let i = 0; i < length; i++) {
    if (i % 4 === 3) { result[i] = 255; continue; }
    for (let f = 0; f < frames.length; f++) samples[f] = frames[f][i];
    samples.sort();
    result[i] = samples[samples.length >> 1];
  }
  return result;
}

export class CloakEngine {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.size = width * height;
    this.bounds = [...PRESETS.green];
    this.background = null;
    this.history = false;
    this.raw = new Uint8Array(this.size);
    this.cleaned = new Uint8Array(this.size);
    this.scratch = new Uint8Array(this.size);
    this.visited = new Uint8Array(this.size);
    this.queue = new Int32Array(this.size);
    this.blur = new Float32Array(this.size);
    this.alpha = new Float32Array(this.size);
    this.output = new Uint8ClampedArray(this.size * 4);
    this.lastBounds = null;
  }

  setBounds(bounds) {
    if (bounds.length !== 6 || bounds.some((v, i) => !Number.isInteger(v) ||
      v < 0 || v > (i % 3 === 0 ? 179 : 255)) || bounds[1] > bounds[4] || bounds[2] > bounds[5]) {
      throw new Error('Invalid HSV bounds. S/V low must not exceed high.');
    }
    this.bounds = [...bounds];
    this.history = false;
  }

  capture(frames) {
    const background = medianBackground(frames);
    if (background.length !== this.size * 4) throw new Error('Capture dimensions changed.');
    this.background = background;
    this.history = false;
  }

  detect(pixels) {
    const [hl, sl, vl, hh, sh, vh] = this.bounds;
    for (let i = 0, p = 0; p < this.size; p++, i += 4) {
      const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
      const max = Math.max(r, g, b), min = Math.min(r, g, b), diff = max - min;
      let hue = 0;
      if (diff) {
        if (max === r) hue = ((g - b) / diff + (g < b ? 6 : 0)) * 30;
        else if (max === g) hue = ((b - r) / diff + 2) * 30;
        else hue = ((r - g) / diff + 4) * 30;
      }
      const sat = max ? diff * 255 / max : 0;
      const inHue = hl <= hh ? hue >= hl && hue <= hh : hue >= hl || hue <= hh;
      this.raw[p] = inHue && sat >= sl && sat <= sh && max >= vl && max <= vh ? 255 : 0;
    }
  }

  morphology(input, output, dilate) {
    const w = this.width, h = this.height;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let value = dilate ? 0 : 255;
        for (let dy = -1; dy <= 1; dy++) {
          const row = Math.max(0, Math.min(h - 1, y + dy)) * w;
          for (let dx = -1; dx <= 1; dx++) {
            const sample = input[row + Math.max(0, Math.min(w - 1, x + dx))];
            value = dilate ? Math.max(value, sample) : Math.min(value, sample);
          }
        }
        output[y * w + x] = value;
      }
    }
  }

  components() {
    const w = this.width, h = this.height, minArea = Math.max(3, this.size * 0.0005);
    this.visited.fill(0);
    let largest = 0, bounds = null;
    for (let start = 0; start < this.size; start++) {
      if (!this.cleaned[start] || this.visited[start]) continue;
      let read = 0, count = 1, minX = w, minY = h, maxX = 0, maxY = 0;
      this.queue[0] = start;
      this.visited[start] = 1;
      while (read < count) {
        const p = this.queue[read++], x = p % w, y = Math.floor(p / w);
        minX = Math.min(minX, x); maxX = Math.max(maxX, x);
        minY = Math.min(minY, y); maxY = Math.max(maxY, y);
        const visit = n => {
          if (this.cleaned[n] && !this.visited[n]) {
            this.visited[n] = 1; this.queue[count++] = n;
          }
        };
        if (x > 0) visit(p - 1);
        if (x < w - 1) visit(p + 1);
        if (y > 0) visit(p - w);
        if (y < h - 1) visit(p + w);
      }
      if (count < minArea) {
        for (let i = 0; i < count; i++) this.cleaned[this.queue[i]] = 0;
      } else if (count > largest) {
        largest = count;
        bounds = {x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1};
      }
    }
    this.lastBounds = bounds;
  }

  refine(smooth, dt) {
    if (smooth) {
      this.morphology(this.raw, this.scratch, false);
      this.morphology(this.scratch, this.cleaned, true);
      this.morphology(this.cleaned, this.scratch, true);
      this.morphology(this.scratch, this.cleaned, false);
    } else this.cleaned.set(this.raw);
    this.components();
    const w = this.width, h = this.height;
    const weight = this.history && smooth ? 1 - Math.exp(-dt / 0.045) : 1;
    if (smooth) {
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const p = y * w + x;
          this.blur[p] = (this.cleaned[y * w + Math.max(x - 1, 0)] +
            this.cleaned[p] * 2 + this.cleaned[y * w + Math.min(x + 1, w - 1)]) / 4;
        }
      }
    }
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const p = y * w + x;
        const value = smooth ? (this.blur[Math.max(0, y - 1) * w + x] +
          this.blur[p] * 2 + this.blur[Math.min(h - 1, y + 1) * w + x]) / 4 : this.cleaned[p];
        this.alpha[p] += (value / 255 - this.alpha[p]) * weight;
      }
    }
    this.history = true;
  }

  render(pixels, {dt = 1 / 30, time = 0, intensity = 1, enabled = true,
    smooth = true, ghost = false, reveal = false, maskView = false} = {}) {
    if (pixels.length !== this.size * 4) throw new Error('Frame dimensions changed.');
    this.detect(pixels);
    this.refine(smooth, dt);
    const w = this.width;
    for (let y = 0; y < this.height; y++) {
      const offset = ghost ? Math.round(2.5 * Math.sin(y * 0.06 + time * 4)) : 0;
      for (let x = 0; x < w; x++) {
        const p = y * w + x, i = p * 4, mask = this.alpha[p];
        const edge = Math.abs(mask - this.alpha[y * w + Math.max(0, x - 2)]) +
          Math.abs(mask - this.alpha[Math.max(0, y - 2) * w + x]);
        const a = this.background && enabled ? mask * intensity * (ghost ? 0.5 : 1) : 0;
        const sample = (y * w + Math.max(0, Math.min(w - 1, x + offset))) * 4;
        for (let c = 0; c < 3; c++) {
          let value = a ? pixels[i + c] * (1 - a) + this.background[sample + c] * a : pixels[i + c];
          if (ghost && enabled && this.background) value += edge * [30, 160, 220][c] * intensity * 0.5;
          if (reveal) value = pixels[i + c] * (1 - mask * 0.35) +
            [175, 65, 225][c] * mask * 0.35 + edge * (0.5 + 0.2 * Math.sin(time * 4)) * [180, 120, 240][c];
          this.output[i + c] = maskView ? mask * 255 : value;
        }
        this.output[i + 3] = 255;
      }
    }
    return {pixels: this.output, bounds: this.lastBounds, mask: this.cleaned};
  }
}
