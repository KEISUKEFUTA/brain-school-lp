// Usage: node render.cjs [stills t1,t2,...]  → frames piped into ffmpeg (or PNG stills)
const { chromium } = require(process.env.PW || 'playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
(async () => {
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ proxy, args: ['--disable-gpu-vsync'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, ignoreHTTPSErrors: true });
  await page.goto('file://' + path.join(__dirname, 'index.html') + '?render=1');
  await page.evaluate(() => window.ready);
  const grab = t => page.evaluate(t => { renderFrame(t, 5); return document.getElementById('out').toDataURL('image/png').split(',')[1]; }, t);
  if (process.argv[2] === 'stills') {
    const dir = process.argv[4] || 'stills'; fs.mkdirSync(dir, { recursive: true });
    for (const t of process.argv[3].split(',').map(Number)) fs.writeFileSync(`${dir}/t${t.toFixed(2)}.png`, Buffer.from(await grab(t), 'base64'));
  } else {
    const out = process.argv[2] || 'frames.mp4';
    const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < 450; f++) {
      const buf = Buffer.from(await grab(f / 30), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 30 === 0) process.stderr.write(`frame ${f}\n`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
