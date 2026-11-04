// Exploding Kittens episode: game-night tabletop scenes.
import { THREE, RoundedBoxGeometry, clamp, ease, fade, win, lerp } from '/pipeline/web/stage.js';
import { GN, buildRoom, makeCard, makeDeck, makeBars, CARD, cardTexture } from '/pipeline/web/gamenight.js';

const NAMED = { MUSTARD: GN.mustard, CORAL: GN.coral, TEAL: GN.teal, BLUE: GN.blue, TEXT: GN.text, MUTED: GN.muted, CREAM: GN.cream };
const EVCARD = { skip: 3, attack: 2, favor: 4, shuffle: 5, future: 7, nope: 6, yup: 6 };
const EVLABEL = { skip: 'SKIP', attack: 'ATTACK!', favor: 'FAVOR', shuffle: 'SHUFFLE', future: 'SEE THE FUTURE', nope: 'NOPE!', yup: 'YUP!', pair: 'STEAL', triple: 'STEAL', defuse: 'DEFUSED', explode: 'BOOM' };

// ------------------------------------------------------------------ shared
function notes(stage, list) {
  for (const n of list || []) {
    stage.text({
      text: n.text, at: n.at, until: n.until, x: n.pos[0], y: n.pos[1], size: n.size || 48, align: n.align,
      color: n.pill ? '#1b1209' : (NAMED[n.color] || GN.text), weight: n.weight || 900, font: n.font || 'rubik', width: n.width,
      pill: n.pill ? (NAMED[n.pill] || GN.mustard) : null, case: 'none',
    });
  }
}
function brand(stage, x = 56, y = 36) {
  stage.text({ text: 'BUH SIMULATES', x, y, size: 26, color: GN.brand, weight: 700, font: 'rubik', at: -1 });
}
function title(stage, s, at = 0.1, y = 54) {
  if (s) stage.text({ text: s, x: 960, y, size: 64, weight: 900, font: 'rubik', align: 'center', at, case: 'none' });
}
function scrim(stage, t, fin = stage.spec.fade_in ?? 0, fout = stage.spec.fade_out ?? 0) {
  // Hard cuts between scenes: a dip to the background at every boundary reads as a flash.
  // Only the end card fades out (and a scene can opt in with spec.fade_in / fade_out).
  stage.clear2d();
  const a = Math.max(1 - fade(t, 0, fin), fade(t, stage.duration - fout, fout));
  if (a > 0.001) { const g = stage.g; g.fillStyle = `rgba(${GN.scrim},${a})`; g.fillRect(0, 0, stage.W, stage.H); }
}
function drift(stage, t, from, to, look, arc = null) {
  // push-in plus a slow arc around the look point (~0.8 deg/s, at most +/-6 deg)
  const deg = arc ?? Math.min(6, 0.4 * stage.duration);
  const k = ease(clamp(t / stage.duration)), a = (-deg + 2 * deg * k) * Math.PI / 180;
  const rot = (p) => { const dx = p[0] - look[0], dz = p[2] - look[2];
    return [look[0] + dx * Math.cos(a) + dz * Math.sin(a), p[1], look[2] - dx * Math.sin(a) + dz * Math.cos(a)]; };
  stage.cameraAt(t, { pos: [rot(from), rot(to)], look: [look] });
}

// ------------------------------------------------------------------ table with a replayed game
const SEATS = [[0, 4.1], [-6.6, 0.2], [0, -3.7], [6.6, 0.2]];
const SEATCOL = [GN.blue, GN.cream, GN.coral, GN.mustard];

