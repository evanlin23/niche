// UNO episode: reuses the shared scene types, adds a table and the 112-card deck with our own card designs.
import { THREE, clamp, ease, fade } from '/pipeline/web/stage.js';
import { GN, buildRoom, makeBars } from '/pipeline/web/gamenight.js';
import { SCENES as BASE, notes, brand, title, scrim } from '/episodes/exploding-kittens/web/scenes.js';
import { makeUno } from '/pipeline/web/unocards.js';

const SCENES = { ...BASE };

const SEATS = [[0, 4.1], [-6.6, 0.2], [0, -3.7], [6.6, 0.2]];
const TOKCOL = [GN.blue, GN.cream, GN.coral, GN.mustard];

SCENES.unotable = async (stage, spec) => {
  buildRoom(stage);
  const p = spec.params;
  SEATS.forEach(([sx, sz], i) => {
    const tok = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.42, 0.9, 32), new THREE.MeshStandardMaterial({ color: TOKCOL[i], roughness: 0.4 }));
    body.position.y = 0.45; body.castShadow = true; tok.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 16), new THREE.MeshStandardMaterial({ color: TOKCOL[i], roughness: 0.4 }));
    head.position.y = 1.15; head.castShadow = true; tok.add(head);
    const dir = Math.atan2(-sx, -sz);
    tok.position.set(sx + Math.sin(dir) * -1.3, 0.06, sz + Math.cos(dir) * -1.3); stage.scene.add(tok);
    const n = 7;
    for (let k = 0; k < n; k++) {
      const c = makeUno(stage, 'back', 0); const off = (k - (n - 1) / 2) * 0.45;
      c.position.set(sx + Math.cos(dir) * off, 0.08 + k * 0.004, sz - Math.sin(dir) * off); c.rotation.y = dir + (k - 3) * 0.05;
    }
  });
  const deck = []; for (let k = 0; k < 30; k++) { const c = makeUno(stage, 'back', 0); c.position.set(-1.1, 0.07 + k * 0.024, 0.2); deck.push(c); }
  // discard pile: a sequence of plays (or a growing +2/+4 stack when params.stack)
  const seq = p.stack ? [[0, 12], [3, 12], [2, 12], [4, 14], [4, 14], [1, 12]] : [[0, 7], [0, 3], [3, 3], [3, 11], [1, 11], [4, 13], [2, 5], [2, 12], [1, 12], [1, 9]];
  const pile = seq.map(([c, k], i) => { const m = makeUno(stage, c, k); m.position.set(1.2 + (i % 3) * 0.05, 0.08 + i * 0.025, 0.2 + (i % 2) * 0.04); m.rotation.y = (i * 0.37) % 0.6 - 0.3; m.visible = false; return m; });
  const counter = stage.text({ text: '', x: 960, y: 820, size: 90, weight: 900, font: 'rubik', color: GN.coral, align: 'center', manual: true });
  notes(stage, p.notes); brand(stage);
  const t0 = stage.at(p.from || 0.3, 0.3), dt = p.every || 1.1;
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 16.5, 15.5], [0, 15.2, 14.2]], look: [[0, 0, 0.9]] });
    let shown = 0, total = 0;
    pile.forEach((m, i) => {
      const k = ease((t - t0 - i * dt) / 0.5);
      m.visible = k > 0; m.position.y = 0.08 + i * 0.025 + (1 - k) * 2.5;
      if (k > 0.5) { shown = i + 1; total += seq[i][1] === 14 ? 4 : seq[i][1] === 12 ? 2 : 0; }
    });
    counter.el.style.opacity = p.stack && shown ? 1 : 0; counter.el.textContent = `+${total}`;
    scrim(stage, t);
    const g = stage.g, gr = g.createLinearGradient(0, 0, 0, 260);
    gr.addColorStop(0, `rgba(${GN.scrim},0.85)`); gr.addColorStop(1, `rgba(${GN.scrim},0)`); g.fillStyle = gr; g.fillRect(0, 0, stage.W, 260);
  };
};

