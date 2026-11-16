"""Small Windows-only SendInput adapter. Importable on other OSes for demo/tests."""
import ctypes
import sys

# Hardware scan codes; the arrow cluster uses the extended-key prefix.
SCAN_CODES = {
    "up": (0x48, True), "down": (0x50, True),
    "left": (0x4B, True), "right": (0x4D, True),
    "w": (0x11, False), "a": (0x1E, False),
    "s": (0x1F, False), "d": (0x20, False),
    "space": (0x39, False), "x": (0x2D, False),
    "enter": (0x1C, False), "p": (0x19, False),
    "shift": (0x2A, False), "ctrl": (0x1D, False), "esc": (0x01, False),
    "r": (0x13, False), "c": (0x2E, False), "z": (0x2C, False),
    "e": (0x12, False), "q": (0x10, False), "f": (0x21, False),
    "b": (0x30, False), "g": (0x22, False), "h": (0x23, False), "i": (0x17, False),
    "j": (0x24, False), "k": (0x25, False), "l": (0x26, False), "m": (0x32, False),
    "n": (0x31, False), "o": (0x18, False), "t": (0x14, False), "u": (0x16, False),
    "v": (0x2F, False), "y": (0x15, False), "tab": (0x0F, False), "backspace": (0x0E, False),
    **{str(value): (code, False) for value, code in zip(range(1, 10), range(0x02, 0x0B))},
    "0": (0x0B, False),
}


class WindowsKeyboard:
    def __init__(self):
        self.available = sys.platform == "win32"
        if not self.available:
            return
        # Use fixed-width fields: Windows LONG/DWORD remain 32-bit on x64.
        u16, u32, i32 = ctypes.c_uint16, ctypes.c_uint32, ctypes.c_int32
        ulong_ptr = ctypes.c_size_t

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", i32), ("dy", i32), ("mouseData", u32),
                        ("dwFlags", u32), ("time", u32), ("dwExtraInfo", ulong_ptr)]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", u16), ("wScan", u16), ("dwFlags", u32),
                        ("time", u32), ("dwExtraInfo", ulong_ptr)]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [("uMsg", u32), ("wParamL", u16), ("wParamH", u16)]

        class INPUTUNION(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

        class INPUT(ctypes.Structure):
            _anonymous_ = ("payload",)
            _fields_ = [("type", u32), ("payload", INPUTUNION)]

        self.INPUT, self.KEYBDINPUT, self.MOUSEINPUT = INPUT, KEYBDINPUT, MOUSEINPUT
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.SendInput.argtypes = [u32, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = u32
        self.user32.GetForegroundWindow.restype = ctypes.c_void_p
        self.user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
        self.user32.GetWindowTextLengthW.restype = ctypes.c_int
        self.user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]

    def foreground(self):
        return int(self.user32.GetForegroundWindow() or 0) if self.available else 0

    def title(self, window):
        if not self.available:
            return ""
        length = self.user32.GetWindowTextLengthW(window)
        buffer = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(window, buffer, length + 1)
        return buffer.value

    def send(self, key, pressed):
        if not self.available:
            raise RuntimeError("Desktop keyboard mode requires Windows.")
        scan, extended = SCAN_CODES[key]
        flags = 0x0008 | (0x0001 if extended else 0) | (0 if pressed else 0x0002)
        event = self.INPUT(type=1)
        event.ki = self.KEYBDINPUT(0, scan, flags, 0, 0)
        if self.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise OSError(ctypes.get_last_error(), "Windows did not accept the keyboard input")

    def _mouse(self, dx=0, dy=0, flags=0):
        if not self.available:
            raise RuntimeError("Desktop mouse mode requires Windows.")
        event = self.INPUT(type=0)
        event.mi = self.MOUSEINPUT(dx, dy, 0, flags, 0, 0)
        if self.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise OSError(ctypes.get_last_error(), "Windows did not accept the mouse input")

    def mouse_move(self, dx, dy):
        self._mouse(dx, dy, 0x0001)  # Relative motion; never warp the cursor.

    def mouse_right(self, pressed):
        self._mouse(flags=0x0008 if pressed else 0x0010)


class InputEngine:
    """Own injected keys/right-click; release on focus/profile/session transitions."""
    def __init__(self, backend=None):
        self.backend = backend or WindowsKeyboard()
        self.held = set()
        self.armed = False
        self.target = 0
        self.target_title = ""
        self.error = ""
        self.right_held = False
        self.mouse_remainder = [0.0, 0.0]

    def release_all(self):
        self.mouse_remainder = [0.0, 0.0]
        if self.right_held:
            try:
                self.backend.mouse_right(False)
                self.right_held = False
            except OSError as exc:
                self.error = str(exc)
        for key in sorted(self.held.copy()):
            try:
                self.backend.send(key, False)
                self.held.remove(key)
            except OSError as exc:
                self.error = str(exc)

    def disarm(self):
        self.armed = False
        self.target = 0
        self.target_title = ""
        self.release_all()

    def arm(self):
        self.disarm()
        if self.held or self.right_held:
            raise RuntimeError("Windows did not release previous inputs. Stop and try again.")
        if not self.backend.available:
            raise RuntimeError("Desktop keyboard mode requires Windows.")
        self.target = self.backend.foreground()
        if not self.target:
            raise RuntimeError("No foreground window found. Try again with your game selected.")
        self.target_title = self.backend.title(self.target)
        self.error = ""
        self.armed = True

    def apply(self, desired):
        if not self.armed:
            self.release_all()
            return
        if self.backend.foreground() != self.target:
            self.disarm()
            return
        try:
            for key in sorted(self.held - desired):
                self.backend.send(key, False)
                self.held.remove(key)
            for key in sorted(desired - self.held):
                self.backend.send(key, True)
                self.held.add(key)
        except OSError as exc:
            self.error = str(exc)
            self.disarm()

    def apply_pointer(self, dx=0, dy=0, right=False):
        if not self.armed:
            self.release_all()
            return
        if self.backend.foreground() != self.target:
            self.disarm()
            return
        try:
            if right != self.right_held:
                self.backend.mouse_right(right)
                self.right_held = right
                if not right:
                    self.mouse_remainder = [0.0, 0.0]
            values = [dx + self.mouse_remainder[0], dy + self.mouse_remainder[1]]
            steps = [int(value) for value in values]
            self.mouse_remainder = [value - step for value, step in zip(values, steps)]
            if any(steps):
                self.backend.mouse_move(*steps)
        except OSError as exc:
            self.error = str(exc)
            self.disarm()
