"""One visual identity for the whole channel: dark background, 5-colour palette,
Inter typeface. Change it here, never per-episode."""
import skia

BG = 0xFF0E1117          # near-black blue
PANEL = 0xFF161B24
GRID = 0xFF262D3A
TEXT = 0xFFE8ECF2
MUTED = 0xFF8A94A6

# the 5 accent colours
TEAL = 0xFF2EC4B6        # cruising / good
AMBER = 0xFFFFB627       # attention
RED = 0xFFE5484D         # stopped / bad
BLUE = 0xFF4C9AFF        # the "hero" agent
VIOLET = 0xFFA78BFA      # secondary series

PALETTE = [TEAL, AMBER, RED, BLUE, VIOLET]

FONT_FAMILY = "Inter"
CHANNEL_NAME = "BUH SIMULATES"


def rgba(c: int) -> tuple[int, int, int, int]:
    return (c >> 16) & 255, (c >> 8) & 255, c & 255, (c >> 24) & 255


def with_alpha(c: int, a: float) -> int:
    return (int(max(0, min(1, a)) * 255) << 24) | (c & 0xFFFFFF)


def lerp_color(c1: int, c2: int, t: float) -> int:
    a, b = rgba(c1), rgba(c2)
    r = [int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4)]
    return (r[3] << 24) | (r[0] << 16) | (r[1] << 8) | r[2]


def speed_color(frac: float) -> int:
    """0 = stopped (red) -> 0.5 amber -> 1 = cruising (teal)."""
    f = max(0.0, min(1.0, frac))
    if f < 0.5:
        return lerp_color(RED, AMBER, f / 0.5)
    return lerp_color(AMBER, TEAL, (f - 0.5) / 0.5)


_FONTS: dict = {}


def font(size: float, weight: str = "regular") -> skia.Font:
    key = (round(size, 2), weight)
    if key not in _FONTS:
        style = {"regular": skia.FontStyle.Normal(), "bold": skia.FontStyle.Bold(),
                 "medium": skia.FontStyle(500, 5, skia.FontStyle.kUpright_Slant),
                 "semibold": skia.FontStyle(600, 5, skia.FontStyle.kUpright_Slant),
                 "black": skia.FontStyle(900, 5, skia.FontStyle.kUpright_Slant)}[weight]
        f = skia.Font(skia.Typeface(FONT_FAMILY, style), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _FONTS[key] = f
    return _FONTS[key]
