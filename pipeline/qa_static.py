"""Static gate: episode scene code may not build cards itself.

    python -m pipeline.qa_static [slug ...]          (default: every episode with web/*.js)

Every card, hand, pile, deck spread and held hand comes from the kit (pipeline/web/kit.js: kitCard + layerY + the
templates), which guarantees CARD_SEP between overlapping cards along their normal, polygon-offset faces and no
coplanar geometry. Hand-built cards in episode files are how flicker and interpenetration kept coming back, so any
of these in episodes/*/web/*.js fails:
  - importing / calling makeCard, makeDeck (gamenight.js) or makeUno (unocards.js)
  - card geometry: CARD.W / CARD.H / CARD.T, RoundedBoxGeometry or PlaneGeometry sized like a card
  - hand-picked stacking steps on cards (e.g. `k * 0.03` in a .position.set/.y of a card) -> use layerY()
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = [
    (re.compile(r"\b(makeCard|makeDeck|makeUno)\s*\("), "builds a card outside the kit (use kitCard / kit templates)"),
    (re.compile(r"import\s*{[^}]*\b(makeCard|makeDeck|makeUno)\b[^}]*}"), "imports a raw card builder (use kitCard from /pipeline/web/kit.js)"),
    (re.compile(r"\bCARD\.(W|H|T)\b"), "uses card geometry directly (stack with layerY / CARD_SEP from the kit)"),
    (re.compile(r"\b\w+\s*\*\s*0\.0[0-4]\d*\s*[,)].*\b(card|c)\b|\b(card|c)\.position\.(y|set)\([^)]*\*\s*0\.0[0-4]"),
     "hand-picked card stacking step (use layerY(i))"),
]


def check_file(p: Path):
    out = []
    for n, line in enumerate(p.read_text().splitlines(), 1):
        code = line.split("//")[0]
        for rx, why in RULES:
            if rx.search(code):
                out.append((n, why, line.strip()[:140]))
                break
    return out


def run(slugs=None):
    files = []
    eps = [ROOT / "episodes" / s for s in slugs] if slugs else sorted((ROOT / "episodes").iterdir())
    for ep in eps:
        files += sorted((ep / "web").glob("*.js")) if (ep / "web").is_dir() else []
    problems = {f: check_file(f) for f in files}
    bad = {f: v for f, v in problems.items() if v}
    lines = [f"STATIC CARD GATE: {len(files)} episode scene files", f"RESULT: {'FAIL' if bad else 'PASS'}", ""]
    for f, v in bad.items():
        lines.append(f"[{f.relative_to(ROOT)}]  {len(v)} problems")
        for n, why, src in v[:40]:
            lines.append(f"  line {n:4d}: {why}\n             {src}")
        if len(v) > 40:
            lines.append(f"  ... {len(v) - 40} more")
        lines.append("")
    print("\n".join(lines))
    return {str(f.relative_to(ROOT)): [{"line": n, "why": w} for n, w, _ in v] for f, v in bad.items()}


def main():
    raise SystemExit(1 if run(sys.argv[1:] or None) else 0)


if __name__ == "__main__":
    main()
