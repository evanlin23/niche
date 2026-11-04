// Generic 3D "tabletop studio" stage for the Buh Simulates channel.
// A scene module (per episode) exports build(stage, spec) -> (frameIndex) => void.
// The page is driven frame-by-frame by capture.js; nothing here depends on wall-clock time.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export { THREE, RoundedBoxGeometry };

// ---------------------------------------------------------------- palette
export const COL = {
  bgCenter: '#4a5470', bgEdge: '#121722', floor: 0x262d3d, board: 0xe9e6dd, road: 0x3a4152,
  white: '#f2f1ec', amber: '#ffb627', red: '#e5484d', teal: '#4fd1c5', blue: '#4c9aff',
  ink: '#c9d1e0', muted: '#8e98ad', card: 'rgba(14,18,28,0.78)', grid: 'rgba(255,255,255,0.10)',
};

// ---------------------------------------------------------------- math helpers
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const ease = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const fade = (t, s, d = 0.4) => (d > 0 ? ease((t - s) / d) : +(t >= s));
export const win = (t, s, e, d = 0.35) => Math.min(fade(t, s, d), 1 - fade(t, e - d, d));
export const lerp = (a, b, t) => a + (b - a) * t;
export const lerp3 = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));

export function decodeF32(b64) {
  const bin = atob(b64); const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return new Float32Array(buf.buffer);
}

// speed (km/h) -> colour: stopped red -> amber -> cruising warm white
export function speedColor(kmh, full = 50) {
  const f = clamp(kmh / full);
  const red = new THREE.Color(COL.red), amb = new THREE.Color(COL.amber), wh = new THREE.Color(COL.white);
  return f < 0.5 ? red.lerp(amb, f / 0.5) : amb.lerp(wh, (f - 0.5) / 0.5);
}
export function speedCss(kmh, full = 50) { return '#' + speedColor(kmh, full).getHexString(); }

// ---------------------------------------------------------------- the stage
export class Stage {
  constructor(spec) {
    this.spec = spec;
    this.W = spec.W; this.H = spec.H; this.scale = spec.scale || 1;
    this.fps = spec.fps; this.duration = spec.duration;
    const root = document.getElementById('root');
    root.style.width = this.W + 'px'; root.style.height = this.H + 'px';
    root.style.transform = `scale(${this.scale})`;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(1);
    this.ssaa = spec.ssaa || 1;   // supersampling: render bigger, browser downsamples (smooth edges without MSAA)
    this.renderer.setSize(this.W * this.scale * this.ssaa, this.H * this.scale * this.ssaa, false);
    Object.assign(this.renderer.domElement.style, { width: this.W + 'px', height: this.H + 'px', position: 'absolute', left: 0, top: 0 });
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    root.appendChild(this.renderer.domElement);
    // 2D overlay canvas (charts) + DOM overlay (text)
    this.c2 = document.createElement('canvas');
    this.c2.width = this.W * this.scale; this.c2.height = this.H * this.scale;
    Object.assign(this.c2.style, { width: this.W + 'px', height: this.H + 'px', position: 'absolute', left: 0, top: 0 });
    root.appendChild(this.c2);
    this.g = this.c2.getContext('2d');
    this.ov = document.createElement('div');
    Object.assign(this.ov.style, { position: 'absolute', inset: 0 });
    root.appendChild(this.ov);

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(spec.fov || 32, this.W / this.H, 0.1, 400);
    if (spec.theme !== 'custom') this.studio();
    this.texts = [];
  }

