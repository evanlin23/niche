"""Numbers in narration ("thirty five percent", "eleven and a half", "three in twenty three", "ten billion",
"thirteen point oh four") and on screen ("35.4%", "10,000,000,000+", "1 in 7"), and whether they agree."""
from __future__ import annotations

import re

UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
UNITS["oh"] = 0
TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
SCALES = {"hundred": 100, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "half": 0.5}


def spoken_numbers(text: str) -> list[float]:
    """All numbers in a narration line (words or digits)."""
    toks = re.findall(r"[a-z]+|\d[\d,]*(?:\.\d+)?", text.lower().replace("-", " "))
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t[0].isdigit():
            v = float(t.replace(",", ""))
            if i + 1 < len(toks) and toks[i + 1] in SCALES and toks[i + 1] != "hundred":
                v *= SCALES[toks[i + 1]]; i += 1
            out.append(v); i += 1; continue
        if t == "a" and i + 1 < len(toks) and toks[i + 1] in SCALES:      # "a billion", "a hundred"
            out.append(SCALES[toks[i + 1]]); i += 2; continue
        if t not in UNITS and t not in TENS or (t == "oh"):
            i += 1; continue
        total, cur, j = 0.0, 0.0, i
        while j < len(toks) and (toks[j] in UNITS or toks[j] in TENS or toks[j] in SCALES or toks[j] == "and"):
            w = toks[j]
            if w == "and":
                if j + 2 < len(toks) and toks[j + 1] == "a" and toks[j + 2] == "half":
                    cur += 0.5; j += 3; break
                if j + 1 < len(toks) and (toks[j + 1] in UNITS or toks[j + 1] in TENS) and (cur >= 100 or total > 0):
                    j += 1; continue
                break
            if w in UNITS and w != "oh":
                cur += UNITS[w]
            elif w in TENS:
                cur += TENS[w]
            elif w == "hundred":
                cur = max(cur, 1) * 100
            elif w in SCALES:
                total += max(cur, 1) * SCALES[w]; cur = 0
            elif w == "oh":
                break
            j += 1
        v = total + cur
        if j < len(toks) and toks[j] == "point":            # "thirteen point oh four"
            digits, k = "", j + 1
            while k < len(toks) and toks[k] in UNITS and UNITS[toks[k]] < 10:
                digits += str(UNITS[toks[k]]); k += 1
            if digits:
                v = float(f"{int(v)}.{digits}"); j = k
        out.append(v)
        i = max(j, i + 1)
    return out


def screen_numbers(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)
            if re.sub(r"[,.]", "", m)]


def agrees(x: float, said: list[float]) -> bool:
    for y in said:
        if abs(x - y) <= 0.051:
            return True
        if float(y * 2).is_integer() and not float(y).is_integer() and abs(x - y) <= 0.25:   # "and a half"
            return True
        if float(y).is_integer() and abs(x - y) < 1.0:     # said rounded: "thirty five" for 35.4
            return True
        if max(abs(x), abs(y)) >= 1000 and abs(x - y) / max(abs(x), abs(y)) <= 0.05:   # "ten billion" vs 10.2B
            return True
        if float(y).is_integer() and abs(x - y) <= 0.5 + 1e-9 and y > 0:
            return True
    return False


if __name__ == "__main__":
    for s in ["thirty five percent", "eleven and a half", "three in twenty three", "thirteen point oh four percent",
              "more than ten billion times", "one hundred and twelve cards", "two thousand and five"]:
        print(s, "->", spoken_numbers(s))
