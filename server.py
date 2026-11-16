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
from controller_profiles import ACTIONS, AXES, PAD_TARGETS, PROFILES, ProfileStore, mapping_valid, validate_profile
from virtual_gamepad import GamepadEngine, build_report, neutral_report
from local_tls import tls_folder, certificate_info

ROOT = Path(__file__).resolve().parent
BUTTONS = ACTIONS

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
    def __init__(self, port, engine=None, addresses=None, profile_path=None, gamepad_backend=None, scheme='http', tls_dir=None):
        self.port = port
        self.scheme = scheme
        self.tls_dir = Path(tls_dir) if tls_dir else tls_folder()
        self.tls_info = certificate_info(self.tls_dir)
        self.addresses = addresses or local_addresses()
        self.token = secrets.token_urlsafe(24)
        self.admin = secrets.token_urlsafe(24)
        self.controller = None
        self.last_seen = 0.0
        self.buttons = set()
        self.raw_buttons = set()
        self.axes = {axis: 0.0 for axis in AXES}
        self.vertical_direction = 0
        self.steering = 0.0
        self.steer_direction = 0
        self.store = ProfileStore(profile_path)
        self.profile = "arrows"
        selected = self.store.get(self.profile)
        self.mapping = selected["mapping"]
        self.pad_mapping = selected["pad_mapping"]
        self.layout = selected["layout"]
        self.output_mode = selected["output_mode"]
        self.tuning = selected["tuning"]
        self.revision = 0
        self.engine = engine or InputEngine()
        self.pad = GamepadEngine(self.engine.backend, gamepad_backend)
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
        return [f"{self.scheme}://{a}:{self.port}/controller#{self.token}" for a in ips]

    def stop(self, note):
        self.buttons.clear()
        self.raw_buttons.clear()
        self.axes = {axis: 0.0 for axis in AXES}
        self.vertical_direction = 0
        self.steering = 0.0
        self.steer_direction = 0
        self.arm_at = 0.0
        self.engine.disarm()
        self.pad.disarm()
        self.note = note
        self.notify()

    @property
    def active_engine(self):
        return self.pad if self.output_mode == "gamepad" else self.engine

    def profile_data(self, name="Custom game"):
        return {"name": name, "layout": self.layout, "output_mode": self.output_mode,
                "mapping": dict(self.mapping), "pad_mapping": dict(self.pad_mapping), "tuning": dict(self.tuning)}

    def set_profile(self, name):
        selected = self.store.get(name)
        self.stop("Game profile loaded. Enable output again when ready.")
        self.profile = name
        self.mapping, self.pad_mapping = selected["mapping"], selected["pad_mapping"]
        self.layout, self.output_mode, self.tuning = selected["layout"], selected["output_mode"], selected["tuning"]
        self.revision += 1
        self.notify()

    def pad_report(self):
        return build_report(self.raw_buttons, self.axes, self.steering, self.profile_data())

    def apply_output(self):
        active = self.active_engine
        was_armed = active.armed
        if self.output_mode == "keyboard":
            self.engine.apply(self.desired_keys())
            self.pad.apply(neutral_report())
        else:
            self.pad.apply(self.pad_report())
            self.engine.apply(set())
        if was_armed and not active.armed:
            self.note = "Output disabled after a focus change or input error."

    def desired_keys(self):
        return {self.mapping[b] for b in self.buttons if self.mapping.get(b)}

    def config(self):
        return {"profile": self.profile, "layout": self.layout, "revision": self.revision,
                "mapping": self.mapping, "pad_mapping": self.pad_mapping, "tuning": self.tuning,
                "output_mode": self.output_mode, "profiles": self.store.catalogue(),
                "armed": self.active_engine.armed}

    def status(self):
        age = time.monotonic() - self.last_seen
        active = self.active_engine
        return {"type": "status", "connected": self.controller is not None and age < 0.8,
                "buttons": sorted(self.buttons), "axes": self.axes, "steering": self.steering, **self.config(),
                "keyboard_available": self.engine.backend.available,
                "gamepad": self.pad.backend.diagnostics(), "gamepad_report": self.pad_report(),
                "output_ready": self.engine.backend.available if self.output_mode == "keyboard" else self.pad.backend.connected,
                "countdown": max(0, self.arm_at - time.monotonic()), "target": active.target_title,
                "note": self.note, "error": active.error, "profile_error": self.store.error,
                "transport": self.scheme, "motion_https": self.tls_info}

    async def watchdog(self):
        while True:
            await asyncio.sleep(0.025)
            now = time.monotonic()
            if self.controller is not None and now - self.last_seen >= 0.8:
                if self.buttons or any(self.axes.values()) or self.steering or self.active_engine.armed or self.arm_at:
                    self.stop("Controller timed out. Inputs released; keyboard disabled.")
                continue
            if self.arm_at and now >= self.arm_at:
                self.arm_at = 0.0
                try:
                    self.active_engine.arm()
                    self.note = "Output enabled for the selected window."
                except RuntimeError as exc:
                    self.note = str(exc)
            self.apply_output()


