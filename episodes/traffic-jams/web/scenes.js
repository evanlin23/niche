// Episode 1 scenes in the 3D tabletop style. build(stage, spec) -> frame(t, i)
import {
  THREE, RoundedBoxGeometry, COL, RingBoard, clamp, ease, fade, win, lerp, decodeF32,
  speedColor, speedCss, card, label, lineChart,
} from '/pipeline/web/stage.js';

const NAMED = { AMBER: COL.amber, RED: COL.red, TEAL: COL.teal, BLUE: COL.blue, TEXT: '#ffffff', MUTED: COL.ink };
const DARK = '#1d2433';

// ---------------------------------------------------------------- shared helpers
function simReader(sim) {
  const X = decodeF32(sim.x), V = decodeF32(sim.v), n = sim.n;
  const at = (arr, t) => {
    const f = clamp((t - sim.t0) / sim.dt, 0, sim.count - 1);
    const i = Math.floor(f), j = Math.min(i + 1, sim.count - 1), w = f - i;
    const out = new Float32Array(n);
    for (let k = 0; k < n; k++) out[k] = arr[i * n + k] * (1 - w) + arr[j * n + k] * w;
    return out;
  };
  const series = (car, ta, tb, arr = V) => {
    const ts = [], ys = [];
    const i0 = Math.max(0, Math.ceil((ta - sim.t0) / sim.dt)), i1 = Math.min(sim.count - 1, Math.floor((tb - sim.t0) / sim.dt));
    for (let i = i0; i <= i1; i++) { ts.push(sim.t0 + i * sim.dt); ys.push(arr[i * n + car]); }
    ts.push(tb); ys.push(at(arr, tb)[car]);
    return { ts, ys };
  };
  const stoppedSeries = (ta, tb) => {
    const ts = [], ys = [];
    const i0 = Math.max(0, Math.ceil((ta - sim.t0) / sim.dt)), i1 = Math.min(sim.count - 1, Math.floor((tb - sim.t0) / sim.dt));
    for (let i = i0; i <= i1; i++) { let c = 0; for (let k = 0; k < n; k++) if (V[i * n + k] < 5) c++; ts.push(sim.t0 + i * sim.dt); ys.push(c); }
    return { ts, ys };
  };
  return { x: (t) => at(X, t), v: (t) => at(V, t), series, stoppedSeries, n, length: sim.length };
}

function notes(stage, list, onBoard = false) {
  for (const n of list || []) {
    let color = NAMED[n.color] || '#ffffff';
    if (onBoard && (!n.color || n.color === 'TEXT' || n.color === 'MUTED')) color = n.color === 'MUTED' ? '#5b6478' : DARK;
    const size = (n.size || 30) * 1.25;
    const pill = n.pill ? (NAMED[n.color] || COL.amber) : null;
    stage.text({
      text: n.text, at: n.at, until: n.until, x: n.pos[0], y: n.pos[1] - size * 0.9, size, align: n.align,
      color: pill ? (n.color === 'RED' || n.color === 'BLUE' ? '#fff' : '#111') : color, pill,
      width: n.width ? n.width * 1.1 : undefined, weight: 700,
    });
  }
}

function brand(stage, x = 56, y = 40) {
  stage.text({ text: 'I SIMULATED IT', x, y, size: 26, color: 'rgba(255,255,255,0.55)', weight: 500 });
}

function legend(g, x, y, alpha = 1) {
  g.save(); g.globalAlpha = alpha;
  const items = [[COL.white, 'cruising'], [COL.amber, 'slow'], [COL.red, 'stopped']];
  let cx = x;
  for (const [c, s] of items) {
    g.fillStyle = c; g.beginPath(); g.roundRect(cx, y - 14, 26, 16, 4); g.fill();
    label(g, s, cx + 36, y, 22, COL.ink, 'left', 500); cx += 36 + g.measureText(s).width + 70;
  }
  g.restore();
}

function scrimFade(stage, t, fin = 0.4, fout = 0.4) {
  const a = Math.max(1 - fade(t, 0, fin), fade(t, stage.duration - fout, fout));
  if (a > 0.001) { const g = stage.g; g.save(); g.fillStyle = `rgba(18,23,34,${a})`; g.fillRect(0, 0, stage.W, stage.H); g.restore(); }
}

function camFor(layout, p) {
  if (p.cam) return p.cam;
  if (layout === 'center') return { pos: [[0, 11.2, 13.2], [0.6, 10.2, 12.0]], look: [[0, 0, 0.7], [0, 0, 0.7]] };
  return { pos: [[-0.6, 10.8, 13.6], [-0.2, 10.0, 12.6]], look: [[1.55, 0, 0.6], [1.55, 0, 0.6]] };
}

function sheetImage(url) {
  return new Promise((res) => { const im = new Image(); im.onload = () => res(im); im.src = url; });
}

