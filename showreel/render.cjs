// Usage: node render.cjs [stills t1,t2,...]  → frames piped into ffmpeg (or PNG stills)
const { chromium } = require(process.env.PW || 'playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
(async () => {
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, ignoreHTTPSErrors: true });
  // serve over http so the photo doesn't taint the canvas (file:// images can't be read back)
  const types = { '.html': 'text/html', '.css': 'text/css', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.wav': 'audio/wav' };
  const server = require('http').createServer((req, res) => {
    const f = path.join(__dirname, decodeURIComponent(req.url.split('?')[0]));
    if (!f.startsWith(__dirname) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
  }).listen(0);
  await page.goto(`http://127.0.0.1:${server.address().port}/index.html?render=1`);
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
  await browser.close(); server.close();
})();