  studio() {
    const cv = document.createElement('canvas'); cv.width = cv.height = 1024;
    const g = cv.getContext('2d');
    const gr = g.createRadialGradient(512, 400, 40, 512, 512, 720);
    gr.addColorStop(0, COL.bgCenter); gr.addColorStop(1, COL.bgEdge);
    g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    this.scene.background = tex;
    this.scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x1a2030, 0.95));
    const key = new THREE.SpotLight(0xfff3e0, 950, 0, Math.PI / 4.5, 0.65, 1.6);
    key.position.set(-6, 18, 9); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 5; key.shadow.bias = -0.0004;
    key.shadow.camera.near = 5; key.shadow.camera.far = 60;
    this.scene.add(key); this.scene.add(key.target); this.key = key;
    const rim = new THREE.DirectionalLight(0x9fb4ff, 0.6); rim.position.set(8, 6, -10); this.scene.add(rim);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(400, 400),
      new THREE.MeshStandardMaterial({ color: COL.floor, roughness: 0.95 }));
    floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; this.scene.add(floor);
  }

  // camera move: {pos:[a,b], look:[a,b]} eased across [t0,t1] (default whole scene)
  // slow orbit: {center:[x,y,z], r:[r0,r1], h:[h0,h1], deg:[a0,a1] or rate (deg/s, centred on 0), look}
  // Angle, radius and height all ease together over the whole scene, so the move starts and ends softly.
  orbitAt(t, o) {
    const k = ease(clamp(t / this.duration));
    const c = o.center || [0, 0, 0];
    const rate = o.rate ?? 1.2, half = Math.min(o.maxDeg ?? 16, rate * this.duration / 2);
    const [a0, a1] = o.deg || [-half, half];
    const a = (a0 + (a1 - a0) * k) * Math.PI / 180;
    const r = Array.isArray(o.r) ? o.r[0] + (o.r[1] - o.r[0]) * k : o.r;
    const h = Array.isArray(o.h) ? o.h[0] + (o.h[1] - o.h[0]) * k : o.h;
    this.camera.position.set(c[0] + Math.sin(a) * r, c[1] + h, c[2] + Math.cos(a) * r);
    const l = o.look || c; this.camera.lookAt(l[0], l[1], l[2]);
    if (o.fov) { this.camera.fov = o.fov; this.camera.updateProjectionMatrix(); }
  }

  cameraAt(t, cam) {
    const k = ease((t - (cam.t0 ?? 0)) / ((cam.t1 ?? this.duration) - (cam.t0 ?? 0)));
    const p = cam.pos.length > 1 ? lerp3(cam.pos[0], cam.pos[1], k) : cam.pos[0];
    const l = cam.look.length > 1 ? lerp3(cam.look[0], cam.look[1], k) : cam.look[0];
    this.camera.position.set(...p); this.camera.lookAt(...l);
    if (cam.fov) { this.camera.fov = cam.fov; this.camera.updateProjectionMatrix(); }
  }

  project(v3) {
    const v = v3.clone().project(this.camera);
    return [(v.x + 1) / 2 * this.W, (1 - v.y) / 2 * this.H];
  }

  // cue references: number | 'id' | 'id+1.5' | 'id:end'
  at(ref, dflt = 0) {
    if (ref === undefined || ref === null) return dflt;
    if (typeof ref === 'number') return ref;
    let off = 0; let r = ref;
    const m = r.match(/^(.*?)([+-][\d.]+)$/); if (m) { r = m[1]; off = parseFloat(m[2]); }
    const end = r.endsWith(':end'); r = r.replace(':end', '');
    const c = this.spec.cues[r]; if (!c) return dflt;
    return (end ? c[1] : c[0]) + off;
  }

  // DOM text with per-frame opacity. note: {text, at, until, x, y, size, color, weight, align, font, width, pill}
  text(note) {
    const d = document.createElement('div');
    const FONTS = { sans: 'Inter, "DejaVu Sans", sans-serif', rubik: 'Rubik, Inter, sans-serif', oswald: 'Oswald, Impact, sans-serif' };
    const font = FONTS[note.font || this.spec.font || 'oswald'];
    Object.assign(d.style, {
      position: 'absolute', left: note.x + 'px', top: note.y + 'px', fontFamily: font,
      fontSize: (note.size || 40) + 'px', fontWeight: note.weight || 700, color: note.color || '#fff',
      textTransform: (note.case || ((note.font || this.spec.font) === 'oswald' || !(note.font || this.spec.font) ? 'uppercase' : 'none')),
      letterSpacing: note.font === 'sans' ? '0' : (note.font || this.spec.font) === 'rubik' ? '-0.5px' : '0.5px', lineHeight: note.lh || 1.05,
      whiteSpace: note.width ? 'normal' : 'nowrap', width: note.width ? note.width + 'px' : 'auto',
      textShadow: note.pill ? 'none' : '0 4px 18px rgba(0,0,0,.45)', opacity: 0,
      fontVariantNumeric: 'tabular-nums',
    });
    if (note.manual) d.style.willChange = 'transform';
    if (note.align === 'center') d.style.transform = 'translateX(-50%)', d.style.textAlign = 'center';
    if (note.align === 'right') d.style.transform = 'translateX(-100%)', d.style.textAlign = 'right';
    if (note.pill) Object.assign(d.style, { background: note.pill, color: note.color || '#111', padding: '6px 18px', borderRadius: '999px' });
    d.innerHTML = note.html || escapeHtml(note.text);
    this.ov.appendChild(d);
    const item = { el: d, note, s: this.at(note.at, 0), e: this.at(note.until, 1e9) };
    this.texts.push(item);
    return item;
  }

  updateTexts(t) {
    for (const it of this.texts) {
      if (it.note.manual) {
        // Scenes place manual labels with style.left/top every frame. Layout positions snap to whole
        // pixels, so labels that follow a moving camera jitter. Move the offset into a composited
        // translate3d (sub-pixel) instead.
        const el = it.el, L = el.style.left, T = el.style.top;
        if (L !== '0px' || it.px == null) it.px = parseFloat(L) || 0;
        if (T !== '0px' || it.py == null) it.py = parseFloat(T) || 0;
        el.style.left = '0px'; el.style.top = '0px';
        const b = it.note.align === 'center' ? ' translateX(-50%)' : it.note.align === 'right' ? ' translateX(-100%)' : '';
        // the tiny rotation stops Chrome snapping the layer/glyphs to whole pixels (measured: smoothest option)
        el.style.transform = `translate3d(${it.px.toFixed(3)}px, ${it.py.toFixed(3)}px, 0)${b} rotate(0.02deg)`;
        continue;
      }
      const a = win(t, it.s, it.e, it.note.fade ?? 0.35);
      it.el.style.opacity = a;
      const rise = (1 - fade(t, it.s, 0.45)) * 18;
      const base = it.note.align === 'center' ? 'translateX(-50%)' : it.note.align === 'right' ? 'translateX(-100%)' : '';
      it.el.style.transform = `${base} translateY(${rise}px)`;
    }
  }

  clear2d() { const g = this.g; g.setTransform(this.scale, 0, 0, this.scale, 0, 0); g.clearRect(0, 0, this.W, this.H); }

  render() { this.renderer.render(this.scene, this.camera); }
}

