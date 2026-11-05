"""Scene kit, Python side: turns a scenes.yaml scene into a stage spec for pipeline/web/kit.js.

* Word anchors ('k5@thirty', 'k5@thirty#2', 'k5@first_card+0.3', 'k5', 'k5:end') are resolved to scene seconds from
  the force-aligned voice; every resolved anchor is logged in spec['qa']['anchors'] (and each dict that had an
  anchored 'at' keeps it as 'at_ref') so the QA gates can check coverage and on-screen numbers.
* Data refs: any value written as '=file.json:path.to.value*100' is read from episodes/<slug>/data/ (lists can be
  filtered: '=results.json:random_play[value=0.15].win*100'). Numbers on screen never get typed by hand.
* Statement lines appear when their first word is spoken; deck piles light up when their name is said
  (params.name_words: {kitten: 0, defuse: 1, ...}).

An episode that only uses the kit needs no sim/scenes3d.py at all (cli falls back to kit.build_spec with the
module /pipeline/web/kit.js, or the episode's own web/scenes.js if it exists).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
ANCHOR_RE = re.compile(r"^(\w+)@([\w']+)(?:#(\d+))?([+-][\d.]+)?$")
PLAIN_RE = re.compile(r"^(\w+)(:end)?([+-][\d.]+)?$")
norm = lambda w: re.sub(r"[^a-z0-9']", "", str(w).lower())


class AnchorError(KeyError):
    pass


def resolve_at(scene, ref):
    """Anchor -> scene seconds. Numbers pass through. Raises AnchorError when the line/word is missing."""
    if ref is None or isinstance(ref, (int, float)):
        return ref
    ref = str(ref)
    m = ANCHOR_RE.match(ref)
    if m:
        lid, word, nth, off = m.group(1), m.group(2), int(m.group(3) or 1), float(m.group(4) or 0)
        cue = scene.cues.get(lid)
        if cue is None:
            raise AnchorError(f"anchor {ref}: line {lid} is not in scene {scene.id}")
        seq = [norm(x) for x in word.split("_")]
        ws = [(norm(w), t0) for w, t0, _ in cue.words]
        hits = [ws[i][1] for i in range(len(ws) - len(seq) + 1) if [w for w, _ in ws[i:i + len(seq)]] == seq]
        if len(hits) < nth:
            raise AnchorError(f"anchor {ref}: '{word.replace('_', ' ')}' (#{nth}) not spoken in {lid}: "
                              f"{' '.join(w for w, _ in ws)}")
        return round(hits[nth - 1] + off, 3)
    m = PLAIN_RE.match(ref)
    if m and m.group(1) in scene.cues:
        c = scene.cues[m.group(1)]
        return round((c.end if m.group(2) else c.start) + float(m.group(3) or 0), 3)
    raise AnchorError(f"anchor {ref}: not a line of scene {scene.id}")


def is_anchor(s) -> bool:
    return isinstance(s, str) and bool(ANCHOR_RE.match(s))


def line_of(ref: str) -> str | None:
    m = ANCHOR_RE.match(ref) or PLAIN_RE.match(ref)
    return m.group(1) if m else None


# ------------------------------------------------------------------ data refs
def data_ref(ep: Path, s: str):
    """'=file.json:a.b[k=v].c*100' -> number (rounded to 1 decimal unless ')/round' given)."""
    m = re.match(r"^=([\w./-]+):([^*/]+)(?:\*([\d.]+))?(?:/round(\d))?$", s)
    if not m:
        raise ValueError(f"bad data ref {s}")
    obj = json.loads((ep / "data" / m.group(1)).read_text())
    for part in re.findall(r"[^.\[\]]+|\[[^\]]+\]", m.group(2)):
        if part.startswith("["):
            k, v = part[1:-1].split("=", 1)
            cand = [x for x in obj if str(x.get(k)) == v or (_num(v) is not None and _num(x.get(k)) == _num(v))]
            if not cand:
                raise KeyError(f"{s}: no element with {k}={v}")
            obj = cand[0]
        elif isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    val = float(obj) * float(m.group(3) or 1)
    return round(val, int(m.group(4) if m.group(4) is not None else 1))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ resolution with a QA log
class Resolver:
    def __init__(self, scene, ep: Path):
        self.scene, self.ep = scene, ep
        self.anchors, self.errors = [], []

    def at(self, ref, path="", drop_on_error=False):
        try:
            v = resolve_at(self.scene, ref)
        except AnchorError as e:
            self.errors.append({"ref": ref, "path": path, "error": str(e)})
            if drop_on_error:
                return None
            raise
        if isinstance(ref, str):
            self.anchors.append({"ref": ref, "t": v, "line": line_of(ref), "path": path})
        return v

    def all(self, obj, path=""):
        if isinstance(obj, str):
            if obj.startswith("=") and ":" in obj:
                return data_ref(self.ep, obj)
            if is_anchor(obj):
                return self.at(obj, path, drop_on_error=True)
            return obj
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k in ("at", "until") and isinstance(v, str) and (is_anchor(v) or PLAIN_RE.match(v)):
                    r = self.at(v, f"{path}.{k}", drop_on_error=True)
                    if r is None:
                        return None                      # the whole item is dropped (and reported)
                    out[k] = r
                    if k == "at":
                        out["at_ref"] = v
                else:
                    out[k] = self.all(v, f"{path}.{k}")
            return out
        if isinstance(obj, list):
            res = [self.all(x, f"{path}[{i}]") for i, x in enumerate(obj)]
            return [x for x in res if x is not None]
        return obj


def statement_lines(scene, lines, R: Resolver | None = None):
    """Display lines appear when the narration reaches each line's first word (or an explicit 'at' anchor)."""
    words = [w for c in scene.cues.values() for w in c.words]
    out, i = [], 0
    for ln in lines:
        ln = ln if isinstance(ln, dict) else {"text": ln}
        first = norm(str(ln["text"]).split()[0])
        j = i
        while j < len(words) and norm(words[j][0]) != first:
            j += 1
        at = words[j][1] if j < len(words) else (words[i][1] if i < len(words) else 0.3)
        if j < len(words):
            i = j + 1
        if isinstance(ln.get("at"), str):
            r = R.at(ln["at"], "lines", drop_on_error=True) if R else resolve_at(scene, ln["at"])
            if r is not None:
                at = r + 0.05
        elif isinstance(ln.get("at"), (int, float)):
            at = ln["at"] + 0.05
        out.append({"text": ln["text"], "at": round(max(0.05, at - 0.05), 3), "color": ln.get("color")})
    if out and out[0]["at"] > 0.3:            # never open on an empty floor
        out[0]["at"] = 0.05
    return out


