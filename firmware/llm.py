"""Local LLM service (virtualized).

On hardware this is Qwen 2.5 1.5B int4 on the Hailo-10H via llama.cpp,
doing three narrow jobs: pick/compose ambient lines, pick practices,
classify email. Here those jobs are stubbed deterministically, and the
service simulates the accelerator's latency and token rate so the rest
of the system experiences realistic timing.

The interface is the contract: swap the body for real inference later.
"""
import random
import time

from . import content

MODEL = "qwen2.5-1.5b-instruct-q4"
TOKENS_PER_SEC = 6.5  # Hailo-10H int4, per PRD 3–8 tok/s


class LocalLLM:
    def __init__(self, bus):
        self._bus = bus
        self._rng = random.Random(7)
        self._recent: dict[str, list[int]] = {}

    def _log(self, msg):
        self._bus({"type": "log", "svc": "llm", "msg": msg})

    def _simulate_inference(self, approx_tokens: int):
        # Keep the demo snappy: simulate at 20x real accelerator speed.
        time.sleep(min(approx_tokens / TOKENS_PER_SEC / 20.0, 1.2))

    # ---------------------------------------------------------- ambient ---
    def ambient_line(self, phase: str) -> tuple[str, str | None]:
        pool = content.AMBIENT.get(phase, content.AMBIENT["afternoon"])
        seen = self._recent.setdefault(phase, [])
        choices = [i for i in range(len(pool)) if i not in seen] or list(range(len(pool)))
        idx = self._rng.choice(choices)
        seen.append(idx)
        if len(seen) > max(1, len(pool) - 1):
            seen.pop(0)
        self._simulate_inference(30)
        self._log(f"ambient line for '{phase}' ({MODEL}, ~{TOKENS_PER_SEC} tok/s)")
        return pool[idx]

    # -------------------------------------------------------- practices ---
    def pick_practice(self, phase: str) -> dict:
        self._simulate_inference(15)
        practice = self._rng.choice(content.MICRO_PRACTICES)
        self._log(f"selected micro-practice '{practice['title']}' for {phase}")
        return practice

    # ------------------------------------------------------------ email ---
    URGENT_CONTACTS = {"jean-louis moreau", "pauline bertry"}
    URGENT_WORDS = ("today", "eod", "urgent", "deadline", "asap", "by end of")

    def classify_email(self, msg: dict) -> tuple[str, str]:
        """Returns (category, one_line_summary). Header-only classification."""
        self._simulate_inference(40)
        sender, subject = msg["sender"], msg["subject"]
        s = f"{sender} {subject}".lower()
        if any(w in s for w in ("newsletter", "unsubscribe", "digest", "appeared in")):
            cat = "ignore"
        elif sender.lower() in self.URGENT_CONTACTS and any(w in s for w in self.URGENT_WORDS):
            cat = "act_now"
        elif sender.lower() in self.URGENT_CONTACTS:
            cat = "review_later"
        else:
            cat = "review_later"
        short = subject if len(subject) <= 52 else subject[:49].rstrip() + "…"
        first = sender.split()[0]
        self._log(f"classified mail from {first}: {cat}")
        return cat, f"{sender} — {short}"
