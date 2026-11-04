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
const SEATS5 = [[0, 4.1], [-6.4, 1.9], [-3.9, -3.5], [3.9, -3.5], [6.4, 1.9]];   // 5 bots: one per seat, no doubling up
const SEATCOL = [GN.blue, GN.cream, GN.coral, GN.mustard, GN.green || '#7fc8a9'];

function makeTable(stage, spec) {
  buildRoom(stage);
  const deck = makeDeck(stage, [-1.0, 0, 0.2], 46);
  const discard = makeCard(stage, 2, true); discard.position.set(1.2, 0.08, 0.2); discard.visible = false;
  const n = spec.trace.players;
  const seats = [];
  for (let i = 0; i < n; i++) {
    const [sx, sz] = (n === 5 ? SEATS5 : SEATS)[i];
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
    c.position.set(px, 0.02 + k * 0.032, pz);   // stacked by real thickness: overlapping hand cards never intersect
    c.rotation.set(0, dir + Math.PI + (k - (count - 1) / 2) * 0.05, 0);   // upright for the person in that seat
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
    const hlOn = (opts.seatHl || []).some(([si, t0]) => si === s.i && opts.t >= t0 && opts.t < t0 + 2.4);
    s.label.el.style.color = hlOn ? GN.mustard : (s.i === 0 && !opts.seatNames ? GN.blue : GN.muted);
    if (hlOn) s.tok.position.y += Math.abs(Math.sin(opts.t * 7)) * 0.25;
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
  const [px, py] = stage.project(seatPos(seat).clone().setY(3.4));   // above the seat's name label
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
  // "what a real player knows" (params.knows = {hand, future, hid} word times): the Patient One picks up its
  // hand and holds it upright while the camera swings behind it; See the Future lifts the top three cards;
  // a Kitten slides into the deck.
  const K = p.knows;
  let held = [], fut = [], hidK = null;
  if (K) {
    held = [1, 3, 6, 8, 2].map((tp) => { const c = makeCard(stage, tp, true); c.visible = false; return c; });
    fut = [8, 0, 3].map((tp) => { const c = makeCard(stage, tp, true); c.visible = false; c.traverse((o) => { o.castShadow = false; }); return c; });
    hidK = makeCard(stage, 0, true); hidK.visible = false;
  }
  const V3 = (a) => new THREE.Vector3(...a);
  const SHOTS = K ? [   // [time, camera pos, look] keyframes, eased between
    [0, [0, 16.5, 15.5], [0, 0, 0.9]],
    [K.hand - 0.2, [0, 15.6, 14.6], [0, 0, 0.9]],
    [K.hand + 0.9, [2.4, 4.6, 9.4], [0, 1.7, 3.1]],          // over the shoulder: the cards as the player sees them
    [K.future - 0.1, [-1.6, 4.8, 9.3], [0, 1.6, 3.1]],       // slow orbit around the held hand
    [K.future + 0.9, [0.2, 7.2, 7.4], [-0.6, 1.2, 0.2]],    // over to the deck
    [K.hid + 0.2, [-0.6, 6.8, 6.9], [-0.8, 0.8, 0.2]],
    [K.hid + 2.4, [0, 12.5, 12.0], [0, 0, 0.9]],
  ] : null;
  function shotAt(t) {
    let i = 0; while (i < SHOTS.length - 1 && t > SHOTS[i + 1][0]) i++;
    if (i >= SHOTS.length - 1) return [V3(SHOTS[i][1]), V3(SHOTS[i][2])];
    const [t0, p0, l0] = SHOTS[i], [t1, p1, l1] = SHOTS[i + 1];
    const k = ease(clamp((t - t0) / Math.max(0.01, t1 - t0)));
    return [V3(p0).lerp(V3(p1), k), V3(l0).lerp(V3(l1), k)];
  }
  return (t) => {
    const u = play ? lerp(e0, e1 + 0.99, clamp(t / (stage.duration - 0.6))) : (p.ev_still ?? 2);
    if (K) { const [cp, cl] = shotAt(t); stage.camera.position.copy(cp); stage.camera.lookAt(cl); }
    else drift(stage, t, cam.from, cam.to, cam.look, cam.arc);
    stage.camera.updateMatrixWorld();
    tableFrame(stage, T, spec, null, u, { odds: !!p.odds, labels: p.labels !== false, pills: play, idle: !play, heroName: p.hero_name, otherName: p.other_name, seatNames: p.seat_names, seatHl: p.seat_hl, t });
    if (K) {
      const seat = T.seats[0];
      // held hand: up on "hand", down a bit after See the Future starts
      const up = ease(clamp((t - K.hand) / 0.6)) * (1 - ease(clamp((t - K.future - 0.6) / 0.6)));
      held.forEach((c, i) => {
        c.visible = up > 0.001;
        const off = i - (held.length - 1) / 2;
        const flat = new THREE.Vector3(seat.sx + off * 0.42, 0.06, seat.sz - 0.2);
        const hold = new THREE.Vector3(off * 0.52, 1.6 - off * off * 0.06, 3.1 + Math.abs(off) * 0.05 - i * 0.012);
        c.position.lerpVectors(flat, hold, up);
        // stand up facing the player (+z), fanned
        c.rotation.set(Math.PI / 2 * up, 0, -off * 0.24 * up);
        c.scale.setScalar(1 + 0.15 * up);
      });
      if (up > 0.001) seat.hand.forEach((c) => (c.visible = false));
      // See the Future: top three cards lift off the deck, turn face up toward the camera, then go back
      const back = Math.max(0.6, Math.min(2.2, K.hid - K.future - 0.5));   // gone before the Kitten is hidden
      const f = ease(clamp((t - K.future) / 0.4)) * (1 - ease(clamp((t - K.future - back) / 0.35)));
      const deckTop = new THREE.Vector3(T.deck.pos[0], T.deck.topY(Math.min(46, spec.trace.events[Math.floor(p.ev_still ?? 2)].deck)) + 0.05, T.deck.pos[2]);
      fut.forEach((c, i) => {
        c.visible = f > 0.001;
        const target = new THREE.Vector3(T.deck.pos[0] - 1.25 + i * 1.25, 1.9, T.deck.pos[2] + 0.9);
        c.position.lerpVectors(deckTop.clone().setY(deckTop.y + i * 0.03), target, f);
        c.rotation.set(Math.PI / 2 * 0.62 * f, 0, 0);
      });
      // hide a Kitten: from the player's seat into the middle of the deck
      const h = clamp((t - K.hid) / 1.4);
      hidK.visible = h > 0 && h < 1;
      if (hidK.visible) {
        const mid = new THREE.Vector3(T.deck.pos[0], deckTop.y * 0.5, T.deck.pos[2]);
        const a = new THREE.Vector3(seat.sx, 0.6, seat.sz - 0.6), b = mid.clone().add(new THREE.Vector3(0, 0, 1.4));
        if (h < 0.6) { const k = ease(h / 0.6); hidK.position.lerpVectors(a, b, k); hidK.position.y += Math.sin(k * Math.PI) * 1.0; }
        else { const k = ease((h - 0.6) / 0.4); hidK.position.lerpVectors(b, mid, k); }
        hidK.rotation.set(0, 0, 0);
      }
    }
    scrim(stage, t);
    const g = stage.g, gr = g.createLinearGradient(0, 0, 0, 260);
    gr.addColorStop(0, `rgba(${GN.scrim},0.85)`); gr.addColorStop(1, `rgba(${GN.scrim},0)`); g.fillStyle = gr; g.fillRect(0, 0, stage.W, 260);
  };
};

// ------------------------------------------------------------------ meet the bots: who they are and what they do
// params.bots: [{name, color, at, habits: [{text, at}]}] (anchors resolved by scenes3d)
SCENES.bots = async (stage, spec) => {
  buildRoom(stage, { feltW: 18, feltD: 9 });
  const p = spec.params, bots = p.bots;
  const COLS = { BLUE: GN.blue, CREAM: GN.cream, CORAL: GN.coral, MUSTARD: GN.mustard, GREEN: GN.green };
  const n = bots.length, gap = 2.6;
  const pawns = bots.map((b, i) => {
    const col = COLS[b.color] || b.color;
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.52, 1.1, 32), new THREE.MeshStandardMaterial({ color: col, roughness: 0.4 }));
    body.position.y = 0.55; body.castShadow = true; g.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.37, 32, 16), new THREE.MeshStandardMaterial({ color: col, roughness: 0.4 }));
    head.position.y = 1.42; head.castShadow = true; g.add(head);
    const x = (i - (n - 1) / 2) * gap;
    g.position.set(x, 0, 0); stage.scene.add(g);
    const lab = stage.text({ text: b.name, x: 0, y: 0, size: 28, weight: 900, font: 'rubik', color: GN.text, manual: true, align: 'center' });
    // habits card: one panel, filled for whoever is being described
    return { b, g, x, lab, col, appear: 0.2 + i * 0.18 };
  });
  title(stage, p.title || "Who's at the table"); brand(stage);
  const panel = document.createElement('div');
  Object.assign(panel.style, { position: 'absolute', left: '50%', top: '128px', transform: 'translateX(-50%)', width: '1180px',
    padding: '26px 40px 30px', borderRadius: '26px', background: 'rgba(20,32,28,0.78)', fontFamily: 'Rubik, sans-serif',
    color: '#fff6e6', opacity: 0, boxSizing: 'border-box' });
  stage.ov.appendChild(panel);
  const head = document.createElement('div'); Object.assign(head.style, { fontSize: '46px', fontWeight: 900, marginBottom: '12px' });
  const list = document.createElement('div'); Object.assign(list.style, { fontSize: '36px', fontWeight: 700, lineHeight: 1.35 });
  panel.appendChild(head); panel.appendChild(list);
  const rows = [];
  for (let k = 0; k < 4; k++) { const r = document.createElement('div'); list.appendChild(r); rows.push(r); }
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 7.4, 13.8], [0, 6.9, 12.9]], look: [[0, 2.4, -0.4]] });   // pawns in the lower half, panel above
    stage.camera.updateMatrixWorld();
    // the bot being described = the last one whose cue has started
    let cur = -1;
    pawns.forEach((pw, i) => { if (pw.b.at != null && t >= pw.b.at) cur = i; });
    pawns.forEach((pw, i) => {
      const k = ease((t - pw.appear) / 0.5);
      const focus = i === cur ? ease(clamp((t - pw.b.at) / 0.35)) : 0;
      const dim = cur >= 0 && i !== cur ? 1 : 0;
      pw.g.visible = k > 0.001;
      pw.g.position.set(pw.x, (1 - k) * 1.5 + focus * 0.35, focus * 1.4);
      pw.g.scale.setScalar(0.001 + k * (1 + focus * 0.3 - dim * 0.12));
      const [lx, ly] = stage.project(new THREE.Vector3(pw.x, 0, pw.g.position.z + 0.9));
      pw.lab.el.style.left = lx + 'px'; pw.lab.el.style.top = ly + 'px';
      pw.lab.el.style.opacity = fade(t, pw.appear + 0.2, 0.3) * (dim ? 0.5 : 1);
      pw.lab.el.style.color = i === cur ? pw.col : GN.text;
    });
    if (cur >= 0) {
      const b = pawns[cur].b;
      panel.style.opacity = Math.min(1, (t - b.at) / 0.25);
      head.textContent = b.name; head.style.color = pawns[cur].col;
      rows.forEach((r, k) => {
        const h = b.habits[k];
        if (!h) { r.textContent = ''; r.style.opacity = 0; return; }
        r.textContent = '\u2022 ' + h.text;
        const a = clamp((t - h.at) / 0.2);
        r.style.opacity = a; r.style.transform = `translateX(${(1 - a) * 18}px)`;
      });
    } else panel.style.opacity = 0;
    scrim(stage, t);
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
  const STEP = 2.9;
  groups.forEach(([tp, n, name], gi) => {
    const row = gi < 5 ? 0 : 1, col = row ? gi - 5 : gi, ncol = row ? 4 : 5;
    // centred rows (5 on top, 4 below); each pile's own fan is centred on its slot too
    const fanW = Math.min(n, 10) * 0.12;
    const gx = (col - (ncol - 1) / 2) * STEP - fanW / 2, gz = -1.5 + row * 3.5;
    const cards = [];
    for (let k = 0; k < n; k++) {
      const c = makeCard(stage, tp === 8 ? 8 + (k % 5) : tp, true);
      // neat fan: one angle per pile and a little air between cards (exactly-touching cards z-fight)
      c.position.set(gx + (k % 10) * 0.12, 0.016 + k * 0.033, gz + Math.floor(k / 10) * 0.45);
      c.rotation.y = -0.1; c.visible = false; cards.push(c);
    }
    const lab = stage.text({ text: `${n} × ${name}`, x: 0, y: 0, size: 28, weight: 900, font: 'rubik', color: GN.text, manual: true, align: 'center' });
    items.push({ cards, lab, gx: gx + fanW / 2, gz, at: 0.6 + gi * 0.35, tp });
  });
  title(stage, 'Original edition · 56 cards');
  // how many players? the deck depends on it (Kittens = players - 1)
  const g4 = spec.cues && spec.cues.g4;
  if (g4) stage.text({ text: 'With 4 players: 3 Kittens go in the deck', x: 960, y: 128, size: 30, weight: 700, font: 'rubik', align: 'center', at: g4[0] + 0.2, case: 'none', pill: 'rgba(244,234,213,0.92)', color: '#1b1209' });
  brand(stage);
  // the "zoom in": one card flies from its pile to front and centre, upright and big, then goes back
  const hero = makeCard(stage, 0, true); hero.visible = false; hero.traverse((o) => { o.castShadow = false; });
  const hl = spec.highlights || [];
  const HOLD = 1.5;
  return (t) => {
    stage.cameraAt(t, { pos: [[0, 13.2, 9.6], [0, 12.4, 8.8]], look: [[0, 0, 0.6]] });
    stage.camera.updateMatrixWorld();
    // which highlight is active
    let cur = null;
    for (const [g, t0] of hl) if (t >= t0 - 0.05 && t < t0 + HOLD + 0.5) cur = [g, t0];
    for (const it of items) {
      const k = ease((t - it.at) / 0.5);
      const active = cur && items[cur[0]] === it;
      it.cards.forEach((c, j) => { c.visible = k > 0; c.position.y = 0.016 + j * 0.033 + (1 - k) * 2; });
      const [lx, ly] = stage.project(new THREE.Vector3(it.gx, 0, it.gz + 1.5));
      it.lab.el.style.left = lx + 'px'; it.lab.el.style.top = ly + 'px';
      // while a card is up, only its own label stays (labels are drawn above the 3D card)
      const z = cur ? ease(clamp((t - cur[1]) / 0.25)) * (1 - ease(clamp((t - cur[1] - HOLD) / 0.4))) : 0;
      it.lab.el.style.opacity = fade(t, it.at + 0.2, 0.4) * (active ? 1 : 1 - z);
      it.lab.el.style.color = active ? GN.mustard : GN.text;
    }
    hero.visible = false;
    if (cur) {
      const it = items[cur[0]], u = t - cur[1];
      const up = ease(clamp(u / 0.35)), down = ease(clamp((u - HOLD) / 0.4));
      const k = up * (1 - down);
      if (k > 0.001) {
        hero.visible = true; hero.setFace(it.tp);
        hero.traverse((o) => { o.castShadow = false; o.receiveShadow = false; });
        const top = it.cards[it.cards.length - 1].position;
        // target: in front of the camera, upright (rotated to face it), big
        const target = new THREE.Vector3(0, 5.4, 4.2);
        hero.position.lerpVectors(new THREE.Vector3(top.x, top.y + 0.05, top.z), target, k);
        // face the camera: tip the card's face (+y) toward the camera (a positive turn about x)
        const cam = stage.camera.position, dy = cam.y - target.y, dz = cam.z - target.z;
        hero.rotation.set(Math.atan2(dz, dy) * k, -0.1 * (1 - k), 0);
        hero.scale.setScalar(1 + 1.05 * k);
      }
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
