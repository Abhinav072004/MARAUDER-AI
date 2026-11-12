import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CloakEngine, PRESETS, medianBackground} from '../engine.js';

function solid(w, h, rgb) {
  const image = new Uint8ClampedArray(w * h * 4);
  for (let p = 0; p < w * h; p++) image.set([...rgb, 255], p * 4);
  return image;
}

for (const [color, rgb] of [['green', [0,255,0]], ['red', [255,0,0]], ['blue', [0,0,255]]]) {
  test(`${color} preset detects cloak and replaces background`, () => {
    const engine = new CloakEngine(16, 16);
    engine.setBounds(PRESETS[color]);
    engine.capture([solid(16,16,[30,40,50]), solid(16,16,[30,40,50]), solid(16,16,[255,255,255])]);
    const result = engine.render(solid(16,16,rgb), {smooth: false});
    assert.deepEqual([...result.pixels.slice(0,4)], [30,40,50,255]);
    assert.equal(result.bounds.width,16);
  });
}

test('unmatched pixels, missing background, disable and intensity zero stay unchanged', () => {
  const engine = new CloakEngine(16,16);
  const green = solid(16,16,[0,255,0]);
  assert.deepEqual(engine.render(green).pixels, green);
  engine.background = solid(16,16,[10,20,30]);
  assert.deepEqual(engine.render(green,{intensity:0}).pixels,green);
  assert.deepEqual(engine.render(green,{enabled:false}).pixels,green);
  const blue = solid(16,16,[0,0,255]);
  assert.deepEqual(engine.render(blue,{smooth:false}).pixels,blue);
});

test('mask refinement rejects isolated noise and colour change resets history', () => {
  const engine = new CloakEngine(24,24);
  const input = solid(24,24,[20,20,20]);
  input.set([0,255,0,255], (12*24+12)*4);
  assert.equal(engine.render(input).bounds,null);
  engine.render(solid(24,24,[0,255,0]));
  engine.setBounds(PRESETS.blue);
  const result=engine.render(solid(24,24,[0,255,0]));
  assert.equal(result.bounds,null);
  assert.equal(engine.alpha[0],0);
});

test('median capture, validation and feathering', () => {
  assert.deepEqual([...medianBackground([new Uint8Array([10,20,30,255]),new Uint8Array([10,20,30,255]),new Uint8Array([255,255,255,255])])],[10,20,30,255]);
  assert.throws(()=>medianBackground([]));
  const engine = new CloakEngine(24,24);
  assert.throws(()=>engine.setBounds([0,200,0,179,100,255]));
  assert.throws(()=>engine.capture([new Uint8Array(4),new Uint8Array(4),new Uint8Array(4)]));
  const input=solid(24,24,[20,20,20]);
  for(let y=6;y<18;y++) for(let x=6;x<18;x++) input.set([0,255,0,255],(y*24+x)*4);
  engine.render(input);
  assert(engine.alpha[12*24+6]>0 && engine.alpha[12*24+6]<1);
  assert.equal(engine.alpha[12*24+12],1);
});

test('wrapped red hue catches both ends of the hue circle', () => {
  const engine = new CloakEngine(4,4);
  engine.setBounds(PRESETS.red);
  engine.detect(solid(4,4,[255,0,10]));
  assert(engine.raw.every(value=>value===255));
  engine.detect(solid(4,4,[255,10,0]));
  assert(engine.raw.every(value=>value===255));
});
