"""Optional Xbox 360 output. No dependency import or driver install at startup."""
import importlib
import importlib.util
import math
import sys

PAD_BUTTONS = {"a": "XUSB_GAMEPAD_A", "b": "XUSB_GAMEPAD_B", "x": "XUSB_GAMEPAD_X", "y": "XUSB_GAMEPAD_Y",
               "lb": "XUSB_GAMEPAD_LEFT_SHOULDER", "rb": "XUSB_GAMEPAD_RIGHT_SHOULDER",
               "start": "XUSB_GAMEPAD_START", "back": "XUSB_GAMEPAD_BACK",
               "dpad_up": "XUSB_GAMEPAD_DPAD_UP", "dpad_down": "XUSB_GAMEPAD_DPAD_DOWN",
               "dpad_left": "XUSB_GAMEPAD_DPAD_LEFT", "dpad_right": "XUSB_GAMEPAD_DPAD_RIGHT"}


def neutral_report():
    return {"buttons": [], "lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "lt": 0.0, "rt": 0.0}


def tuned(value, deadzone, sensitivity):
    magnitude = abs(value)
    return 0.0 if magnitude <= deadzone else math.copysign(min(1.0, (magnitude - deadzone) / (1 - deadzone) * sensitivity), value)


def build_report(buttons, axes, steering, profile):
    report = neutral_report()
    tune = profile["tuning"]
    for axis in ["lx", "ly", "rx", "ry"]:
        value = steering if axis == "lx" and profile["layout"] == "racing" else axes.get(axis, 0)
        report[axis] = tuned(value, tune["deadzone"], tune["sensitivity"])
    for x, y in [("lx", "ly"), ("rx", "ry")]:
        length = math.hypot(report[x], report[y])
        if length > 1:
            report[x] /= length; report[y] /= length
    if tune["invert_y"]:
        report["ry"] *= -1
    report["lt"], report["rt"] = axes.get("lt", 0), axes.get("rt", 0)
    pressed = set()
    for action in buttons:
        target = profile["pad_mapping"].get(action)
        if target in {"lt", "rt"}:
            report[target] = 1.0
        elif target:
            pressed.add(target)
    report["buttons"] = sorted(pressed)
    return report


class VirtualXboxBackend:
    def __init__(self):
        self.available = sys.platform == "win32"
        self.pad = None
        self.module = None
        self.error = ""

    @property
    def connected(self):
        return self.pad is not None

    def diagnostics(self):
        installed = importlib.util.find_spec("vgamepad") is not None
        return {"supported": self.available, "package_installed": installed, "connected": self.connected,
                "error": self.error, "dependency_status": "ViGEmBus is retired upstream; this backend is optional."}

    def connect(self):
        if self.connected:
            return
        if not self.available:
            raise RuntimeError("Xbox output currently requires Windows.")
        try:
            self.module = importlib.import_module("vgamepad")
            self.pad = self.module.VX360Gamepad()
            self.send(neutral_report())
            self.error = ""
        except Exception as exc:
            self.pad = None
            self.error = f"Xbox output could not connect: {exc}. See docs/GAMEPAD_SETUP.md."
            raise RuntimeError(self.error) from exc

    def send(self, report):
        if not self.connected:
            raise RuntimeError("Connect the virtual Xbox controller first.")
        self.pad.reset()
        self.pad.left_joystick_float(x_value_float=report["lx"], y_value_float=-report["ly"])
        self.pad.right_joystick_float(x_value_float=report["rx"], y_value_float=-report["ry"])
        self.pad.left_trigger_float(value_float=report["lt"])
        self.pad.right_trigger_float(value_float=report["rt"])
        for button in report["buttons"]:
            self.pad.press_button(button=getattr(self.module.XUSB_BUTTON, PAD_BUTTONS[button]))
        self.pad.update()

    def disconnect(self):
        if self.connected:
            try:
                self.send(neutral_report())
            finally:
                self.pad = None  # CPython releases the target through vgamepad's destructor.


class GamepadEngine:
    def __init__(self, focus, backend=None):
        self.focus = focus
        self.backend = backend or VirtualXboxBackend()
        self.armed = False
        self.target = 0
        self.target_title = ""
        self.error = ""
        self.report = neutral_report()
        self.neutral_pending = False

    def disarm(self):
        self.armed = False; self.target = 0; self.target_title = ""
        if self.backend.connected:
            try:
                self.backend.send(neutral_report())
                self.report = neutral_report(); self.neutral_pending = False
            except Exception as exc:
                self.error = str(exc); self.neutral_pending = True

    def arm(self):
        self.disarm()
        if self.neutral_pending:
            raise RuntimeError("Could not neutralize Xbox output. Disconnect and reconnect it first.")
        if not self.backend.connected or not self.focus.available:
            raise RuntimeError("Connect Xbox output on Windows before enabling it.")
        self.target = self.focus.foreground()
        if not self.target:
            raise RuntimeError("Select your game window and try again.")
        self.target_title = self.focus.title(self.target); self.error = ""; self.armed = True

    def apply(self, report):
        if not self.armed:
            if self.neutral_pending:
                self.disarm()
            return
        if self.focus.foreground() != self.target:
            self.disarm(); return
        if report == self.report:
            return
        try:
            self.backend.send(report); self.report = report
        except Exception as exc:
            self.error = str(exc); self.disarm()
