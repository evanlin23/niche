// Buh Simulates scene kit: reusable, data-driven scene templates for every episode.
//
// Every template is driven by scenes.yaml params (word anchors already resolved to seconds by pipeline/kit.py),
// keeps moving (orbit / push-in + events on the words), and lays itself out for BOTH 16:9 and 9:16:
// the 3D content is fitted into a "content rect" (camera distance + view offset), and the DOM text lives in
// rows (title, player pill, callout chip, note chip) that never overlap the content or each other.
//
// QA hooks (pipeline/qa_visual.py reads them through pipeline/web/probe.js):
//   stage.qa.tweens   every eased transition: {name, at, dur}  -> "nothing mid-animation at the cut"
//   obj.userData.qa   'key' (must be inside title-safe), 'decor' (must be inside the frame), 'idle' (ambient loop)
//   el.dataset.qa     role of a DOM label; el.dataset.anchor = the word anchor it was timed from ('k5@thirty')
//
// Docs + params examples: docs/scene-kit.md
import { THREE, RoundedBoxGeometry, clamp, ease, lerp } from '/pipeline/web/stage.js';
import { GN, buildRoom, makeCard, CARD, cardTexture } from '/pipeline/web/gamenight.js';
import { unoTexture } from '/pipeline/web/unocards.js';

export const NAMED = () => ({ MUSTARD: GN.mustard, CORAL: GN.coral, TEAL: GN.teal, BLUE: GN.blue, TEXT: GN.text,
  MUTED: GN.muted, CREAM: GN.cream, GREEN: GN.green, RED: GN.red, PLUM: GN.plum, NAVY: GN.ink, GREY: '#8d8273' });
export const col = (c, dflt = GN.cream) => (c == null ? dflt : (NAMED()[c] || c));
const INK = '#1b1209';

// ================================================================== layout
// Title-safe = 5% margin on every side. Rows are stacked from the top; the content rect is what is left.
export function layoutFor(stage) {
  const W = stage.W, H = stage.H, vert = H > W, short = !!stage.spec.short;
  const m = 0.05;
  const safe = { l: W * m, t: H * m, r: W * (1 - m), b: H * (1 - m) };
  return { W, H, vert, short, safe, sw: safe.r - safe.l, cx: W / 2, u: vert ? 1.12 : 1 };
}

// ================================================================== DOM labels (own system: sub-pixel, QA tagged)
const FONT = 'Rubik, Inter, sans-serif';
class Labels {
  constructor(stage, L) { this.stage = stage; this.L = L; this.items = []; }
  add(o) {
    const d = document.createElement('div');
    const size = o.size || 36;
    Object.assign(d.style, {
      position: 'absolute', left: '0px', top: '0px', fontFamily: FONT, fontSize: size + 'px', fontWeight: o.weight || 900,
      color: o.pill ? (o.color || INK) : col(o.color, GN.text), lineHeight: o.lh || 1.12, letterSpacing: '-0.5px',
      whiteSpace: o.maxW ? 'normal' : 'nowrap', maxWidth: o.maxW ? o.maxW + 'px' : 'none', opacity: 0,
      textAlign: o.align || 'center', fontVariantNumeric: 'tabular-nums', willChange: 'transform,opacity',
      textShadow: o.pill ? 'none' : '0 4px 18px rgba(0,0,0,.45)', boxSizing: 'border-box',
    });
    if (o.pill) Object.assign(d.style, { background: col(o.pill, GN.mustard), padding: `${Math.round(size * 0.16)}px ${Math.round(size * 0.5)}px`, borderRadius: '999px' });
    if (o.stroke) d.style.webkitTextStroke = o.stroke;
    d.textContent = o.text ?? '';
    d.dataset.qa = o.role || 'label';
    if (o.anchor) d.dataset.anchor = o.anchor;
    this.stage.ov.appendChild(d);
    const it = { el: d, o, at: o.at ?? -1, until: o.until ?? 1e9, fade: o.fade ?? 0.25, x: o.x ?? 0, y: o.y ?? 0 };
    this.items.push(it);
    return it;
  }
  measure(it) { return [it.el.offsetWidth, it.el.offsetHeight]; }
  update(t) {
    const S = this.L.safe;
    for (const it of this.items) {
      const o = it.o;
      let a = o.alpha ? o.alpha(t) : Math.min(clamp((t - it.at) / it.fade), 1 - clamp((t - (it.until - it.fade)) / it.fade));
      if (it.at <= 0 && !o.alpha) a = Math.min(1, 1 - clamp((t - (it.until - it.fade)) / it.fade));
      a = clamp(a);
      it.el.style.opacity = a < 0.002 ? 0 : a;
      if (a < 0.002) continue;
      let [x, y] = o.pos ? o.pos(t) : [it.x, it.y];
      const [w, h] = this.measure(it);
      // anchor: x is the centre (align center) / left / right edge; y is the top
      let left = o.align === 'left' ? x : o.align === 'right' ? x - w : x - w / 2;
      if (o.clamp !== false) {                      // projected labels never leave the title-safe area
        left = Math.max(S.l, Math.min(S.r - w, left));
        y = Math.max(S.t, Math.min(S.b - h, y));
      }
      const rise = o.rise === false || it.at <= 0 ? 0 : (1 - clamp((t - it.at) / (it.fade + 0.1))) * 14;
      it.el.style.transform = `translate3d(${left.toFixed(2)}px, ${(y + rise).toFixed(2)}px, 0) rotate(0.02deg)`;
    }
  }
}

// ================================================================== camera fitting
const _v = new THREE.Vector3();
function projectAll(cam, pts, W, H) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const p of pts) {
    _v.copy(p).applyMatrix4(cam.matrixWorldInverse);
    if (_v.z > -0.05) return null;                 // behind the camera
    _v.applyMatrix4(cam.projectionMatrix);
    const x = (_v.x + 1) / 2 * W, y = (1 - _v.y) / 2 * H;
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  }
  return [x0, y0, x1, y1];
}
function placeCam(cam, look, dir, d) {
  cam.position.copy(look).addScaledVector(dir, d); cam.lookAt(look); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
}
export function dirFrom(elevDeg, yawDeg = 0) {
  const e = elevDeg * Math.PI / 180, a = yawDeg * Math.PI / 180;
  return new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e));
}
// smallest distance at which every pose in `dirs` keeps the points inside a w x h box
function fitDistance(stage, pts, look, dirs, w, h) {
  const cam = stage.camera; cam.clearViewOffset();
  let lo = 0.3, hi = 600;
  for (let i = 0; i < 46; i++) {
    const d = (lo + hi) / 2;
    let ok = true;
    for (const dir of dirs) {
      placeCam(cam, look, dir, d);
      const b = projectAll(cam, pts, stage.W, stage.H);
      if (!b || b[2] - b[0] > w || b[3] - b[1] > h) { ok = false; break; }
    }
    if (ok) hi = d; else lo = d;
  }
  return hi;
}
export function boxPoints(x0, y0, z0, x1, y1, z1) {
  const out = [];
  for (const x of [x0, x1]) for (const y of [y0, y1]) for (const z of [z0, z1]) out.push(new THREE.Vector3(x, y, z));
  return out;
}

// ================================================================== Kit: one per scene
export class Kit {
  constructor(stage, spec, { room = true, dark = false } = {}) {
    this.stage = stage; this.spec = spec; this.p = spec.params || {};
    this.L = layoutFor(stage);
    stage.qa = stage.qa || { tweens: [] };
    if (room) {
      this.room = buildRoom(stage, { feltW: 18, feltD: 9 });
      if (dark) {                                  // darker floor behind big 3D text
        if (this.room.floor) this.room.floor.material.color.multiplyScalar(0.72);
        stage.scene.background = new THREE.Color(stage.scene.background).multiplyScalar(0.72);
        if (stage.scene.fog) stage.scene.fog.color.multiplyScalar(0.72);
      }
    }
    this.labels = new Labels(stage, this.L);
    this.rowY = this.L.safe.t;                     // next free row (top of the header stack)
    this.bottomY = this.L.safe.b;                  // content ends here
    this.updaters = [];
    if (this.L.short) this._shortChrome(); else if (!this.p.no_brand) this._brand();
    this.content = null;
  }

  // ---------------------------------------------------------------- QA-registered tweens
  // every transition finishes before the cut: one starting on the scene's last word is shortened (min 0.12 s)
  tw(name, at, dur = 0.5) {
    const sp = this.stage.spec, end = (sp.n_frames ? (sp.n_frames - 1) / sp.fps : this.stage.duration) - 0.02;   // the last frame drawn
    if (at < end) dur = Math.max(0.12, Math.min(dur, end - at));
    this.stage.qa.tweens.push({ name, at, dur });
    const f = (t) => ease((t - at) / dur); f.dur = dur;
    return f;
  }
  key(obj, kind = 'key') { obj.userData.qa = kind; return obj; }
  // the main visual: in a long video it builds on its word; in a Short (first second decides everything) it is
  // pre-built in the first ~0.4 s (staggered by idx) and the word becomes an emphasis pulse instead.
  build(name, at, dur = 0.9, idx = 0) {
    if (!this.L.short) { const k = this.tw(name, at, dur); k.emph = () => 0; return k; }
    const k = this.tw(`${name} (pre-built)`, -0.52 + idx * 0.03, 0.6);   // frame 1: ~95% built AND still moving
    const e = this.tw(`${name} emphasis`, at, 0.7);
    k.emph = (t) => (t >= at ? Math.sin(Math.PI * e(t)) : 0);
    return k;
  }

