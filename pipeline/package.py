"""Package an episode's simulation as a sellable, runnable "source pack" zip."""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(ep_dir: Path, out_dir: Path) -> Path:
    pack = ep_dir / "pack"
    files: dict[str, Path] = {}
    for p in (ROOT / "sims").glob("*.py"):
        files[f"sims/{p.name}"] = p
    for p in pack.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            files[str(p.relative_to(pack))] = p
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{ep_dir.name}-source-pack.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, p in sorted(files.items()):
            z.write(p, f"{ep_dir.name}/{arc}")
    return zpath