// sheet card (2D overlay): image revealed up to time ts. returns mapping helpers
function drawSheet(g, im, rect, sheet, ts, alpha = 1, opts = {}) {
  const [x, y, w, h] = rect;
  g.save(); g.globalAlpha = alpha;
  g.shadowColor = 'rgba(0,0,0,0.45)'; g.shadowBlur = 30; g.shadowOffsetY = 12;
  g.fillStyle = '#ece8de'; g.beginPath(); g.roundRect(x - 18, y - 18, w + 36, h + 36, 10); g.fill();
  g.shadowColor = 'transparent';
  const frac = ts == null ? 1 : clamp((ts - sheet.t0) / (sheet.t1 - sheet.t0));
  if (frac > 0) g.drawImage(im, 0, 0, im.width * frac, im.height, x, y, w * frac, h);
  g.strokeStyle = 'rgba(29,36,51,0.35)'; g.lineWidth = 2; g.strokeRect(x, y, w, h);
  if (opts.labels !== false) {
    label(g, 'position on ring', x, y - 28, 20, '#5b6478', 'left', 600);
    label(g, 'time →', x + w, y + h + 34, 20, '#5b6478', 'right', 600);
  }
  g.restore();
  const tx = (t) => x + (t - sheet.t0) / (sheet.t1 - sheet.t0) * w;
  const py = (pos) => y + h - pos / 1000 * h;
  return { tx, py };
}

// ---------------------------------------------------------------- scenes
const SCENES = {};

SCENES.ring = async (stage, spec) => {
  const p = spec.params, layout = p.layout || 'split';
  const sim = simReader(spec.sim);
  const board = new RingBoard(stage, { n: sim.n, pos: layout === 'center' ? [0, 0, 0] : [-3.0, 0, 0] });
  const roles = {};
  for (const [k, r] of Object.entries(p.highlight || {})) {
    roles[+k] = r;
    if (r === 'brake') board.pin(+k, COL.amber);
    if (r === 'track') board.pin(+k, 0xffffff);
  }
  const cam = camFor(layout, p);
  notes(stage, p.notes, layout === 'center');
  if (p.title) stage.text({ text: p.title, x: 56, y: 80, size: 56 });
  brand(stage);
  const brakeTag = stage.text({ text: 'braking', x: 0, y: 0, size: 26, pill: COL.amber, color: '#111', manual: true });
  const im = spec.sheet ? await sheetImage(spec.sheet.url) : null;
  const panel = layout === 'center' ? 'none' : (p.panel || 'chart');
  const chartColors = (p.chart_colors || ['TEXT']).map((c) => NAMED[c] || '#fff');
  const panelAt = stage.at(p.panel_at, 0), legendAt = stage.at(p.legend_at, 0);

  return (t, i) => {
    const ts = spec.frame_t[i];
    const x = sim.x(ts), v = sim.v(ts);
    const r = { ...roles };
    for (const [k, role] of Object.entries(roles)) if (role === 'smooth' && !(spec.smoother_on != null && ts >= spec.smoother_on - 8)) delete r[k];
    board.update(x, v, sim.length, r);
    stage.cameraAt(t, cam);
    stage.clear2d();
    const g = stage.g;
    // braking tag
    const bi = Object.keys(roles).find((k) => roles[k] === 'brake');
    const braking = spec.brake && bi != null && ts >= spec.brake[0] && ts < spec.brake[1] + 1;
    brakeTag.el.style.opacity = braking ? 1 : 0;
    if (braking) { const [sx, sy] = stage.project(board.carWorld(+bi)); brakeTag.el.style.left = sx - 50 + 'px'; brakeTag.el.style.top = sy - 110 + 'px'; }
    const pa = fade(t, panelAt, 0.6);
    const R = [1090, 250, 740, 470];
    if (panel === 'chart' && pa > 0) {
      card(g, R[0] - 50, R[1] - 80, R[2] + 90, R[3] + 190, 22, `rgba(14,18,28,${0.78 * pa})`);
      label(g, 'SPEED (KM/H)', R[0], R[1] - 30, 24, `rgba(201,209,224,${pa})`, 'left', 700, 'Oswald');
      label(g, `t = ${ts.toFixed(0)} s`, R[0] + R[2], R[1] - 30, 22, `rgba(142,152,173,${pa})`, 'right', 500);
      const series = (p.chart_cars || [39]).map((car, k) => ({ ...sim.series(car, Math.max(0, ts - 60), ts), color: chartColors[k] }));
      lineChart(g, R, [Math.max(0, ts - 60), Math.max(60, ts)], [0, 80], series, { yticks: [0, 20, 40, 60, 80], alpha: pa });
      let lx = R[0];
      (p.chart_labels || ['tracked car']).forEach((s, k) => {
        g.save(); g.globalAlpha = pa; g.fillStyle = chartColors[k]; g.beginPath(); g.arc(lx + 8, R[1] + R[3] + 52, 8, 0, 7); g.fill(); g.restore();
        label(g, s, lx + 26, R[1] + R[3] + 60, 24, `rgba(255,255,255,${pa})`, 'left', 500); lx += g.measureText(s).width + 90;
      });
    } else if (panel === 'stopped' && pa > 0) {
      card(g, R[0] - 50, R[1] - 80, R[2] + 90, R[3] + 150, 22, `rgba(14,18,28,${0.78 * pa})`);
      label(g, 'CARS STOPPED (< 5 KM/H)', R[0], R[1] - 30, 24, `rgba(201,209,224,${pa})`, 'left', 700, 'Oswald');
      label(g, `t = ${ts.toFixed(0)} s`, R[0] + R[2], R[1] - 30, 22, `rgba(142,152,173,${pa})`, 'right', 500);
      const s = sim.stoppedSeries(p.t0, ts);
      lineChart(g, R, [p.t0, p.t1], [0, 12], [{ ...s, color: COL.red }], { yticks: [0, 4, 8, 12], alpha: pa });
    } else if (panel === 'spacetime' && im) {
      drawSheet(g, im, [1100, 230, 720, 560], spec.sheet, ts, pa);
    }
    if (layout !== 'center' && p.legend !== false) legend(g, 1100, 1000, fade(t, legendAt, 0.5));
    scrimFade(stage, t, p.fade_in ?? 0.35, p.fade_out ?? 0.35);
  };
};

