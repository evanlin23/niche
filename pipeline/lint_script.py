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
    # Wikipedia "Signs of AI writing" (significance inflation, copula avoidance, AI vocabulary)
    "stands as", "serves as", "a testament", "a reminder that", "underscores", "underscoring", "highlighting",
    "showcasing", "fostering", "boasts", "key role", "vital role", "pivotal moment", "evolving", "indelible",
    "deeply rooted", "setting the stage", "broader", "nuanced", "multifaceted", "notably", "comprehensive",
    "meticulous", "vibrant", "profound", "intriguing", "invaluable", "paramount", "showcase",
    # spoken-script tics
    "here's the thing", "here's where it gets interesting", "let's break it down", "let's break that down",
    "spoiler alert", "plot twist", "and honestly", "the truth is", "simply put", "in short", "bottom line",
    "the bottom line", "it turns out that", "make no mistake", "think about that", "let that sink in",
    "and that's the key", "that changes everything", "genuinely", "truly", "incredibly",
]
HEDGES = ["may potentially", "could arguably", "might possibly", "somewhat", "arguably", "it depends on your"]
TTS_SYMBOLS = re.compile(r"[$%/()\[\]&@#*_~<>]|\be\.g\.|\bi\.e\.|\bvs\b|\betc\b|\bapprox\b")
NOT_JUST = re.compile(r"\bnot (just|only)\b.*\bbut\b|\bisn't just\b|\bit's not just\b", re.I)
MAX_WORDS = 28
NEG_PARALLEL = re.compile(r"\b(that's|it's|this is|isn't) not (a |an |the |about )?\w+[^.?!]*[.,;]\s*(it's|that's|this is)\b"
                          r"|\bnot because\b[^.?!]*\bbut because\b|\brather than\b", re.I)
REVEAL_Q = re.compile(r"(^|[.!]\s+)(the (answer|result|catch|twist|reason|winner)|why|so what)\?\s", re.I)
ING_TAIL = re.compile(r",\s+(making|showing|proving|meaning|giving|leaving|turning|ensuring|highlighting|creating)\s+[^.?!]*[.!]$", re.I)
LABEL = re.compile(r"^(spoiler|confession|plot twist|twist|update|warning|one limitation|one catch|fun fact|"
                   r"side note|quick note|the catch|the verdict|the result|the problem|translation)\.?$", re.I)
HERES = re.compile(r"\bhere's (why|how|what|the|my|a|where|when)\b", re.I)
THE_ONE = re.compile(r"\bis the (\w+ )?(one|thing)\b[.!]", re.I)
QUIP = re.compile(r"^(bring snacks|hold onto that( one)?|you heard that right|no pressure|go figure|wild|yikes|oof)[.!]?$", re.I)
ANTI = re.compile(r"\b(doesn't|does not|isn't|is not|won't|can't)\b[^.?!]{0,60}[.!]\s+(it|that|this)( just| only)? \w+", re.I)
TRICOLON = re.compile(r"\b\w+(?: \w+){0,2}, \w+(?: \w+){0,2},? and \w+(?: \w+){0,2}[.!]")


def lint(path: Path) -> int:
    lines = []
    for raw in Path(path).read_text().splitlines():
        m = LINE_RE.match(raw.strip())
        if m:
            lines.append((m.group(1), m.group(2)))
    errors = warns = 0
    not_just = 0
    words_total = 0
    tricolons = 0
    sentences = []
    heres = the_one = antis = starts_and = n_sents = 0

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
        if NEG_PARALLEL.search(text):
            report("WARN", lid, "negative parallelism ('it's not X, it's Y' / 'rather than'): just say what it is")
        if REVEAL_Q.search(" " + text):
            report("WARN", lid, "fake-suspense question ('The answer? ...'): state it plainly")
        for sent in re.split(r"(?<=[.!?])\s+", text):
            if ING_TAIL.search(sent):
                report("WARN", lid, f"trailing '-ing' significance clause: '{sent[-60:]}'")
        sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
        for x in sents:
            if LABEL.match(x):
                report("WARN", lid, f"label fragment '{x}': fold it into a real sentence ('I'll be honest, ...')")
            if QUIP.match(x):
                report("WARN", lid, f"stock quip '{x}': cut it or say something only you would say")
        heres += len(HERES.findall(text)); the_one += len(THE_ONE.findall(text))
        antis += len(ANTI.findall(text))
        starts_and += sum(1 for x in sents if re.match(r"(and|but|so)\b", x, re.I)); n_sents += len(sents)
        if TRICOLON.search(text):
            tricolons += 1
        sentences += [len(x.split()) for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    if heres > 2:
        report("WARN", "-", f"'Here's why/the/my...' setups used {heres} times (max 2): just say the thing")
    if the_one > 1:
        report("WARN", "-", f"'X is the sneaky/mean/strange one' template used {the_one} times (max 1)")
    if antis > 2:
        report("WARN", "-", f"{antis} 'It doesn't X. It Y.' antithesis pairs (max 2): they read as slogans")
    if n_sents and starts_and / n_sents > 0.15:
        report("WARN", "-", f"{starts_and / n_sents:.0%} of sentences start with And/But/So (keep under 15%)")
    if tricolons > 3:
        report("WARN", "-", f"{tricolons} rule-of-three lists (keep it to ~3 per script; vary list lengths)")
    if len(sentences) > 20:
        import statistics
        sd = statistics.pstdev(sentences); mean = statistics.mean(sentences)
        short = sum(1 for n in sentences if n <= 5) / len(sentences)
        if sd / mean < 0.45 or short < 0.08:
            report("WARN", "-", f"sentence rhythm too even (mean {mean:.0f} words, spread {sd:.0f}, {short:.0%} very short): "
                               "mix in short punches and the odd long run-on, like real speech")
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