function makeTable(stage, spec) {
  buildRoom(stage);
  const deck = makeDeck(stage, [-1.0, 0, 0.2], 46);
  const discard = makeCard(stage, 2, true); discard.position.set(1.2, 0.08, 0.2); discard.visible = false;
  const n = spec.trace.players;
  const seats = [];
  for (let i = 0; i < n; i++) {
    const [sx, sz] = SEATS[i];
    const tok = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.42, 0.9, 32), new THREE.MeshStandardMaterial({ color: SEATCOL[i], roughness: 0.4 }));
    body.position.y = 0.45; body.castShadow = true; tok.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 16), new THREE.MeshStandardMaterial({ color: SEATCOL[i], roughness: 0.4 }));
    head.position.y = 1.15; head.castShadow = true; tok.add(head);
    const dir = Math.atan2(-sx, -sz);
    tok.position.set(sx * 1.0 + Math.sin(dir) * -1.3, 0.06, sz + Math.cos(dir) * -1.3);
    stage.scene.add(tok);
    const hand = [];
    for (let k = 0; k < 14; k++) { const c = makeCard(stage, 'back', false); c.visible = false; hand.push(c); }
    const label = stage.text({ text: i === 0 ? 'TEST BOT' : `PLAYER ${i + 1}`, x: 0, y: 0, size: 26, weight: 900, font: 'rubik', color: i === 0 ? GN.blue : GN.muted, manual: true, align: 'center' });
    seats.push({ i, sx, sz, dir, tok, hand, label });
  }
  const mover = makeCard(stage, 'back', false); mover.visible = false;
  mover.traverse((o) => { o.castShadow = false; });
  const pill = stage.text({ text: '', x: 0, y: 0, size: 34, weight: 900, font: 'rubik', pill: GN.mustard, color: '#1b1209', manual: true, align: 'center' });
  const odds = stage.text({ text: '', x: 0, y: 0, size: 40, weight: 900, font: 'rubik', color: GN.text, manual: true, align: 'center' });
  const oddsSub = stage.text({ text: 'chance the next card is a Kitten', x: 0, y: 0, size: 20, weight: 700, font: 'rubik', color: GN.muted, manual: true, align: 'center' });
  return { deck, discard, seats, mover, pill, odds, oddsSub, n };
}

function layoutHand(seat, count, dead) {
  const { sx, sz, dir } = seat;
  seat.hand.forEach((c, k) => {
    c.visible = !dead && k < count;
    if (!c.visible) return;
    const spread = Math.min(0.42, 4.2 / Math.max(1, count));
    const off = (k - (count - 1) / 2) * spread;
    const px = sx + Math.cos(dir) * off, pz = sz - Math.sin(dir) * off;
    c.position.set(px, 0.08 + k * 0.004, pz);
    c.rotation.set(0, dir + (k - (count - 1) / 2) * 0.05, 0);
  });
}

function seatPos(seat) { return new THREE.Vector3(seat.sx * 0.86, 0.3, seat.sz * 0.86); }