SCENES.title = async (stage, spec) => {
  const board = new RingBoard(stage, { n: spec.still.x.length });
  board.update(spec.still.x, spec.still.v, 1000);
  const p = spec.params;
  stage.text({ text: 'I SIMULATED IT · EPISODE 1', x: 960, y: 250, size: 40, color: COL.amber, align: 'center', weight: 500, at: 0.3 });
  p.lines.forEach((s, k) => stage.text({ text: s, x: 960, y: 330 + k * 150, size: 150, align: 'center', at: 0.5 + 0.25 * k }));
  stage.text({ text: p.sub || '', x: 960, y: 690, size: 40, color: COL.ink, align: 'center', weight: 500, at: 1.2 });
  return (t) => {
    const a = t * 0.05;
    stage.cameraAt(t, { pos: [[Math.sin(a) * 15, 9 - t * 0.15, Math.cos(a) * 15]], look: [[0, 0, 0]] });
    stage.clear2d();
    const g = stage.g;
    const gr = g.createLinearGradient(0, 0, 0, stage.H); gr.addColorStop(0, 'rgba(18,23,34,0.55)'); gr.addColorStop(1, 'rgba(18,23,34,0.85)');
    g.fillStyle = gr; g.fillRect(0, 0, stage.W, stage.H);
    scrimFade(stage, t);
  };
};

SCENES.experiment = async (stage, spec) => {
  const n = 22, L = 230;
  const board = new RingBoard(stage, { n, radius: 3.2, size: 8.6, pos: [-3.4, 0, 0], carScale: 1.15 });
  const facts = [['exp1', '22 cars'], ['exp1+3.0', '230 m circuit'], ['exp1+6.0', 'target: 30 km/h'], ['exp2', 'no lights · no junctions'], ['exp3', 'result: a jam, anyway']];
  stage.text({ text: 'Sugiyama et al. (2008)', x: 1060, y: 190, size: 72, at: 0.2 });
  stage.text({ text: 'New Journal of Physics 10, 033001', x: 1062, y: 280, size: 26, color: COL.ink, font: 'sans', weight: 500, at: 0.4 });
  facts.forEach(([cue, s], k) => stage.text({ text: s, x: 1062, y: 360 + k * 90, size: 60, at: cue, color: s.includes('jam') ? COL.red : '#fff' }));
  stage.text({ text: '(animation is illustrative)', x: 1062, y: 860, size: 22, color: COL.muted, font: 'sans', weight: 500, at: 'exp3+1.0' });
  brand(stage);
  const jamAt = stage.at('exp3+1.0');
  return (t) => {
    const jam = fade(t, jamAt, 2.5);
    const x = [], v = [];
    for (let k = 0; k < n; k++) {
      const a0 = k / n, base = t * 0.035;
      const d = ((a0 + base - (0.5 - 0.02 * t)) % 1 + 1) % 1 - 0.5;
      const sq = -jam * 0.08 * Math.exp(-((d / 0.12) ** 2)) * Math.sign(d);
      x.push(((a0 + base + sq) % 1 + 1) % 1 * L);
      v.push(50 * (1 - jam * Math.exp(-((d / 0.07) ** 2))));
    }
    board.update(x, v, L);
    stage.cameraAt(t, { pos: [[-1.2, 10.5, 12.5], [-0.8, 9.6, 11.6]], look: [[1.4, 0, 0.6]] });
    stage.clear2d(); scrimFade(stage, t);
  };
};