export function escapeHtml(s) { return String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

// ---------------------------------------------------------------- 2D drawing helpers (overlay canvas)
export function card(g, x, y, w, h, r = 18, fill = COL.card) {
  g.save(); g.fillStyle = fill; g.beginPath(); g.roundRect(x, y, w, h, r); g.fill(); g.restore();
}
export function label(g, s, x, y, size = 20, color = COL.muted, align = 'left', weight = 500, font = 'Inter') {
  g.save(); g.font = `${weight} ${size}px ${font}, sans-serif`; g.fillStyle = color; g.textAlign = align; g.fillText(s, x, y); g.restore();
}
// line chart. series: [{ts:[...], ys:[...], color}]
export function lineChart(g, rect, xlim, ylim, series, opts = {}) {
  const [x, y, w, h] = rect;
  const px = (t) => x + (t - xlim[0]) / (xlim[1] - xlim[0]) * w;
  const py = (v) => y + h - (v - ylim[0]) / (ylim[1] - ylim[0]) * h;
  g.save(); g.globalAlpha = opts.alpha ?? 1;
  for (const yt of opts.yticks || []) {
    g.strokeStyle = COL.grid; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x, py(yt)); g.lineTo(x + w, py(yt)); g.stroke();
    label(g, String(yt), x - 12, py(yt) + 7, 19, COL.muted, 'right');
  }
  g.beginPath(); g.rect(x, y - 8, w, h + 16); g.clip();
  for (const s of series) {
    if (s.ts.length < 2) continue;
    g.strokeStyle = s.color; g.lineWidth = s.width || 5; g.lineJoin = g.lineCap = 'round';
    g.beginPath(); s.ts.forEach((t, i) => (i ? g.lineTo(px(t), py(s.ys[i])) : g.moveTo(px(t), py(s.ys[i])))); g.stroke();
    const n = s.ts.length - 1; g.fillStyle = s.color; g.beginPath(); g.arc(px(s.ts[n]), py(s.ys[n]), (s.width || 5) * 1.5, 0, 7); g.fill();
  }
  g.restore();
  return { px, py };
}

