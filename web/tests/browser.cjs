const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const artifacts = path.resolve(__dirname,'../test-results');
fs.mkdirSync(artifacts,{recursive:true});
const base = process.env.BASE_URL || 'http://127.0.0.1:8765/';
(async () => {
 const browser = await chromium.launch({...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH} : {}), headless:true,
   args:['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
 try {
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!r.url().startsWith(new URL(base).origin)&&!r.url().startsWith('data:'))external.push(r.url())});
  await page.goto(base);
  await page.screenshot({path:path.join(artifacts,'welcome.png'), fullPage:true});
  await page.getByRole('button',{name:'Try a synthetic demo'}).click();
  await page.waitForFunction(()=>document.querySelector('#fps').textContent!=='— FPS');
  await page.locator('[data-mode="ghost"]').click();
  await page.locator('[data-mode="sparkles"]').click();
  await page.waitForTimeout(1500);
  assert.equal(await page.locator('[data-mode="ghost"]').getAttribute('aria-pressed'),'true');
  await page.keyboard.press('g');
  assert.equal(await page.locator('[data-mode=ghost]').getAttribute('aria-pressed'),'false');
  await page.keyboard.press('g');
  await page.locator('#capture').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Background locked'),null,{timeout:10000});
  await page.locator('[data-mode="freeze"]').click();
  await page.waitForTimeout(200);
  const before=await page.locator('#preview').evaluate(c=>c.toDataURL());
  await page.waitForTimeout(400);
  const after=await page.locator('#preview').evaluate(c=>c.toDataURL());
  assert.equal(before,after);
  await page.locator('[data-mode="freeze"]').click();
  await page.waitForTimeout(1000);
  await page.screenshot({path:path.join(artifacts,'demo.png'),fullPage:true});
  const fps=await page.locator('#fps').textContent();
  await page.locator('#stop').click();
  assert.equal(await page.locator('#source').textContent(),'LAB OFFLINE');
  await page.locator('#start').click();
  await page.waitForFunction(()=>document.querySelector('#source').textContent.startsWith('LIVE CAMERA'),null,{timeout:10000});
  await page.locator('#capture').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Background locked'),null,{timeout:10000});
  await page.locator('#stop').click();
  assert(await page.locator('#camera').evaluate(v=>v.srcObject===null));
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(artifacts,'mobile.png'),fullPage:true});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.addInitScript(() => {
   Object.defineProperty(navigator.mediaDevices, 'getUserMedia', {
    value: async () => {throw new DOMException('Denied in test','NotAllowedError')}
   });
  });
  await page.reload();
  await page.locator('#start').click();
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('permission denied'));
  await page.getByRole('button',{name:'Try a synthetic demo'}).click();
  await page.waitForFunction(()=>document.querySelector('#source').textContent==='SYNTHETIC DEMO');
  await page.locator('#stop').click();
  assert.deepEqual(errors,[]);
  assert.deepEqual(external,[],'No third-party requests during camera/demo use');
  console.log('Browser tests passed: demo, background capture, mode toggles, freeze, fake-webcam capture, device cleanup, permission-denial recovery, mobile layout. Demo:',fps);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
