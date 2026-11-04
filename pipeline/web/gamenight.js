// "Warm game night" look: walnut table, felt mat, pendant-lamp lighting, our own card designs.
import { THREE, RoundedBoxGeometry, clamp, ease, fade } from '/pipeline/web/stage.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export const GN = {
  roomTop: '#3b2a20', roomEdge: '#0f0a08', wood: '#5b3a24', felt: '#1f5a46',
  cream: '#f4ead5', ink: '#22304a', brand: 'rgba(255,246,230,0.55)', scrim: '15,10,8', coral: '#ff6b57', mustard: '#f2b134', teal: '#2a9d8f',
  blue: '#4c8dff', plum: '#8e5a9e', red: '#d6403a', green: '#3fae6a', muted: '#cdbfa6', text: '#fff6e6',
};

// ------------------------------------------------------------------ room
function woodTexture() {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 1024;
  const g = c.getContext('2d');
  g.fillStyle = GN.wood; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 260; i++) {
    const y = Math.random() * 1024, a = 0.03 + Math.random() * 0.08;
    g.strokeStyle = Math.random() < 0.5 ? `rgba(30,15,6,${a})` : `rgba(255,220,170,${a * 0.6})`;
    g.lineWidth = 1 + Math.random() * 5;
    g.beginPath();
    for (let x = 0; x <= 1024; x += 16) g.lineTo(x, y + Math.sin(x / 140 + i) * 6 + Math.sin(x / 37 + i * 3) * 1.5);
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3); return t;
}
function feltTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d'); g.fillStyle = GN.felt; g.fillRect(0, 0, 512, 512);
  const img = g.getImageData(0, 0, 512, 512);
  for (let i = 0; i < img.data.length; i += 4) { const n = (Math.random() - 0.5) * 16; img.data[i] += n; img.data[i + 1] += n; img.data[i + 2] += n; }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(4, 3); return t;
}

// Seeded random so every frame/run builds an identical room
let _seed = 1;
const rnd = () => { _seed = (_seed * 16807) % 2147483647; return _seed / 2147483647; };

export const LOOKS = {
  'clean-light': { bg: '#ece6dc', floor: '#e9e2d6', text: '#1f2633', muted: '#6c6a66', brand: 'rgba(31,38,51,0.5)', scrim: '236,230,220', bar: '#d9cfbf' },
  'clean-ink':   { bg: '#151c27', floor: '#18202c', text: '#f5f1ea', muted: '#9aa3b2', brand: 'rgba(245,241,234,0.5)', scrim: '21,28,39', bar: '#e8e1d4' },
  'clean-sage':  { bg: '#2f4a46', floor: '#33504b', text: '#f6f2ea', muted: '#b9c8c2', brand: 'rgba(246,242,234,0.55)', scrim: '47,74,70', bar: '#efe7d8' },
};

function cleanRoom(stage, L) {
  const S = stage.scene;
  S.background = new THREE.Color(L.bg);
  S.fog = new THREE.Fog(L.bg, 22, 48);
  Object.assign(GN, { text: L.text, muted: L.muted, cream: L.bar, brand: L.brand, scrim: L.scrim });
  S.add(new THREE.HemisphereLight(0xffffff, new THREE.Color(L.bg), 1.1));
  const key = new THREE.DirectionalLight(0xfff4e6, 2.2);
  key.position.set(-6, 18, 10); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 10; key.shadow.blurSamples = 12; key.shadow.bias = -0.0005;
  Object.assign(key.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 60 });
  S.add(key);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: L.floor, roughness: 1 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; S.add(floor);
  if (stage.spec.quality === 'high') {
    const pm = new THREE.PMREMGenerator(stage.renderer);
    S.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; S.environmentIntensity = 0.25;
  }
  stage.renderer.shadowMap.type = THREE.VSMShadowMap;
  return { floor };
}