  // ---------------------------------------------------------------- header rows
  _row(h, gap = 10) { const y = this.rowY; this.rowY += h + gap; return y; }
  label(o) { return this.labels.add(o); }
  title(text) {
    if (!text || this.L.short) return null;        // Shorts: the hook replaces the scene title
    const L = this.L, size = L.vert ? 60 : 60;
    const it = this.label({ text, size, role: 'title', at: -1, maxW: L.sw, lh: 1.08, x: L.cx });
    const [, h] = this.labels.measure(it);
    it.y = this._row(h, 14);
    return it;
  }
  pill(text) {           // player count / fair share: always on screen
    if (!text) return null;
    const it = this.label({ text, size: this.L.vert ? 32 : 30, weight: 700, role: 'pill', at: -1, pill: 'rgba(244,234,213,0.92)', x: this.L.cx, maxW: this.L.sw });
    const [, h] = this.labels.measure(it);
    it.y = this._row(h, 12);
    return it;
  }
  // callouts: [{text, at, color?, hold?, at_ref?}] one at a time in their own row (word-timed key facts)
  chips(list, { role = 'callout', size = 36, hold = 3.2, persistent = false, footer = false } = {}) {
    list = (list || []).filter((c) => typeof c.at === 'number').sort((a, b) => a.at - b.at);
    if (!list.length) return [];
    const L = this.L;
    const its = list.map((c, i) => {
      const next = list[i + 1] ? list[i + 1].at : 1e9;
      let until = persistent ? next - 0.02 : Math.min(next - 0.05, c.at + (c.hold || hold));
      if (until > this.stage.duration - 0.3) until = 1e9;      // would fade right at the cut: hold through it
      return this.label({ text: c.text, size, role, at: c.at, until, fade: 0.14, anchor: c.at_ref, maxW: L.sw, x: L.cx,
        pill: c.color === 'CORAL' ? GN.coral : c.color === 'CREAM' ? 'rgba(244,234,213,0.95)' : (c.pill ? col(c.pill) : GN.mustard) });
    });
    const h = Math.max(...its.map((it) => this.labels.measure(it)[1]));
    let y;
    if (footer) { this.bottomY -= h + 12; y = this.bottomY + 6; } else y = this._row(h, 12);
    its.forEach((it) => (it.y = y));
    return its;
  }
  notes(list) { return this.chips((list || []).map((n) => ({ ...n, color: n.color || 'CREAM', pill: n.pill })), { role: 'note', size: this.L.vert ? 34 : 34, persistent: true }); }
  // a free text row (e.g. the odds headline); returns the label
  headRow(o) {
    const it = this.label({ maxW: this.L.sw, x: this.L.cx, ...o, text: o.text || 'Xg' });
    const [, h] = this.labels.measure(it);
    it.el.textContent = o.text || '';
    it.y = this._row(o.h || h, 8);
    return it;
  }
  // standard header for most templates
  header({ title, pill, callouts, notes } = {}) {
    this.title(title ?? this.p.title);
    this.pill(pill ?? this.p.pill);
    this.notes(notes ?? this.p.notes);
    // 16:9: callouts in a footer row above the brand (keeps the header short); 9:16: under the notes
    this.chips(callouts ?? this.p.callouts, { footer: !this.L.vert });
  }
  // the rect the 3D content is fitted into (call after the header rows)
  contentRect(pad = 18) {
    const S = this.L.safe;
    this.content = { l: S.l, r: S.r, t: this.rowY + pad, b: this.bottomY - pad };
    this.content.w = this.content.r - this.content.l; this.content.h = this.content.b - this.content.t;
    this.stage.qa.content = this.content;          // the gate checks the main visual fills it (Shorts)
    return this.content;
  }
  // split the content rect: 16:9 -> left/right, 9:16 -> top/bottom. f = share of the first part
  split(f = 0.5, gap = 30) {
    const c = this.content || this.contentRect();
    if (this.L.vert) {
      const m = c.t + c.h * f;
      return [{ ...c, b: m - gap / 2, h: m - gap / 2 - c.t }, { ...c, t: m + gap / 2, h: c.b - m - gap / 2 }];
    }
    const m = c.l + c.w * f;
    return [{ ...c, r: m - gap / 2, w: m - gap / 2 - c.l }, { ...c, l: m + gap / 2, w: c.r - m - gap / 2 }];
  }

  // ---------------------------------------------------------------- camera rig: fit once, then orbit + push-in
  // pts: world points that must stay inside `rect`; elev: camera elevation (deg); yaw: max +/- deg of the orbit
  // (or 0 for a level push-in, e.g. overhead text); push: fraction of distance closed over the scene.
  fit(pts, { rect = null, elev = 28, yaw = 6, push = 0.07, look = null, fov = 30, margin = null } = {}) {
    margin = margin ?? (this.L.short ? 0.012 : 0.04);
    const stage = this.stage, cam = stage.camera, r = rect || this.content || this.contentRect();
    cam.fov = fov; cam.updateProjectionMatrix();
    const bb = new THREE.Box3().setFromPoints(pts);
    look = look ? new THREE.Vector3(...look) : bb.getCenter(new THREE.Vector3());
    const amp = Math.min(yaw, 0.5 * stage.duration);          // ~1 deg/s, never more than +/- yaw
    const dirs = [dirFrom(elev, -amp), dirFrom(elev, 0), dirFrom(elev, amp)];
    if (this.L.short && this.spec.short.first) dirs.push(dirFrom(elev, -amp - 12));   // the opening swing stays in frame too
    const dEnd = fitDistance(stage, pts, look, dirs, r.w * (1 - 2 * margin), r.h * (1 - 2 * margin));
    // view offset so the fitted content is centred in the rect (measured at the middle pose)
    placeCam(cam, look, dirs[1], dEnd);
    const b = projectAll(cam, pts, stage.W, stage.H);
    const dx = (r.l + r.r) / 2 - (b[0] + b[2]) / 2, dy = (r.t + r.b) / 2 - (b[1] + b[3]) / 2;
    this.rig = { look, elev, amp, d1: dEnd, d0: dEnd / (1 - push), dx, dy, pts, rect: r };
    // depth precision: a near plane scaled to the shot (a fixed 0.1 near at 30-60 units of distance left too few
    // depth steps for stacked cards: z-fighting flicker). Nothing in a kit shot comes closer than ~0.4 d.
    cam.near = Math.max(0.1, dEnd * 0.12); cam.far = this.rig.d0 * 5; cam.updateProjectionMatrix();
    // fog scaled to the shot: big boards sit far away and the room's fixed fog washed them out
    if (stage.scene.fog) { stage.scene.fog.near = this.rig.d0 * 1.4; stage.scene.fog.far = this.rig.d0 * 3.2; }
    this.applyCam(0);
    return this.rig;
  }
  applyCam(t) {
    const R = this.rig; if (!R) return;
    const stage = this.stage, cam = stage.camera;
    const k = this.L.short ? clamp(t / stage.duration) : ease(clamp(t / stage.duration));   // Shorts: moving from frame 1
    // Shorts open on a quick sideways swing, fastest at frame 1 and settled by 1.2 s: motion from the first frame
    // without starting smaller (an opening dolly-out made frame 1 emptier than the rest: opening gate)
    const swing = this.L.short && this.spec.short.first ? 12 * (1 - clamp(t / 1.2)) ** 2 : 0;
    const dir = dirFrom(R.elev, lerp(-R.amp, R.amp, k) - swing);
    cam.clearViewOffset();
    // Shorts open on a quick dolly-in, fastest at frame 1 and settled by 1.2 s (motion in the first second is the
    // retention gate); the slow orbit carries on from there
    placeCam(cam, R.look, dir, lerp(R.d0, R.d1, k));
    cam.setViewOffset(stage.W, stage.H, -R.dx, -R.dy, stage.W, stage.H);
    cam.updateProjectionMatrix(); cam.updateMatrixWorld();
  }
  project(v) { return this.stage.project(v instanceof THREE.Vector3 ? v : new THREE.Vector3(...v)); }
  // a label glued to a world point (below/above it), clamped to title-safe
  worldLabel(o, world, dy = 0) {
    const w = typeof world === 'function' ? world : () => world;
    return this.label({ ...o, pos: (t) => { const [x, y] = this.project(w(t)); return [x, y + dy]; } });
  }

  // ---------------------------------------------------------------- Shorts chrome (hook, captions, CTA + Buh)
  _shortChrome() {
    const L = this.L, sh = this.stage.spec.short, S = L.safe;
    const lines = String(sh.hook || '').split('\n');
    let y = S.t;
    if (sh.game) {   // context: which game this is (no "I simulated N games": that's the copycat template)
      const pill = document.createElement('div');
      pill.textContent = sh.game; pill.dataset.qa = 'context';
      Object.assign(pill.style, { position: 'absolute', left: L.cx + 'px', top: y + 'px', transform: 'translateX(-50%)',
        font: `700 34px ${FONT}`, color: GN.text, background: '#14281f', padding: '10px 28px', borderRadius: '40px',
        whiteSpace: 'nowrap', letterSpacing: '0.5px' });
      this.stage.ov.appendChild(pill);
      y += 74;
    }
    lines.forEach((ln, i) => {
      const it = this.label({ text: ln, size: lines.length > 2 ? 58 : 68, role: 'hook', at: -1, x: L.cx, y, maxW: L.sw,
        color: i === lines.length - 1 ? GN.mustard : GN.text, lh: 1.04 });
      y += this.labels.measure(it)[1] + 4;
    });
    this.rowY = y + 14;
    // CTA at the bottom: Buh + "Full video on my channel"
    const ctaH = 160, ctaY = S.b - ctaH;
    const box = document.createElement('div');
    Object.assign(box.style, { position: 'absolute', left: S.l + 'px', top: ctaY + 'px', width: L.sw + 'px', height: ctaH + 'px',
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '30px', opacity: 1 });
    const img = document.createElement('img'); img.src = '/branding/buh-happy.png';
    Object.assign(img.style, { width: '150px', height: '150px', borderRadius: '50%', objectFit: 'cover', objectPosition: '50% 58%' });
    img.dataset.qa = 'buh';
    const txt = document.createElement('div');
    txt.innerHTML = `<div data-qa="cta" style="font:900 52px ${FONT};color:${GN.text};letter-spacing:-0.5px">Full video</div>` +
      `<div data-qa="cta" style="font:700 42px ${FONT};color:${GN.mustard}">on my channel ▶</div>`;
    box.appendChild(img); box.appendChild(txt); this.stage.ov.appendChild(box);
    // captions: big 1-3 word chunks, timed from the aligned words, just above the CTA
    const capH = 120;
    this.bottomY = ctaY - capH - 4;
    const capY = ctaY - capH + 6;
    const words = sh.words || [];
    const chunks = []; let cur = [];
    for (const w of words) {
      cur.push(w);
      if (cur.length >= 3 || /[.,!?;:]$/.test(w[0]) || cur.map((x) => x[0]).join(' ').length > 14) { chunks.push(cur); cur = []; }
    }
    if (cur.length) chunks.push(cur);
    chunks.forEach((c, i) => {
      const a = c[0][1], nx = chunks[i + 1] ? chunks[i + 1][0][1] : c[c.length - 1][2] + 0.4;
      let until = nx - c[c.length - 1][2] > 0.6 ? c[c.length - 1][2] + 0.35 : nx;
      if (until > this.stage.duration - 0.2) until = 1e9;     // runs into the cut: hold, never fade at the cut
      const text = c.map((x) => x[0]).join(' ').toUpperCase().replace(/%/g, ' PERCENT').replace(/\s+/g, ' ').trim();
      // one line always: long chunks shrink (Rubik Black caps ~0.66 em per character) instead of wrapping into the CTA
      const size = Math.round(Math.min(80, L.sw / (0.66 * Math.max(1, text.length))));
      this.label({ text, size, role: 'caption', at: a, until, fade: 0.04, rise: false, x: L.cx, y: capY + (80 - size) / 2,
        color: GN.text, stroke: '3px #14281f' });
    });
  }
  _brand() {
    const S = this.L.safe;
    this.label({ text: 'BUH SIMULATES', size: 24, weight: 700, color: GN.brand, role: 'brand', at: -1, align: 'left', x: S.l, y: S.b - 30 });
    this.bottomY = S.b - 44;
  }

  // ---------------------------------------------------------------- per-frame
  frame(fn) {
    return (t, i) => {
      this.applyCam(t);
      this.stage.clear2d();
      if (fn) fn(t, i);
      for (const u of this.updaters) u(t);
      this.labels.update(t);
      const fo = this.spec.fade_out || 0, fi = this.spec.fade_in || 0;   // hard cuts by default
      const a = Math.max(fi ? 1 - clamp(t / fi) : 0, fo ? clamp((t - (this.stage.duration - fo)) / fo) : 0);
      if (a > 0.001) { const g = this.stage.g; g.fillStyle = `rgba(${GN.scrim},${a})`; g.fillRect(0, 0, this.stage.W, this.stage.H); }
    };
  }
}

