"""Print a recording script (one numbered line per audio file) for an episode.

    python -m pipeline.recording_script episodes/<slug>
"""
import re
import sys
from pathlib import Path

ep = Path(sys.argv[1])
src = (ep / "script.md").read_text()
out = [f"RECORDING SCRIPT: {src.splitlines()[0].lstrip('# ').strip()}", "",
       "How to record",
       "- One file per line, named exactly as the id in brackets, e.g. h1.m4a, h2.m4a.",
       "- Phone voice memos are fine. Quiet room (closet full of clothes = great), phone ~20 cm away, same spot every time.",
       "- Leave a second of silence before and after; the pipeline trims it.",
       "- Re-word anything that doesn't sound like you. If you change a line, change it in script.md too",
       "  (captions use the script text). Then run `make lint-script SLUG=" + ep.name + "`.",
       f"- Put the files in {ep}/voice/ and render with:",
       f"    TTS_ENGINE=recorded VOICE_DIR={ep}/voice make episode SLUG={ep.name}",
       "- Lines you skip are filled in with the AI voice, so you can do a few at a time.", ""]
for line in src.splitlines():
    if line.startswith("## ") and "source" not in line.lower():
        out += ["", line[3:].upper()]
    m = re.match(r"^\[([\w-]+)\] (.+)$", line)
    if m:
        out.append(f"[{m.group(1)}]  {m.group(2)}")
dest = Path("docs") / f"recording-script-{ep.name}.txt"
dest.write_text("\n".join(out) + "\n")
print("wrote", dest)
