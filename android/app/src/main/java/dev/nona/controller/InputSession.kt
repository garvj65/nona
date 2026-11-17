package dev.nona.controller

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.roundToInt
import kotlin.math.sin

enum class ControlProfile(val title: String) { MOVE_LOOK("Move & look"), RACING("Racing") }

class InputSession(
    private val sink: ReportSink,
    private val clock: () -> Long = { System.nanoTime() / 1_000_000 },
    private val failed: () -> Unit = {}
) {
    var active = false; private set
    var profile = ControlProfile.MOVE_LOOK
        set(value) { pause(); field = value }
    var holdRight = true
    var lookSpeed = 1f
    /** Racing only: duty-cycle the arrow key so keyboard games see proportional steering. */
    var pulsedSteering = true
    private var steer = 0f
    private var steerSign = 0
    private var pulseStart = 0L
    private val actions = mutableSetOf<String>()
    private var horizontal = 0
    private var vertical = 0
    private var lookHeld = false
    private var dx = 0f
    private var dy = 0f
    private var keyboardCache: ByteArray? = null
    private var mouseButtons = false

    fun start(): Boolean {
        pause()
        if (!sink.ready) return false
        active = true
        flush()
        return active
    }

    fun pause() {
        active = false
        actions.clear(); horizontal = 0; vertical = 0; lookHeld = false; dx = 0f; dy = 0f
        steer = 0f; steerSign = 0
        keyboardCache = null; mouseButtons = false
        sink.send(HidReports.KEYBOARD, HidReports.keyboard())
        sink.send(HidReports.MOUSE, HidReports.mouse())
    }

    private fun direction(value: Float, previous: Int): Int = when {
        value > .22f -> 1
        value < -.22f -> -1
        previous == 1 && value > .12f -> 1
        previous == -1 && value < -.12f -> -1
        else -> 0
    }

    fun move(x: Float, y: Float) {
        if (!active || !x.isFinite() || !y.isFinite()) return
        val cx = x.coerceIn(-1f, 1f); val cy = y.coerceIn(-1f, 1f)
        if (profile == ControlProfile.RACING) {
            steer = cx
            horizontal = direction(cx, horizontal); vertical = 0
        } else {
            val (h, v) = StickMath.eightWay(cx, cy, horizontal, vertical)
            horizontal = h; vertical = v
        }
    }

    /** Which steering key is down right now. Full lock holds it; partial lock pulses it. */
    private fun steeringKey(now: Long): Int {
        if (!pulsedSteering) return horizontal
        val sign = when { steer > StickMath.STEER_DEADZONE -> 1; steer < -StickMath.STEER_DEADZONE -> -1; else -> 0 }
        if (sign != steerSign) { steerSign = sign; pulseStart = now } // new press starts "on" for immediate response
        if (sign == 0) return 0
        val duty = StickMath.steerDuty(abs(steer))
        val phase = Math.floorMod(now - pulseStart, StickMath.PULSE_PERIOD_MS)
        return if (phase < duty * StickMath.PULSE_PERIOD_MS) sign else 0
    }

    fun action(name: String, down: Boolean) {
        if (!active || name !in setOf("a", "b", "x", "y")) return
        if (down) actions.add(name) else actions.remove(name)
        flush() // Preserve short taps even between continuous-input ticks.
    }

    fun look(down: Boolean) {
        if (!active) return
        lookHeld = down && profile == ControlProfile.MOVE_LOOK
        if (!lookHeld) { dx = 0f; dy = 0f }
        flush()
    }

    fun camera(x: Float, y: Float) {
        if (!active || !lookHeld || !x.isFinite() || !y.isFinite()) return
        dx = (dx + x * lookSpeed).coerceIn(-127f, 127f)
        dy = (dy + y * lookSpeed).coerceIn(-127f, 127f)
    }

    fun flush() {
        if (!active) return
        if (!sink.ready) { pause(); failed(); return }
        val keys = mutableSetOf<Int>()
        var modifiers = 0
        if (profile == ControlProfile.MOVE_LOOK) {
            if (horizontal < 0) keys.add(0x04) else if (horizontal > 0) keys.add(0x07)
            if (vertical < 0) keys.add(0x1A) else if (vertical > 0) keys.add(0x16)
            if ("a" in actions) keys.add(0x2C)
            if ("b" in actions) modifiers = 2
            if ("x" in actions) keys.add(0x08)
            if ("y" in actions) keys.add(0x14)
        } else {
            val steering = steeringKey(clock())
            if (steering < 0) keys.add(0x50) else if (steering > 0) keys.add(0x4F)
            if ("a" in actions) keys.add(0x52)
            if ("b" in actions) keys.add(0x51)
            if ("x" in actions) keys.add(0x2C)
            if ("y" in actions) modifiers = 2
        }
        val keyboard = HidReports.keyboard(keys, modifiers)
        if (keyboardCache?.contentEquals(keyboard) != true) {
            if (!sink.send(HidReports.KEYBOARD, keyboard)) { pause(); failed(); return }
            keyboardCache = keyboard
        }
        val x = dx.toInt(); val y = dy.toInt()
        dx -= x; dy -= y
        val right = lookHeld && holdRight
        if (x != 0 || y != 0 || right != mouseButtons) {
            if (!sink.send(HidReports.MOUSE, HidReports.mouse(x, y, right))) { pause(); failed(); return }
            mouseButtons = right
        }
    }
}