// ================================================================== cards: EK types, Uno, or generic faces
const _gtex = {};
function genericTexture(f) {
  const key = JSON.stringify(f);
  if (_gtex[key]) return _gtex[key];
  const c = document.createElement('canvas'); c.width = 256; c.height = 356;
  const g = c.getContext('2d');
  g.beginPath(); g.roundRect(0, 0, 256, 356, 26); g.clip();
  g.fillStyle = GN.cream; g.fillRect(0, 0, 256, 356);
  g.fillStyle = col(f.color, GN.mustard); g.fillRect(0, 0, 256, 92);
  g.fillStyle = '#fff'; g.font = '900 30px Rubik'; g.textAlign = 'center';
  const lines = String(f.name || '').split('\n');
  lines.forEach((l, i) => g.fillText(l, 128, (lines.length > 1 ? 40 : 58) + i * 32));
  if (f.value != null) { g.fillStyle = col(f.color, GN.ink); g.font = '900 120px Rubik'; g.fillText(String(f.value), 128, 266); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  _gtex[key] = t; return t;
}
export function faceTex(face) {
  if (face == null || face === 'back') return cardTexture('back');
  if (typeof face === 'number') return cardTexture(face);
  if (typeof face === 'string' && face.startsWith('uno:')) { const [, c, k] = face.split(':'); return c === 'back' ? unoTexture('back', 0) : unoTexture(+c, +k); }
  if (typeof face === 'string') return genericTexture({ name: face });
  return genericTexture(face);
}
// ---- THE card builder. Every card in every kit scene comes from kitCard(), and every stack/overlap is laid out with
// layerY(): cards that overlap are always CARD_SEP apart along their normal (thickness + 6 mm-equivalent), so no two
// card faces are ever coplanar or interpenetrating (the probe's clipping check and the flicker gate verify it).
// Episode scene files must not build cards themselves (pipeline/qa_static.py fails them).
export const CARD_SEP = CARD.T + 0.004 + 0.006;   // body + the face plane lifted 0.004 + 6 mm-equivalent of air
export const layerY = (i, base = 0.02, scale = 1) => base + i * CARD_SEP * scale;
// a card lying flat (face up unless face is 'back'); card.setFace(face) swaps the art
export function kitCard(stage, face = 'back') {
  const c = makeCard(stage, 'back', false);
  c.setFace = (f) => { const m = c.userData.face.material; const tx = faceTex(f); if (m.map !== tx) { m.map = tx; m.needsUpdate = true; } };
  c.setFace(face);
  return c;
}
// orient a card to face a world point, top edge up (square-on to the camera)
function faceToward(card, target) {
  const d = new THREE.Vector3().subVectors(target, card.position).normalize();
  card.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
}

// ================================================================== pawns + Buh
export function makePawn(stage, color, s = 1) {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: col(color), roughness: 0.4 });
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.3 * s, 0.46 * s, 1.0 * s, 32), m); body.position.y = 0.5 * s; body.castShadow = true; g.add(body);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.33 * s, 32, 16), m); head.position.y = 1.28 * s; head.castShadow = true; g.add(head);
  g.userData.mat = m; g.userData.h = 1.62 * s;
  stage.scene.add(g); return g;
}
// Buh: the round teal cyclops, always happy (branding option H)
export function makeBuh(stage) {
  const g = new THREE.Group();
  const flat = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.55 });
  const add = (geo, y, x = 0, z = 0, mat) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; g.add(m); return m; };
  const teal = flat(GN.teal), ink = flat(0x1d2b3a), white = flat(0xffffff), must = flat(GN.mustard);
  add(new THREE.SphereGeometry(1.0, 48, 32), 1.05, 0, 0, teal).scale.set(1, 1.05, 0.95);
  add(new THREE.SphereGeometry(0.42, 32, 24), 1.25, 0, 0.8, white).scale.z = 0.55;
  add(new THREE.SphereGeometry(0.22, 24, 16), 1.32, 0.04, 0.95, ink).scale.z = 0.5;
  add(new THREE.SphereGeometry(0.06, 12, 8), 1.38, 0.09, 1.02, white);
  const smile = add(new THREE.TorusGeometry(0.16, 0.035, 10, 24, Math.PI * 0.8), 0.62, 0, 0.86, ink); smile.rotation.z = Math.PI * 1.1;
  for (const s of [-1, 1]) {
    add(new THREE.SphereGeometry(0.22, 20, 14), 0.08, s * 0.4, 0.2, must).scale.set(1.1, 0.55, 1.5);
    add(new THREE.CapsuleGeometry(0.11, 0.22, 8, 16), 0.95, s * 1.02, 0.05, teal).rotation.z = s * 0.6;
  }
  add(new THREE.CylinderGeometry(0.03, 0.03, 0.4, 12), 2.28, 0, 0, flat(0x8d8273));
  add(new THREE.SphereGeometry(0.12, 24, 16), 2.52, 0, 0, new THREE.MeshStandardMaterial({ color: GN.mustard, emissive: GN.mustard, emissiveIntensity: 0.4 }));
  stage.scene.add(g);
  return g;
}

// ================================================================== 3D text (statement / title)
import { TTFLoader } from 'three/addons/loaders/TTFLoader.js';
import { Font } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
let _font = null;
export async function rubikFont() {
  if (_font) return _font;
  const json = await new Promise((res, rej) => new TTFLoader().load('/pipeline/web/fonts/rubik-latin-900.ttf', res, undefined, rej));
  return (_font = new Font(json));
}
function wrapLines(lines, vert, maxChars) {
  if (!vert) return lines;
  const out = [];
  for (const ln of lines) {
    const ws = ln.text.split(' ');
    if (ln.text.length <= maxChars || ws.length < 2) { out.push(ln); continue; }
    const cut = [...Array(ws.length - 1).keys()].map((k) => k + 1)
      .reduce((b, k) => (Math.abs(ws.slice(0, k).join(' ').length - ws.slice(k).join(' ').length) < Math.abs(ws.slice(0, b).join(' ').length - ws.slice(b).join(' ').length) ? k : b), 1);
    out.push({ ...ln, text: ws.slice(0, cut).join(' ') }, { ...ln, text: ws.slice(cut).join(' ') });
  }
  return out;
}

const T = {};   // templates

// ---------------------------------------------------------------- statement: big 3D words on the floor, orbit
// params: lines [text | {text, color, at}], size, kicker
T.statement = async (stage, spec, { kicker = null, ring = false } = {}) => {
  const K = new Kit(stage, spec, { dark: true });
  const p = K.p, font = await rubikFont();
  if (kicker) K.headRow({ text: kicker, size: 40, weight: 700, color: GN.mustard, role: 'kicker', at: 0.02, fade: 0.15 });
  K.chips(p.callouts);
  K.contentRect(30);
  const raw = (spec.lines || p.lines || []).map((l) => (typeof l === 'string' ? { text: l, at: 0.05 } : { at: 0.05, ...l }));
  const lines = wrapLines(raw, K.L.vert, K.L.short ? 8 : 13);
  const size = p.size || 1.0, gap = size * (K.L.short ? 1.9 : 1.45);   // Shorts: a taller block fills the band
  const meshes = lines.map((ln, k) => {
    const geo = new TextGeometry(String(ln.text).toUpperCase(), { font, size, depth: size * 0.32, curveSegments: 6,
      bevelEnabled: true, bevelThickness: size * 0.03, bevelSize: size * 0.025, bevelSegments: 3 });
    geo.computeBoundingBox(); const bb = geo.boundingBox; geo.translate(-(bb.max.x + bb.min.x) / 2, 0, 0);
    const c = new THREE.Color(ln.color === 'MUSTARD' ? '#ffcc33' : ln.color === 'CORAL' ? '#ff7a63' : col(ln.color, '#ffffff'));
    const face = new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.55, roughness: 0.5, transparent: true, opacity: 0 });
    const side = new THREE.MeshStandardMaterial({ color: c.clone().multiplyScalar(0.55), roughness: 0.6, transparent: true, opacity: 0 });
    const m = new THREE.Mesh(geo, [face, side]); m.rotation.x = -Math.PI / 2;
    const z = (k - (lines.length - 1) / 2) * gap + size * 0.5;
    m.position.set(0, 0, z); m.visible = false;
    m.userData.k = K.tw(`line ${k + 1}`, ln.at, 0.3);
    m.userData.w = bb.max.x - bb.min.x;
    K.key(m); stage.scene.add(m);
    return m;
  });
  let wmax = Math.max(...meshes.map((m) => m.userData.w), 2);
  let zr = (lines.length * gap) / 2 + size * 0.4;
  if (K.L.short && meshes.length > 1) {
    // Shorts: stacked-poster lines, each scaled to the block's width (up to 2x), so the block fills the band
    let z = 0;
    const sc = meshes.map((m) => Math.min(2, wmax / m.userData.w));
    const hs = sc.map((k) => k * size * 1.25);
    const total = hs.reduce((a, b) => a + b, 0);
    meshes.forEach((m, k) => {
      m.scale.setScalar(sc[k]); z += hs[k];
      m.position.z = z - total / 2 - hs[k] * 0.12 + size * 0.5;
    });
    zr = total / 2 + size * 0.3;
  }
  let cards = [];
  if (ring) {        // title: our own cards around the words, inside the frame
    const faces = p.cards || [0, 1, 2, 3, 6, 7, 8, 4, 5];
    cards = faces.map((f, k) => {
      // on a rectangle around the words (an ellipse cut into the corners of wrapped lines)
      const c = kitCard(stage, f); const a = k / faces.length * Math.PI * 2 + 0.3, A = wmax / 2 + 1.3, B = zr + 1.0;
      const q = Math.max(Math.abs(Math.cos(a)) / A, Math.abs(Math.sin(a)) / B);
      c.position.set(Math.cos(a) / q, layerY(k, 0.08), Math.sin(a) / q + size * 0.5);
      c.rotation.y = 0; K.key(c, 'idle'); return c;
    });
  }
  const ext = ring ? [wmax / 2 + 2.0, zr + 2.0] : [wmax / 2 + 0.2, zr];
  K.fit(boxPoints(-ext[0], 0, size * 0.5 - ext[1], ext[0], size * 0.32, size * 0.5 + ext[1]), { elev: K.L.short ? 74 : 66, yaw: 3, push: 0.08, fov: 30 });
  return K.frame((t) => {
    for (const m of meshes) {
      const k = m.userData.k(t);
      m.material.forEach((mt) => (mt.opacity = k));
      m.visible = k > 0.001; m.castShadow = k > 0.6;
      m.position.y = (1 - k) * 0.25;
    }
    cards.forEach((c, k) => { c.position.y = layerY(k, 0.08) + Math.max(0, Math.sin(t * 1.4 + k)) * 0.03; });
  });
};
T.title = (stage, spec) => T.statement(stage, spec, { kicker: 'BUH SIMULATES', ring: true });

