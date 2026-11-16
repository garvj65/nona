"""Validated game profiles and atomic, local-only persistence."""
import copy
import json
import os
import tempfile
import uuid
from pathlib import Path

from windows_input import SCAN_CODES

ACTIONS = {"up", "down", "left", "right", "a", "b", "x", "y", "lb", "rb", "lt", "rt",
           "start", "select", "handbrake", "nitro"}
AXES = {"lx", "ly", "rx", "ry", "lt", "rt"}
PAD_TARGETS = {"a", "b", "x", "y", "lb", "rb", "lt", "rt", "start", "back",
               "dpad_up", "dpad_down", "dpad_left", "dpad_right"}
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
DEFAULT_PAD = {"up": "dpad_up", "down": "dpad_down", "left": "dpad_left", "right": "dpad_right",
               "a": "a", "b": "b", "x": "x", "y": "y", "lb": "lb", "rb": "rb", "lt": "lt", "rt": "rt",
               "start": "start", "select": "back", "handbrake": "x", "nitro": "a"}
TUNING = {"deadzone": 0.12, "sensitivity": 1.0, "invert_y": False}


def mapping_valid(value, allowed):
    return (isinstance(value, dict) and 0 < len(value) <= len(ACTIONS)
            and all(action in ACTIONS and isinstance(target, str) and (not target or target in allowed)
                    for action, target in value.items()))


def validate_profile(value):
    if not isinstance(value, dict):
        raise ValueError("A profile must be a JSON object.")
    name, layout, mode = value.get("name"), value.get("layout"), value.get("output_mode")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("Give the profile a name of 1–80 characters.")
    if (not isinstance(layout, str) or not isinstance(mode, str)
            or layout not in {"gamepad", "racing", "dualstick"} or mode not in {"keyboard", "gamepad"}):
        raise ValueError("Choose a supported layout and output mode.")
    mapping, pad = value.get("mapping"), value.get("pad_mapping")
    if not mapping_valid(mapping, SCAN_CODES) or not mapping_valid(pad, PAD_TARGETS):
        raise ValueError("Profile contains unsupported key or Xbox bindings.")
    tuning = value.get("tuning", TUNING)
    if not isinstance(tuning, dict) or set(tuning) - set(TUNING):
        raise ValueError("Unsupported tuning settings.")
    tuning = {**TUNING, **tuning}
    for key, lo, hi in [("deadzone", 0, .4), ("sensitivity", .25, 2)]:
        if type(tuning[key]) not in {int, float} or not lo <= tuning[key] <= hi:
            raise ValueError(f"{key} must be between {lo} and {hi}.")
    if type(tuning["invert_y"]) is not bool:
        raise ValueError("invert_y must be true or false.")
    return {"name": name.strip(), "layout": layout, "output_mode": mode,
            "mapping": dict(mapping), "pad_mapping": dict(pad), "tuning": tuning}


def templates():
    names = {"arrows": "Gamepad · Arrows", "wasd": "Gamepad · WASD",
             "racing_arrows": "Racing · Arrows", "racing_wasd": "Racing · WASD"}
    result = {key: {"name": names[key], "layout": "racing" if key.startswith("racing_") else "gamepad",
                    "output_mode": "keyboard", "mapping": dict(mapping),
                    "pad_mapping": dict(DEFAULT_PAD), "tuning": dict(TUNING)} for key, mapping in PROFILES.items()}
    race_pad = {**DEFAULT_PAD, "left": "", "right": "", "up": "rt", "down": "lt", "a": "rt", "b": "lt"}
    result["xbox_racing"] = {**copy.deepcopy(result["racing_arrows"]), "name": "Racing · Xbox analog",
                             "output_mode": "gamepad", "pad_mapping": race_pad}
    result["xbox_standard"] = {**copy.deepcopy(result["wasd"]), "name": "Universal · Xbox dual sticks",
                               "layout": "dualstick", "output_mode": "gamepad"}
    result["platformer"] = {**copy.deepcopy(result["arrows"]), "name": "Platformer · Keyboard",
                            "mapping": {**PROFILES["arrows"], "x": "ctrl", "y": "shift", "lb": "q", "rb": "e"}}
    return result


class ProfileStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.saved = {}
        self.error = ""
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("profiles"), dict):
                    raise ValueError("Unsupported profile file format.")
                for key, value in data["profiles"].items():
                    if not isinstance(key, str) or not key.startswith("saved_") or len(key) > 64:
                        raise ValueError("Invalid saved profile identifier.")
                    self.saved[key] = validate_profile(value)
            except (OSError, ValueError, TypeError) as exc:
                self.saved = {}
                self.error = f"Could not load saved profiles: {exc} Original file was left unchanged."

    def all(self):
        return {**templates(), **copy.deepcopy(self.saved)}

    def get(self, key):
        return copy.deepcopy(self.all()[key])

    def catalogue(self):
        return [{"id": key, "name": value["name"], "layout": value["layout"],
                 "output_mode": value["output_mode"], "saved": key in self.saved} for key, value in self.all().items()]

    def save(self, value, key=None):
        if self.error:
            raise ValueError("Fix or back up the unreadable profile file before saving over it.")
        if key is not None and key not in self.saved:
            raise ValueError("Only an existing saved profile can be replaced.")
        profile = validate_profile(value)
        key = key or "saved_" + uuid.uuid4().hex
        updated = {**self.saved, key: profile}
        if len(updated) > 100:
            raise ValueError("The limit is 100 saved profiles.")
        self._write(updated)
        self.saved = updated
        return key

    def _write(self, profiles):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="profiles-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump({"version": 1, "profiles": profiles}, output, indent=2)
                output.flush(); os.fsync(output.fileno())
            os.replace(temporary, self.path)
        finally:
            Path(temporary).unlink(missing_ok=True)


def default_profile_path():
    base = Path(os.environ["LOCALAPPDATA"]) / "NONA" if os.environ.get("LOCALAPPDATA") else Path.home() / ".local" / "share" / "nona"
    return base / "profiles.json"
