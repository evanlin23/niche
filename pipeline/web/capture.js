// Usage: node capture.js job.json
// job: {root, spec: "/url/of/spec.json", out, width, height, fps, n_frames, crf}
const fs = require('fs'), path = require('path'), http = require('http'), { spawn } = require('child_process');
const { chromium } = require('playwright');
const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.ttf': 'font/ttf', '.jpg': 'image/jpeg' };

const server = http.createServer((req, res) => {
  const p = path.join(job.root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(job.root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: job.width, height: job.height } });
  page.on('pageerror', (e) => { console.error('pageerror:', e.message); process.exitCode = 1; });
  page.on('console', (m) => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/pipeline/web/stage.html`);
  await page.waitForFunction('window.READY');
  const n = await page.evaluate((u) => window.setup(u), job.spec);
  const ff = job.png ? null : spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(job.fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', String(job.crf || 18), '-pix_fmt', 'yuv420p', '-r', String(job.fps),
    '-movflags', '+faststart', job.out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const cdp = await page.context().newCDPSession(page);
  const frames = job.only_frame != null ? [job.only_frame] : [...Array(n).keys()];
  for (const i of frames) {
    await page.evaluate((k) => window.frame(k), i);
    const { data } = await cdp.send('Page.captureScreenshot', { format: job.png ? 'png' : 'jpeg', quality: 93, optimizeForSpeed: true });
    const buf = Buffer.from(data, 'base64');
    if (job.png) { fs.writeFileSync(job.png, buf); continue; }
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  if (ff) { ff.stdin.end(); await new Promise((r) => ff.on('close', r)); }
  await browser.close(); server.close();
})().catch((e) => { console.error(e); process.exit(1); });