// ---------------------------------------------------------------- bars: ranking / comparison chart
// params.chart: {players, fair, unit, maxV, items: [{label, value, color, at, hl}]}  (+ title, callouts, notes)
function buildBars(K, ch, { x0, width, height, z = 0 }) {
  const stage = K.stage, items = ch.items, n = items.length;
  const unit = ch.unit ?? '%';
  const maxV = ch.maxV || Math.max(...items.map((i) => i.value)) / (K.L.short ? 0.9 : 0.74);   // tallest bar ~75% of the axis (Shorts: 90%, fill the frame)
  const gap = width / n, bw = Math.min(1.6, gap * 0.62), hq = stage.spec.quality === 'high';
  const dec = ch.decimals ?? 1;
  const bars = items.map((it, i) => {
    const color = col(it.color, GN.cream);
    const mat = hq ? new THREE.MeshPhysicalMaterial({ color, roughness: 0.32, clearcoat: 0.6, clearcoatRoughness: 0.25 })
                   : new THREE.MeshStandardMaterial({ color, roughness: 0.45 });
    const m = new THREE.Mesh(new RoundedBoxGeometry(bw, 1, bw, hq ? 6 : 3, hq ? 0.12 : 0.08), mat);
    const x = x0 + gap * (i + 0.5);
    m.position.set(x, 0, z); m.castShadow = m.receiveShadow = true; m.scale.y = 0.001; m.visible = false;
    K.key(m); stage.scene.add(m);
    const k = K.build(`bar ${it.label}`, it.at ?? 0.3, 0.9, i);
    const H = it.value / maxV * height;
    // context: true = a value implied by what is said (e.g. the 2-player complement); the number gate treats it like the fair line
    const val = K.worldLabel({ text: '', size: K.L.vert ? 46 : 44, role: it.context ? 'context' : 'value', at: K.L.short ? -1 : it.at ?? 0.3, anchor: it.at_ref, fade: 0.3,
      color: it.hl ? GN.mustard : GN.text }, () => new THREE.Vector3(x, Math.max(0.001, H * k(K.t)) + 0.2, z), -58);
    const lab = K.worldLabel({ text: it.label, size: K.L.vert ? 30 : 26, weight: 700, role: 'label', at: K.L.short ? -1 : it.at ?? 0.3, fade: 0.3,
      color: GN.muted, lh: 1.08 }, new THREE.Vector3(x, 0, z + bw / 2 + 0.3), 6);
    return { m, it, k, H, val, lab, x };
  });
  let fairMesh = null, fairLab = null;
  if (ch.fair != null) {
    const fy = ch.fair / maxV * height;
    fairMesh = new THREE.Mesh(new THREE.BoxGeometry(width + 0.6, 0.03, 0.05), new THREE.MeshStandardMaterial({ color: GN.text, emissive: GN.text, emissiveIntensity: 0.4 }));
    // in front of the bars with room for the emphasis pulse (bars widen 18%: the line went through them)
    fairMesh.position.set(x0 + width / 2, fy, z + bw / 2 * 1.2 + 0.06); fairMesh.visible = false; K.key(fairMesh); stage.scene.add(fairMesh);
    const first = K.L.short ? -1 : Math.min(...items.map((i) => i.at ?? 0.3));
    // 16:9: beside the end of the line (room reserved in the fit); 9:16: the player pill already says it
    if (!K.L.vert) fairLab = K.worldLabel({ text: `fair share ${ch.fair}${unit}`, size: 26, weight: 700, role: 'fair', at: first, fade: 0.4, align: 'left' },
      new THREE.Vector3(x0 + width + 0.45, fy, z + bw / 2 * 1.2 + 0.06), -16);
  }
  const pts = boxPoints(x0 - 0.4, 0, z - bw / 2, x0 + width + (ch.fair != null && !K.L.vert ? 3.4 : 0.4), height * 1.0, z + bw / 2 + 0.6);
  return {
    pts, maxV, bars,
    layoutLabels() {        // label wrap width = the bar spacing on screen
      const a = K.project([x0, 0, z]), b = K.project([x0 + gap, 0, z]);
      const gp = Math.abs(b[0] - a[0]);
      const vs = Math.round(clamp(gp * 0.36, 26, K.L.vert ? 48 : 46));    // value labels never collide
      bars.forEach((B) => { B.lab.el.style.maxWidth = Math.max(120, gp * 0.94) + 'px'; B.lab.el.style.whiteSpace = 'normal'; B.val.el.style.fontSize = vs + 'px'; });
    },
    update(t) {
      for (const B of bars) {
        const k = B.k(t), h = Math.max(0.001, B.H * k), e = B.k.emph(t);
        B.m.scale.y = h; B.m.position.y = h / 2; B.m.visible = k > 0.002;
        B.m.scale.x = B.m.scale.z = 1 + 0.18 * e;                       // emphasis on the word (Shorts)
        B.val.el.style.color = e > 0.05 || B.it.hl ? GN.mustard : GN.text;
        B.val.el.textContent = `${(B.it.value * Math.min(1, k * 1.02)).toFixed(dec)}${unit}`;
      }
      if (fairMesh) fairMesh.visible = clamp((t - (K.L.short ? -1 : Math.min(...bars.map((B) => B.it.at ?? 0.3)))) / 0.4) > 0.01;
    },
  };
}
function pillText(ch) {
  if (!ch || !ch.players) return ch && ch.pill;
  return `${ch.players} players` + (ch.fair != null ? ` · fair share ${ch.fair}${ch.unit ?? '%'}` : '');
}
T.bars = async (stage, spec) => {
  const K = new Kit(stage, spec), ch = spec.chart || K.p.chart;
  K.header({ pill: pillText(ch) });
  K.contentRect(70);                                   // room for value labels above / names below
  const vert = K.L.vert, n = ch.items.length;
  const r = K.content;
  const width = vert ? Math.min(8.4, 1.9 * n + 0.6) : Math.min(13.5, 2.6 * n + 1.5);
  const insT = K.L.short ? 64 : 50, insB = K.L.short ? 96 : vert ? 110 : 80;          // value labels above, names below
  const fr = { ...r, t: r.t + insT, b: r.b - insB, h: r.h - insT - insB };
  // Shorts: the chart takes the band's own aspect so it fills it (creator: "chart in the upper half, empty middle")
  const height = K.L.short ? clamp((width + 0.8) * fr.h / fr.w * 0.97, 3.6, 18)
                           : clamp(width * (r.h - 130) / r.w * (vert ? 1.0 : 1.25), 3.6, vert ? 11 : 6.4);
  const B = buildBars(K, ch, { x0: -width / 2, width, height });
  K.fit(B.pts, { rect: fr, elev: K.L.short ? 10 : 18, yaw: K.p.yaw ?? 6, push: 0.06 });
  B.layoutLabels();
  return K.frame((t) => { K.t = t; B.update(t); });
};

// ---------------------------------------------------------------- deck: card piles (rules) or a spread row (placement)
// piles: params.piles [{card, count, label}], params.highlights [[pileIndex, time]] (kit.py fills it from
//        params.name_words {word: pileIndex}); each named pile's card flies up big while it is said.
// row:   params.row {count, ends: [TOP, BOTTOM]}, params.hero (face), params.plan [[time, slot]] (hero moves between
//        slots, a gap opens), optional params.chart (bars) beside (16:9) or below (9:16).
T.deck = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p;
  K.header({ pill: p.chart ? pillText(p.chart) : p.pill });
  K.contentRect(40);
  return p.row ? deckRow(K, stage, spec) : deckPiles(K, stage, spec);
};
function deckPiles(K, stage, spec) {
  const p = K.p, piles = p.piles || [], vert = K.L.vert;
  const ncol = vert ? Math.min(3, piles.length) : Math.min(5, piles.length);
  const nrow = Math.ceil(piles.length / ncol);
  const SX = 2.9, SZ = 3.6;
  const items = piles.map((pl, gi) => {
    const row = Math.floor(gi / ncol), inRow = Math.min(ncol, piles.length - row * ncol), cIx = gi - row * ncol;
    const n = pl.count || 4, fanW = Math.min(n, 10) * 0.12;
    const gx = (cIx - (inRow - 1) / 2) * SX, gz = (row - (nrow - 1) / 2) * SZ - 0.4;
    const at = pl.at ?? (0.3 + gi * 0.3);
    const k = K.build(`pile ${gi}`, at, 0.5, gi);
    const cards = [];
    for (let j = 0; j < n; j++) {
      const c = kitCard(stage, Array.isArray(pl.card) ? pl.card[j % pl.card.length] : pl.card);
      c.position.set(gx - fanW / 2 + (j % 10) * 0.12, layerY(j, 0.016), gz + Math.floor(j / 10) * 0.45);
      c.visible = false; K.key(c); cards.push(c);
    }
    const lab = K.worldLabel({ text: pl.label ?? '', size: vert ? 30 : 28, role: 'label', at: at + 0.2, fade: 0.3, maxW: vert ? 300 : 340 },
      new THREE.Vector3(gx, 0, gz + CARD.H / 2 + 0.25 + Math.floor((n - 1) / 10) * 0.45), 4);
    return { cards, lab, k, gx, gz, face: Array.isArray(pl.card) ? pl.card[0] : pl.card };
  });
  const hx = (ncol - 1) / 2 * SX + 1.0, hz = (nrow - 1) / 2 * SZ + 1.6;
  K.fit(boxPoints(-hx, 0, -hz - 0.6, hx, 0.4, hz + 0.6), { elev: 66, yaw: 0, push: 0.05, fov: 24 });
  const hero = kitCard(stage, 'back'); hero.visible = false; hero.traverse((o) => { o.castShadow = false; }); K.key(hero);
  const HOLD = 1.5;
  const hl = (p.highlights || []).map(([g, t0]) => [g, t0]);
  hl.forEach(([g, t0], i) => { K.tw(`highlight ${g} up`, t0, 0.35); K.tw(`highlight ${g} down`, t0 + HOLD, 0.4); });
  return K.frame((t) => {
    let cur = null;
    for (const h of hl) if (t >= h[1] - 0.05 && t < h[1] + HOLD + 0.45) cur = h;
    items.forEach((it, gi) => {
      const k = it.k(t), active = cur && cur[0] === gi;
      it.cards.forEach((c, j) => { c.visible = k > 0; c.position.y = layerY(j, 0.016) + (1 - k) * 2; });
      const z = cur ? ease(clamp((t - cur[1]) / 0.25)) * (1 - ease(clamp((t - cur[1] - HOLD) / 0.4))) : 0;
      it.lab.o.alpha = (tt) => clamp((tt - it.lab.at) / 0.3) * (active ? 1 : 1 - z);
      it.lab.el.style.color = active ? GN.mustard : GN.text;
    });
    hero.visible = false;
    if (cur) {
      const it = items[cur[0]], u = t - cur[1];
      const k = ease(clamp(u / 0.35)) * (1 - ease(clamp((u - HOLD) / 0.4)));
      if (k > 0.001 && items[cur[0]]) {
        hero.visible = true; hero.setFace(it.face);
        const top = it.cards[it.cards.length - 1].position;
        const cam = stage.camera.position, look = K.rig.look;
        const target = look.clone().lerp(cam, 0.42);
        hero.position.lerpVectors(new THREE.Vector3(top.x, top.y + 0.05, top.z), target, k);
        hero.quaternion.identity(); const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), cam.clone().sub(target).normalize());
        hero.quaternion.slerp(q, k);
        hero.scale.setScalar(1 + 0.75 * k);
      }
    }
  });
}
function deckRow(K, stage, spec) {
  const p = K.p, vert = K.L.vert, R = p.row, n = R.count || 12;
  const SC = 1.45, RS = 0.6, DY = 2 * CARD_SEP * SC + 0.004;   // two layers per slot: the hero fits between two cards
  const rowW = (n + 1.8) * RS;
  let RX, RZ = 0, chart = null;
  if (p.chart) {
    if (vert) { RX = -rowW / 2; RZ = K.L.short ? -21 : -13; chart = buildBars(K, p.chart, { x0: -4.0, width: 8.0, height: K.L.short ? 10 : 6.5, z: 0.6 }); }
    else { RX = -rowW - 0.6; RZ = 0.2; chart = buildBars(K, p.chart, { x0: 1.0, width: 6.6, height: 5.2, z: 0.5 }); }
  } else RX = -rowW / 2;
  const rowY = (j) => 0.06 + (n - j) * DY;
  const row = [];
  for (let k = 0; k < n; k++) { const c = kitCard(stage, R.back || 'back'); c.scale.setScalar(SC); c.position.set(RX + k * RS, rowY(k), RZ); K.key(c); row.push(c); }
  const hero = kitCard(stage, p.hero ?? 0); hero.scale.setScalar(SC); K.key(hero);
  const ends = R.ends || ['TOP OF DECK', 'BOTTOM'];
  K.worldLabel({ text: ends[0], size: 26, role: 'label', color: GN.mustard, at: -1, align: 'left' }, new THREE.Vector3(RX - CARD.W * SC / 2, 0, RZ + CARD.H * SC / 2 + 0.2), 4);
  K.worldLabel({ text: ends[1], size: 26, role: 'label', color: GN.muted, at: -1, align: 'right' }, new THREE.Vector3(RX + (n + 0.8) * RS + CARD.W * SC / 2, 0, RZ + CARD.H * SC / 2 + 0.2), 4);
  const plan = (p.plan || [[0.6, Math.floor(n / 2)]]).map(([a, s]) => [typeof a === 'number' ? a : 0.6, s]);
  if (K.L.short) plan[0][0] = Math.min(plan[0][0], -0.6);    // Shorts: the hero card is already in its slot in frame 1
  const planDur = plan.map(([a, s], i) => K.tw(`hero to slot ${s}`, a, i === 0 ? 0.6 : 0.9).dur);
  const rowPts = boxPoints(RX - CARD.W * SC / 2, 0, RZ - CARD.H * SC / 2 - 0.4, RX + n * RS + CARD.W * SC / 2, 1.4, RZ + CARD.H * SC / 2 + 0.5);
  K.fit(chart ? [...rowPts, ...chart.pts] : rowPts, { elev: chart ? (vert ? 30 : 22) : 40, yaw: 4, push: 0.05,
    rect: chart ? { ...K.content, t: K.content.t + 50, h: K.content.h - 120, b: K.content.b - 70 } : K.content });
  if (chart) chart.layoutLabels();
  return K.frame((t) => {
    K.t = t;
    let slot = plan[0][1], prev = plan[0][1], ts = plan[0][0];
    let pd = 0.9; plan.forEach(([at, s], i) => { if (t >= at) { prev = slot; slot = s; ts = at; pd = planDur[i]; } });
    // like a hand would: pull the hero out of the row toward the viewer, move it (and change layer height) while clear
    // of the row, then push it back in at its new layer. Lifting/dropping through the row went through the cards
    // above it (probe clipping check).
    const u = clamp((t - ts) / pd), k = ease(u), sl = lerp(prev, slot, ease(clamp((u - 0.25) / 0.5)));
    const outZ = prev === slot ? 0 : CARD.H * SC * 1.08 * Math.min(1, ease(u / 0.25), ease((1 - u) / 0.25));
    row.forEach((c, j) => { const g = clamp(j - sl + 1); c.position.x = RX + j * RS + g * RS * 1.8; c.position.y = rowY(j); });
    const arrive = ease((t - plan[0][0] + 0.6) / 0.6);
    hero.visible = t >= plan[0][0] - 0.6;
    // deck order = stacking order: under the card before it, over the card after it (nothing under it at the bottom)
    // arrives the same way: sliding in level from the front, already at its layer height
    hero.position.set(RX + (sl + 0.4) * RS, rowY(sl) + DY * 0.5, RZ + Math.max(outZ, (1 - arrive) * CARD.H * SC * 1.3));
    if (chart) chart.update(t);
  });
}

