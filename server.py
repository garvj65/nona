"""NONA: one local host, one paired phone controller, no cloud services."""
import asyncio
import contextlib
import io
import ipaddress
import json
import math
import secrets
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from windows_input import InputEngine, SCAN_CODES

ROOT = Path(__file__).resolve().parent
BUTTONS = {"up", "down", "left", "right", "a", "b", "start", "select", "handbrake", "nitro"}
PROFILES = {
    "arrows": {"up": "up", "down": "down", "left": "left", "right": "right",
               "a": "space", "b": "x", "start": "enter", "select": "p"},
    "wasd": {"up": "w", "down": "s", "left": "a", "right": "d",
             "a": "space", "b": "x", "start": "enter", "select": "p"},
    "racing_arrows": {"up": "up", "down": "down", "left": "left", "right": "right",
                      "a": "up", "b": "down", "handbrake": "space", "nitro": "shift",
                      "start": "enter", "select": "r"},
    "racing_wasd": {"up": "w", "down": "s", "left": "a", "right": "d",
                    "a": "w", "b": "s", "handbrake": "space", "nitro": "shift",
                    "start": "enter", "select": "r"},
}


def steering_direction(value, previous=0):
    """Hysteresis keeps a noisy wheel from repeatedly toggling keyboard keys."""
    if value >= 0.22:
        return 1
    if value <= -0.22:
        return -1
    if previous == 1 and value > 0.12:
        return 1
    if previous == -1 and value < -0.12:
        return -1
    return 0


def local_addresses():
    addresses = {"127.0.0.1", "localhost"}
    with contextlib.suppress(OSError):
        for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(result[4][0])
    with contextlib.suppress(OSError):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))  # routing lookup; no packet is sent
            addresses.add(probe.getsockname()[0])
    return addresses


class Room:
    def __init__(self, port, engine=None, addresses=None):
        self.port = port
        self.addresses = addresses or local_addresses()
        self.token = secrets.token_urlsafe(24)
        self.admin = secrets.token_urlsafe(24)
        self.controller = None
        self.last_seen = 0.0
        self.buttons = set()
        self.steering = 0.0
        self.steer_direction = 0
        self.profile = "arrows"
        self.mapping = dict(PROFILES[self.profile])
        self.engine = engine or InputEngine()
        self.arm_at = 0.0
        self.note = "Ready to pair. Desktop keyboard is off."
        self.monitors = set()

    def notify(self):
        snapshot = self.status()
        for queue in self.monitors:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(snapshot)

    def urls(self):
        ips = sorted(a for a in self.addresses if a not in {"localhost", "127.0.0.1"})
        return [f"http://{a}:{self.port}/controller#{self.token}" for a in ips]

    def stop(self, note):
        self.buttons.clear()
        self.steering = 0.0
        self.steer_direction = 0
        self.arm_at = 0.0
        self.engine.disarm()
        self.note = note
        self.notify()

    def set_profile(self, name):
        self.stop("Controls changed. Re-enable desktop keyboard if needed.")
        self.profile = name
        self.mapping = dict(PROFILES[name])
        self.notify()

    def desired_keys(self):
        return {self.mapping[b] for b in self.buttons if self.mapping.get(b)}

    def config(self):
        return {"profile": self.profile, "layout": "racing" if self.profile.startswith("racing_") else "gamepad",
                "mapping": self.mapping, "armed": self.engine.armed}

    def status(self):
        age = time.monotonic() - self.last_seen
        return {"type": "status", "connected": self.controller is not None and age < 0.8,
                "buttons": sorted(self.buttons), "steering": self.steering, **self.config(),
                "keyboard_available": self.engine.backend.available,
                "armed": self.engine.armed, "countdown": max(0, self.arm_at - time.monotonic()),
                "target": self.engine.target_title, "note": self.note,
                "error": self.engine.error}

    async def watchdog(self):
        while True:
            await asyncio.sleep(0.025)
            now = time.monotonic()
            if self.controller is not None and now - self.last_seen >= 0.8:
                if self.buttons or self.engine.armed or self.arm_at:
                    self.stop("Controller timed out. Inputs released; keyboard disabled.")
                continue
            if self.arm_at and now >= self.arm_at:
                self.arm_at = 0.0
                try:
                    self.engine.arm()
                    self.note = "Keyboard enabled for the selected window."
                except RuntimeError as exc:
                    self.note = str(exc)
            was_armed = self.engine.armed
            self.engine.apply(self.desired_keys())
            if was_armed and not self.engine.armed:
                self.note = "Keyboard disabled after a focus change or input error."