def name_hits(scene, name_words: dict, min_gap=1.6):
    """Every time the narration names a pile ({word: pileIndex}), that pile is highlighted: [[pile, t], ...]."""
    hits = []
    for c in scene.cues.values():
        seen = set()
        for w, t0, _ in c.words:
            k = name_words.get(norm(w))
            if k is not None and k not in seen:
                seen.add(k); hits.append([k, round(t0, 3)])
    hits.sort(key=lambda x: x[1])
    out, last = [], -9
    for k, t0 in hits:
        if t0 - last >= min_gap:
            out.append([k, t0]); last = t0
    return out


def look(ep: Path) -> dict:
    cfg = yaml.safe_load((ep / "scenes.yaml").read_text())
    return {"look": cfg.get("look"), "quality": cfg.get("quality", "normal"), "grade": cfg.get("grade"),
            "ssaa": float(os.environ.get("RENDER_SSAA", cfg.get("ssaa", 1)))}


def module_for(ep: Path) -> str:
    own = ep / "web" / "scenes.js"
    return f"/episodes/{ep.name}/web/scenes.js" if own.exists() else "/pipeline/web/kit.js"


def build_spec(ctx, module: str | None = None, charts: dict | None = None) -> dict:
    """Generic spec for a kit scene. `charts` = optional {name: fn() -> chart dict} for params.chart: <name>."""
    ep, sc = Path(ctx.ep_dir), ctx.scene
    n = max(1, int(round(sc.duration * FPS)))
    R = Resolver(sc, ep)
    params = dict(sc.params or {})
    s = {"module": module or module_for(ep), "type": sc.render, "W": ctx.fmt.width, "H": ctx.fmt.height, "fps": FPS,
         "duration": sc.duration, "n_frames": n, "id": sc.id, "theme": "custom", "font": "rubik",
         "cues": {k: [c.start, c.end] for k, c in sc.cues.items()}, "captions": ctx.captions, "hook": ctx.hook,
         **look(ep)}
    for k in ("fade_in", "fade_out"):
        if k in params:
            s[k] = params[k]
    if sc.render in ("statement", "title"):
        s["lines"] = statement_lines(sc, params.get("lines", []), R)
    if sc.render == "deck" and params.get("name_words") and not params.get("highlights"):
        params["highlights"] = name_hits(sc, {norm(k): v for k, v in params["name_words"].items()})
    ch = params.get("chart")
    if isinstance(ch, str):
        if not charts or ch not in charts:
            raise KeyError(f"scene {sc.id}: chart '{ch}' is not defined")
        params["chart"] = charts[ch]()
    if isinstance(params.get("plan"), list):    # [[anchor, slot], ...]
        params["plan"] = [[R.at(a, "plan", drop_on_error=True), slot] for a, slot in params["plan"]]
        params["plan"] = [x for x in params["plan"] if x[0] is not None]
    for key in ("highlight", "seat_hl", "out"):  # [[seat, anchor], ...]
        if isinstance(params.get(key), list) and params[key] and isinstance(params[key][0], list):
            params[key] = [[a, R.at(b, key, drop_on_error=True)] for a, b in params[key]]
            params[key] = [x for x in params[key] if x[1] is not None]
    s["params"] = R.all(params, "params")
    if "chart" in s["params"]:
        s["chart"] = s["params"]["chart"]
    if getattr(ctx, "short", None):
        s["short"] = ctx.short
    s["qa"] = {"anchors": R.anchors, "anchor_errors": R.errors}
    for e in R.errors:
        print(f"  ANCHOR {sc.id}: {e['error']}", flush=True)
    return s