// ---------------------------------------------------------------- fan: a hand of cards held by a seat
// params.cards [faces], params.highlights [{card, at, label?}] (that card lifts, its name pops),
// params.play [{card, at}] (card flies to the pile in the middle), params.seat_label
T.fan = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert;
  K.header({});
  K.contentRect(30);
  const faces = p.cards || [1, 3, 6, 8, 2], n = faces.length;
  const pawn = makePawn(stage, p.color || 'BLUE', 1.0); pawn.position.set(0, 0, 3.6); K.key(pawn);   // the seat, in front: cards above its head
  const cards = faces.map((f) => { const c = kitCard(stage, f); c.scale.setScalar(K.L.short ? 1.9 : 1.8); K.key(c); return c; });
  const pile = kitCard(stage, p.pile ?? 'back'); pile.position.set(0, 0.05, -0.4); pile.scale.setScalar(1.3); K.key(pile);
  const spread = vert ? (K.L.short ? 0.84 : 0.8) : 1.05;
  const handY = K.L.short ? 4.6 : 3.0;     // Shorts (tall frame): the hand held high above the seat
  const slot = (i) => { const off = i - (n - 1) / 2; const r = n > 1 ? off / ((n - 1) / 2) : 0;   // -1..1 across the hand: the arc depth is bounded whatever the hand size
    return [new THREE.Vector3(off * spread, handY - r * r * 0.3, 2.0), -r * 0.35]; };
  const hl = (p.highlights || []).filter((h) => typeof h.at === 'number');
  const plays = (p.play || []).filter((h) => typeof h.at === 'number');
  hl.forEach((h) => K.tw(`lift card ${h.card}`, h.at, 0.3));
  plays.forEach((h) => K.tw(`play card ${h.card}`, h.at, 0.9));
  const appear = K.tw('hand up', 0.05, 0.5);
  const pill = K.label({ text: '', size: 34, role: 'label', pill: GN.mustard, at: -1, alpha: () => 0, pos: () => [0, 0] });
  if (p.seat_label) K.worldLabel({ text: p.seat_label, size: 30, role: 'label', at: -1, color: GN.text }, new THREE.Vector3(0, 0, 4.3), 4);
  const w = (n - 1) / 2 * spread + 1.1;
  const rise = plays.length ? CARD.H * cards[0].scale.x * 1.2 : 0;     // played cards rise above the hand: keep them in frame
  K.fit(boxPoints(-Math.max(w, 1.8), 0, -1.4, Math.max(w, 1.8), handY + 1.4 + rise, 4.4), { elev: 20, yaw: 5, push: 0.06 });
  return K.frame((t) => {
    const up = appear(t), cam = stage.camera.position;
    // ONE plane for the whole hand (facing the camera from the hand's centre): with a per-card facing, neighbouring
    // planes weren't parallel and their edges crossed (probe clipping check)
    const hc = new THREE.Vector3(0, handY, 2.0), n0 = cam.clone().sub(hc).normalize();
    const q0 = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), n0), flat = new THREE.Quaternion();
    let cur = null; for (const h of hl) if (t >= h.at && t < h.at + 1.8) cur = h;
    cards.forEach((c, i) => {
      const [pos, rz] = slot(i);
      const pl = plays.find((h) => h.card === i);
      const lift = cur && cur.card === i ? ease(clamp((t - cur.at) / 0.3)) * (1 - ease(clamp((t - cur.at - 1.5) / 0.3))) : 0;
      c.quaternion.copy(q0); c.rotateY(rz);                 // tilt within the hand's plane (normals stay parallel)
      // one layer per card along the shared normal; a highlighted card lifts up and toward the camera (never into the others)
      const inPlane = pos.clone().addScaledVector(n0, -pos.clone().sub(hc).dot(n0));   // the arc lies IN the hand's plane
      // highlight = lift within the hand's plane (stays in its own layer: moving toward the camera went through cards)
      const upIn = new THREE.Vector3(0, 0, -1).applyQuaternion(q0);
      // appears by rising into place from just above the table (rising from 1.5 below went through the table)
      c.position.copy(inPlane).addScaledVector(upIn, lift * 0.7).add(new THREE.Vector3(0, (1 - up) * -(handY - 0.3 - CARD.H * c.scale.x * 0.62 - 0.1), 0))
        .addScaledVector(n0, i * CARD_SEP * c.scale.x);
      c.visible = up > 0.01;
      if (pl && t >= pl.at) {
        // rise clear above the hand (in its plane), then travel to the pile and land flat: going straight back
        // passed through the cards behind it, and an upright card landing went edge-first into the table
        // 3 phases: rise in the hand's plane until clear, travel back over the hand at that height, then descend
        // and flatten onto the pile (straight lines went through the hand, and an upright card landed edge-first)
        const u = clamp((t - pl.at) / 0.9), k1 = ease(clamp(u / 0.3)), k2 = ease(clamp((u - 0.3) / 0.3)), k3 = ease(clamp((u - 0.6) / 0.4));
        const landed = plays.filter((h) => h.at <= pl.at).length - 1;      // played cards stack in play order
        const top = c.position.clone().addScaledVector(upIn, k1 * CARD.H * c.scale.x * 1.15), hq = c.quaternion.clone();
        const pileTop = new THREE.Vector3(0, layerY(landed + 1, 0.05 + CARD.T * 1.3, c.scale.x), -0.4);
        const over = new THREE.Vector3(pileTop.x, top.y, pileTop.z);
        c.position.lerpVectors(top, over, k2).lerp(pileTop, k3);
        c.quaternion.slerpQuaternions(hq, flat, k3);
      }
    });
    if (cur) {
      const [x, y] = K.project(slot(cur.card)[0].clone().add(new THREE.Vector3(0, 1.6, 0)));
      pill.el.textContent = cur.label || ''; pill.o.alpha = (tt) => (cur.label ? clamp((tt - cur.at) / 0.15) * (1 - clamp((tt - cur.at - 1.6) / 0.15)) : 0);
      pill.o.pos = () => [x, y - 60];
    } else pill.o.alpha = () => 0;
  });
};

