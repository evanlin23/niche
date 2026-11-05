// QA + stills driver: one headless Chromium for many scenes.
// Usage: node probe.js job.json
//   job = {root, mode: 'shots'|'probe', items: [{spec, W, H, scale, shots: [{frame, png}], frames: [..], out}]}
//   shots: render those frames to PNG.  probe: step the scene WITHOUT drawing at each frame and write the stage state
//   (every visible DOM text: rect, opacity, text, role, anchor; every scene object: visibility, world position,
//   opacity, projected bbox, QA kind; kit tweens in flight) as JSON lines to item.out (pipeline/qa_visual.py reads it).
const fs = require('fs'), path = require('path'), http = require('http');
const { chromium } = require('playwright');
const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.ttf': 'font/ttf', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const p = path.join(job.root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(job.root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

// runs inside the page
function qaState(t) {
  const S = window.STAGE;
  window.__ids = window.__ids || new WeakMap(); window.__n = window.__n || 0;
  const id = (o) => { if (!window.__ids.has(o)) window.__ids.set(o, ++window.__n); return window.__ids.get(o); };
  const root = document.getElementById('root');
  const texts = [];
  for (const el of root.querySelectorAll('div,span')) {
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('').trim();
    if (!own) continue;
    let op = 1, e = el, hidden = false;
    while (e && e !== root) { const cs = getComputedStyle(e); op *= parseFloat(cs.opacity); if (cs.display === 'none' || cs.visibility === 'hidden') hidden = true; e = e.parentElement; }
    if (hidden || op < 0.02) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    let role = el.dataset.qa, anchor = el.dataset.anchor;
    if (!role && el.parentElement && el.parentElement.dataset) role = el.parentElement.dataset.qa;
    texts.push({ id: id(el), text: el.textContent.trim().slice(0, 160), op: +op.toFixed(3), r: [r.left, r.top, r.right, r.bottom].map((v) => +v.toFixed(1)), role: role || '', anchor: anchor || '' });
  }
  const cam = S.camera, W = S.W, H = S.H;
  const objs = [];
  const units = [];
  const marked = (o) => o.userData && o.userData.qa;
  let anyMarked = false; S.scene.traverse((o) => { if (marked(o)) anyMarked = true; });
  const walk = (o, depth) => {
    for (const c of o.children) {
      if (c.isLight || c.isCamera) continue;
      if (marked(c)) { units.push([c, c.userData.qa]); continue; }
      if (!anyMarked && depth === 0 && (c.isGroup || c.isMesh)) { units.push([c, 'auto']); continue; }
      walk(c, depth + 1);
    }
  };
  walk(S.scene, 0);
  for (const [o, kind] of units) {
    let vis = true, e = o; while (e) { if (!e.visible) { vis = false; break; } e = e.parent; }
    if (!vis) continue;
    const b = window.__box.setFromObject(o);
    if (b.isEmpty()) continue;
    const sz = b.getSize(window.__v1);
    if (kind === 'auto' && Math.max(sz.x, sz.y, sz.z) > 8) continue;      // floor, table, room
    let op = 1; o.traverse((m) => { if (m.isMesh && m.visible) { const ms = Array.isArray(m.material) ? m.material : [m.material]; for (const mt of ms) if (mt.transparent) op = Math.min(op, mt.opacity); } });
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, behind = false;
    for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
      const v = window.__v2.set(x, y, z); v.applyMatrix4(cam.matrixWorldInverse); if (v.z > -0.01) behind = true; v.applyMatrix4(cam.projectionMatrix);
      const px = (v.x + 1) / 2 * W, py = (1 - v.y) / 2 * H; x0 = Math.min(x0, px); x1 = Math.max(x1, px); y0 = Math.min(y0, py); y1 = Math.max(y1, py);
    }
    const c = b.getCenter(window.__v1);
    objs.push({ id: id(o), kind, name: o.name || o.type, op: +op.toFixed(3), p: [c.x, c.y, c.z].map((v) => +v.toFixed(4)),
      s: [+o.scale.x.toFixed(4)], r: behind ? null : [x0, y0, x1, y1].map((v) => +v.toFixed(1)) });
  }
  // ---- geometric clipping: oriented boxes for every unit, pairwise separating-axis test
  const obbs = [];
  const inv = new window.__M4(), rel = new window.__M4();
  for (const [o, kind] of units) {
    let vis = true, e = o; while (e) { if (!e.visible) { vis = false; break; } e = e.parent; }
    if (!vis) continue;
    o.updateMatrixWorld(true);
    inv.copy(o.matrixWorld).invert();
    let lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9], op = 1;
    o.traverse((m) => {
      if (!m.isMesh || !m.visible || !m.geometry) return;
      const ms = Array.isArray(m.material) ? m.material : [m.material];
      for (const mt of ms) if (mt.transparent) op = Math.min(op, mt.opacity);
      if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
      const bb = m.geometry.boundingBox; rel.multiplyMatrices(inv, m.matrixWorld);
      for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) {
        const v = window.__v2.set(x, y, z).applyMatrix4(rel);
        lo = [Math.min(lo[0], v.x), Math.min(lo[1], v.y), Math.min(lo[2], v.z)]; hi = [Math.max(hi[0], v.x), Math.max(hi[1], v.y), Math.max(hi[2], v.z)];
      }
    });
    if (lo[0] > hi[0] || op < 0.05) continue;
    const me = o.matrixWorld.elements, ax = [], ext = [];
    for (let k = 0; k < 3; k++) {
      const L = Math.hypot(me[k * 4], me[k * 4 + 1], me[k * 4 + 2]) || 1;
      ax.push([me[k * 4] / L, me[k * 4 + 1] / L, me[k * 4 + 2] / L]); ext.push((hi[k] - lo[k]) / 2 * L);
    }
    const lc = window.__v2.set((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2).applyMatrix4(o.matrixWorld);
    const c = [lc.x, lc.y, lc.z];
    if (kind === 'auto' && Math.max(...ext) > 4) continue;            // room / table / floor
    const name = (o.userData.card ? 'card' : o.name || o.type) + '#' + id(o);
    if (o.userData.noclip) continue;                                   // containers (connect-4 frame) hold their pieces
    obbs.push({ c, ax, ext, name, card: !!o.userData.card });
  }
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const overlapOn = (A, B, d, L) => {          // overlap of the two boxes' projections on axis L (negative = gap)
    const ra = A.ext[0] * Math.abs(dot(A.ax[0], L)) + A.ext[1] * Math.abs(dot(A.ax[1], L)) + A.ext[2] * Math.abs(dot(A.ax[2], L));
    const rb = B.ext[0] * Math.abs(dot(B.ax[0], L)) + B.ext[1] * Math.abs(dot(B.ax[1], L)) + B.ext[2] * Math.abs(dot(B.ax[2], L));
    return ra + rb - Math.abs(dot(d, L));
  };
  const clips = [];
  for (let i = 0; i < obbs.length; i++) {
    const A = obbs[i];
    if (A.card) {                             // cards never go below the table surface
      let minY = A.c[1]; for (let k = 0; k < 3; k++) minY -= A.ext[k] * Math.abs(A.ax[k][1]);
      if (minY < -0.002) clips.push([A.name, 'table', +(-minY).toFixed(4), 'below']);
    }
    for (let j = i + 1; j < obbs.length; j++) {
      const B = obbs[j];
      const d = [B.c[0] - A.c[0], B.c[1] - A.c[1], B.c[2] - A.c[2]];
      const rA = Math.hypot(...A.ext), rB = Math.hypot(...B.ext);
      if (Math.hypot(...d) > rA + rB) continue;
      const axes = [...A.ax, ...B.ax];
      for (const a of A.ax) for (const b of B.ax) { const x = cross(a, b), n = Math.hypot(...x); if (n > 1e-6) axes.push(x.map((v) => v / n)); }
      let minOv = 1e9; for (const L of axes) minOv = Math.min(minOv, overlapOn(A, B, d, L));
      if (minOv > 0.002) { clips.push([A.name, B.name, +minOv.toFixed(4), 'intersect']); continue; }
      if (A.card && B.card) {                 // parallel overlapping cards: enough air along the normal?
        const nA = A.ax[1], nB = B.ax[1];
        if (Math.abs(dot(nA, nB)) > 0.999) {
          const inPlane = overlapOn(A, B, d, A.ax[0]) > 0.01 && overlapOn(A, B, d, A.ax[2]) > 0.01;
          const gap = -overlapOn(A, B, d, nA);
          if (inPlane && gap < 0.003) clips.push([A.name, B.name, +gap.toFixed(4), 'too-close']);
        }
      }
    }
  }
  const tw = ((S.qa && S.qa.tweens) || []).filter((w) => t > w.at + 1e-4 && t < w.at + w.dur - 1e-4).map((w) => w.name);
  const content = S.qa && S.qa.content ? [S.qa.content.l, S.qa.content.t, S.qa.content.r, S.qa.content.b] : null;
  return { t: +t.toFixed(3), texts, objs, tw, content, clips: clips.slice(0, 200) };
}

