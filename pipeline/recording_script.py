"""Print a recording script (one numbered line per audio file) for an episode.

    python -m pipeline.recording_script episodes/<slug>
"""
import re
import sys
from pathlib import Path

ep = Path(sys.argv[1])
src = (ep / "script.md").read_text()
out = [f"RECORDING SCRIPT: {src.splitlines()[0].lstrip('# ').strip()}", "",
       "How to record (one long take is easiest)",
       "- Pixel Recorder, phone ~15-20 cm from your mouth, quiet room (a closet is great), away from windows.",
       "- Start with ~10 seconds of silence (room tone, used for noise cleanup).",
       "- Read top to bottom with a 1-2 second pause between lines.",
       "- Mess up? Pause, then redo the whole sentence. The LAST take wins automatically.",
       "- Say every number exactly as written ('percent' included). Slow down a touch on punchlines.",
       "- Send me the file; I split it, clean it and drop it into the video.", ""]
for line in src.splitlines():
    if line.startswith("## ") and "source" not in line.lower():
        out += ["", line[3:].upper()]
    m = re.match(r"^\[([\w-]+)\] (.+)$", line)
    if m:
        out.append(f"[{m.group(1)}]  {m.group(2)}")
dest = Path("docs") / f"recording-script-{ep.name}.txt"
dest.write_text("\n".join(out) + "\n")
print("wrote", dest)