function tableFrame(stage, T, spec, ev, u, opts = {}) {
  const events = spec.trace.events;
  const i = clamp(Math.floor(u), 0, events.length - 1), f = u - Math.floor(u);
  const e = events[i];
  const dead = new Set(); let kittens = T.n - 1;
  for (let k = 0; k <= i; k++) if (events[k].ev === 'explode') { dead.add(events[k].p); if (k < i || f > 0.6) kittens -= 0; }
  for (let k = 0; k <= i; k++) if (events[k].ev === 'explode') kittens--;
  T.deck.setCount(Math.min(46, e.deck));
  T.seats.forEach((s) => {
    const isDead = dead.has(s.i) && !(e.ev === 'explode' && e.p === s.i && f < 0.6);
    layoutHand(s, Math.max(0, e.hands[s.i]), isDead);
    s.tok.rotation.z = isDead ? lerp(0, Math.PI / 2.2, 1) : 0;
    s.tok.position.y = isDead ? 0.3 : 0.06;
    const front = s.sz > 2;   // seat nearest the camera: label goes below the pawn, not over the cards
    const [lx, ly] = stage.project(front ? new THREE.Vector3(s.tok.position.x, 0, s.tok.position.z + 1.4) : new THREE.Vector3(s.tok.position.x, 1.8, s.tok.position.z));
    s.label.el.style.left = lx + 'px'; s.label.el.style.top = (front ? ly + 4 : ly - 30) + 'px'; s.label.el.style.opacity = opts.labels === false ? 0 : 1;
    s.label.el.textContent = isDead ? 'OUT' : (opts.seatNames ? opts.seatNames[s.i] : (s.i === 0 ? (opts.heroName || 'TEST BOT') : (opts.otherName || `PLAYER ${s.i + 1}`)));
  });
  // last played card on discard
  let last = null;
  for (let k = i; k >= 0; k--) if (EVCARD[events[k].ev] != null) { last = EVCARD[events[k].ev]; break; }
  if (last != null) { T.discard.visible = true; T.discard.setFace(last); }
  // moving card for the current event
  const seat = T.seats[e.p] || T.seats[0];
  const deckTop = new THREE.Vector3(T.deck.pos[0], T.deck.topY(Math.min(46, e.deck)) + 0.05, T.deck.pos[2]);
  const k = ease(f / 0.75);
  T.mover.visible = false;
  let label = EVLABEL[e.ev] || '';
  if (e.ev === 'draw') {
    T.mover.visible = f < 0.8; T.mover.setFace(e.p === 0 ? e.arg : 'back');
    T.mover.position.lerpVectors(deckTop, seatPos(seat), k); T.mover.position.y += Math.sin(k * Math.PI) * 1.2;
    label = '';
  } else if (EVCARD[e.ev] != null) {
    T.mover.visible = f < 0.8; T.mover.setFace(EVCARD[e.ev]);
    T.mover.position.lerpVectors(seatPos(seat), new THREE.Vector3(1.2, 0.2, 0.2), k); T.mover.position.y += Math.sin(k * Math.PI) * 1.5;
    if (e.ev === 'attack' && e.target >= 0) label = `ATTACK → ${e.target === 0 ? 'TEST BOT' : 'P' + (e.target + 1)}`;
  } else if (e.ev === 'defuse') {
    T.mover.visible = true; T.mover.setFace(0);
    const up = seatPos(seat).clone(); up.y = 2.2;
    T.mover.position.copy(f < 0.5 ? up.clone().lerp(up, 0) : up.clone().lerp(deckTop, ease((f - 0.5) / 0.4)));
  } else if (e.ev === 'explode') {
    T.mover.visible = true; T.mover.setFace(0);
    const up = seatPos(seat).clone(); up.y = 2.4;
    T.mover.position.lerpVectors(deckTop, up, ease(f / 0.4));
  } else if (e.ev === 'pair' || e.ev === 'triple') {
    T.mover.visible = f < 0.8; T.mover.setFace(8);
    T.mover.position.lerpVectors(seatPos(seat), new THREE.Vector3(1.2, 0.2, 0.2), k);
  }
  T.mover.rotation.set(0, 0, 0);
  if (opts.idle) { T.mover.visible = false; label = ''; }
  const [px, py] = stage.project(seatPos(seat).clone().setY(2.6));
  T.pill.el.style.opacity = label && opts.pills !== false ? win(f, 0.05, 0.95, 0.1) : 0;
  T.pill.el.textContent = label; T.pill.el.style.left = px + 'px'; T.pill.el.style.top = py - 40 + 'px';
  T.pill.el.style.background = e.ev === 'explode' ? GN.coral : e.ev === 'defuse' ? GN.green : GN.mustard;
  // odds
  const show = opts.odds ? 1 : 0;
  const ox = 230, oy = 860;
  const deckN = Math.max(1, e.deck);
  T.odds.el.textContent = kittens > 0 ? `Kitten odds: 1 in ${Math.max(1, Math.round(deckN / kittens))}` : '';
  T.odds.el.style.left = ox + 'px'; T.odds.el.style.top = oy - 70 + 'px'; T.odds.el.style.opacity = show;
  T.oddsSub.el.style.left = ox + 'px'; T.oddsSub.el.style.top = oy - 20 + 'px'; T.oddsSub.el.style.opacity = show;
}

const SCENES = {};