// ---------------------------------------------------------------- table: N seats with pawns, hands, deck + pile
// params.players, names [..], colors [..], hands (cards per seat), highlight [[seat, at], ..] (pawn hops, name lights up),
// turns [{at, seat, ev: draw|play, card, label}] or turns_auto {from, every} (plays round the table), out [[seat, at]]
T.table = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert;
  const n = p.players || (p.names || []).length || 4;
  K.header({ pill: p.pill ?? `${n} players` });
  K.contentRect(40);
  const COLS = ['BLUE', 'CREAM', 'CORAL', 'MUSTARD', 'GREEN', 'PLUM'];
  const rx = vert ? 3.9 : 7.2, rz = vert ? (K.L.short ? 6.6 : 5.6) : 3.5;
  const deck = []; for (let k = 0; k < 24; k++) { const c = kitCard(stage, p.back || 'back'); c.position.set(-0.9, layerY(k, 0.03), 0); K.key(c, 'decor'); deck.push(c); }
  const pile = []; const mover = kitCard(stage, 'back'); mover.visible = false; mover.traverse((o) => { o.castShadow = false; }); K.key(mover);
  const seats = [];
  for (let i = 0; i < n; i++) {
    const a = Math.PI / 2 + i / n * Math.PI * 2;        // seat 0 nearest the camera
    const sx = Math.cos(a) * rx, sz = Math.sin(a) * rz;
    const dir = Math.atan2(-sx, -sz);
    const pawn = makePawn(stage, (p.colors || [])[i] || COLS[i % COLS.length]);
    pawn.position.set(sx * 1.18, 0.02, sz * 1.18); K.key(pawn);
    const hand = [];
    const cnt = Array.isArray(p.hands) ? p.hands[i] : (p.hands ?? 5);
    for (let k = 0; k < cnt; k++) {
      const c = kitCard(stage, p.back || 'back'); const off = (k - (cnt - 1) / 2) * 0.42;
      c.position.set(sx * 0.82 + Math.cos(dir) * off, layerY(k, 0.02), sz * 0.82 - Math.sin(dir) * off);
      c.rotation.set(0, dir + Math.PI, 0); K.key(c, 'decor'); hand.push(c);
    }
    const front = sz > 1;
    const name = (p.names || [])[i] || `PLAYER ${i + 1}`;
    const lab = K.worldLabel({ text: name, size: vert ? 30 : 26, role: 'label', at: -1, color: GN.muted, maxW: vert ? 320 : 360 },
      new THREE.Vector3(pawn.position.x, front ? 0 : 2.0, pawn.position.z + (front ? 0.9 : 0)), front ? 4 : -34);
    seats.push({ i, sx, sz, pawn, hand, lab, home: pawn.position.clone() });
  }
  const hl = (p.highlight || p.seat_hl || []).filter((h) => typeof h[1] === 'number');
  const hlK = hl.map(([s, at]) => K.tw(`seat ${s} hop`, at, 2.3));
  let turns = (p.turns || []).filter((e) => typeof e.at === 'number');
  if (p.turns_auto) {
    const A = p.turns_auto, every = A.every || 1.2, faces = A.cards || [2, 3, 6, 7, 1, 4];
    for (let t0 = A.from ?? 0.4, k = 0; t0 < stage.duration - 1.2; t0 += every, k++) turns.push({ at: t0, seat: k % n, ev: k % 3 === 2 ? 'draw' : 'play', card: faces[k % faces.length] });
  }
  turns.sort((a, b) => a.at - b.at);
  turns.forEach((e) => { e.dur = K.tw(`${e.ev} by seat ${e.seat}`, e.at, 0.75).dur; });   // lands before the cut
  const outs = (p.out || []).filter((h) => typeof h[1] === 'number');
  const pill = K.label({ text: '', size: 30, role: 'label', pill: GN.mustard, at: -1, alpha: () => 0, pos: () => [0, 0] });
  const ex = rx * 1.18 + 0.8, ez = rz * 1.18 + 0.9;
  K.fit(boxPoints(-ex, 0, -ez, ex, 2.0, ez), { elev: vert ? 58 : 50, yaw: 5, push: 0.06 });
  return K.frame((t) => {
    seats.forEach((s) => {
      let on = false, hop = 0;
      hl.forEach(([si, t0], q) => { if (si === s.i && t >= t0 && t < t0 + hlK[q].dur) { on = true; hop = Math.abs(Math.sin((t - t0) * 7)) * 0.3 * (1 - hlK[q](t)); } });
      s.lab.el.style.color = on ? GN.mustard : GN.muted;
      s.pawn.position.copy(s.home);
      const o = outs.find(([si]) => si === s.i);
      const ko = o ? ease(clamp((t - o[1]) / 0.5)) : 0;
      s.pawn.rotation.z = ko * Math.PI / 2.2; s.pawn.position.y += ko * 0.3;
      s.pawn.position.y += hop;
    });
    // turns
    let e = null; for (const x of turns) if (t >= x.at && t < x.at + x.dur + 0.25) e = x;
    mover.visible = false;
    const played = turns.filter((x) => x.ev === 'play' && t >= x.at + x.dur);
    while (pile.length < played.length) { const c = kitCard(stage, 'back'); c.traverse((o) => { o.castShadow = false; }); K.key(c, 'decor'); pile.push(c); }
    pile.forEach((c, i) => { c.setFace(played[i].card); c.position.set(1.0 + (i % 2) * 0.05, layerY(i, 0.03), 0.02 * (i % 3)); c.visible = true; });
    deck.forEach((c, i) => { c.visible = i < 24 - turns.filter((x) => x.ev === 'draw' && t >= x.at).length; });
    if (e) {
      const s = seats[e.seat % n], k = ease(clamp((t - e.at) / e.dur));
      // the mover lands one layer above the pile's current top (never inside it)
      const seatP = new THREE.Vector3(s.sx * 0.82, layerY(14, 0.02), s.sz * 0.82), deckP = new THREE.Vector3(-0.9, layerY(24, 0.03), 0), pileP = new THREE.Vector3(1.0, layerY(played.length, 0.03), 0);
      if (k < 1) {
        mover.visible = true; mover.setFace(e.ev === 'draw' ? (p.back || 'back') : e.card);
        if (e.ev === 'draw') mover.position.lerpVectors(deckP, seatP, k); else mover.position.lerpVectors(seatP, pileP, k);
        mover.position.y += Math.sin(k * Math.PI) * 1.3; mover.rotation.set(0, 0, 0);
      }
      const front = s.sz > 1;     // front seats: name below the pawn, pill above it; back seats: pill above the name
      const [px, py0] = K.project(new THREE.Vector3(s.pawn.position.x, front ? 2.6 : 2.0, s.pawn.position.z));
      const py = front ? py0 : py0 - 34 - s.lab.el.offsetHeight - 12;
      pill.el.textContent = e.label || '';
      const holdToCut = e.at + e.dur + 0.3 > stage.duration;     // a late event keeps its pill through the cut
      pill.o.alpha = (tt) => (e.label ? clamp((tt - e.at) / 0.1) * (holdToCut ? 1 : 1 - clamp((tt - e.at - e.dur - 0.1) / 0.12)) : 0);
      pill.o.pos = () => [px, py - 50];
    } else pill.o.alpha = () => 0;
  });
};

// ---------------------------------------------------------------- lineup: meet the players (pawns + habits panel)
// params.bots [{name, color, at, habits: [{text, at}]}]
T.lineup = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert, bots = p.bots || [];
  K.header({});
  const c = K.contentRect(20);
  // panel: above the pawns on 16:9, below them on 9:16
  const panelH = vert ? 520 : 250;
  const panelRect = vert ? { t: c.b - panelH, b: c.b } : { t: c.t, b: c.t + panelH };
  const pawnRect = vert ? { ...c, b: c.b - panelH - 30, h: c.h - panelH - 30 } : { ...c, t: c.t + panelH + 30, h: c.h - panelH - 30 };
  const panel = document.createElement('div');
  Object.assign(panel.style, { position: 'absolute', left: K.L.safe.l + 'px', top: panelRect.t + 'px', width: K.L.sw + 'px',
    maxHeight: panelH + 'px', padding: '22px 36px', borderRadius: '26px', background: 'rgba(20,32,28,0.78)', fontFamily: FONT,
    color: GN.text, opacity: 0, boxSizing: 'border-box', overflow: 'hidden' });
  stage.ov.appendChild(panel);
  const head = document.createElement('div'); Object.assign(head.style, { fontSize: (vert ? 50 : 44) + 'px', fontWeight: 900, marginBottom: '8px' });
  head.dataset.qa = 'panel-head';
  const list = document.createElement('div'); Object.assign(list.style, { fontSize: (vert ? 38 : 32) + 'px', fontWeight: 700, lineHeight: 1.3 });
  panel.appendChild(head); panel.appendChild(list);
  const rows = []; for (let k = 0; k < 4; k++) { const r = document.createElement('div'); r.dataset.qa = 'habit'; list.appendChild(r); rows.push(r); }
  const n = bots.length, perRow = vert && n > 3 ? Math.ceil(n / 2) : n, gap = 2.6;
  const pawns = bots.map((b, i) => {
    const r = Math.floor(i / perRow), inRow = Math.min(perRow, n - r * perRow), ci = i - r * perRow;
    const x = (ci - (inRow - 1) / 2) * gap, z = r * 3.2 - (Math.ceil(n / perRow) - 1) * 1.6;
    const g = makePawn(stage, b.color || 'CREAM', 1.1); g.position.set(x, 0, z); K.key(g);
    const appear = K.L.short ? K.tw(`pawn ${b.name}`, -0.45 + i * 0.04, 0.6) : K.tw(`pawn ${b.name}`, 0.2 + i * 0.18, 0.5);
    if (typeof b.at === 'number') K.tw(`focus ${b.name}`, b.at, 0.35);
    (b.habits || []).forEach((h) => typeof h.at === 'number' && K.tw(`habit ${h.text}`, h.at, 0.2));
    const lab = K.worldLabel({ text: b.name, size: vert ? 30 : 28, role: 'label', at: 0.4 + i * 0.18, maxW: vert ? 280 : 300 }, new THREE.Vector3(x, 0, z + 0.9), 4);
    return { b, g, x, z, appear, lab, col: col(b.color, GN.text) };
  });
  const hx = (perRow - 1) / 2 * gap + 1.2, z0 = Math.min(...pawns.map((q) => q.z)) - 1, z1 = Math.max(...pawns.map((q) => q.z)) + 2.4;
  K.fit(boxPoints(-hx, 0, z0, hx, 2.4, z1), { rect: pawnRect, elev: 24, yaw: 5, push: 0.05 });
  return K.frame((t) => {
    let cur = -1; pawns.forEach((q, i) => { if (typeof q.b.at === 'number' && t >= q.b.at) cur = i; });
    pawns.forEach((q, i) => {
      const k = q.appear(t), focus = i === cur ? ease(clamp((t - q.b.at) / 0.35)) : 0, dim = cur >= 0 && i !== cur;
      q.g.visible = k > 0.001;
      q.g.position.set(q.x, (1 - k) * 1.5 + focus * 0.3, q.z + focus * 0.8);
      q.g.scale.setScalar(0.001 + k * (1 + focus * 0.2 - (dim ? 0.1 : 0)));
      q.lab.el.style.color = i === cur ? q.col : GN.text;
      q.lab.o.alpha = (tt) => clamp((tt - q.lab.at) / 0.3) * (dim ? 0.55 : 1);
    });
    if (cur >= 0) {
      const b = pawns[cur].b;
      panel.style.opacity = clamp((t - b.at) / 0.25);
      head.textContent = b.name; head.style.color = pawns[cur].col;
      rows.forEach((r, k) => {
        const h = (b.habits || [])[k];
        if (!h) { r.textContent = ''; r.style.opacity = 0; return; }
        r.textContent = '• ' + h.text; const a = clamp((t - h.at) / 0.2);
        r.style.opacity = a; r.style.transform = `translateX(${(1 - a) * 18}px)`;
      });
    } else panel.style.opacity = 0;
  });
};