SCENES.equation = async (stage, spec) => {
  // a short straight road with "you" and "car ahead"
  const road = new THREE.Mesh(new RoundedBoxGeometry(16, 0.3, 2.2, 3, 0.12), new THREE.MeshStandardMaterial({ color: COL.board, roughness: 0.85 }));
  road.position.set(0, 0.15, 3.2); road.receiveShadow = road.castShadow = true; stage.scene.add(road);
  const asphalt = new THREE.Mesh(new THREE.PlaneGeometry(15.4, 1.1), new THREE.MeshStandardMaterial({ color: COL.road }));
  asphalt.rotation.x = -Math.PI / 2; asphalt.position.set(0, 0.302, 3.2); asphalt.receiveShadow = true; stage.scene.add(asphalt);
  const carGeo = new RoundedBoxGeometry(1.1, 0.45, 0.6, 3, 0.15);
  const you = new THREE.Mesh(carGeo, new THREE.MeshStandardMaterial({ color: COL.white, roughness: 0.45 }));
  const lead = new THREE.Mesh(carGeo, new THREE.MeshStandardMaterial({ color: COL.white, roughness: 0.45 }));
  [you, lead].forEach((m) => { m.castShadow = true; m.position.y = 0.53; stage.scene.add(m); });
  lead.position.set(3.4, 0.53, 3.2);
  const hl = (cue0, cue1, col, html) => `<span data-a="${cue0}" data-b="${cue1}" data-c="${col}" style="padding:0 8px;border-radius:10px;transition:none">${html}</span>`;
  const eq1 = stage.text({ html: `acceleration = a · [ ${hl('mod3', 'mod4', COL.teal, '1 − (v / v₀)⁴')} − ${hl('mod4', 'mod6', COL.red, '( s* / s )²')} ]`, x: 960, y: 300, size: 64, font: 'sans', weight: 500, align: 'center', at: 'mod2' });
  const eq2 = stage.text({ html: `s* = ${hl('mod4', 'mod5', COL.red, 's₀ + v·T + v·Δv / 2√(ab)')}`, x: 960, y: 410, size: 46, font: 'sans', weight: 500, align: 'center', at: 'mod2+0.4' });
  stage.text({ text: 'The Intelligent Driver Model', x: 960, y: 110, size: 72, align: 'center', at: 0.1 });
  stage.text({ text: 'Treiber, Hennecke & Helbing — Phys. Rev. E 62, 1805 (2000)', x: 960, y: 200, size: 24, color: COL.ink, font: 'sans', weight: 500, align: 'center', at: 0.3 });
  stage.text({ text: 'urge to go', x: 690, y: 520, size: 40, color: COL.teal, at: 'mod3', until: 'mod6', align: 'center' });
  stage.text({ text: 'urge to keep your distance', x: 1220, y: 520, size: 40, color: COL.red, at: 'mod4', until: 'mod6', align: 'center' });
  const rows = ['v₀ = 108 km/h', 'T = 1.2 s', 'a = 0.8 m/s²', 'b = 1.5 m/s²', 's₀ = 2 m'];
  stage.text({ html: rows.join('&nbsp;&nbsp;·&nbsp;&nbsp;') + '&nbsp;&nbsp;— <span style="color:#ffb627">same for every car</span>', x: 960, y: 520, size: 30, font: 'sans', weight: 500, color: COL.ink, align: 'center', at: 'mod6' });
  const spans = [...stage.ov.querySelectorAll('span[data-a]')].map((el) => ({ el, a: stage.at(el.dataset.a), b: stage.at(el.dataset.b), c: el.dataset.c }));
  const gapTag = stage.text({ text: 'gap  s', x: 0, y: 0, size: 40, color: COL.amber, manual: true });
  const youTag = stage.text({ text: 'you', x: 0, y: 0, size: 32, color: COL.ink, manual: true });
  const leadTag = stage.text({ text: 'car ahead', x: 0, y: 0, size: 32, color: COL.ink, manual: true });
  const diagAt = stage.at('mod4');
  brand(stage);
  return (t) => {
    for (const s of spans) {
      const h = win(t, s.a, s.b, 0.4);
      s.el.style.background = h > 0 ? `${s.c}${Math.round(h * 0x30).toString(16).padStart(2, '0')}` : 'transparent';
      s.el.style.color = h > 0.5 ? s.c : '#fff';
    }
    you.position.x = -3.4 + 0.5 * Math.sin(t * 0.8);
    stage.cameraAt(t, { pos: [[0, 3.2, 15.5], [0, 3.0, 14.5]], look: [[0, 1.6, 0]] });
    stage.clear2d();
    const g = stage.g, da = fade(t, diagAt, 0.6);
    const [ax, ay] = stage.project(new THREE.Vector3(you.position.x + 0.6, 0.55, 3.2));
    const [bx, by] = stage.project(new THREE.Vector3(lead.position.x - 0.6, 0.55, 3.2));
    if (da > 0) {
      g.save(); g.globalAlpha = da; g.strokeStyle = COL.amber; g.lineWidth = 5; g.setLineDash([14, 10]);
      g.beginPath(); g.moveTo(ax + 10, ay - 60); g.lineTo(bx - 10, by - 60); g.stroke(); g.restore();
    }
    for (const [tag, x0, y0, a] of [[gapTag, (ax + bx) / 2 - 60, ay - 140, da], [youTag, ax - 90, ay + 70, da], [leadTag, bx - 30, by + 70, da]]) {
      tag.el.style.left = x0 + 'px'; tag.el.style.top = y0 + 'px'; tag.el.style.opacity = a;
    }
    scrimFade(stage, t);
  };
};

