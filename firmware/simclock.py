"""Simulated device clock.

The firmware never reads the wall clock directly; it asks SimClock.
This lets the shell warp time to demo the daily rhythm engine.
"""
import time
from datetime import datetime, timedelta


class SimClock:
    def __init__(self, start: datetime | None = None, speed: float = 1.0):
        self._base = start or datetime.now().replace(second=0, microsecond=0)
        self._anchor = time.monotonic()
        self._speed = speed

    def now(self) -> datetime:
        elapsed = (time.monotonic() - self._anchor) * self._speed
        return self._base + timedelta(seconds=elapsed)

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, speed: float):
        self._base = self.now()
        self._anchor = time.monotonic()
        self._speed = max(0.0, min(speed, 3600.0))

    def warp_to(self, hour: int, minute: int = 0):
        now = self.now()
        self._base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        self._anchor = time.monotonic()
