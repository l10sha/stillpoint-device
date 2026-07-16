"""HTTP bridge between the virtual device and the browser shell.

stdlib only: static files, a Server-Sent Events stream for panel/audio/log
events, and a POST endpoint for physical inputs (lid touch, voice, shell
controls). On real hardware none of this exists — the shell *is* the
enclosure, panel, and speaker.
"""
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SHELL_DIR = Path(__file__).resolve().parent.parent / "shell"

_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()
_last_screen: dict | None = None  # replay for late joiners


def broadcast(event: dict):
    global _last_screen
    if event.get("type") == "screen":
        _last_screen = event
    with _clients_lock:
        for q in list(_clients):
            try:
                q.put_nowait(event)
            except queue.Full:
                pass


class Handler(BaseHTTPRequestHandler):
    device = None  # injected by run()

    def log_message(self, *args):
        pass

    def _serve_file(self, name, ctype):
        path = SHELL_DIR / name
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif self.path == "/shell.css":
            self._serve_file("shell.css", "text/css; charset=utf-8")
        elif self.path == "/shell.js":
            self._serve_file("shell.js", "text/javascript; charset=utf-8")
        elif self.path == "/shell3d.js":
            self._serve_file("shell3d.js", "text/javascript; charset=utf-8")
        elif self.path == "/events":
            self._serve_events()
        else:
            self.send_error(404)

    def _serve_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        q: queue.Queue = queue.Queue(maxsize=256)
        with _clients_lock:
            _clients.append(q)
        if _last_screen:
            q.put({**_last_screen, "refresh": "full"})
        try:
            while True:
                try:
                    event = q.get(timeout=15)
                    payload = f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    payload = ": keepalive\n\n"
                self.wfile.write(payload.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)

    def do_POST(self):
        if self.path != "/input":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            action = body["action"]
            assert action in ("tap", "sit", "email", "warp", "speed")
        except (json.JSONDecodeError, KeyError, AssertionError):
            self.send_error(400, "bad input event")
            return
        self.device.input(action, body.get("arg"))
        self.send_response(204)
        self.end_headers()


def run(device, port=8777):
    import os
    port = int(os.environ.get("PORT", port))
    Handler.device = device
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"StillPoint virtual device · http://0.0.0.0:{port}")
    server.serve_forever()
