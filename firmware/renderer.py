"""Screen composition for the 2072×1072 wide e-ink panel (Carta 1300 class).

Layout philosophy matched to the product photography:
  • Generous whitespace — the calm comes from what is empty
  • Main content large and centered, filling the wide screen
  • Clock is small, light, centered at the top — almost invisible

Font: Inter (bundled) — Rasmus Andersson's humanist sans-serif.
Falls back to Avenir Next on macOS for local development.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .panel import WIDTH, HEIGHT

# ── Font loading: bundled Inter for deployment, Avenir fallback for macOS ──
_FONT_DIR = Path(__file__).parent / "fonts"
_AVENIR = "/System/Library/Fonts/Avenir Next.ttc"

# Mapping: role → (bundled TTF path, Avenir TTC index)
_FONT_MAP = {
    "regular":       (_FONT_DIR / "Inter-Regular.ttf",       7),
    "medium":        (_FONT_DIR / "Inter-Medium.ttf",        5),
    "medium_italic": (_FONT_DIR / "Inter-MediumItalic.ttf",  6),
    "semibold":      (_FONT_DIR / "Inter-SemiBold.ttf",      2),
    "bold":          (_FONT_DIR / "Inter-Bold.ttf",          0),
    "ultralight":    (_FONT_DIR / "Inter-ExtraLight.ttf",    10),
}

PAPER = 255
INK = 20
SOFT = 90
FAINT = 160

# Generous side margins
LM = 150        # left margin
RM = 150        # right margin
TEXT_W = WIDTH - LM - RM

# Partial-refresh regions (x, y, w, h)
CLOCK_REGION = (WIDTH // 2 - 260, 48, 520, 116)
NIGHT_CLOCK_REGION = (WIDTH // 2 - 330, HEIGHT // 2 - 90, 660, 260)
TIMER_REGION = (WIDTH // 2 - 420, HEIGHT // 2 - 240, 840, 410)


def _font(size: int, role: str = "regular") -> ImageFont.FreeTypeFont:
    entry = _FONT_MAP[role]
    bundled = entry[0]
    if bundled.exists():
        return ImageFont.truetype(str(bundled), size)
    # Fallback to macOS Avenir Next
    return ImageFont.truetype(_AVENIR, size, index=entry[1])


# Sizes matched to the product photography proportions
F_CLOCK = _font(64, "regular")              # small and light, like the photos
F_QUOTE = _font(132, "medium")              # main content — confident but not screaming
F_QUOTE_SM = _font(106, "medium")
F_ATTR = _font(64, "medium_italic")
F_LABEL = _font(76, "regular")              # "Time for formal practice" label
F_TITLE = _font(148, "bold")                # "See, Hear, Feel" — bold, commanding
F_BODY = _font(96, "regular")               # "7 min", body text
F_FOOT = _font(60, "regular")               # "Press above to begin"
F_TIMER = _font(280, "ultralight")          # airy countdown numerals
F_ANCHOR = _font(84, "medium_italic")       # anchor phrase during session
F_NIGHT = _font(132, "ultralight")


def _blank() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("L", (WIDTH, HEIGHT), PAPER)
    return img, ImageDraw.Draw(img)


def _wrap(draw, text: str, font, max_w: int) -> list[str]:
    lines = []
    for raw in text.split("\n"):
        words, cur = raw.split(), ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def _left_block(draw, lines: list[str], font, y: int, fill=INK, leading=1.45):
    """Left-aligned text block anchored at (LM, y). Returns y after last line."""
    lh = int(font.size * leading)
    for line in lines:
        draw.text((LM, y), line, font=font, fill=fill)
        y += lh
    return y


def _center_block(draw, lines: list[str], font, cy: int, fill=INK, leading=1.45):
    """Horizontally centered text block, vertically centered around cy."""
    lh = int(font.size * leading)
    total = lh * len(lines)
    y = cy - total // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((WIDTH - w) // 2, y), line, font=font, fill=fill)
        y += lh
    return y


def _center_line(draw, text: str, font, y: int, fill=INK):
    """Single centered line at vertical position y."""
    w = draw.textlength(text, font=font)
    draw.text(((WIDTH - w) // 2, y), text, font=font, fill=fill)


def _clock(draw, time_str: str):
    w = draw.textlength(time_str, font=F_CLOCK)
    draw.text(((WIDTH - w) // 2, 62), time_str, font=F_CLOCK, fill=FAINT)


def _day_circle(draw, day_frac: float):
    cx, cy, r = WIDTH - 120, HEIGHT - 120, 44
    box = (cx - r, cy - r, cx + r, cy + r)
    draw.ellipse(box, outline=FAINT, width=2)
    if day_frac > 0.01:
        draw.arc(box, start=-90, end=-90 + 360 * min(day_frac, 1.0), fill=SOFT, width=6)


# ------------------------------------------------------------- screens ---

def ambient(time_str: str, line: str, attribution: str | None,
            day_frac: float, footer: str | None = None) -> Image.Image:
    """Quote centered on screen — horizontally and vertically."""
    img, d = _blank()
    _clock(d, time_str)

    font = F_QUOTE if len(line) < 45 else F_QUOTE_SM
    lines = _wrap(d, line, font, TEXT_W)

    # Shifted down from true center to compensate for 3D screen tilt
    cy = int(HEIGHT // 2)
    if attribution:
        cy -= 20  # scoot up slightly to make room for attribution
    bottom = _center_block(d, lines, font, cy)

    if attribution:
        aw = d.textlength(f"— {attribution}", font=F_ATTR)
        d.text(((WIDTH - aw) // 2, bottom + 20), f"— {attribution}", font=F_ATTR, fill=SOFT)
    if footer:
        fw = d.textlength(footer, font=F_FOOT)
        d.text(((WIDTH - fw) // 2, HEIGHT - 110), footer, font=F_FOOT, fill=SOFT)
    _day_circle(d, day_frac)
    return img


def invite(time_str: str, title: str, body: str, day_frac: float) -> Image.Image:
    """Centered stack: label above, bold title below."""
    img, d = _blank()

    # Shifted down to compensate for 3D screen tilt
    cy = int(HEIGHT // 2)

    # Body text above the title (may be multiline)
    body_lines = _wrap(d, body, F_LABEL, TEXT_W)
    _center_block(d, body_lines, F_LABEL, cy - 130, fill=SOFT)

    # Bold title
    _center_line(d, title, F_TITLE, cy + 40, fill=INK)

    # Hint at bottom
    hint = "touch the lid to begin · or simply let this pass"
    _center_line(d, hint, F_FOOT, HEIGHT - 110, fill=FAINT)
    _day_circle(d, day_frac)
    return img


def session(remaining: str, anchor: str) -> Image.Image:
    """Centered timer + anchor."""
    img, d = _blank()
    cy = int(HEIGHT // 2)
    w = d.textlength(remaining, font=F_TIMER)
    d.text(((WIDTH - w) // 2, cy - 230), remaining, font=F_TIMER, fill=INK)
    w = d.textlength(anchor, font=F_ANCHOR)
    d.text(((WIDTH - w) // 2, cy + 180), anchor, font=F_ANCHOR, fill=SOFT)
    return img


def reflection(text: str) -> Image.Image:
    """Centered reflection text."""
    img, d = _blank()
    lines = _wrap(d, text, F_QUOTE, TEXT_W)
    _center_block(d, lines, F_QUOTE, int(HEIGHT // 2))
    return img


def email(time_str: str, summary: str, day_frac: float) -> Image.Image:
    """Centered email summary."""
    img, d = _blank()
    _clock(d, time_str)

    # Center the summary
    lines = _wrap(d, summary, F_QUOTE_SM, TEXT_W)
    _center_block(d, lines, F_QUOTE_SM, int(HEIGHT // 2))

    hint = "when you next open your inbox — no rush"
    _center_line(d, hint, F_FOOT, HEIGHT - 110, fill=FAINT)
    _day_circle(d, day_frac)
    return img


def night(time_str: str) -> Image.Image:
    """Centered, minimal."""
    img, d = _blank()
    _center_line(d, time_str, F_NIGHT, int(HEIGHT // 2) - 50, fill=FAINT)
    return img