SCENES.table = async (stage, spec) => {
  const p = spec.params;
  const T = makeTable(stage, spec);
  notes(stage, p.notes); brand(stage);
  const evs = spec.trace.events;
  const e0 = p.ev_from ?? 0, e1 = Math.min(evs.length - 1, p.ev_to ?? evs.length - 1);
  const play = p.mode !== 'idle';
  const cam = p.cam || { from: [0, 16.5, 15.5], to: [0, 15.2, 14.2], look: [0, 0, 0.9] };
  return (t) => {
    const u = play ? lerp(e0, e1 + 0.99, clamp(t / (stage.duration - 0.6))) : (p.ev_still ?? 2);
    drift(stage, t, cam.from, cam.to, cam.look, cam.arc);
    stage.camera.updateMatrixWorld();
    tableFrame(stage, T, spec, null, u, { odds: !!p.odds, labels: p.labels !== false, pills: play, idle: !play, heroName: p.hero_name, otherName: p.other_name, seatNames: p.seat_names });
    scrim(stage, t);
    const g = stage.g, gr = g.createLinearGradient(0, 0, 0, 260);
    gr.addColorStop(0, `rgba(${GN.scrim},0.85)`); gr.addColorStop(1, `rgba(${GN.scrim},0)`); g.fillStyle = gr; g.fillRect(0, 0, stage.W, 260);
  };
};

SCENES.title = async (stage, spec) => {
  buildRoom(stage);
  const p = spec.params;
  const types = [0, 1, 2, 3, 6, 7, 8, 4, 5];
  const cards = types.map((tp, k) => { const c = makeCard(stage, tp, true); const a = k / types.length * Math.PI * 2; c.position.set(Math.cos(a) * 5.2, 0.08 + k * 0.01, Math.sin(a) * 3.2); c.rotation.y = a * 1.7; return c; });
  // short title beat: everything is readable within ~0.2 s (a slow stagger got cut off when the card was shortened)
  const quick = spec.duration < 2.0;
  stage.text({ text: 'BUH SIMULATES', x: 960, y: 300, size: 40, weight: 700, font: 'rubik', color: GN.mustard, align: 'center', at: quick ? 0.02 : 0.3, fade: quick ? 0.15 : 0.35 });
  (p.lines || []).forEach((s, k) => stage.text({ text: s, x: 960, y: 370 + k * 130, size: 120, weight: 900, font: 'rubik', align: 'center', at: quick ? 0.04 + k * 0.06 : 0.5 + k * 0.25, fade: quick ? 0.15 : 0.35, case: 'none' }));
  return (t) => {
    const a = t * 0.06;
    stage.cameraAt(t, { pos: [[Math.sin(a) * 4, 15 - t * 0.2, 9 + Math.cos(a) * 2]], look: [[0, 0, 0]] });
    cards.forEach((c, k) => { c.position.y = 0.08 + k * 0.01 + Math.max(0, Math.sin(t * 1.4 + k)) * 0.03; });
    scrim(stage, t);
    const g = stage.g; g.fillStyle = `rgba(${GN.scrim},0.45)`; g.fillRect(0, 0, stage.W, stage.H);
  };
};