export function buildRoom(stage, { feltW = 16, feltD = 10 } = {}) {
  const S = stage.scene;
  const look = LOOKS[stage.spec.look];
  if (look) return cleanRoom(stage, look);
  _seed = 7; const mr = Math.random; Math.random = rnd;
  const cv = document.createElement('canvas'); cv.width = cv.height = 1024;
  const g = cv.getContext('2d');
  const gr = g.createRadialGradient(512, 380, 30, 512, 512, 760);
  gr.addColorStop(0, GN.roomTop); gr.addColorStop(1, GN.roomEdge);
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  const bg = new THREE.CanvasTexture(cv); bg.colorSpace = THREE.SRGBColorSpace; S.background = bg;
  if (stage.spec.quality === 'high') {   // studio reflections for glossy materials
    const pm = new THREE.PMREMGenerator(stage.renderer);
    S.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    S.environmentIntensity = 0.35;
  }
  S.add(new THREE.HemisphereLight(0xffe9cc, 0x2a1a10, 0.55));
  const lamp = new THREE.SpotLight(0xffd9a8, 1400, 0, Math.PI / 4.2, 0.75, 1.7);
  lamp.position.set(0, 20, 3); lamp.castShadow = true; lamp.shadow.mapSize.set(stage.spec.quality === 'high' ? 4096 : 2048, stage.spec.quality === 'high' ? 4096 : 2048);
  lamp.shadow.radius = 6; lamp.shadow.bias = -0.0004; lamp.shadow.camera.near = 5; lamp.shadow.camera.far = 50;
  S.add(lamp); S.add(lamp.target);
  const fill = new THREE.DirectionalLight(0x9fb4ff, 0.35); fill.position.set(-10, 8, 12); S.add(fill);
  const table = new THREE.Mesh(new RoundedBoxGeometry(feltW + 6, 0.6, feltD + 6, 4, 0.25),
    new THREE.MeshStandardMaterial({ map: woodTexture(), roughness: 0.55, metalness: 0.05 }));
  table.position.y = -0.3; table.receiveShadow = true; S.add(table);
  const felt = new THREE.Mesh(new RoundedBoxGeometry(feltW, 0.06, feltD, 4, 0.03),
    new THREE.MeshStandardMaterial({ map: feltTexture(), roughness: 1 }));
  felt.position.y = 0.03; felt.receiveShadow = true; S.add(felt);
  Math.random = mr;
  return { table, felt, lamp };
}