SCENES.unodeck = async (stage, spec) => {
  buildRoom(stage);
  const groups = [];
  for (let c = 0; c < 4; c++) groups.push([[c, 0], 19, `19 × ${['red', 'yellow', 'green', 'blue'][c]} 0–9`]);
  groups.push([[1, 12], 8, '8 × Draw Two'], [[3, 11], 8, '8 × Reverse'], [[2, 10], 8, '8 × Skip'],
    [[4, 13], 4, '4 × Wild'], [[4, 14], 4, '4 × Wild Draw Four'], [[4, 15], 1, '1 × Shuffle Hands'], [[4, 16], 3, '3 × blank Wild']);
  const items = groups.map(([[c, k], n, name], gi) => {
    const col = gi % 6, row = Math.floor(gi / 6);
    const gx = -6.8 + col * 2.7, gz = -1.4 + row * 3.4;
    const cards = [];
    for (let j = 0; j < n; j++) {
      const kk = gi < 4 ? (j < 1 ? 0 : 1 + Math.floor((j - 1) / 2)) : k;
      const m = makeUno(stage, c, kk); m.position.set(gx + (j % 10) * 0.1, 0.08 + j * 0.02, gz + Math.floor(j / 10) * 0.4); m.rotation.y = -0.12; m.visible = false; cards.push(m);
    }
    const lab = stage.text({ text: name, x: 0, y: 0, size: 24, weight: 900, font: 'rubik', color: GN.text, manual: true, align: 'center' });
    return { cards, lab, gx, gz, at: 0.5 + gi * 0.35 };
  });
  title(stage, 'Official deck · 112 cards'); brand(stage);
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 13, 9.5], [0, 12, 8.6]], look: [[0, 0, 0.8]] });
    stage.camera.updateMatrixWorld();
    for (const it of items) {
      const k = ease((t - it.at) / 0.5);
      it.cards.forEach((m, j) => { m.visible = k > 0; m.position.y = 0.08 + j * 0.02 + (1 - k) * 2; });
      const [lx, ly] = stage.project(new THREE.Vector3(it.gx + 0.5, 0, it.gz + 1.5));
      it.lab.el.style.left = lx + 'px'; it.lab.el.style.top = ly + 'px'; it.lab.el.style.opacity = fade(t, it.at + 0.2, 0.4);
    }
    scrim(stage, t);
  };
};

SCENES.title = async (stage, spec) => {
  buildRoom(stage);
  const p = spec.params;
  const cards = [[0, 7], [3, 12], [2, 11], [4, 14], [1, 3], [4, 13], [2, 10], [0, 9], [3, 0]].map(([c, k], i) => {
    const m = makeUno(stage, c, k); const a = i / 9 * Math.PI * 2;
    m.position.set(Math.cos(a) * 5.2, 0.08 + i * 0.01, Math.sin(a) * 3.2); m.rotation.y = a * 1.7; return m;
  });
  stage.text({ text: 'BUH SIMULATES', x: 960, y: 300, size: 40, weight: 700, font: 'rubik', color: GN.mustard, align: 'center', at: 0.3 });
  (p.lines || []).forEach((s, k) => stage.text({ text: s, x: 960, y: 370 + k * 130, size: 120, weight: 900, font: 'rubik', align: 'center', at: 0.5 + k * 0.25, case: 'none' }));
  return (t) => {
    const a = t * 0.06;
    stage.cameraAt(t, { pos: [[Math.sin(a) * 4, 15 - t * 0.2, 9 + Math.cos(a) * 2]], look: [[0, 0, 0]] });
    scrim(stage, t);
    const g = stage.g; g.fillStyle = `rgba(${GN.scrim},0.45)`; g.fillRect(0, 0, stage.W, stage.H);
  };
};

export async function build(stage, spec) {
  const f = SCENES[spec.type];
  if (!f) throw new Error('unknown scene type ' + spec.type);
  return f(stage, spec);
}