SCENES.deck56 = async (stage, spec) => {
  buildRoom(stage);
  const groups = [[0, 4, 'Exploding Kittens'], [1, 6, 'Defuse'], [2, 4, 'Attack'], [3, 4, 'Skip'], [4, 4, 'Favor'],
    [5, 4, 'Shuffle'], [6, 5, 'Nope'], [7, 5, 'See the Future'], [8, 20, 'Cat cards']];
  const items = [];
  groups.forEach(([tp, n, name], gi) => {
    const col = gi % 5, row = Math.floor(gi / 5);
    const gx = -6.6 + col * 2.9, gz = -1.6 + row * 3.6;
    const cards = [];
    for (let k = 0; k < n; k++) {
      const c = makeCard(stage, tp === 8 ? 8 + (k % 5) : tp, true);
      // neat fan: one angle per pile and a little air between cards (exactly-touching cards z-fight and the
      // per-card jitter made edges cut through each other)
      c.position.set(gx + (k % 10) * 0.12, 0.012 + k * 0.026, gz + Math.floor(k / 10) * 0.45);
      c.rotation.y = -0.1; c.visible = false; cards.push(c);
    }
    const lab = stage.text({ text: `${n} × ${name}`, x: 0, y: 0, size: 28, weight: 900, font: 'rubik', color: GN.text, manual: true, align: 'center' });
    items.push({ cards, lab, gx, gz, at: 0.6 + gi * 0.45 });
  });
  title(stage, 'Original edition · 56 cards');
  brand(stage);
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 13, 9.5], [0, 12, 8.5]], look: [[0, 0, 0.8]] });
    stage.camera.updateMatrixWorld();
    for (const it of items) {
      const k = ease((t - it.at) / 0.5);
      // named in the card rundown: the pile lifts for ~1.6 s and its label turns mustard
      const h = spec.highlights && spec.highlights[String(items.indexOf(it))];
      const on = h != null ? win(t, h - 0.1, h + 1.6, 0.25) : 0;
      it.cards.forEach((c, j) => { c.visible = k > 0; c.position.y = 0.012 + j * 0.026 + (1 - k) * 2 + on * 0.6; });
      const [lx, ly] = stage.project(new THREE.Vector3(it.gx + 0.6, 0, it.gz + 1.6));
      it.lab.el.style.left = lx + 'px'; it.lab.el.style.top = ly + 'px'; it.lab.el.style.opacity = fade(t, it.at + 0.2, 0.4);
      it.lab.el.style.color = on > 0.5 ? GN.mustard : GN.text;
    }
    scrim(stage, t);
  };
};

SCENES.bars = async (stage, spec) => {
  buildRoom(stage, { feltW: 18, feltD: 9 });
  const ch = spec.chart, p = spec.params;
  // a chart with a note pill gets shorter bars so the pill never covers a value label
  const hasNotes = (p.notes || []).length > 0;
  const bars = makeBars(stage, ch.items, { x0: -6.3, width: 12.6, maxV: ch.maxV, height: hasNotes ? 5.2 : 6.2, z: 0, fair: ch.fair, unit: ch.unit ?? '%', fairSide: ch.fairSide ?? 'right' });
  const shifted = ch.players ? (p.notes || []).map((n) => ({ ...n, pos: n.pos ? [n.pos[0], n.pos[1] + 58] : n.pos })) : p.notes;
  title(stage, p.title); notes(stage, shifted); brand(stage);
  if (ch.players) {        // always say how many players this chart is about (charts used to switch silently)
    const fair = ch.fair != null ? ` · fair share ${ch.fair}%` : '';
    stage.text({ text: `${ch.players} players${fair}`, x: 960, y: 128, size: 30, weight: 700, font: 'rubik', align: 'center', at: 0.05, case: 'none', pill: 'rgba(244,234,213,0.92)', color: '#1b1209' });
  }
  return (t) => {
    // slow arc around the chart (labels are world-anchored and sub-pixel, so they glide with it)
    stage.orbitAt(t, { center: [0, 0, 0], look: [0, 2.6, 0], r: [16.6, 15.2], h: [6.4, 5.9], rate: 1.0, maxDeg: 8, ...(p.orbit || {}) });
    stage.camera.updateMatrixWorld();
    bars.update(t);
    scrim(stage, t);
  };
};

