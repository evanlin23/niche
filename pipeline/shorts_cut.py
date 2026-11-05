"""Cut vertical Shorts (1080x1920) out of a finished long video, each one pointing back to it.

Layout: hook headline on top, the 16:9 video full-width in the middle, big word-timed captions under it
(from the aligned script words), and "Full video on my channel" + Buh at the bottom. Audio = the long video's
own mix (voice + music), so nothing is re-recorded.

    python -m pipeline.shorts_cut episodes/<slug> [--video out/final/<slug>.mp4] [--only id ...]

Segments live in episodes/<slug>/shorts_cut.yaml:
    shorts:
      - id: kitten-placement
        from: k2            # first script line
        to: k5              # last script line (inclusive)
        hook: "Where do you put\\nthe Kitten back?"
        title: "..."        # YouTube title (also written to <id>.txt with the description)
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "pipeline" / "web" / "fonts"
W, H = 1080, 1920
VID_Y = 640                      # top of the 16:9 video (1080x608)
TOP, BOT = (40, 75, 65), (51, 95, 81)
CREAM, MUSTARD = (255, 246, 230), (242, 177, 52)


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"rubik-latin-{weight}.ttf"), size)


def background(hook, out):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    d.text((W // 2, 150), "BUH SIMULATES", font=font(700, 34), fill=(205, 191, 166), anchor="mm")
    lines = hook.split("\n")
    f = font(900, 92 if max(len(l) for l in lines) <= 18 else 78)
    y = 360 - (len(lines) - 1) * 55
    for i, l in enumerate(lines):
        d.text((W // 2, y + i * 110), l, font=f, fill=MUSTARD if i == len(lines) - 1 else CREAM, anchor="mm",
               stroke_width=4, stroke_fill=(20, 40, 34))
    # bottom call to action + Buh
    buh = Image.open(ROOT / "branding" / "buh-happy.png").convert("RGBA")
    bb = buh.getbbox(); buh = buh.crop((bb[0] + 150, bb[1] + 100, bb[2] - 150, bb[3] - 60))
    buh.thumbnail((260, 260))
    mask = Image.new("L", buh.size, 0); ImageDraw.Draw(mask).ellipse((0, 0, *buh.size), fill=255)
    im.paste(buh, (110, 1580), mask)
    d.text((410, 1650), "Full video", font=font(900, 64), fill=CREAM, anchor="lm")
    d.text((410, 1730), "on my channel", font=font(700, 52), fill=MUSTARD, anchor="lm")
    x = 410 + d.textlength("on my channel", font=font(700, 52)) + 28      # play arrow (no glyph in Rubik)
    d.polygon([(x, 1708), (x, 1752), (x + 38, 1730)], fill=MUSTARD)
    im.save(out)


def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def captions(words, out):
    """Words -> 1-3 word chunks, current chunk in big type under the video."""
    chunks, cur = [], []
    for w, a, b in words:
        cur.append((w, a, b))
        if len(cur) >= 3 or re.search(r"[.,!?;:]$", w) or sum(len(x[0]) for x in cur) > 14:
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    ev = []
    for i, c in enumerate(chunks):
        a = c[0][1]; b = chunks[i + 1][0][1] if i + 1 < len(chunks) else c[-1][2] + 0.4
        if b - c[-1][2] > 0.6:
            b = c[-1][2] + 0.35
        text = " ".join(x[0] for x in c).upper().replace("%", " PERCENT").strip()
        ev.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{text}")
    out.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Rubik Black,92,&H00E6F6FF,&H00E6F6FF,&H00223A31,&H64000000,1,0,0,0,100,100,0,0,1,7,0,8,60,60,{VID_Y + 608 + 90},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("--video"); ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    ep = Path(a.episode).resolve(); slug = ep.name
    video = Path(a.video) if a.video else ep / "out" / "final" / f"{slug}.mp4"
    timeline = json.loads((ep / "out" / "final" / "timeline.json").read_text())
    cues = {k: v for s in timeline for k, v in s["cues"].items()}
    order = [k for s in timeline for k in s["cues"]]
    spec = yaml.safe_load((ep / "shorts_cut.yaml").read_text())
    out = ep / "out" / "shorts"; out.mkdir(parents=True, exist_ok=True)
    for sh in spec["shorts"]:
        if a.only and sh["id"] not in a.only:
            continue
        ids = order[order.index(sh["from"]): order.index(sh["to"]) + 1]
        t0 = cues[ids[0]][0] - 0.15
        t1 = cues[ids[-1]][1] + sh.get("tail", 0.6)
        words = []
        for lid in ids:
            meta = json.loads((ep / "voice" / f"{lid}.json").read_text())
            for w in meta.get("aligned_words") or meta["words"]:
                words.append((w[0], cues[lid][0] + w[1] - t0, cues[lid][0] + w[2] - t0))
        bg = out / f"{sh['id']}-bg.png"; ass = out / f"{sh['id']}.ass"
        background(sh["hook"].replace("\\n", "\n"), bg); captions(words, ass)
        dst = out / f"{sh['id']}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", str(video),
                        "-loop", "1", "-i", str(bg), "-filter_complex",
                        f"[0:v]scale={W}:-2,setsar=1[v];[1:v][v]overlay=0:{VID_Y}:shortest=1,"
                        f"ass={ass}:fontsdir={FONTS},format=yuv420p[o];"
                        f"[0:a]afade=t=in:d=0.08,afade=t=out:st={t1 - t0 - 0.3:.3f}:d=0.3[a]",
                        "-map", "[o]", "-map", "[a]", "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)], check=True)
        (out / f"{sh['id']}.txt").write_text(f"{sh['title']}\n\n{sh.get('description', '')}\n")
        bg.unlink(); ass.unlink()
        print(f"{sh['id']}: {t1 - t0:.1f}s -> {dst}")


if __name__ == "__main__":
    main()