(async () => {
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  for (const it of job.items) {
    const page = await browser.newPage({ viewport: { width: Math.round(it.W * it.scale), height: Math.round(it.H * it.scale) } });
    let failed = null;
    page.on('pageerror', (e) => { console.error(`pageerror (${it.spec}):`, e.message); failed = e.message; });
    page.on('console', (m) => { if (m.type() === 'error') console.error('console:', m.text()); });
    await page.goto(`http://127.0.0.1:${port}/pipeline/web/stage.html`);
    await page.waitForFunction('window.READY');
    const n = await page.evaluate((u) => window.setup(u), it.spec);
    if (job.mode === 'probe') {
      await page.evaluate(async () => {
        const T = await import('three'); window.__box = new T.Box3(); window.__v1 = new T.Vector3(); window.__v2 = new T.Vector3(); window.__M4 = T.Matrix4;
      });
      await page.evaluate(`window.qaState = ${qaState.toString()}`);
      const lines = [];
      for (const f of it.frames) {
        if (f >= n) continue;
        const st = await page.evaluate(([k, fps]) => { window.step(k, false); return window.qaState(k / fps); }, [f, it.fps || 30]);
        st.f = f;
        if (!lines.length) st.alltw = await page.evaluate(() => ((window.STAGE.qa && window.STAGE.qa.tweens) || []));
        lines.push(JSON.stringify(st));
      }
      fs.writeFileSync(it.out, lines.join('\n') + '\n');
      if (failed) fs.appendFileSync(it.out, JSON.stringify({ error: failed }) + '\n');
    } else {
      const cdp = await page.context().newCDPSession(page);
      for (const s of it.shots) {
        await page.evaluate((k) => window.frame(k), Math.min(s.frame, n - 1));
        const { data } = await cdp.send('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(s.png, Buffer.from(data, 'base64'));
      }
    }
    await page.close();
    if (failed) process.exitCode = 1;
  }
  await browser.close(); server.close();
})().catch((e) => { console.error(e); process.exit(1); });
