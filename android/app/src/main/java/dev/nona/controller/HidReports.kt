package dev.nona.controller

object HidReports {
    const val KEYBOARD = 1
    const val MOUSE = 2
    // Standard keyboard (6-key rollover + modifiers) and relative three-button mouse.
    val descriptor: ByteArray = ("05 01 09 06 A1 01 85 01 05 07 19 E0 29 E7 15 00 25 01 75 01 95 08 81 02 " +
        "75 08 95 01 81 01 05 08 19 01 29 05 75 01 95 05 91 02 75 03 95 01 91 01 " +
        "05 07 19 00 29 73 15 00 25 73 75 08 95 06 81 00 C0 " +
        "05 01 09 02 A1 01 85 02 09 01 A1 00 05 09 19 01 29 03 15 00 25 01 75 01 95 03 81 02 " +
        "75 05 95 01 81 01 05 01 09 30 09 31 09 38 15 81 25 7F 75 08 95 03 81 06 C0 C0")
        .split(' ').map { it.toInt(16).toByte() }.toByteArray()

    fun keyboard(keys: Set<Int> = emptySet(), modifiers: Int = 0): ByteArray {
        require(keys.size <= 6 && keys.all { it in 4..0x73 } && modifiers in 0..255)
        return ByteArray(8).also { report ->
            report[0] = modifiers.toByte()
            keys.sorted().forEachIndexed { index, key -> report[index + 2] = key.toByte() }
        }
    }

    fun mouse(dx: Int = 0, dy: Int = 0, right: Boolean = false): ByteArray {
        require(dx in -127..127 && dy in -127..127)
        return byteArrayOf(if (right) 2 else 0, dx.toByte(), dy.toByte(), 0)
    }
}

interface ReportSink {
    val ready: Boolean
    fun send(id: Int, report: ByteArray): Boolean
}