def create_app(port=8765, engine=None, addresses=None, profile_path=None, gamepad_backend=None, scheme='http', tls_dir=None):
    room = Room(port, engine, addresses, profile_path, gamepad_backend, scheme, tls_dir)

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
            with contextlib.suppress(Exception):
                room.pad.backend.disconnect()

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
            raise HTTPException(403, f"Open the laptop dashboard at {room.scheme}://localhost:{room.port}.")

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

    @app.get("/controller-test")
    async def controller_test(request: Request):
        require_local(request)
        return FileResponse(ROOT / "web" / "controller-test.html")

    @app.get("/api/session")
    async def session(request: Request):
        require_local(request)
        return {"urls": room.urls(), "admin": room.admin, "key_options": sorted(SCAN_CODES), "pad_options": sorted(PAD_TARGETS), **room.status()}

    @app.get('/motion-ca.crt')
    async def public_motion_ca():
        path = room.tls_dir / 'NONA-local-CA.crt'
        if not room.tls_info.get('prepared') or not path.is_file():
            raise HTTPException(404, 'Prepare local HTTPS first. See docs/MOTION_TEST.md.')
        return FileResponse(path, media_type='application/x-x509-ca-cert', filename='NONA-local-CA.crt')

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

    @app.post("/api/output/arm")
    @app.post("/api/keyboard")
    async def keyboard(request: Request):
        require_admin(request)
        data = await request.json()
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise HTTPException(400, "Expected enabled: true or false.")
        room.stop("Controller output disabled.")
        if data["enabled"]:
            if not room.engine.backend.available:
                raise HTTPException(400, "Output currently requires Windows.")
            if room.output_mode == "gamepad" and not room.pad.backend.connected:
                raise HTTPException(400, "Connect the optional Xbox controller first.")
            if room.controller is None or time.monotonic() - room.last_seen >= 0.8:
                raise HTTPException(400, "Connect your phone first.")
            room.arm_at = time.monotonic() + 4
            room.note = "Select your game window now. Enabling output in 4 seconds."
        return room.status()

    @app.post("/api/profile")
    async def profile(request: Request):
        require_admin(request)
        data = await request.json()
        name = data.get("profile") if isinstance(data, dict) else None
        if not isinstance(name, str) or name not in room.store.all():
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
        room.revision += 1
        room.notify()
        return room.status()

    @app.get("/api/current-profile")
    async def current_profile(request: Request):
        require_local(request)
        return {"version": 1, "profile": room.profile_data(room.store.get(room.profile)["name"])}

    @app.get("/api/profiles/{key}")
    async def export_profile(key: str, request: Request):
        require_local(request)
        if key not in room.store.all():
            raise HTTPException(404, "Unknown game profile.")
        return {"version": 1, "profile": room.store.get(key)}

    @app.post("/api/profiles")
    async def save_profile(request: Request):
        require_admin(request)
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(400, "Expected a profile object.")
        value = data.get("profile", room.profile_data(data.get("name", "Custom game")))
        try:
            key = room.store.save(value, data.get("replace_id"))
            room.set_profile(key)
        except (ValueError, TypeError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return room.status()

    @app.post("/api/output")
    async def output_mode(request: Request):
        require_admin(request)
        data = await request.json()
        if not isinstance(data, dict) or (not isinstance(data.get("mode"), str) or data["mode"] not in {"keyboard", "gamepad"}):
            raise HTTPException(400, "Choose keyboard or gamepad output.")
        room.stop("Output mode changed. Enable again when ready.")
        room.output_mode = data["mode"]
        room.revision += 1
        room.notify()
        return room.status()

    @app.post("/api/pad-mapping")
    async def pad_mapping(request: Request):
        require_admin(request)
        data = await request.json()
        values = data.get("mapping") if isinstance(data, dict) else None
        if not mapping_valid(values, PAD_TARGETS):
            raise HTTPException(400, "Use supported controller actions and Xbox bindings.")
        room.stop("Xbox bindings changed. Enable again when ready.")
        room.pad_mapping = dict(values)
        room.revision += 1
        room.notify()
        return room.status()

    @app.post("/api/tuning")
    async def tuning(request: Request):
        require_admin(request)
        data = await request.json()
        try:
            profile = validate_profile({**room.profile_data(), "tuning": data})
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        room.stop("Controller tuning changed. Enable again when ready.")
        room.tuning = profile["tuning"]
        room.revision += 1
        room.notify()
        return room.status()

    @app.post("/api/gamepad")
    async def gamepad_connection(request: Request):
        require_admin(request)
        data = await request.json()
        if not isinstance(data, dict) or (not isinstance(data.get("action"), str) or data["action"] not in {"connect", "disconnect"}):
            raise HTTPException(400, "Choose connect or disconnect.")
        room.stop("Virtual controller connection changed. Enable output when ready.")
        try:
            if data["action"] == "connect":
                room.pad.backend.connect()
            else:
                room.pad.backend.disconnect()
        except Exception as exc:
            raise HTTPException(400, str(exc)) from exc
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
                axes = data.get("axes", {})
                disarm = data.get("disarm", False)
                if (type(disarm) is not bool or type(seq) is not int or seq <= last_seq or not isinstance(buttons, list)
                        or len(buttons) > len(BUTTONS)
                        or any(type(b) is not str or b not in BUTTONS for b in buttons)
                        or len(buttons) != len(set(buttons))
                        or type(steering) not in {int, float} or abs(steering) > 1
                        or not math.isfinite(steering)
                        or not isinstance(axes, dict) or set(axes) - AXES
                        or any(type(v) not in {int, float} or abs(v) > 1 or not math.isfinite(v)
                               or (key in {"lt", "rt"} and v < 0) for key, v in axes.items())
                        or (profile is not None and (type(profile) is not str or profile not in room.store.all()))):
                    raise ValueError("Invalid controller state")
                last_seq = seq
                if disarm:
                    room.stop("Output stopped from the phone.")
                    buttons, steering, axes = [], 0, {}
                if profile is not None and profile != room.profile:
                    room.set_profile(profile)
                    buttons, steering, axes = [], 0, {}
                axes = {axis: float(axes.get(axis, 0)) for axis in AXES}
                direction = steering_direction(steering if room.layout == "racing" or steering else axes["lx"], room.steer_direction)
                effective = set(buttons)
                if direction:
                    effective.discard("right" if direction < 0 else "left")
                    effective.add("left" if direction < 0 else "right")
                vertical = steering_direction(axes["ly"], room.vertical_direction)
                if vertical:
                    effective.discard("up" if vertical > 0 else "down")
                    effective.add("down" if vertical > 0 else "up")
                for trigger in ["lt", "rt"]:
                    if axes[trigger] > .5:
                        effective.add(trigger)
                changed = room.buttons != effective or room.steering != steering or room.axes != axes
                room.raw_buttons, room.axes, room.vertical_direction = set(buttons), axes, vertical
                room.buttons, room.steering, room.steer_direction = effective, steering, direction
                room.last_seen = now
                room.apply_output()
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