// ---------------------------------------------------------------- grid board: checkers (floor) / connect-4 (upright)
// params.rows, cols, style: checkers|connect4, pieces [[r, c, color, king?]], moves:
//   checkers [{at, from: [r,c], to: [r,c], capture: [[r,c]], king}]   connect4 [{at, col, color}]
// highlight [{at, until, cells: [[r,c]], color}], colors {a, b} for the two sides
T.grid = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert;
  K.header({ pill: p.pill });
  K.contentRect(30);
  const R = p.rows || 8, C = p.cols || 8, c4 = p.style === 'connect4';
  const PC = { RED: '#d6403a', BLACK: '#2b2f38', YELLOW: '#f2c230', WHITE: '#f4ead5' };
  const pcol = (c) => PC[c] || col(c, GN.coral);
  const cell = (r, c) => c4 ? new THREE.Vector3(c - (C - 1) / 2, (R - 1 - r) + 0.7, 0.32) : new THREE.Vector3(c - (C - 1) / 2, 0.36, r - (R - 1) / 2);
  const board = new THREE.Group(); stage.scene.add(board);
  if (c4) {
    const frame = new THREE.Mesh(new RoundedBoxGeometry(C + 0.6, R + 0.6, 0.5, 4, 0.12), new THREE.MeshStandardMaterial({ color: '#2f6fd6', roughness: 0.5 }));
    frame.position.set(0, R / 2 + 0.2, 0); frame.castShadow = true; board.add(frame);
    const hole = new THREE.MeshStandardMaterial({ color: '#1a2d4a', roughness: 0.9 });
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) { const h = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.02, 32), hole); h.rotation.x = Math.PI / 2; h.position.copy(cell(r, c)).setZ(0.26); board.add(h); }
  } else {
    const base = new THREE.Mesh(new RoundedBoxGeometry(C + 0.8, 0.3, R + 0.8, 4, 0.1), new THREE.MeshStandardMaterial({ color: '#5b3a24', roughness: 0.6 }));
    base.position.y = 0.15; base.receiveShadow = true; board.add(base);
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
      const sq = new THREE.Mesh(new THREE.BoxGeometry(1, 0.02, 1), new THREE.MeshStandardMaterial({ color: (r + c) % 2 ? '#3d5a4c' : '#efe7d8', roughness: 0.8 }));
      sq.position.copy(cell(r, c)).setY(0.31); sq.receiveShadow = true; board.add(sq);
    }
  }
  K.key(board); board.userData.noclip = true;     // a frame with holes: its own pieces sit inside it by design
  const hlMeshes = [];
  for (const h of (p.highlight || [])) {
    if (typeof h.at !== 'number') continue;
    const k = K.tw('highlight cells', h.at, 0.3);
    for (const [r, c] of h.cells || []) {
      const m = new THREE.Mesh(c4 ? new THREE.TorusGeometry(0.46, 0.06, 12, 32) : new THREE.BoxGeometry(0.96, 0.03, 0.96),
        new THREE.MeshStandardMaterial({ color: col(h.color, GN.mustard), emissive: col(h.color, GN.mustard), emissiveIntensity: 0.6, transparent: true, opacity: 0 }));
      m.position.copy(cell(r, c)); if (c4) m.position.z = 0.6; else m.position.y = 0.335;
      stage.scene.add(m); hlMeshes.push({ m, k, until: h.until ?? 1e9 });
    }
  }
  // pieces
  const geo = new THREE.CylinderGeometry(0.4, 0.4, c4 ? 0.22 : 0.16, 40);
  const pieces = [];
  const mkPiece = (r, c, color, king) => {
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: pcol(color), roughness: 0.35 }));
    if (c4) m.rotation.x = Math.PI / 2;
    m.castShadow = true; stage.scene.add(m); K.key(m);
    const crown = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.05, 10, 24), new THREE.MeshStandardMaterial({ color: GN.mustard, emissive: GN.mustard, emissiveIntensity: 0.3 }));
    crown.rotation.x = Math.PI / 2; crown.visible = !!king; m.add(crown); crown.position.y = 0.1;
    const P = { m, r, c, color, crown, path: [] };
    pieces.push(P); return P;
  };
  for (const [r, c, color, king] of (p.pieces || [])) mkPiece(r, c, color, king);
  const moves = (p.moves || []).filter((m) => typeof m.at === 'number').sort((a, b) => a.at - b.at);
  // replay the moves once at build time into per-piece keyframes
  const occ = (r, c) => pieces.find((q) => q.r === r && q.c === c && !q.gone);
  for (const mv of moves) {
    K.tw(c4 ? `drop col ${mv.col}` : `move ${mv.from}`, mv.at, 0.7);
    if (c4) {
      let r = R - 1; while (r >= 0 && pieces.some((q) => q.r === r && q.c === mv.col)) r--;
      const P = mkPiece(-9, mv.col, mv.color || 'RED'); P.r = r; P.drop = { at: mv.at, r };
    } else {
      const P = occ(mv.from[0], mv.from[1]); if (!P) continue;
      P.path.push({ at: mv.at, from: [P.r, P.c], to: mv.to, hop: !!(mv.capture || []).length, king: mv.king });
      for (const [cr, cc] of mv.capture || []) { const Q = occ(cr, cc); if (Q) { Q.gone = mv.at + 0.45; } }
      P.r = mv.to[0]; P.c = mv.to[1];
    }
  }
  pieces.forEach((P) => { if (!c4) { const f = P.path[0]; if (f) { P.r0 = f.from; } else P.r0 = [P.r, P.c]; } });
  const ext = c4 ? boxPoints(-C / 2 - 0.4, 0, -0.3, C / 2 + 0.4, R + 1.6, 0.6) : boxPoints(-C / 2 - 0.5, 0, -R / 2 - 0.5, C / 2 + 0.5, 0.6, R / 2 + 0.5);
  K.fit(ext, c4 ? { elev: 12, yaw: 6, push: 0.05 } : { elev: vert ? 62 : 55, yaw: 5, push: 0.05 });
  return K.frame((t) => {
    for (const h of hlMeshes) { const a = h.k(t) * (1 - clamp((t - h.until) / 0.3)); h.m.material.opacity = a * 0.85; h.m.visible = a > 0.01; }
    for (const P of pieces) {
      if (c4) {
        if (!P.drop) { P.m.position.copy(cell(P.r, P.c)); continue; }
        const k = clamp((t - P.drop.at) / 0.55);
        P.m.visible = t >= P.drop.at;
        const top = cell(-1.2, P.c), dst = cell(P.drop.r, P.c);
        const kk = k * k;                       // falls (gravity), tiny bounce at the end
        P.m.position.lerpVectors(top, dst, kk); if (k >= 1) P.m.position.y = dst.y + Math.max(0, Math.sin(clamp((t - P.drop.at - 0.55) / 0.15) * Math.PI)) * 0.12;
        continue;
      }
      let [r, c] = P.r0, y = 0.44, king = false;
      for (const s of P.path) {
        if (t < s.at) break;
        const k = ease(clamp((t - s.at) / 0.7));
        r = lerp(s.from[0], s.to[0], k); c = lerp(s.from[1], s.to[1], k);
        y = 0.44 + Math.sin(k * Math.PI) * (s.hop ? 1.0 : 0.35);
        if (s.king && k >= 1) king = true;
      }
      const pos = cell(r, c); P.m.position.set(pos.x, y, pos.z);
      P.crown.visible = king || P.crown.visible && !P.path.length;
      if (P.gone) { const g = clamp((t - P.gone) / 0.35); P.m.visible = g < 1; P.m.position.y += g * 1.2; P.m.material.transparent = true; P.m.material.opacity = 1 - g; }
    }
  });
};

// ---------------------------------------------------------------- track board: Sorry!/Ludo-style loop
// params.length (squares), players (colours per side), start_square [per player], home_len, slides [{from, len, player}],
// pawns [{id, player, on: 'start' | square | 'home:k'}], moves [{at, pawn, to: square | 'start' | 'home:k', steps?}],
// highlight [{at, until, squares: [..], color}]
T.track = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p;
  K.header({ pill: p.pill });
  K.contentRect(30);
  const N = p.length || 60, side = N / 4, S = 0.9, half = side * S / 2;
  const COLS = p.colors || ['RED', 'BLUE', 'MUSTARD', 'GREEN'];
  const PC = { RED: '#d6403a', BLUE: '#3f7fe0', YELLOW: '#f2c230', GREEN: '#3fae6a' };
  const pc = (i) => PC[COLS[i]] || col(COLS[i]);
  const sq = (i) => {                                   // square i around the loop, clockwise from the top-left
    i = ((i % N) + N) % N; const s = Math.floor(i / side), f = (i % side) * S;
    return [[-half + f, -half], [half, -half + f], [half - f, half], [-half, half - f]][s].map((v, k) => v + (k === 0 ? S / 2 : S / 2) * 0);
  };
  const pos = (i) => { const [x, z] = sq(i); return new THREE.Vector3(x, 0.36, z); };
  const base = new THREE.Mesh(new RoundedBoxGeometry(side * S + 1.4, 0.3, side * S + 1.4, 4, 0.12), new THREE.MeshStandardMaterial({ color: '#24413b', roughness: 0.8 }));
  base.position.y = 0.15; base.receiveShadow = true; stage.scene.add(base); K.key(base);
  const sqGeo = new THREE.BoxGeometry(S * 0.92, 0.04, S * 0.92);
  for (let i = 0; i < N; i++) { const m = new THREE.Mesh(sqGeo, new THREE.MeshStandardMaterial({ color: '#f4ead5', roughness: 0.7 })); m.position.copy(pos(i)).setY(0.32); m.receiveShadow = true; stage.scene.add(m); }
  for (const sl of (p.slides || [])) for (let k = 0; k < sl.len; k++) { const m = new THREE.Mesh(new THREE.BoxGeometry(S * 0.5, 0.05, S * 0.5), new THREE.MeshStandardMaterial({ color: pc(sl.player || 0) })); m.position.copy(pos(sl.from + k)).setY(0.35); stage.scene.add(m); }
  const starts = p.start_square || [4, 4 + side, 4 + 2 * side, 4 + 3 * side];
  const HL = p.home_len ?? 5;
  const inward = (pl) => [[0, 1], [-1, 0], [0, -1], [1, 0]][Math.floor((((starts[pl] - 2) % N) + N) % N / side)];
  const entry = (pl) => (starts[pl] - 2 + N) % N;
  const homeSq = (pl, k) => { const e = pos(entry(pl)), d = inward(pl); return new THREE.Vector3(e.x + d[0] * S * (k + 1), 0.36, e.z + d[1] * S * (k + 1)); };
  const startZone = (pl, j) => { const e = pos(starts[pl]), d = inward(pl); const sideV = [d[1], -d[0]]; return new THREE.Vector3(e.x + d[0] * S * 1.6 + sideV[0] * (j - 1.5) * 0.55, 0.42, e.z + d[1] * S * 1.6 + sideV[1] * (j - 1.5) * 0.55); };
  for (let pl = 0; pl < COLS.length; pl++) {
    for (let k = 0; k < HL; k++) { const m = new THREE.Mesh(sqGeo, new THREE.MeshStandardMaterial({ color: pc(pl), roughness: 0.6 })); m.position.copy(homeSq(pl, k)).setY(0.32); stage.scene.add(m); }
    const z = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 0.04, 40), new THREE.MeshStandardMaterial({ color: pc(pl), roughness: 0.6, transparent: true, opacity: 0.45 }));
    z.position.copy(startZone(pl, 1.5)).setY(0.33); stage.scene.add(z);
  }
  const where = (pl, at, j) => (at === 'start' || at == null ? startZone(pl, j) : typeof at === 'string' && at.startsWith('home:') ? homeSq(pl, +at.slice(5)) : pos(+at));
  const pawns = {}; const cnt = {};
  for (const pw of (p.pawns || [])) {
    const j = cnt[pw.player] = (cnt[pw.player] ?? -1) + 1;
    const g = makePawn(stage, pc(pw.player), 0.62); K.key(g);
    pawns[pw.id] = { g, pl: pw.player, j, keys: [{ t: -1, path: [where(pw.player, pw.on, j)] }], cur: pw.on };
  }
  for (const mv of (p.moves || []).filter((m) => typeof m.at === 'number').sort((a, b) => a.at - b.at)) {
    const P = pawns[mv.pawn]; if (!P) continue;
    const path = [];
    if (typeof P.cur === 'number' && typeof mv.to === 'number') {   // step square by square
      const fwd = ((mv.to - P.cur) % N + N) % N, back = mv.back || mv.steps < 0;
      const n = back ? -(((P.cur - mv.to) % N + N) % N) : fwd;
      for (let k = 0; k <= Math.abs(n); k++) path.push(pos(P.cur + Math.sign(n) * k));
    } else { path.push(where(P.pl, P.cur, P.j)); path.push(where(P.pl, mv.to, P.j)); }
    P.keys.push({ t: mv.at, path, bump: mv.to === 'start' });
    K.tw(`move ${mv.pawn}`, mv.at, Math.min(2.2, 0.18 * path.length + 0.2));
    P.cur = mv.to;
  }
  const hls = (p.highlight || []).filter((h) => typeof h.at === 'number').map((h) => {
    const k = K.tw('highlight squares', h.at, 0.3);
    const ms = (h.squares || []).map((i) => { const m = new THREE.Mesh(new THREE.BoxGeometry(S * 0.98, 0.06, S * 0.98), new THREE.MeshStandardMaterial({ color: col(h.color, GN.mustard), emissive: col(h.color, GN.mustard), emissiveIntensity: 0.6, transparent: true, opacity: 0 })); m.position.copy(pos(i)).setY(0.34); stage.scene.add(m); return m; });
    return { k, ms, until: h.until ?? 1e9 };
  });
  const e = half + 1.0;
  K.fit(boxPoints(-e, 0, -e, e, 1.0, e), { elev: 64, yaw: 5, push: 0.05 });
  return K.frame((t) => {
    for (const h of hls) { const a = h.k(t) * (1 - clamp((t - h.until) / 0.3)); h.ms.forEach((m) => { m.material.opacity = a * 0.8; m.visible = a > 0.01; }); }
    for (const P of Object.values(pawns)) {
      let key = P.keys[0]; for (const k of P.keys) if (t >= k.t) key = k;
      const path = key.path, dur = Math.min(2.2, 0.18 * path.length + 0.2);
      const u = key.t < 0 ? 1 : clamp((t - key.t) / dur) * (path.length - 1);
      const i = Math.min(path.length - 2, Math.floor(u)), f = u - Math.max(0, i);
      if (path.length < 2) { P.g.position.copy(path[0]).setY(0.36); continue; }
      const a = path[Math.max(0, i)], b = path[Math.max(0, i) + 1];
      P.g.position.lerpVectors(a, b, ease(f)); P.g.position.y = 0.36 + Math.sin(f * Math.PI) * (key.bump ? 1.2 : 0.35) * (u < path.length - 1 ? 1 : 0);
    }
  });
};