SCENES.chain = async (stage, spec) => {
  const mins = spec.mins, n = mins.length, gap = 0.34, hs = 0.3;
  const geo = new RoundedBoxGeometry(0.26, 1, 0.26, 2, 0.05);
  const bars = mins.map((m, k) => {
    const b = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: speedColor(m), roughness: 0.5, emissive: COL.red, emissiveIntensity: m < 8 ? 0.3 : 0 }));
    b.position.set(k * gap, 0, 0); b.castShadow = true; b.scale.y = 0.001; stage.scene.add(b); return b;
  });
  for (let lap = 1; lap * 40 < n; lap++) {
    const plate = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.02, 1.4), new THREE.MeshStandardMaterial({ color: 0x8e98ad }));
    plate.position.set((lap * 40 - 0.5) * gap, 0.01, 0); stage.scene.add(plate);
  }
  const r0 = stage.at('amp1+1.0'), r1 = stage.at('amp3+2.5');
  stage.text({ text: 'Lowest speed as the slowdown passes each car', x: 80, y: 60, size: 60, at: 0.1 });
  const lapTags = [];
  for (let lap = 1; lap * 40 < n; lap++) lapTags.push([lap, stage.text({ text: `lap ${lap + 1}`, x: 0, y: 0, size: 24, color: COL.muted, manual: true })]);
  const t1 = stage.text({ text: `first car: ${mins[0].toFixed(0)} km/h`, x: 0, y: 0, size: 34, color: COL.amber, manual: true });
  const t2 = stage.text({ text: 'softened', x: 0, y: 0, size: 30, pill: COL.teal, color: '#111', manual: true });
  const t3 = stage.text({ text: `first full stop · handoff ${spec.first_stop}`, x: 0, y: 0, size: 30, pill: COL.red, color: '#fff', manual: true });
  stage.text({ text: 'STRING INSTABILITY', x: 960, y: 930, size: 56, pill: COL.amber, color: '#111', align: 'center', at: 'amp4' });
  stage.text({ text: 'car-to-car handoffs →', x: 1840, y: 1010, size: 24, color: COL.muted, font: 'sans', weight: 500, align: 'right', at: 0.3 });
  brand(stage);
  const a2 = stage.at('amp2'), a3 = stage.at('amp3'), a1 = stage.at('amp1+1');
  return (t) => {
    const k = n * ease((t - r0) / Math.max(1e-6, r1 - r0));
    bars.forEach((b, j) => { const grow = clamp(k - j); const h = Math.max(0.001, mins[j] * hs * grow); b.scale.y = h; b.position.y = h / 2; });
    const cx = clamp(k, 12, n) * gap;
    const far = clamp((k - 30) / (n - 30));
    stage.cameraAt(t, {
      pos: [[lerp(4, n * gap / 2, ease(far)), lerp(6, 16, ease(far)), lerp(16, 120, ease(far))]],
      look: [[lerp(4, n * gap / 2, ease(far)), lerp(4, 5.5, ease(far)), 0]], fov: 32,
    });
    // keep the newest column in frame early on
    if (far <= 0) stage.cameraAt(t, { pos: [[cx - 4, 6, 16]], look: [[cx - 4, 4, 0]] });
    stage.camera.updateMatrixWorld();
    const place = (tag, x3, y3, dx, dy, a) => { const [sx, sy] = stage.project(new THREE.Vector3(x3, y3, 0)); tag.el.style.left = sx + dx + 'px'; tag.el.style.top = sy + dy + 'px'; tag.el.style.opacity = a; };
    lapTags.forEach(([lap, tag]) => place(tag, (lap * 40) * gap, 0, -10, 20, k > lap * 40 ? 1 : 0));
    place(t1, 0, mins[0] * hs, -40, -80, fade(t, a1, 0.5));
    place(t2, 12 * gap, mins[12] * hs, -40, -90, k > 30 ? fade(t, a2, 0.5) : 0);
    place(t3, spec.first_stop * gap, 0.3, -380, -170, k > spec.first_stop ? fade(t, a3, 0.5) : 0);
    stage.clear2d(); scrimFade(stage, t);
  };
};

