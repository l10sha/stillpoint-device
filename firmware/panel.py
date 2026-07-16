"""Virtual e-paper panel driver.

Mimics a wide-format Carta 1300 EPD driver surface (init / display /
display_partial / sleep) so the application layer is portable to real hardware:
swap this module for the SPI driver and the rest of the firmware is unchanged.
The 2072×1072 resolution matches the industrial-design screen aspect (~1.93:1).

Instead of shifting the framebuffer out over SPI, refresh events are published
to an event bus (the browser shell renders them, including refresh artifacts).
"""
import base64
import io
import time

from PIL import Image

WIDTH, HEIGHT = 2072, 1072
GRAY_LEVELS = 16
DPI = 229

# Carta 1300 timings (seconds) — ~25% faster full, ~60% faster partial vs Carta 1000
FULL_REFRESH_TIME = 1.2
PARTIAL_REFRESH_TIME = 0.12


def _quantize(img: Image.Image) -> Image.Image:
    """Collapse to the panel's 16 gray levels."""
    return img.convert("L").point(lambda p: (p >> 4) * 17)


def _encode(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class VirtualEPD:
    """Drop-in stand-in for a 7.8" Carta 1300 EPD via IT8951 controller."""

    width = WIDTH
    height = HEIGHT

    def __init__(self, bus):
        self._bus = bus  # callable(event: dict)
        self._asleep = True
        self._full_refreshes = 0
        self._partial_refreshes = 0

    def init(self):
        self._asleep = False
        self._bus({"type": "log", "svc": "epd", "msg": "panel init, waveform LUT loaded"})

    def sleep(self):
        self._asleep = True
        self._bus({"type": "log", "svc": "epd", "msg": "deep sleep (0 µW static hold)"})

    def clear(self):
        self.display(Image.new("L", (WIDTH, HEIGHT), 255))

    def display(self, img: Image.Image):
        """Full refresh: the whole panel flashes through inversion cycles."""
        if self._asleep:
            self.init()
        self._full_refreshes += 1
        self._bus({
            "type": "screen",
            "refresh": "full",
            "png": _encode(_quantize(img)),
            "busy_ms": int(FULL_REFRESH_TIME * 1000),
        })
        self._bus({
            "type": "log", "svc": "epd",
            "msg": f"full refresh #{self._full_refreshes} ({FULL_REFRESH_TIME:.1f}s busy)",
        })
        time.sleep(0.05)  # token nod to the BUSY line

    def display_partial(self, img: Image.Image, region: tuple[int, int, int, int]):
        """Partial refresh: only `region` (x, y, w, h) updates, no flash, slight ghosting."""
        if self._asleep:
            self.init()
        self._partial_refreshes += 1
        self._bus({
            "type": "screen",
            "refresh": "partial",
            "png": _encode(_quantize(img)),
            "region": list(region),
            "busy_ms": int(PARTIAL_REFRESH_TIME * 1000),
        })