// ---------------------------------------------------------------- odds: a probability grid (cards or dots)
// params.frames [{at, total, hits, head, sub}], params.item: card|dot, hit_face (card face of a hit)
T.odds = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert, frames = p.frames || [];
  K.header({});
  const head = K.headRow({ text: '', size: vert ? 58 : 60, role: 'odds-head', at: frames[0] ? frames[0].at : 0.2, fade: 0.25 });
  const sub = K.headRow({ text: '', size: vert ? 38 : 36, role: 'odds-sub', color: GN.mustard, at: frames[0] ? frames[0].at + 0.25 : 0.4, fade: 0.25 });
  K.contentRect(30);
  frames.forEach((f, i) => K.tw(`odds frame ${i}`, f.at, i ? 0.8 : 0.6));
  const MAX = Math.max(...frames.map((f) => f.total), 1), colsN = vert ? 6 : 12;
  const dots = p.item === 'dot';
  const SX = dots ? 1.0 : 1.02, SZ = dots ? 1.0 : 1.38;
  const slot = (i, n) => { const cols = Math.min(colsN, n), rows = Math.ceil(n / cols), r = Math.floor(i / cols), inRow = r < rows - 1 ? cols : n - r * cols;
    return [(i % cols - (inRow - 1) / 2) * SX, 0.03, (r - (rows - 1) / 2) * SZ]; };
  const hitIdx = (n, k) => { const out = new Set(); for (let a = 0; a < k; a++) out.add(Math.min(n - 1, Math.floor((a + 0.5) * n / k))); return out; };
  const items = [];
  for (let i = 0; i < MAX; i++) {
    let m;
    if (dots) { m = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.14, 32), new THREE.MeshStandardMaterial({ color: GN.cream, roughness: 0.4 })); m.castShadow = true; stage.scene.add(m); }
    else m = kitCard(stage, 'back');
    K.key(m); items.push(m);
  }
  const rowsMax = Math.ceil(MAX / Math.min(colsN, MAX)), hx = Math.min(colsN, MAX) / 2 * SX + 0.6, hz = rowsMax / 2 * SZ + 0.6;
  const discard = frames.some((f, i) => i && f.total < frames[i - 1].total);
  K.fit(boxPoints(-hx, 0, -hz, hx + (discard ? 1.8 : 0), 0.3, hz), { elev: 76, yaw: 0, push: 0.05, fov: 22 });
  return K.frame((t) => {
    if (!frames.length) return;
    let fi = 0; frames.forEach((f, i) => { if (t >= f.at) fi = i; });
    const f = frames[fi], prev = frames[Math.max(0, fi - 1)];
    const k = fi === 0 ? 1 : ease(clamp((t - f.at) / 0.8));
    const hits = hitIdx(f.total, f.hits), appear = K.L.short ? ease(clamp((t + 0.3) / 0.4)) : ease(clamp((t - (frames[0].at - 0.6)) / 0.6));
    items.forEach((c, i) => {
      const inNow = i < f.total, inPrev = i < prev.total;
      const [px, , pz] = slot(Math.min(i, prev.total - 1), prev.total), [nx, y, nz] = slot(Math.min(i, f.total - 1), f.total);
      c.visible = (fi === 0 ? inNow : inNow || (inPrev && k < 1)) && appear > 0.01;
      if (!c.visible) return;
      if (!inNow && inPrev) c.position.set(lerp(px, hx + 1.0, k), layerY(i - f.total, y) + Math.sin(k * Math.PI) * 1.2, lerp(pz, 0, k));   // to a discard pile in frame, one layer each (from the start)
      else c.position.set(inNow ? lerp(px, nx, k) : px, y + (1 - appear) * 1.5, inNow ? lerp(pz, nz, k) : pz);
      const hit = hits.has(i) && inNow;
      if (dots) c.material.color.set(hit ? GN.coral : GN.cream); else c.setFace(hit ? (p.hit_face ?? 0) : 'back');
    });
    head.el.textContent = f.head || `${f.hits} in ${f.total}`; sub.el.textContent = f.sub || '';
  });
};

// ---------------------------------------------------------------- checklist / recipe
// params.items [{text, at, verdict?, color?}], params.cards (decor faces, kept fully in frame)
T.checklist = async (stage, spec) => {
  const K = new Kit(stage, spec), p = K.p, vert = K.L.vert, items = p.items || [];
  K.header({});
  const c = K.contentRect(20);
  const [listR, decoR] = vert ? K.split(0.72) : K.split(0.7);
  const size = p.size || (vert ? 44 : 42);
  const step = Math.min(p.step || (vert ? 150 : 110), listR.h / Math.max(1, items.length));
  items.forEach((it, k) => {
    const y = listR.t + k * step;
    K.label({ text: '✓', size: size * 1.2, role: 'check', color: GN.mustard, at: it.at, align: 'left', x: listR.l + 10, y: y - 4, anchor: it.at_ref });
    K.label({ text: it.text, size, weight: 700, role: 'item', at: it.at, align: 'left', x: listR.l + size * 1.4, y, maxW: listR.w - size * 1.4 - (it.verdict ? 260 : 0), anchor: it.at_ref });
    if (it.verdict) K.label({ text: it.verdict, size: size * 0.75, role: 'verdict', at: it.at, align: 'right', x: listR.r, y, pill: col(it.color, GN.mustard) });
    K.tw(`item ${k + 1}`, it.at ?? 0.2, 0.25);
  });
  const faces = p.cards || [0, 1, 3, 6, 7, 8];
  const deco = faces.map((f, k) => { const m = kitCard(stage, f); m.position.set(k * 0.55, layerY(k, 0.03), -k * 0.1); K.key(m, 'decor'); return m; });
  const w = faces.length * 0.55;
  K.fit(boxPoints(-0.7, 0, -CARD.H / 2 - 0.7, w + 0.2, 0.3, CARD.H / 2 + 0.2), { rect: decoR, elev: 55, yaw: 5, push: 0.06 });
  // the list sits on a darker band so it reads over the floor
  return K.frame(() => { const g = stage.g; g.fillStyle = `rgba(${GN.scrim},0.45)`; g.fillRect(0, 0, stage.W, stage.H); });
};

// ---------------------------------------------------------------- end card: next video + subscribe + Buh (happy)
// params.next_title; leaves room for YouTube's end-screen elements (video left, subscribe right on 16:9)
T.endcard = async (stage, spec) => {
  spec.fade_out = spec.fade_out ?? 1.0;            // the only scene that fades
  const K = new Kit(stage, spec), p = K.p, L = K.L, S = L.safe;
  const buh = makeBuh(stage); K.key(buh);
  let vid, sub, buhRect;
  if (L.vert) {
    buhRect = { l: S.l, r: S.r, t: S.t + 120, b: S.t + 720 }; vid = { x: L.cx - 420, y: 900, w: 840, h: 472 }; sub = { x: L.cx, y: 1580, r: 130 };
  } else {
    vid = { x: 230, y: 330, w: 800, h: 450 }; sub = { x: 1340, y: 555, r: 150 }; buhRect = { l: 1520, r: S.r, t: 330, b: 820 };
  }
  buhRect.w = buhRect.r - buhRect.l; buhRect.h = buhRect.b - buhRect.t;
  K.label({ text: 'NEXT', size: 40, role: 'label', color: GN.mustard, at: 0.3, align: 'left', x: vid.x, y: vid.y - 64 });
  K.label({ text: p.next_title || '', size: 52, role: 'title', at: 0.5, x: vid.x + vid.w / 2, y: vid.y + vid.h / 2 - 30, maxW: vid.w - 60 });
  K.label({ text: 'subscribe', size: 40, weight: 700, role: 'label', color: GN.muted, at: 0.5, x: sub.x, y: sub.y - 22 });
  K.fit(boxPoints(-1.2, 0, -1.0, 1.2, 2.7, 1.0), { rect: buhRect, elev: 8, yaw: 8, push: 0.05, look: [0, 1.25, 0] });
  const wave = K.tw('buh hop', 0.4, 0.6);
  return K.frame((t) => {
    buh.position.y = Math.sin(wave(t) * Math.PI) * 0.4;
    buh.rotation.y = Math.sin(t * 0.8) * 0.25; K.key(buh, t > 1.2 ? 'idle' : 'key');
    const g = stage.g, al = clamp((t - 0.3) / 0.6);
    g.fillStyle = `rgba(${GN.scrim},0.35)`; g.fillRect(0, 0, stage.W, stage.H);
    g.save(); g.globalAlpha = al; g.fillStyle = 'rgba(34,48,74,0.9)'; g.beginPath(); g.roundRect(vid.x, vid.y, vid.w, vid.h, 22); g.fill();
    g.beginPath(); g.arc(sub.x, sub.y, sub.r, 0, 7); g.fill(); g.restore();
  });
};

export const KIT = T;
export const TEMPLATES = Object.keys(T);

// Episode modules: `export const build = buildWith({ ...KIT, myScene })`, or re-export build for a kit-only episode.
export function buildWith(templates) {
  return async (stage, spec) => {
    const f = templates[spec.type];
    if (!f) throw new Error(`unknown scene type ${spec.type} (kit: ${Object.keys(templates).join(', ')})`);
    return f(stage, spec);
  };
}
export const build = buildWith(T);