SCENES.spacetime = async (stage, spec) => {
  const p = spec.params, sh = spec.sheet;
  const im = await sheetImage(sh.url);
  brand(stage);
  const rf = stage.at(p.reveal_from || 'st2'), rt = stage.at(p.reveal_to || 'st3');
  const st2 = stage.at('st2'), st3 = stage.at('st3+2.5'), st4 = stage.at('st4');
  stage.text({ text: 'Space-time diagram', x: 300, y: 50, size: 56, at: 0.2 });
  stage.text({ text: 'jam moves backwards · ~14 km/h', x: 0, y: 0, size: 30, pill: COL.red, color: '#fff', at: 'st3+2.5', manual: false, ...{} });
  const jamTag = stage.texts[stage.texts.length - 1];
  stage.text({ text: 'real highways: ~15–20 km/h', x: 330, y: 170, size: 30, pill: COL.amber, color: '#111', at: 'st4' });
  // a little 3D board in the corner, so the "where" stays physical
  const R = [300, 160, 1500, 760];
  return (t) => {
    const ts = t >= rf ? sh.t0 + (sh.t1 - sh.t0) * ease((t - rf) / Math.max(1e-6, rt - rf)) : sh.t0;
    stage.cameraAt(t, { pos: [[0, 6, 20]], look: [[0, 2, 0]] });
    stage.clear2d();
    const g = stage.g;
    const { tx, py } = drawSheet(g, im, R, sh, ts);
    // time ticks
    for (let m = 0; m <= (sh.t1 - sh.t0) / 60; m += 2) label(g, `${m} min`, tx(sh.t0 + m * 60), R[1] + R[3] + 34, 20, COL.ink, 'center', 500);
    for (const pos of [0, 250, 500, 750, 1000]) label(g, `${pos} m`, R[0] - 28, py(pos) + 7, 20, COL.ink, 'right', 500);
    const a = fade(t, st2, 0.5);
    if (a > 0) {
      g.save(); g.globalAlpha = a; g.strokeStyle = COL.white; g.lineWidth = 6; g.lineCap = 'round';
      g.beginPath(); g.moveTo(170, 830); g.lineTo(170, 380); g.moveTo(150, 410); g.lineTo(170, 380); g.lineTo(190, 410); g.stroke();
      label(g, 'TRAFFIC', 170, 880, 28, '#fff', 'center', 700, 'Oswald'); g.restore();
    }
    const a3 = fade(t, st3, 0.6);
    if (a3 > 0 && spec.jam_guide) {
      const [ta, xa, tb, xb] = spec.jam_guide;
      g.save(); g.globalAlpha = a3; g.strokeStyle = DARK; g.lineWidth = 6; g.lineCap = 'round';
      g.beginPath(); g.moveTo(tx(ta), py(xa)); g.lineTo(tx(tb), py(xb)); g.stroke(); g.restore();
      jamTag.el.style.left = tx(tb) - 520 + 'px'; jamTag.el.style.top = py(xb) + 20 + 'px';
    }
    scrimFade(stage, t);
  };
};

SCENES.why = async (stage, spec) => {
  const lag = spec.lag;
  // density strips (3D, right side)
  const mk = (z, n, color) => {
    const strip = new THREE.Mesh(new RoundedBoxGeometry(8.4, 0.25, 1.1, 3, 0.1), new THREE.MeshStandardMaterial({ color: COL.board }));
    strip.position.set(4.2, 0.125, z); strip.receiveShadow = strip.castShadow = true; stage.scene.add(strip);
    const sp = 1000 / n, scale = 8 / 250;    // 250 m of road shown
    const geo = new RoundedBoxGeometry(5 * scale * 1.0, 0.18, 0.42, 2, 0.05);
    for (let k = 0; k * sp < 245; k++) {
      const c = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color }));
      c.position.set(0.2 + 4.2 - 4 + k * sp * scale + 0.1, 0.34, z); c.castShadow = true; stage.scene.add(c);
    }
  };
  mk(-0.4, 40, COL.red); mk(1.9, 30, COL.teal);
  stage.text({ text: 'Two ingredients', x: 80, y: 60, size: 70, at: 0.1 });
  stage.text({ text: '1 · LAG', x: 120, y: 220, size: 60, color: COL.amber, at: 'why2' });
  stage.text({ text: '2 · DENSITY', x: 1020, y: 220, size: 60, color: COL.red, at: 'why3' });
  stage.text({ text: '40 cars → 20 m gaps', x: 1020, y: 330, size: 40, color: COL.red, at: 'why3' });
  stage.text({ text: '30 cars → 28 m gaps', x: 1020, y: 690, size: 40, color: COL.teal, at: 'why3' });
  stage.text({ text: '(250 m of road shown)', x: 1020, y: 940, size: 22, color: COL.muted, font: 'sans', weight: 500, at: 'why3' });
  brand(stage);
  const w2 = stage.at('why2'), w3 = stage.at('why3');
  return (t) => {
    stage.cameraAt(t, { pos: [[2.5, 9, 9.5]], look: [[2.5, 0, 0.7]] });
    // hide strips until why3 by sinking them
    stage.scene.children.forEach((o) => { if (o.isMesh && o.position.x > 0 && o.geometry.type !== 'PlaneGeometry') o.visible = t >= w3 - 0.1; });
    stage.clear2d();
    const g = stage.g, a = fade(t, w2, 0.5);
    if (a > 0) {
      card(g, 90, 280, 820, 700, 22, `rgba(14,18,28,${0.82 * a})`);
      const k = ease((t - w2) / 6), te = 18 + 32 * k;
      const sel = (arr) => arr.filter((_, j) => lag.t[j] <= te);
      const ts = sel(lag.t);
      lineChart(g, [170, 360, 680, 480], [18, 50], [25, 60], [
        { ts, ys: sel(lag.lead), color: COL.amber }, { ts, ys: sel(lag.follow), color: '#fff' }], { yticks: [30, 40, 50, 60], alpha: a });
      label(g, 'km/h', 170, 340, 20, COL.muted);
      label(g, '● car ahead', 170, 920, 26, COL.amber, 'left', 600); label(g, '● you (reacting later)', 400, 920, 26, '#fff', 'left', 600);
    }
    scrimFade(stage, t);
  };
};