SCENES.placement = async (stage, spec) => {
  buildRoom(stage, { feltW: 18, feltD: 9 });
  const p = spec.params, ch = spec.chart;
  // the deck laid out as a row: left = top of the deck
  const row = [];
  const RX = -8.2, RS = 0.56;
  for (let k = 0; k < 12; k++) { const c = makeCard(stage, 'back', false); c.position.set(RX + k * RS, 0.08, -1.2); row.push(c); }
  const kitten = makeCard(stage, 0, true);
  const bars = makeBars(stage, ch.items, { x0: 0.2, width: 7.6, maxV: ch.maxV, height: 5.0, z: 0.5, fair: ch.fair, fairSide: 'left' });
  stage.text({ text: 'TOP OF DECK', x: 0, y: 0, size: 24, weight: 900, font: 'rubik', color: GN.mustard, manual: true });
  const topLab = stage.texts[stage.texts.length - 1];
  stage.text({ text: 'BOTTOM', x: 0, y: 0, size: 24, weight: 900, font: 'rubik', color: GN.muted, manual: true });
  const botLab = stage.texts[stage.texts.length - 1];
  title(stage, p.title); notes(stage, p.notes); brand(stage);
  // targets: slot index over time (random -> bottom -> top -> second)
  const plan = [[stage.at('k2+3', 0.6), 6], [stage.at('k3'), 12], [stage.at('k4'), 0], [stage.at('k4+4'), 1], [stage.at('k4+6'), 2], [stage.at('k5'), 0]];
  return (t) => {
    stage.cameraAt(t, { pos: [[-0.2, 7.2, 17.5], [0, 6.8, 16.8]], look: [[-0.2, 1.8, 0]] });
    stage.camera.updateMatrixWorld();
    let slot = 6, prev = 6, ts = 0;
    for (const [at, s] of plan) if (t >= at) { prev = slot; slot = s; ts = at; }
    const k = ease((t - ts) / 0.8);
    const sl = lerp(prev, slot, k);
    // open a gap in the row at the slot
    row.forEach((c, j) => { const shift = j >= sl ? RS : 0; c.position.x = RX + j * RS + shift; });
    const lift = Math.sin(k * Math.PI) * 1.2;
    kitten.position.set(RX + sl * RS, 0.25 + lift + (t < plan[0][0] ? 1.5 : 0), -1.2);
    const [tx, ty] = stage.project(new THREE.Vector3(RX, 0, -0.2));
    const [bx, by] = stage.project(new THREE.Vector3(RX + 12.5 * RS, 0, -0.2));
    topLab.el.style.left = tx - 60 + 'px'; topLab.el.style.top = ty + 'px'; topLab.el.style.opacity = 1;
    botLab.el.style.left = bx - 30 + 'px'; botLab.el.style.top = by + 'px'; botLab.el.style.opacity = 1;
    bars.update(t);
    scrim(stage, t);
  };
};

SCENES.checklist = async (stage, spec) => {
  buildRoom(stage);
  const p = spec.params;
  const deco = [0, 1, 3, 6, 7, 8].map((tp, k) => { const c = makeCard(stage, tp, true); c.position.set(2.9 + k * 0.4, 0.08 + k * 0.01, 2.2 - k * 0.12); c.rotation.y = -0.35 + k * 0.1; return c; });   // fanned on the right, clear of the list
  title(stage, p.title);
  (p.items || []).forEach((it, k) => {
    const y = 170 + k * (p.step || 120);
    stage.text({ text: it.text, x: 360, y, size: p.size || 46, weight: 700, font: 'rubik', at: it.at, case: 'none', width: 1100 });
    if (it.verdict) stage.text({ text: it.verdict, x: 1500, y: y - 4, size: 34, weight: 900, font: 'rubik', at: (typeof it.at === 'string' ? it.at : it.at) , pill: NAMED[it.color] || GN.mustard, color: '#1b1209' });
    else stage.text({ text: '✓', x: 290, y: y - 6, size: 56, weight: 900, font: 'rubik', color: GN.mustard, at: it.at });
  });
  brand(stage);
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 12, 10], [0.6, 11.4, 9.4]], look: [[0, 0, 0]] });
    scrim(stage, t);
    const g = stage.g; g.fillStyle = `rgba(${GN.scrim},0.62)`; g.fillRect(0, 0, stage.W, stage.H);
  };
};