object StickMath {
    const val STEER_DEADZONE = .12f
    const val PULSE_PERIOD_MS = 100L
    private const val SECTOR = PI / 4
    private const val KEEP = PI / 8 + PI / 24 // 22.5° sector half-width + 7.5° hysteresis

    /**
     * Map a radial stick to 8-way WASD. Per-axis thresholds made "straight ahead" leak into
     * strafing once the thumb drifted ~13°; 45° sectors give every direction equal room.
     */
    fun eightWay(x: Float, y: Float, previousH: Int = 0, previousV: Int = 0): Pair<Int, Int> {
        val length = hypot(x, y)
        val wasActive = previousH != 0 || previousV != 0
        if (!length.isFinite() || length < if (wasActive) .12f else .22f) return 0 to 0
        val angle = atan2(y.toDouble(), x.toDouble())
        if (wasActive) {
            val previous = atan2(previousV.toDouble(), previousH.toDouble())
            var gap = abs(angle - previous) % (2 * PI)
            if (gap > PI) gap = 2 * PI - gap
            if (gap <= KEEP) return previousH to previousV
        }
        val centre = (angle / SECTOR).roundToInt() * SECTOR
        return cos(centre).roundToInt() to sin(centre).roundToInt()
    }

    /** 0.12 → 15% key-down time, 0.9+ → held continuously. */
    fun steerDuty(magnitude: Float): Float = when {
        !magnitude.isFinite() || magnitude <= STEER_DEADZONE -> 0f
        magnitude >= .9f -> 1f
        else -> .15f + .85f * (magnitude - STEER_DEADZONE) / (.9f - STEER_DEADZONE)
    }
}

object MotionMath {
    fun gyro(x: Float, y: Float, rotation: Int, seconds: Float): Pair<Float, Float> {
        if (!x.isFinite() || !y.isFinite() || !seconds.isFinite() || seconds <= 0 || seconds > .15f) return 0f to 0f
        val angle = rotation * Math.PI / 2
        val yaw = -x * kotlin.math.sin(angle) + y * kotlin.math.cos(angle)
        val pitch = x * kotlin.math.cos(angle) + y * kotlin.math.sin(angle)
        fun value(rate: Double): Float {
            val degrees = Math.toDegrees(rate)
            return if (abs(degrees) < .6) 0f else (degrees.coerceIn(-360.0, 360.0) * minOf(seconds, .05f) * 3).toFloat().coerceIn(-48f, 48f)
        }
        return value(yaw) to value(pitch)
    }
}