def create_app(port=8765, engine=None, addresses=None):
    room = Room(port, engine, addresses)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(room.watchdog())
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            room.stop("Stopped")

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.room = room
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=sorted(room.addresses))

    def local_client(connection):
        if not connection.client:
            return False
        with contextlib.suppress(ValueError):
            return ipaddress.ip_address(connection.client.host).is_loopback
        return False

    def valid_origin(connection):
        origin = connection.headers.get("origin", "")
        parsed = urlsplit(origin)
        expected_scheme = "https" if connection.url.scheme in {"https", "wss"} else "http"
        return parsed.scheme == expected_scheme and parsed.netloc == connection.headers.get("host")

    def require_local(request):
        if not local_client(request):
            raise HTTPException(403, "Open the laptop dashboard at http://localhost:8765.")

    def require_admin(request):
        require_local(request)
        if not valid_origin(request) or not secrets.compare_digest(
                request.headers.get("x-pocketpad-admin", ""), room.admin):
            raise HTTPException(403, "Open the dashboard on this laptop and try again.")

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        return response

    @app.get("/")
    async def dashboard(request: Request):
        require_local(request)
        return FileResponse(ROOT / "web" / "index.html")

    @app.get("/controller")
    async def controller():
        return FileResponse(ROOT / "web" / "controller.html")

    @app.get("/game")
    async def game(request: Request):
        require_local(request)
        return FileResponse(ROOT / "web" / "game.html")

    @app.get("/race")
    async def race(request: Request):
        require_local(request)
        return FileResponse(ROOT / "web" / "race.html")

    @app.get("/api/session")
    async def session(request: Request):
        require_local(request)
        return {"urls": room.urls(), "admin": room.admin, "key_options": sorted(SCAN_CODES), **room.status()}

    @app.get("/api/qr")
    async def qr(request: Request, index: int = 0):
        require_local(request)
        urls = room.urls()
        if not 0 <= index < len(urls):
            raise HTTPException(404, "No LAN address found. Check Wi-Fi.")
        try:
            import qrcode
            import qrcode.image.svg
        except ImportError:
            raise HTTPException(503, "QR module missing. Type the displayed link instead.")
        output = io.BytesIO()
        qrcode.make(urls[index], image_factory=qrcode.image.svg.SvgPathImage,
                    border=3).save(output)
        return Response(output.getvalue(), media_type="image/svg+xml")

    @app.post("/api/keyboard")
    async def keyboard(request: Request):
        require_admin(request)
        data = await request.json()
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise HTTPException(400, "Expected enabled: true or false.")
        room.stop("Desktop keyboard disabled.")
        if data["enabled"]:
            if not room.engine.backend.available:
                raise HTTPException(400, "Desktop keyboard mode requires Windows.")
            if room.controller is None or time.monotonic() - room.last_seen >= 0.8:
                raise HTTPException(400, "Connect your phone first.")
            room.arm_at = time.monotonic() + 4
            room.note = "Select your game window now. Enabling keyboard in 4 seconds."
        return room.status()

    @app.post("/api/profile")
    async def profile(request: Request):
        require_admin(request)
        data = await request.json()
        name = data.get("profile") if isinstance(data, dict) else None
        if not isinstance(name, str) or name not in PROFILES:
            raise HTTPException(400, "Choose a supported gamepad or racing profile.")
        room.set_profile(name)
        return room.status()

    @app.post("/api/mapping")
    async def mapping(request: Request):
        require_admin(request)
        data = await request.json()
        values = data.get("mapping") if isinstance(data, dict) else None
        if (not isinstance(values, dict) or not values or len(values) > len(BUTTONS)
                or any(button not in BUTTONS or not isinstance(key, str)
                       or (key and key not in SCAN_CODES) for button, key in values.items())):
            raise HTTPException(400, "Use supported controller actions and keys.")
        room.stop("Key mapping saved. Re-enable desktop keyboard for your game.")
        room.mapping = dict(values)
        room.notify()
        return room.status()

    @app.websocket("/ws/monitor")
    async def monitor(ws: WebSocket):
        if not local_client(ws) or not valid_origin(ws):
            await ws.close(code=1008)
            return
        await ws.accept()
        queue = asyncio.Queue(maxsize=64)
        room.monitors.add(queue)
        try:
            await ws.send_json(room.status())
            while True:
                try:
                    snapshot = await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    snapshot = room.status()
                await ws.send_json(snapshot)
        except (WebSocketDisconnect, RuntimeError, OSError):
            pass
        finally:
            room.monitors.discard(queue)

    @app.websocket("/ws/controller")
    async def control(ws: WebSocket):
        if (not valid_origin(ws) or not secrets.compare_digest(
                ws.query_params.get("token", ""), room.token) or room.controller is not None):
            await ws.close(code=1008)
            return
        # Reserve before await: concurrent connection attempts cannot claim the room.
        room.controller = ws
        room.last_seen = time.monotonic()
        room.stop("Phone connected. Try the demo game.")
        last_seq = -1
        rate_start, rate_count = time.monotonic(), 0
        try:
            await ws.accept()
            while True:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=0.8)
                now = time.monotonic()
                if now - rate_start > 1:
                    rate_start, rate_count = now, 0
                rate_count += 1
                if len(raw) > 1024 or rate_count > 120:
                    await ws.close(code=1008)
                    break
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("Expected an object")
                seq, buttons = data.get("seq"), data.get("buttons")
                steering = data.get("steering", 0)
                profile = data.get("profile")
                if (type(seq) is not int or seq <= last_seq or not isinstance(buttons, list)
                        or len(buttons) > len(BUTTONS)
                        or any(type(b) is not str or b not in BUTTONS for b in buttons)
                        or type(steering) not in {int, float} or abs(steering) > 1
                        or not math.isfinite(steering)
                        or (profile is not None and (type(profile) is not str or profile not in PROFILES))):
                    raise ValueError("Invalid controller state")
                last_seq = seq
                if profile is not None and profile != room.profile:
                    room.set_profile(profile)
                    buttons, steering = [], 0
                direction = steering_direction(steering, room.steer_direction)
                effective = set(buttons)
                if direction:
                    effective.discard("right" if direction < 0 else "left")
                    effective.add("left" if direction < 0 else "right")
                changed = room.buttons != effective or room.steering != steering
                room.buttons, room.steering, room.steer_direction = effective, steering, direction
                room.last_seen = now
                was_armed = room.engine.armed
                room.engine.apply(room.desired_keys())
                if was_armed and not room.engine.armed:
                    room.note = "Keyboard disabled after a focus change or input error."
                if changed:
                    room.notify()
                await ws.send_json({"type": "ack", "seq": seq, **room.config()})
        except (WebSocketDisconnect, asyncio.TimeoutError, ValueError, TypeError, RuntimeError):
            with contextlib.suppress(RuntimeError, OSError):
                await ws.close(code=1008)
        finally:
            if room.controller is ws:
                room.controller = None
                room.stop("Phone disconnected. Inputs released; keyboard disabled.")

    app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")
    return app