SCENES.endcard = async (stage, spec) => {
  buildRoom(stage);
  const p = spec.params;
  const cards = [0, 1, 6].map((tp, k) => { const c = makeCard(stage, tp, true); c.position.set(-1 + k * 1.1, 0.08, 0); c.rotation.y = -0.2 + k * 0.2; return c; });
  stage.text({ text: 'NEXT', x: 260, y: 250, size: 40, weight: 900, font: 'rubik', color: GN.mustard, at: 0.3 });
  stage.text({ text: p.next_title || '', x: 660, y: 520, size: 60, weight: 900, font: 'rubik', align: 'center', at: 0.5, case: 'none' });
  stage.text({ text: 'subscribe', x: 1440, y: 530, size: 40, weight: 700, font: 'rubik', color: GN.muted, align: 'center', at: 0.5 });
  return (t) => {
    const a = t * 0.05;
    stage.cameraAt(t, { pos: [[Math.sin(a) * 9, 10, Math.cos(a) * 9]], look: [[0, 0, 0]] });
    scrim(stage, t, 0, 1.0);
    const g = stage.g, al = fade(t, 0.3, 0.6);
    g.fillStyle = `rgba(${GN.scrim},0.55)`; g.fillRect(0, 0, stage.W, stage.H);
    g.save(); g.globalAlpha = al; g.fillStyle = 'rgba(34,48,74,0.9)'; g.beginPath(); g.roundRect(260, 330, 800, 450, 22); g.fill();
    g.beginPath(); g.arc(1440, 555, 150, 0, 7); g.fill(); g.restore();
  };
};

SCENES.thumb = async (stage, spec) => {
  const room = buildRoom(stage);
  const v = spec.variant || 'A';
  const font = await rubikFont();
  const word = (txt, color, size, x, z, scale = 1) => {
    const geo = new TextGeometry(txt, { font, size, depth: size * 0.3, curveSegments: 6, bevelEnabled: true, bevelThickness: size * 0.03, bevelSize: size * 0.025, bevelSegments: 3 });
    geo.computeBoundingBox(); const bb = geo.boundingBox; geo.translate(-(bb.max.x + bb.min.x) / 2, 0, 0);
    const col = new THREE.Color(color);
    const m = new THREE.Mesh(geo, [new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 0.55, roughness: 0.5 }),
                                   new THREE.MeshStandardMaterial({ color: col.clone().multiplyScalar(0.5), roughness: 0.6 })]);
    m.rotation.x = -Math.PI / 2; m.position.set(x, 0, z); m.scale.setScalar(scale); m.castShadow = true; stage.scene.add(m); return m;
  };
  const kitten = (x, z, s, ry) => { const c = makeCard(stage, 0, true); c.scale.setScalar(s); c.position.set(x, 0.1, z); c.rotation.y = ry; return c; };
  if (room.floor) room.floor.material.color.multiplyScalar(0.8);
  if (v === 'A') {            // the counter-intuitive verdict
    word('DO', '#ffffff', 1.7, -3.4, -1.9); word('NOTHING.', '#ffcc33', 1.3, -1.2, 0.15);
    kitten(6.0, -0.4, 2.4, -0.22);
    word('WIN 40%', '#ff7a63', 1.0, -2.2, 2.6);
  } else if (v === 'B') {     // the gap
    const bar = (x, h, col) => { const m = new THREE.Mesh(new RoundedBoxGeometry(1.8, h, 1.8, 6, 0.14), new THREE.MeshPhysicalMaterial({ color: col, roughness: 0.32, clearcoat: 0.6 })); m.position.set(x, h / 2, 0.6); m.castShadow = true; stage.scene.add(m); };
    bar(-5.0, 0.9, '#ff6b57'); bar(-1.2, 2.8, '#f2b134');
    word('11%', '#ffffff', 0.85, -5.0, 2.6); word('35%', '#ffcc33', 0.85, -1.2, 2.6);
    kitten(4.6, 0.2, 2.3, 0.2);
    word('SAME CARDS.', '#ffffff', 0.7, 3.4, -2.6);
  } else {                    // the mistakes
    word('5', '#ff7a63', 3.2, -4.6, 0.6);
    word('MISTAKES', '#ffffff', 1.0, 0.6, -1.0); word('EVERYONE', '#ffcc33', 1.0, 0.6, 0.5); word('MAKES', '#ffffff', 1.0, 0.6, 2.0);
    kitten(5.4, -2.6, 1.5, 0.35);
  }
  return () => {
    const cam = v === 'B' ? { pos: [[0, 13, 7.5]], look: [[0, 0.6, 0.2]] } : { pos: [[0, 14.5, 3.2]], look: [[0, 0, 0.1]] };
    stage.cameraAt(0, cam); stage.clear2d();
  };
};

