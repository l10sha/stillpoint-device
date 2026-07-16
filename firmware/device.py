"""StillPoint application layer: scheduler, daily rhythm engine, state machine.

Runs as a single tick loop (5 Hz). Simulated-time triggers drive the daily
rhythm (phases, ambient rotation, micro-practice invitations, IMAP sync);
real-time actions drive anything paced against the human (speech, timeouts).
"""
import heapq
import math
import queue
import random
import threading
import time
from datetime import datetime

from . import content, renderer
from .llm import LocalLLM
from .panel import VirtualEPD
from .simclock import SimClock

PHASES = [
    (7, 9, "morning"), (9, 12, "focus"), (12, 13, "midday"),
    (13, 17, "afternoon"), (17, 20, "evening"),
]  # everything else -> night

INVITE_TIMES = ((10, 30), (14, 0), (16, 30))
INVITE_TIMEOUT_S = 60          # per PRD: return to ambient, no follow-up, no guilt
AMBIENT_ROTATE_MIN = 10        # full refresh cadence in ambient mode
EMAIL_HOLD_MIN = 6             # how long an act-now line stays on screen
SPEECH_CPS = 12.0              # chars/sec estimate at meditation pace


def fmt12(dt: datetime, suffix: bool = False) -> str:
    """12-hour clock. The device screen stays suffix-free (calm, like the renders);
    the test bench shows am/pm for clarity."""
    h = dt.hour % 12 or 12
    s = f"{h}:{dt.minute:02d}"
    return f"{s} {'am' if dt.hour < 12 else 'pm'}" if suffix else s


def phase_of(dt: datetime) -> str:
    for lo, hi, name in PHASES:
        if lo <= dt.hour < hi:
            return name
    return "night"


def day_fraction(dt: datetime) -> float:
    """Waking day 07:00–22:00 mapped to 0..1 for the day circle."""
    minutes = dt.hour * 60 + dt.minute
    return max(0.0, min(1.0, (minutes - 7 * 60) / (15 * 60)))