SCENES.endcard = async (stage, spec) => {
  const board = new RingBoard(stage, { n: spec.still.x.length });
  const p = spec.params;
  stage.text({ text: 'NEXT EPISODE', x: 260, y: 250, size: 40, color: COL.amber, at: 0.3 });
  stage.text({ text: p.next_title || '', x: 660, y: 520, size: 64, align: 'center', at: 0.5 });
  stage.text({ text: 'subscribe', x: 1440, y: 525, size: 40, color: COL.ink, align: 'center', at: 0.5 });
  stage.text({ text: 'Simulation code: link in the description', x: 960, y: 880, size: 34, color: COL.ink, font: 'sans', weight: 500, align: 'center', at: 0.8 });
  return (t) => {
    const x = spec.still.x.map((v) => v + t * 10);
    const roles = { 20: 'smooth' };
    board.update(x, spec.still.v, 1000, roles);
    const a = t * 0.04;
    stage.cameraAt(t, { pos: [[Math.sin(a) * 15, 10, Math.cos(a) * 15]], look: [[0, 0, 0]] });
    stage.clear2d();
    const g = stage.g, al = fade(t, 0.3, 0.6);
    g.fillStyle = 'rgba(18,23,34,0.6)'; g.fillRect(0, 0, stage.W, stage.H);
    card(g, 260, 330, 800, 450, 20, `rgba(14,18,28,${0.85 * al})`);
    g.save(); g.globalAlpha = al; g.fillStyle = 'rgba(14,18,28,0.85)'; g.beginPath(); g.arc(1440, 555, 150, 0, 7); g.fill(); g.restore();
    scrimFade(stage, t, 0.35, 1.0);
  };
};