export async function build(stage, spec) {
  const f = SCENES[spec.type];
  if (!f) throw new Error('unknown scene type ' + spec.type);
  return f(stage, spec);
}

// ------------------------------------------------------------------ statement cards (3D text, lines pop in with the voice)
import { TTFLoader } from 'three/addons/loaders/TTFLoader.js';
import { Font } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';

let _font = null;
async function rubikFont() {
  if (_font) return _font;
  const json = await new Promise((res, rej) => new TTFLoader().load('/pipeline/web/fonts/rubik-latin-900.ttf', res, undefined, rej));
  _font = new Font(json);
  return _font;
}

SCENES.statement = async (stage, spec) => {
  const room = buildRoom(stage);
  if (room.floor) room.floor.material.color.multiplyScalar(0.72);   // darker floor behind text
  stage.scene.background = new THREE.Color(stage.scene.background).multiplyScalar(0.72);
  if (stage.scene.fog) stage.scene.fog.color.multiplyScalar(0.72);
  const font = await rubikFont();
  const lines = spec.lines;              // [{text, at, color}]
  const size = spec.params.size || 1.0, gapY = size * 1.45, maxW = spec.params.max_width || 10.5;
  const meshes = lines.map((ln, k) => {
    const geo = new TextGeometry(ln.text.toUpperCase(), { font, size, depth: size * 0.32, curveSegments: 6,
      bevelEnabled: true, bevelThickness: size * 0.03, bevelSize: size * 0.025, bevelSegments: 3 });
    geo.computeBoundingBox(); const bb = geo.boundingBox;
    geo.translate(-(bb.max.x + bb.min.x) / 2, 0, 0);
    const w = bb.max.x - bb.min.x;
    const col = new THREE.Color(ln.color === 'MUSTARD' ? '#ffcc33' : ln.color === 'CORAL' ? '#ff7a63' : ln.color ? (NAMED[ln.color] || ln.color) : '#ffffff');
    // bright, slightly self-lit faces + darker sides = crisp letter edges on the floor
    const face = new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 0.55, roughness: 0.5, transparent: true, opacity: 0 });
    const side = new THREE.MeshStandardMaterial({ color: col.clone().multiplyScalar(0.55), roughness: 0.6, transparent: true, opacity: 0 });
    const m = new THREE.Mesh(geo, [face, side]); m.castShadow = true;
    m.material.opacity = 0;
    const s = Math.min(ln.scale || 1, maxW / w); m.scale.set(s, s, s);
    const z0 = (k - (lines.length - 1) / 2) * gapY;     // lines lie on the floor, first line farthest
    m.rotation.x = -Math.PI / 2;
    m.userData = { z0, at: ln.at };
    stage.scene.add(m); return m;
  });
  if (!spec.params.no_brand) brand(stage);
  // orbit (creator request): lines fade up in place on their cue; the camera circles slowly at ~60 deg elevation,
  // so the extruded letters show their depth. Relative yaw stays small (+/-4 deg) so the words remain readable.
  const center = new THREE.Vector3(0, 0, 0.1 + size * 0.5);
  return (t) => {
    for (const m of meshes) {
      const k = ease((t - m.userData.at) / 0.3);
      m.material.forEach((mt) => (mt.opacity = k));
      m.visible = k > 0.001; m.castShadow = k > 0.6;
      m.position.set(0, (1 - k) * 0.25, m.userData.z0 + size * 0.5);   // tiny settle, no drop
      m.rotation.x = -Math.PI / 2;
    }
    const k = spec.params.static ? 0 : ease(clamp(t / stage.duration));
    const yaw = (-3 + 6 * k) * Math.PI / 180;
    const r = lerp(7.2, 6.4, k), h = lerp(16.4, 15.2, k);
    stage.camera.position.set(center.x + Math.sin(yaw) * r, h, center.z + Math.cos(yaw) * r);
    stage.camera.lookAt(center.x, 0, center.z);
    scrim(stage, t);
  };
};

// shared with other episodes (generic scene types + helpers)
export { SCENES, notes, brand, title, scrim, rubikFont };
