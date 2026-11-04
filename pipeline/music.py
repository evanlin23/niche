"""Procedurally generated background music (original, royalty-free by construction).

A slow 4-chord ambient pad + sparse pentatonic plucks, rendered as a seamless loop
(circular-convolution reverb), then tiled to the needed length.
"""
from __future__ import annotations

import numpy as np

SR = 48000


def midi_hz(m):
    return 440.0 * 2 ** ((np.asarray(m) - 69) / 12)


PROGRESSIONS = {
    # Am(add9) - Fmaj7 - Cmaj7 - Gsus2 (calm, curious)
    "curious": [[57, 64, 67, 71], [53, 60, 64, 69], [48, 55, 64, 67], [55, 62, 67, 69]],
    # Dm9 - Bbmaj7 - Fmaj7 - C (slightly tense, for problem sections)
    "tension": [[50, 57, 60, 64], [46, 53, 57, 62], [53, 57, 60, 64], [48, 55, 60, 62]],
}
PENTA = [69, 72, 74, 76, 79, 81, 84]


def _pad_note(f, n, rng):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        ph = rng.random() * 2 * np.pi
        out += np.sin(2 * np.pi * ff * t + ph) + 0.18 * np.sin(4 * np.pi * ff * t + ph)
    return out / 3


def _env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def loop(mood="curious", chord_len=8.0, seed=0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    chords = PROGRESSIONS[mood]
    n_chord = int(chord_len * SR)
    total = n_chord * len(chords)
    out = np.zeros(total)
    for ci, chord in enumerate(chords):
        n = int(n_chord * 1.25)                     # overlap into next chord
        seg = sum(_pad_note(f, n, rng) for f in midi_hz(chord)) / len(chord)
        seg += 0.6 * np.sin(2 * np.pi * midi_hz(chord[0] - 12) * np.arange(n) / SR)  # sub
        seg *= _env(n, 2.5, 3.0)
        idx = (np.arange(n) + ci * n_chord) % total
        np.add.at(out, idx, seg * 0.35)
    # plucks
    step = int(0.5 * SR)
    for k in range(total // step):
        if rng.random() < 0.28:
            f = midi_hz(PENTA[rng.integers(len(PENTA))])
            n = int(1.6 * SR)
            t = np.arange(n) / SR
            p = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 3.2)
            p *= np.minimum(1, t / 0.004)
            idx = (np.arange(n) + k * step) % total
            np.add.at(out, idx, p * 0.10)
    # one-pole lowpass (vectorised approx via FFT) + circular reverb
    F = np.fft.rfft(out)
    freqs = np.fft.rfftfreq(total, 1 / SR)
    F *= 1 / np.sqrt(1 + (freqs / 2500) ** 2)
    ir_n = int(2.8 * SR)
    ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 2.2)
    ir_full = np.zeros(total); ir_full[:ir_n] = ir / np.sqrt(np.sum(ir ** 2))
    wet = np.fft.irfft(F * np.fft.rfft(ir_full), total)
    dry = np.fft.irfft(F, total)
    mix = 0.55 * dry + 0.45 * wet
    return (mix / (np.abs(mix).max() + 1e-9)).astype(np.float32)


def bed(duration: float, mood="curious", seed=0) -> np.ndarray:
    """Seamless music bed of the requested length, with 2 s fade in / 4 s fade out."""
    a, b = loop(mood, seed=seed), loop(mood, seed=seed + 1)
    n = int(duration * SR)
    reps = []
    k = 0
    while sum(len(r) for r in reps) < n:
        reps.append(a if k % 2 == 0 else b); k += 1
    out = np.concatenate(reps)[:n]
    fi, fo = int(2 * SR), int(4 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out