class Device:
    def __init__(self, bus, clock: SimClock):
        self._bus = bus
        self.clock = clock
        self.epd = VirtualEPD(bus)
        self.llm = LocalLLM(bus)
        self._rng = random.Random(11)

        self.mode = "boot"
        self._inputs: queue.Queue = queue.Queue()
        self._actions: list = []   # heap of (monotonic_due, seq, fn)
        self._seq = 0
        self._epoch = 0            # invalidates pending actions on mode change

        self._last_minute = None
        self._last_rotate = None
        self._phase = None
        self._fired_invites: set = set()
        self._ambient_line = ("", None)
        self._pending_mail: list = []
        self._practice = None
        self._email_summary = None
        self._last_sync = None
        self._session = None

    # ------------------------------------------------------------ plumbing
    def _log(self, svc, msg):
        self._bus({"type": "log", "svc": svc, "msg": msg})

    def _state(self):
        now = self.clock.now()
        self._bus({
            "type": "state", "mode": self.mode, "phase": phase_of(now),
            "simtime": fmt12(now, suffix=True), "speed": self.clock.speed,
        })

    def _after(self, seconds, fn, tied_to_mode=True):
        epoch = self._epoch if tied_to_mode else None
        self._seq += 1
        heapq.heappush(self._actions, (time.monotonic() + seconds, self._seq, epoch, fn))

    def _set_mode(self, mode):
        self.mode = mode
        self._epoch += 1
        self._state()

    def _speak(self, text):
        self._bus({"type": "speak", "text": text})
        self._log("tts", f'"{text[:46]}{"…" if len(text) > 46 else ""}" (chatterbox-0.5b, cached)')

    def _chime(self):
        self._bus({"type": "chime"})

    def input(self, action, arg=None):
        self._inputs.put((action, arg))

    # ------------------------------------------------------------- screens
    def _time_str(self):
        return fmt12(self.clock.now())

    def _show_ambient(self, full=True):
        now = self.clock.now()
        if phase_of(now) == "night":
            img = renderer.night(self._time_str())
        else:
            line, attr = self._ambient_line
            img = renderer.ambient(self._time_str(), line, attr, day_fraction(now))
        if full:
            self.epd.display(img)
        else:
            region = (renderer.NIGHT_CLOCK_REGION if phase_of(now) == "night"
                      else renderer.CLOCK_REGION)
            self.epd.display_partial(img, region)

    def _rotate_ambient(self):
        now = self.clock.now()
        if phase_of(now) != "night":
            self._ambient_line = self.llm.ambient_line(phase_of(now))
        self._show_ambient(full=True)
        self._last_rotate = now

    # ---------------------------------------------------------------- boot
    def boot(self):
        self._log("sys", "stillpoint-os 0.1 · dietpi · services: epd llm tts imap sched")
        self.epd.init()
        self._rotate_ambient()
        self._set_mode("ambient")

    # ---------------------------------------------------------- tick loop
    def run(self):
        self.boot()
        last_state_push = 0.0
        while True:
            time.sleep(0.2)
            mono = time.monotonic()

            while self._actions and self._actions[0][0] <= mono:
                _, _, epoch, fn = heapq.heappop(self._actions)
                if epoch is None or epoch == self._epoch:
                    fn()

            try:
                while True:
                    action, arg = self._inputs.get_nowait()
                    self._handle_input(action, arg)
            except queue.Empty:
                pass

            self._sim_triggers()

            if mono - last_state_push > 1.0:
                self._state()
                last_state_push = mono

    # ----------------------------------------------------- sim-time logic
    def _sim_triggers(self):
        now = self.clock.now()
        minute = now.replace(second=0, microsecond=0)

        phase = phase_of(now)
        if phase != self._phase:
            old, self._phase = self._phase, phase
            if old is not None:
                self._log("sched", f"daily rhythm: {old} → {phase}")
                if self.mode == "ambient":
                    self._rotate_ambient()

        if minute != self._last_minute:
            self._last_minute = minute
            if self.mode == "ambient":
                self._show_ambient(full=False)  # clock via partial refresh
            elif self.mode == "email" and self._email_summary:
                img = renderer.email(self._time_str(), self._email_summary,
                                     day_fraction(now))
                self.epd.display_partial(img, renderer.CLOCK_REGION)
            if self.mode == "ambient" and phase != "night":
                hhmm = (now.hour, now.minute)
                if hhmm in INVITE_TIMES and hhmm not in self._fired_invites:
                    self._fired_invites.add(hhmm)
                    self._begin_invite()
            if now.hour == 0 and now.minute == 0:
                self._fired_invites.clear()

        if self._last_rotate is None or abs((now - self._last_rotate).total_seconds()) >= AMBIENT_ROTATE_MIN * 60:
            if self.mode == "ambient":
                self._rotate_ambient()

        if self._last_sync is None or abs((now - self._last_sync).total_seconds()) >= 30 * 60:
            self._last_sync = now
            if self._pending_mail:
                self._sync_mail()
            else:
                self._log("imap", "sync: no new messages")

    # ---------------------------------------------------------- invitations
    def _begin_invite(self):
        practice = self.llm.pick_practice(self._phase)
        self._practice = practice
        self._set_mode("invite")
        self._chime()
        img = renderer.invite(self._time_str(), practice["title"], practice["body"],
                              day_fraction(self.clock.now()))
        self.epd.display(img)
        self._log("sched", f"invitation shown · returns to ambient in {INVITE_TIMEOUT_S}s if untouched")
        self._after(INVITE_TIMEOUT_S, self._back_to_ambient)

    def _accept_invite(self):
        practice = self._practice
        self._set_mode("practice")
        t = 0.0
        for pause, text in practice["speech"]:
            t += pause
            self._after(t, lambda tx=text: self._speak(tx))
            t += max(1.5, len(text) / SPEECH_CPS)
        self._after(t + 2.0, self._back_to_ambient)

    def _back_to_ambient(self):
        self._set_mode("ambient")
        self._rotate_ambient()

    # ------------------------------------------------------------ sessions
    def start_session(self, key=None):
        if key is None:
            key = "metta" if self._phase in ("evening", "night") else "settling"
        s = content.SESSIONS[key]
        total = sum(p + (max(1.5, len(t) / SPEECH_CPS) if t else 0.0) for p, t in s["script"]) + 6
        self._session = {"spec": s, "start": time.monotonic(), "total": total}
        self._set_mode("session")
        self._log("sched", f"session '{s['name']}' · ~{int(total)}s · scripts pre-rendered by tts")
        self._chime()
        self.epd.display(renderer.session(self._fmt_remaining(total), s["anchor"]))

        t = 3.0
        for pause, text in s["script"]:
            t += pause
            if text:
                self._after(t, lambda tx=text: self._speak(tx))
                t += max(1.5, len(text) / SPEECH_CPS)
        self._after(15, self._tick_session_timer)
        self._after(total, self._end_session)

    def _fmt_remaining(self, seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _tick_session_timer(self):
        if self.mode != "session" or not self._session:
            return
        left = self._session["total"] - (time.monotonic() - self._session["start"])
        img = renderer.session(self._fmt_remaining(math.ceil(left / 15) * 15),
                               self._session["spec"]["anchor"])
        self.epd.display_partial(img, renderer.TIMER_REGION)
        self._after(15, self._tick_session_timer)

    def _end_session(self, early=False):
        spec = self._session["spec"] if self._session else content.SESSIONS["settling"]
        self._session = None
        self._chime()
        self._set_mode("reflect")
        self.epd.display(renderer.reflection(spec["reflection"]))
        self._log("sched", "session complete · no streaks, no scores, nothing tracked")
        self._after(20, self._back_to_ambient)

    # --------------------------------------------------------------- email
    def inject_email(self, kind):
        msg = self._rng.choice(content.EMAIL_SAMPLES[kind])
        self._pending_mail.append(msg)
        self._log("imap", f"1 new message (headers only) — next classify pass shortly")
        self._after(1.5, self._sync_mail, tied_to_mode=False)

    def _sync_mail(self):
        pending, self._pending_mail = self._pending_mail, []
        for msg in pending:
            cat, summary = self.llm.classify_email(msg)
            if cat == "act_now" and self.mode == "ambient":
                self._surface_email(summary)
            elif cat != "act_now":
                self._log("imap", f"held quietly ({cat}) — nothing surfaced")
        self._last_sync = self.clock.now()

    def _surface_email(self, summary):
        self._email_summary = summary
        self._set_mode("email")
        self.epd.display(renderer.email(self._time_str(), summary,
                                        day_fraction(self.clock.now())))
        self._after(EMAIL_HOLD_MIN * 60 / max(1.0, self.clock.speed), self._back_to_ambient)

    # --------------------------------------------------------------- input
    def _handle_input(self, action, arg):
        if action == "tap":
            self._log("touch", "capacitive zone on walnut lid")
            if self.mode == "invite":
                self._accept_invite()
            elif self.mode == "ambient":
                self.start_session()
            elif self.mode == "session":
                self._end_session(early=True)
            elif self.mode in ("email", "reflect"):
                self._back_to_ambient()
        elif action == "sit":
            self._log("mic", 'wake phrase: "stillpoint, let\'s sit"')
            if self.mode in ("ambient", "invite", "email", "reflect"):
                self.start_session(arg)
        elif action == "email":
            self.inject_email(arg or "urgent")
        elif action == "warp":
            h, m = arg
            self.clock.warp_to(h, m)
            self._log("sys", f"[shell] clock warped to {fmt12(self.clock.now(), suffix=True)}")
            self._fired_invites.clear()
            if self.mode != "session":   # sessions run on real time, no clock shown
                self._back_to_ambient()
        elif action == "speed":
            self.clock.set_speed(float(arg))
            self._log("sys", f"[shell] clock speed ×{int(self.clock.speed)}")


def start(bus, clock) -> Device:
    dev = Device(bus, clock)
    threading.Thread(target=dev.run, daemon=True).start()
    return dev