// ------------------------------------------------------------------ cards (our own designs)
export const CARDS = {
  0: { name: 'EXPLODING\nKITTEN', band: '#1b1b1b', bg: '#2a2a2a', fg: GN.coral, icon: 'bomb' },
  1: { name: 'DEFUSE', band: GN.green, icon: 'check' },
  2: { name: 'ATTACK', band: GN.coral, icon: 'arrow2' },
  3: { name: 'SKIP', band: GN.blue, icon: 'skip' },
  4: { name: 'FAVOR', band: GN.plum, icon: 'heart' },
  5: { name: 'SHUFFLE', band: '#9c6b3f', icon: 'shuffle' },
  6: { name: 'NOPE', band: GN.red, icon: 'x' },
  7: { name: 'SEE THE\nFUTURE', band: '#6c5ce7', icon: 'eye' },
  8: { name: 'CAT', band: GN.mustard, icon: 'paw' }, 9: { name: 'CAT', band: GN.mustard, icon: 'paw' },
  10: { name: 'CAT', band: GN.mustard, icon: 'paw' }, 11: { name: 'CAT', band: GN.mustard, icon: 'paw' },
  12: { name: 'CAT', band: GN.mustard, icon: 'paw' },
};
const _tex = {};
function drawIcon(g, kind, x, y, r, col) {
  g.save(); g.strokeStyle = col; g.fillStyle = col; g.lineWidth = r * 0.22; g.lineCap = g.lineJoin = 'round';
  g.beginPath();
  switch (kind) {
    case 'bomb': g.arc(x, y + r * 0.1, r * 0.75, 0, 7); g.fill(); g.beginPath(); g.moveTo(x + r * 0.4, y - r * 0.5); g.quadraticCurveTo(x + r * 0.9, y - r * 1.1, x + r * 1.1, y - r * 0.8); g.stroke(); break;
    case 'check': g.moveTo(x - r * 0.7, y); g.lineTo(x - r * 0.15, y + r * 0.55); g.lineTo(x + r * 0.8, y - r * 0.6); g.stroke(); break;
    case 'arrow2': for (const dx of [-0.35, 0.35]) { g.moveTo(x + (dx - 0.35) * r, y - r * 0.6); g.lineTo(x + (dx + 0.25) * r, y); g.lineTo(x + (dx - 0.35) * r, y + r * 0.6); } g.stroke(); break;
    case 'skip': g.moveTo(x - r * 0.6, y - r * 0.6); g.lineTo(x + r * 0.1, y); g.lineTo(x - r * 0.6, y + r * 0.6); g.moveTo(x + r * 0.5, y - r * 0.6); g.lineTo(x + r * 0.5, y + r * 0.6); g.stroke(); break;
    case 'heart': g.moveTo(x, y + r * 0.7); g.bezierCurveTo(x - r * 1.2, y - r * 0.1, x - r * 0.5, y - r * 1.0, x, y - r * 0.35); g.bezierCurveTo(x + r * 0.5, y - r * 1.0, x + r * 1.2, y - r * 0.1, x, y + r * 0.7); g.fill(); break;
    case 'shuffle': g.moveTo(x - r * 0.8, y - r * 0.5); g.bezierCurveTo(x, y - r * 0.5, x, y + r * 0.5, x + r * 0.8, y + r * 0.5); g.moveTo(x - r * 0.8, y + r * 0.5); g.bezierCurveTo(x, y + r * 0.5, x, y - r * 0.5, x + r * 0.8, y - r * 0.5); g.stroke(); break;
    case 'x': g.moveTo(x - r * 0.6, y - r * 0.6); g.lineTo(x + r * 0.6, y + r * 0.6); g.moveTo(x + r * 0.6, y - r * 0.6); g.lineTo(x - r * 0.6, y + r * 0.6); g.stroke(); break;
    case 'eye': g.moveTo(x - r, y); g.quadraticCurveTo(x, y - r * 0.9, x + r, y); g.quadraticCurveTo(x, y + r * 0.9, x - r, y); g.stroke(); g.beginPath(); g.arc(x, y, r * 0.3, 0, 7); g.fill(); break;
    case 'paw': g.arc(x, y + r * 0.25, r * 0.45, 0, 7); g.fill(); for (const [dx, dy] of [[-0.55, -0.35], [-0.2, -0.7], [0.2, -0.7], [0.55, -0.35]]) { g.beginPath(); g.arc(x + dx * r, y + dy * r, r * 0.17, 0, 7); g.fill(); } break;
  }
  g.restore();
}
export function cardTexture(type) {
  const key = type === 'back' ? 'back' : String(type);
  if (_tex[key]) return _tex[key];
  const c = document.createElement('canvas'); c.width = 256; c.height = 356;
  const g = c.getContext('2d');
  const r = 26;
  g.beginPath(); g.roundRect(0, 0, 256, 356, r); g.clip();
  if (type === 'back') {
    g.fillStyle = GN.ink; g.fillRect(0, 0, 256, 356);
    g.strokeStyle = 'rgba(244,234,213,0.5)'; g.lineWidth = 6; g.beginPath(); g.roundRect(16, 16, 224, 324, 18); g.stroke();
    g.fillStyle = GN.mustard; g.font = '900 58px Rubik'; g.textAlign = 'center'; g.fillText('BUH', 128, 198);
  } else {
    const d = CARDS[type];
    g.fillStyle = d.bg || GN.cream; g.fillRect(0, 0, 256, 356);
    g.fillStyle = d.band; g.fillRect(0, 0, 256, 92);
    drawIcon(g, d.icon, 128, 210, 62, d.fg || d.band);
    g.fillStyle = type === 0 ? GN.coral : '#fff'; g.font = '900 30px Rubik'; g.textAlign = 'center';
    const lines = d.name.split('\n');
    lines.forEach((l, i) => g.fillText(l, 128, (lines.length > 1 ? 40 : 58) + i * 32));
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  _tex[key] = t; return t;
}

const CW = 0.9, CH = 1.26, CT = 0.02;
// card body = rounded rectangle (same corner radius as the printed face), extruded to the card's thickness.
// A box with square corners showed cream corners behind the rounded face art.
const CR = 0.09;   // 26 px of the 256 px card art
function _roundedCardGeo() {
  const w = CW / 2, h = CH / 2, r = CR, sh = new THREE.Shape();
  sh.moveTo(-w + r, -h); sh.lineTo(w - r, -h); sh.quadraticCurveTo(w, -h, w, -h + r);
  sh.lineTo(w, h - r); sh.quadraticCurveTo(w, h, w - r, h); sh.lineTo(-w + r, h);
  sh.quadraticCurveTo(-w, h, -w, h - r); sh.lineTo(-w, -h + r); sh.quadraticCurveTo(-w, -h, -w + r, -h);
  const g = new THREE.ExtrudeGeometry(sh, { depth: CT, bevelEnabled: false, curveSegments: 6 });
  g.translate(0, 0, -CT / 2); g.rotateX(-Math.PI / 2);      // lie flat: thickness along y, centred
  g.computeVertexNormals();
  return g;
}
const _cardGeo = _roundedCardGeo();
const _faceGeo = new THREE.PlaneGeometry(CW * 0.98, CH * 0.98);
export function makeCard(stage, type, faceUp = true) {
  const grp = new THREE.Group();
  const body = new THREE.Mesh(_cardGeo, new THREE.MeshStandardMaterial({ color: 0xf1e7d0, roughness: 0.6 }));
  body.castShadow = true; body.receiveShadow = true; grp.add(body);
  const face = new THREE.Mesh(_faceGeo, new THREE.MeshStandardMaterial({ map: cardTexture(faceUp ? type : 'back'), roughness: 0.55, transparent: true }));
  face.rotation.x = -Math.PI / 2; face.position.y = CT / 2 + 0.001; grp.add(face);
  grp.userData = { face, type };
  grp.setFace = (tp) => { face.material.map = cardTexture(tp); face.material.needsUpdate = true; };
  stage.scene.add(grp);
  return grp;
}
export const CARD = { W: CW, H: CH, T: CT };

// a deck: n stacked cards (backs up). setCount(n) shows/hides cards.
export function makeDeck(stage, pos, max = 60) {
  const cards = [];
  for (let i = 0; i < max; i++) {
    const c = makeCard(stage, 'back', false);
    c.position.set(pos[0] + Math.sin(i * 2.1) * 0.012, 0.07 + i * (CT + 0.004), pos[2] + Math.cos(i * 1.7) * 0.012);
    c.rotation.y = Math.sin(i * 1.3) * 0.03;
    cards.push(c);
  }
  return { cards, pos, setCount(n) { cards.forEach((c, i) => (c.visible = i < n)); }, topY(n) { return 0.07 + n * (CT + 0.004); } };
}

// ------------------------------------------------------------------ 3D bar chart on the felt
// items: [{label, value, color, at}] values in %, fair: % line. Returns update(t) + label anchors.
export function makeBars(stage, items, { x0 = -6, width = 12, maxV = 60, height = 6, z = 0, fair = null, unit = '%', fairSide = 'right' } = {}) {
  const n = items.length, gap = width / n, bw = Math.min(1.6, gap * 0.62);
  const bars = items.map((it, i) => {
    const hq = stage.spec.quality === 'high';
    const m = new THREE.Mesh(new RoundedBoxGeometry(bw, 1, bw, hq ? 6 : 3, hq ? 0.12 : 0.08),
      hq ? new THREE.MeshPhysicalMaterial({ color: (it.color === '#f4ead5' ? GN.cream : it.color) || GN.cream, roughness: 0.32, clearcoat: 0.6, clearcoatRoughness: 0.25 })
         : new THREE.MeshStandardMaterial({ color: (it.color === '#f4ead5' ? GN.cream : it.color) || GN.cream, roughness: 0.45 }));
    m.position.set(x0 + gap * (i + 0.5), 0, z); m.castShadow = true; m.receiveShadow = true; m.scale.y = 0.001;
    stage.scene.add(m);
    const vt = stage.text({ text: `${it.value.toFixed(1)}${unit}`, x: 0, y: 0, size: 44, weight: 900, font: 'rubik', color: GN.text, align: 'center', manual: true });
    const lt = stage.text({ text: it.label, x: 0, y: 0, size: 26, weight: 700, font: 'rubik', color: GN.muted, align: 'center', manual: true, width: Math.max(180, gap * 95) });
    return { m, it, vt, lt, at: stage.at(it.at, 0) };
  });
  let fairMesh = null, fairText = null;
  if (fair != null) {
    fairMesh = new THREE.Mesh(new THREE.BoxGeometry(width + 0.6, 0.03, 0.05), new THREE.MeshStandardMaterial({ color: GN.text, emissive: GN.text, emissiveIntensity: 0.4 }));
    fairMesh.position.set(x0 + width / 2, fair / maxV * height, z + bw / 2 + 0.05); stage.scene.add(fairMesh);
    fairText = stage.text({ text: `fair share ${fair.toFixed(0)}${unit}`, x: 0, y: 0, size: 26, weight: 700, font: 'rubik', color: GN.text, manual: true });
  }
  return {
    update(t) {
      for (const b of bars) {
        const k = ease((t - b.at) / 0.9);
        const h = Math.max(0.001, b.it.value / maxV * height * k);
        b.m.scale.y = h; b.m.position.y = h / 2; b.m.visible = k > 0.002;
        const [sx, sy] = stage.project(new THREE.Vector3(b.m.position.x, h + 0.25, z));
        const [lx, ly] = stage.project(new THREE.Vector3(b.m.position.x, 0, z + bw / 2 + 0.3));
        const a = fade(t, b.at, 0.4);
        b.vt.el.style.left = sx + 'px'; b.vt.el.style.top = sy - 56 + 'px'; b.vt.el.style.opacity = a;
        b.vt.el.textContent = `${(b.it.value * Math.min(1, k * 1.02)).toFixed(1)}${unit}`;
        b.vt.el.style.color = b.it.hl ? GN.mustard : GN.text;
        b.lt.el.style.left = lx + 'px'; b.lt.el.style.top = ly + 4 + 'px'; b.lt.el.style.opacity = a;
      }
      if (fairMesh) {
        const fxw = fairSide === 'left' ? x0 - 0.15 : x0 + width + 0.2;
        const [fx, fy] = stage.project(new THREE.Vector3(fxw, fair / maxV * height, z + bw / 2 + 0.05));
        const fw = fairText.el.offsetWidth, safe = stage.W * 0.05;
        // beside the end of the line when it fits in the title-safe area, else above the line's end
        const beside = fairSide === 'left' ? fx - 14 - fw >= safe : fx + 14 + fw <= stage.W - safe;
        let lx = fairSide === 'left' ? (beside ? fx - 14 - fw : fx) : (beside ? fx + 14 : fx - fw);
        lx = Math.max(safe, Math.min(stage.W - safe - fw, lx));
        fairText.el.style.left = lx + 'px'; fairText.el.style.top = fy + (beside ? -16 : -40) + 'px';
        const a = fade(t, bars.length ? Math.min(...bars.map((b) => b.at)) : 0, 0.5);
        fairText.el.style.opacity = a; fairMesh.visible = a > 0.01;
      }
    },
  };
}