// ---------------------------------------------------------------- tabletop ring road
export class RingBoard {
  constructor(stage, { n, radius = 4.2, size = 11, carScale = 1, pos = [0, 0, 0], opacity = 1 }) {
    this.stage = stage; this.R = radius; this.n = n;
    const grp = new THREE.Group(); grp.position.set(...pos); this.group = grp;
    const transparent = opacity < 1;
    const slab = new THREE.Mesh(new RoundedBoxGeometry(size, 0.35, size, 4, 0.18),
      new THREE.MeshStandardMaterial({ color: COL.board, roughness: 0.82, transparent, opacity }));
    slab.position.y = 0.175; slab.castShadow = slab.receiveShadow = true; grp.add(slab);
    const road = new THREE.Mesh(new THREE.RingGeometry(radius - 0.45, radius + 0.45, 256),
      new THREE.MeshStandardMaterial({ color: COL.road, roughness: 0.9, transparent, opacity }));
    road.rotation.x = -Math.PI / 2; road.position.y = 0.352; road.receiveShadow = true; grp.add(road);
    const dashMat = new THREE.MeshStandardMaterial({ color: 0xcfd3dc, transparent, opacity });
    for (let k = 0; k < 72; k++) {
      const a = k / 72 * Math.PI * 2;
      const d = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.004, 0.03), dashMat);
      d.position.set(Math.cos(a) * radius, 0.356, Math.sin(a) * radius); d.rotation.y = -a; grp.add(d);
    }
    const geo = new RoundedBoxGeometry(0.26 * carScale, 0.2 * carScale, 0.46 * carScale, 3, 0.07 * carScale);
    this.cars = [];
    for (let i = 0; i < n; i++) {
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: COL.white, roughness: 0.45, transparent, opacity }));
      m.castShadow = true; grp.add(m); this.cars.push(m);
    }
    this.pins = {};
    stage.scene.add(grp);
  }

  carWorld(i) { const v = new THREE.Vector3(); this.cars[i].getWorldPosition(v); return v; }

  // pin above a car: kind -> colour
  pin(i, color) {
    if (this.pins[i]) return this.pins[i];
    const g = new THREE.Group();
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.5, 8), new THREE.MeshStandardMaterial({ color: 0xdddddd }));
    stick.position.y = 0.25; g.add(stick);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.13, 24, 16), new THREE.MeshStandardMaterial({ color, roughness: 0.3, emissive: color, emissiveIntensity: 0.25 }));
    head.position.y = 0.55; head.castShadow = true; g.add(head);
    this.group.add(g); this.pins[i] = g; return g;
  }

  // x: positions (m, any wrap), v: speeds km/h, length: ring length (m)
  update(x, v, length, roles = {}) {
    for (let i = 0; i < this.n; i++) {
      const a = (x[i] % length) / length * Math.PI * 2;
      const m = this.cars[i];
      m.position.set(Math.cos(a) * this.R, 0.46, Math.sin(a) * this.R);
      m.rotation.y = -a;
      const role = roles[i];
      let col = speedColor(v[i]);
      let em = v[i] < 8 ? 0.35 : 0;
      if (role === 'smooth') { col = new THREE.Color(COL.blue); em = 0.25; }
      m.material.color.copy(col);
      m.material.emissive.copy(role === 'smooth' ? new THREE.Color(COL.blue) : new THREE.Color(COL.red));
      m.material.emissiveIntensity = em;
      const p = this.pins[i]; if (p) p.position.set(m.position.x, 0.56, m.position.z);
    }
  }
}
