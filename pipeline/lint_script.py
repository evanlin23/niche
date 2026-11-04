"""Lint a narration script (script.md) for AI tells and TTS problems.

    python -m pipeline.lint_script episodes/<slug>/script.md

Rules come from docs/script-style-guide.md. Exit code 1 if any ERROR.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from .timeline import LINE_RE

BANNED = [
    "delve", "dive in", "let's dive", "deep dive", "buckle up", "in today's video", "without further ado",
    "it's important to note", "it's worth noting", "in conclusion", "ultimately", "game-changer",
    "game changer", "unlock", "landscape", "tapestry", "navigate", "realm", "journey", "testament",
    "crucial", "pivotal", "furthermore", "moreover", "additionally", "the answer might surprise you",
    "here's the kicker", "mind-blowing", "mind blowing", "ever wondered", "at the end of the day",
    "seamless", "robust", "elevate", "harness", "embark", "whether you're a", "let's explore",
    "fascinating", "intricate", "plays a vital role", "a world where", "so next time you",
]
HEDGES = ["may potentially", "could arguably", "might possibly", "somewhat", "arguably", "it depends on your"]
TTS_SYMBOLS = re.compile(r"[$%/()\[\]&@#*_~<>]|\be\.g\.|\bi\.e\.|\bvs\b|\betc\b|\bapprox\b")
NOT_JUST = re.compile(r"\bnot (just|only)\b.*\bbut\b|\bisn't just\b|\bit's not just\b", re.I)
MAX_WORDS = 28


def lint(path: Path) -> int:
    lines = []
    for raw in Path(path).read_text().splitlines():
        m = LINE_RE.match(raw.strip())
        if m:
            lines.append((m.group(1), m.group(2)))
    errors = warns = 0
    not_just = 0
    words_total = 0

    def report(level, lid, msg):
        nonlocal errors, warns
        if level == "ERROR":
            errors += 1
        else:
            warns += 1
        print(f"{level:5s} [{lid}] {msg}")

    for lid, text in lines:
        low = text.lower()
        words_total += len(text.split())
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", low):
                report("ERROR", lid, f"banned phrase: '{b}'")
        for h in HEDGES:
            if h in low:
                report("WARN", lid, f"hedge: '{h}'")
        if "—" in text or " - " in text or "--" in text:
            report("WARN", lid, "dash: TTS reads it badly and it's an AI-ish rhythm; use a full stop or comma")
        sym = TTS_SYMBOLS.findall(text)
        if sym:
            report("ERROR", lid, f"symbols/abbreviations the voice will misread: {sorted(set(sym))}")
        if re.search(r"\d", re.sub(r"\b(19|20)\d\d\b", "", text)):   # years are fine
            report("WARN", lid, "digits: write numbers the way you'd say them ('fifty thousand')")
        for sent in re.split(r"(?<=[.!?])\s+", text):
            n = len(sent.split())
            if n > MAX_WORDS:
                report("WARN", lid, f"long sentence ({n} words): split it for breath")
        if NOT_JUST.search(text):
            not_just += 1
        if text.count("?") >= 2:
            report("WARN", lid, "stacked rhetorical questions")
    if not_just > 1:
        report("WARN", "-", f"'not just X but Y' used {not_just} times (max 1 per script)")
    if lines:
        first30 = " ".join(t for _, t in lines[:3])
        print(f"\n{len(lines)} lines, {words_total} words (~{words_total / 150:.1f} min at 150 wpm). "
              f"{errors} errors, {warns} warnings.")
        print(f"Hook check (first lines): \"{first30[:160]}...\"  -> is the verdict/answer stated here?")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(lint(Path(sys.argv[1])))
