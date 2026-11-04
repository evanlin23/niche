// Our own UNO-style card faces (no trademark oval/logo): flat colour, big centred value, small corner marks.
import { THREE, RoundedBoxGeometry } from '/pipeline/web/stage.js';
import { CARD } from '/pipeline/web/gamenight.js';

export const UCOL = ['#e5484d', '#f2b134', '#3fae6a', '#4c8dff', '#22252c'];   // red, yellow, green, blue, wild
const LABEL = { 10: '⊘', 11: '⇄', 12: '+2', 13: 'W', 14: '+4', 15: '⟳', 16: '✎' };
const _tex = {};

export function unoTexture(c, k) {
  const key = c + ':' + k;
  if (_tex[key]) return _tex[key];
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 356;
  const g = cv.getContext('2d');
  g.beginPath(); g.roundRect(0, 0, 256, 356, 24); g.clip();
  if (c === 'back') {
    g.fillStyle = '#22252c'; g.fillRect(0, 0, 256, 356);
    g.strokeStyle = '#f2b134'; g.lineWidth = 8; g.beginPath(); g.roundRect(18, 18, 220, 320, 16); g.stroke();
    g.fillStyle = '#f2b134'; g.font = '900 60px Rubik'; g.textAlign = 'center'; g.fillText('BUH', 128, 200);
  } else {
    g.fillStyle = UCOL[c]; g.fillRect(0, 0, 256, 356);
    if (c === 4) {   // wild: four colour quadrants in a circle
      ['#e5484d', '#f2b134', '#3fae6a', '#4c8dff'].forEach((col, i) => {
        g.fillStyle = col; g.beginPath(); g.moveTo(128, 178); g.arc(128, 178, 90, i * Math.PI / 2, (i + 1) * Math.PI / 2); g.fill();
      });
    }
    g.strokeStyle = 'rgba(255,255,255,0.85)'; g.lineWidth = 6; g.beginPath(); g.roundRect(14, 14, 228, 328, 16); g.stroke();
    const s = k <= 9 ? String(k) : LABEL[k];
    g.fillStyle = '#fff'; g.textAlign = 'center';
    g.font = `900 ${s.length > 1 ? 120 : 150}px Rubik`;
    g.shadowColor = 'rgba(0,0,0,0.35)'; g.shadowBlur = 8; g.fillText(s, 128, 230);
    g.shadowBlur = 0; g.font = '900 40px Rubik'; g.fillText(s, 40, 58); g.save(); g.translate(216, 300); g.rotate(Math.PI); g.fillText(s, 0, 0); g.restore();
  }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  _tex[key] = t; return t;
}

const _geo = new RoundedBoxGeometry(CARD.W, CARD.T, CARD.H, 2, 0.008);
const _face = new THREE.PlaneGeometry(CARD.W * 0.98, CARD.H * 0.98);
export function makeUno(stage, c, k) {
  const grp = new THREE.Group();
  const body = new THREE.Mesh(_geo, new THREE.MeshStandardMaterial({ color: 0xf4f1ea, roughness: 0.6 }));
  body.castShadow = true; body.receiveShadow = true; grp.add(body);
  const face = new THREE.Mesh(_face, new THREE.MeshStandardMaterial({ map: unoTexture(c, k), roughness: 0.5 }));
  face.rotation.x = -Math.PI / 2; face.position.y = CARD.T / 2 + 0.001; grp.add(face);
  grp.setFace = (c2, k2) => { face.material.map = unoTexture(c2, k2); face.material.needsUpdate = true; };
  stage.scene.add(grp);
  return grp;
}