SCENES.short = async (stage, spec) => {
  const p = spec.params, mode = p.mode || 'ring';
  const sim = simReader(spec.sim);
  const im = spec.sheet ? await sheetImage(spec.sheet.url) : null;
  let board = null;
  if (mode !== 'spacetime') board = new RingBoard(stage, { n: sim.n });
  const roles = {};
  for (const [k, r] of Object.entries(p.highlight || {})) { roles[+k] = r; if (r === 'brake' && board) board.pin(+k, COL.amber); }
  (spec.hook || '').split('\n').forEach((s, k) => stage.text({ text: s, x: 540, y: 150 + k * 120, size: 118, align: 'center', at: -1 }));
  notes(stage, p.notes, true);
  stage.text({ text: 'I SIMULATED IT', x: 540, y: 1690, size: 30, color: 'rgba(255,255,255,0.6)', align: 'center', weight: 500, at: -1 });
  const cap = stage.text({ text: '', x: 540, y: 0, size: 84, align: 'center', manual: true });
  cap.el.style.webkitTextStroke = '3px #000'; cap.el.style.paintOrder = 'stroke fill'; cap.el.style.width = '960px'; cap.el.style.whiteSpace = 'normal'; cap.el.style.lineHeight = '1.08';
  const capY = p.caption_y || 1460;
  const brakeTag = stage.text({ text: 'braking', x: 0, y: 0, size: 34, pill: COL.amber, color: '#111', manual: true });
  return (t, i) => {
    const ts = spec.frame_t[i];
    stage.clear2d();
    const g = stage.g;
    if (board) {
      const r = { ...roles };
      for (const [k, role] of Object.entries(roles)) if (role === 'smooth' && !(spec.smoother_on != null && ts >= spec.smoother_on - 8)) delete r[k];
      board.update(sim.x(ts), sim.v(ts), sim.length, r);
      if (mode === 'ring') stage.cameraAt(t, { pos: [[0, 17.5, 13.5], [0, 16.5, 12.5]], look: [[0, 0, 0.9]], fov: 42 });
      else stage.cameraAt(t, { pos: [[0, 15, 12]], look: [[0, 0, -3.5]], fov: 42 });
      const bi = Object.keys(roles).find((k) => roles[k] === 'brake');
      const braking = spec.brake && bi != null && ts >= spec.brake[0] && ts < spec.brake[1] + 1;
      brakeTag.el.style.opacity = braking ? 1 : 0;
      if (braking) { const [sx, sy] = stage.project(board.carWorld(+bi)); brakeTag.el.style.left = sx - 70 + 'px'; brakeTag.el.style.top = sy - 140 + 'px'; }
    } else stage.cameraAt(t, { pos: [[0, 6, 20]], look: [[0, 2, 0]] });
    if (mode === 'spacetime') {
      const rev = p.reveal || [0.3, stage.duration * 0.6];
      const tt = sh(spec).t0 + (sh(spec).t1 - sh(spec).t0) * ease((t - rev[0]) / (rev[1] - rev[0]));
      const R = [110, 470, 900, 780];
      const { tx, py } = drawSheet(g, im, R, spec.sheet, tt);
      const a = fade(t, stage.at(p.arrow_at, 5), 0.5);
      if (a > 0) {
        g.save(); g.globalAlpha = a; g.strokeStyle = COL.white; g.lineWidth = 7; g.lineCap = 'round';
        g.beginPath(); g.moveTo(55, 1200); g.lineTo(55, 560); g.moveTo(33, 595); g.lineTo(55, 560); g.lineTo(77, 595); g.stroke();
        g.restore(); label(g, 'CARS', 55, 1250, 34, '#fff', 'center', 700, 'Oswald');
      }
      const a2 = fade(t, stage.at(p.jam_at, 9), 0.5);
      if (a2 > 0 && spec.jam_guide) {
        const [ta, xa, tb, xb] = spec.jam_guide;
        g.save(); g.globalAlpha = a2; g.strokeStyle = DARK; g.lineWidth = 8; g.lineCap = 'round';
        g.beginPath(); g.moveTo(tx(ta), py(xa)); g.lineTo(tx(tb), py(xb)); g.stroke(); g.restore();
        card(g, tx(tb) - 330, py(xb) + 24, 340, 64, 32, `rgba(229,72,77,${a2})`);
        label(g, 'JAM ↓ ~14 KM/H', tx(tb) - 160, py(xb) + 70, 36, `rgba(255,255,255,${a2})`, 'center', 700, 'Oswald');
      }
    } else if (mode === 'ring_st') {
      drawSheet(g, im, [110, 1180, 860, 420], spec.sheet, ts, 1, { labels: false });
    }
    // captions
    const c = spec.captions.find(([s, e]) => t >= s - 0.05 && t < e + 0.12);
    if (c) {
      const words = c[2].toUpperCase();
      if (cap.el.dataset.t !== words) { cap.el.dataset.t = words; cap.el.innerHTML = `<span style="color:${COL.amber}">${words}</span>`; }
      const pop = 1 + 0.08 * (1 - ease((t - c[0]) / 0.12));
      cap.el.style.opacity = 1; cap.el.style.top = capY - 84 + 'px'; cap.el.style.transform = `translateX(-50%) scale(${pop})`;
    } else cap.el.style.opacity = 0;
    const a = 1 - fade(t, 0, 0.15);
    if (a > 0) { g.fillStyle = `rgba(18,23,34,${a})`; g.fillRect(0, 0, stage.W, stage.H); }
  };
};
const sh = (spec) => spec.sheet;

SCENES.thumb = async (stage, spec) => {
  const board = new RingBoard(stage, { n: spec.still.x.length, pos: [-2.6, 0, 0] });
  board.update(spec.still.x, spec.still.v, 1000);
  stage.text({ text: 'ONE', x: 1030, y: 110, size: 230, at: -1 });
  stage.text({ text: 'BRAKE', x: 1030, y: 340, size: 230, color: COL.amber, at: -1 });
  stage.text({ text: 'TAP.', x: 1030, y: 570, size: 230, at: -1 });
  stage.text({ text: 'NO ACCIDENT. STILL STUCK.', x: 1040, y: 860, size: 56, pill: COL.red, color: '#fff', at: -1 });
  return () => { stage.cameraAt(0, { pos: [[-3.4, 11, 12.6]], look: [[0.6, 0, 0.6]] }); stage.clear2d(); };
};

export async function build(stage, spec) {
  const f = SCENES[spec.type];
  if (!f) throw new Error('unknown scene type ' + spec.type);
  return f(stage, spec);
}
