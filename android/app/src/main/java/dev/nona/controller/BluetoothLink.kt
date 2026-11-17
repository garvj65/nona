package dev.nona.controller

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.*
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Handler
import android.os.Looper

data class Computer(val address: String, val name: String)
data class LinkStatus(
    val stage: String = "idle", val registered: Boolean = false,
    val host: Computer? = null, val message: String = "Set up Bluetooth to connect your computer."
) { val ready: Boolean get() = registered && host != null }

interface ControllerLink : ReportSink {
    var changed: (LinkStatus) -> Unit
    val status: LinkStatus
    val preview: Boolean get() = false
    fun start()
    fun computers(): List<Computer>
    fun connect(computer: Computer)
    fun disconnect()
    fun stop()
}

@SuppressLint("MissingPermission") // Each entry checks permission; revocation is caught at the Bluetooth boundary.
class BluetoothLink(private val context: Context) : ControllerLink {
    private val adapter = context.getSystemService(BluetoothManager::class.java)?.adapter
    private val preferences = context.getSharedPreferences("nona-host", Context.MODE_PRIVATE)
    private var proxy: BluetoothHidDevice? = null
    private var selected: BluetoothDevice? = null
    private var connected: BluetoothDevice? = null
    private var wanted = false
    private var requesting = false
    private var epoch = 0
    private val timer = Handler(Looper.getMainLooper())
    private var keyboard = HidReports.keyboard()
    private var mouse = HidReports.mouse()
    override var changed: (LinkStatus) -> Unit = {}
    override var status = LinkStatus(); private set
    override val ready: Boolean get() = wanted && status.ready && proxy != null && connected?.address == selected?.address

    private fun permitted() = Build.VERSION.SDK_INT < 31 ||
        context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED

    private fun update(value: LinkStatus) { status = value; changed(value) }
    private fun host(device: BluetoothDevice) = Computer(device.address, (device.name ?: "Windows computer").take(80))

    override fun start() {
        if (!permitted()) { update(LinkStatus("permission", message = "Allow Nearby devices to connect to your PC.")); return }
        if (adapter == null) { update(LinkStatus("unsupported", message = "Bluetooth is not available on this phone.")); return }
        try {
            if (!adapter.isEnabled) { update(LinkStatus("disabled", message = "Turn on Bluetooth to continue.")); return }
            wanted = true
            if (status.registered || requesting) return
            if (proxy != null) { stop(); wanted = true }
            requesting = true
            val generation = ++epoch
            update(LinkStatus("preparing", message = "Preparing the phone controller…"))
            val accepted = adapter.getProfileProxy(context, object : BluetoothProfile.ServiceListener {
                override fun onServiceConnected(profile: Int, service: BluetoothProfile) {
                    val hid = service as? BluetoothHidDevice ?: return
                    if (!wanted || generation != epoch) { adapter.closeProfileProxy(profile, hid); return }
                    requesting = false
                    proxy = hid
                    val sdp = BluetoothHidDeviceAppSdpSettings("NONA Controller", "Phone keyboard and mouse",
                        "NONA", BluetoothHidDevice.SUBCLASS1_COMBO, HidReports.descriptor)
                    try {
                        if (!hid.registerApp(sdp, null, null, context.mainExecutor, callback(hid, generation))) {
                            update(LinkStatus("unsupported", message = "This phone could not start Bluetooth input. Try again, or use the Wi-Fi controller."))
                        }
                    } catch (_: SecurityException) { permissionLost() }
                    catch (_: RuntimeException) { update(LinkStatus("error", message = "Bluetooth input could not start. Turn Bluetooth off and on, then retry.")) }
                }

                override fun onServiceDisconnected(profile: Int) {
                    if (generation != epoch) return
                    proxy = null; connected = null; requesting = false
                    update(LinkStatus("disconnected", message = "Bluetooth service disconnected. Set up Bluetooth again."))
                }
            }, BluetoothProfile.HID_DEVICE)
            if (!accepted) { requesting = false; update(LinkStatus("unsupported", message = "Bluetooth input is not supported by this phone's Bluetooth service.")) }
            else timer.postDelayed({
                if (wanted && generation == epoch && !status.registered) {
                    stop(); update(LinkStatus("error", message = "Bluetooth input did not become ready. Retry setup or use the Wi-Fi controller."))
                }
            }, 12000)
        } catch (_: SecurityException) { permissionLost() }
    }

    private fun callback(hid: BluetoothHidDevice, generation: Int) = object : BluetoothHidDevice.Callback() {
        private fun current() = wanted && generation == epoch && proxy === hid
        override fun onAppStatusChanged(pluggedDevice: BluetoothDevice?, registered: Boolean) {
            if (!current()) return
            if (!registered) { connected = null; update(LinkStatus("disconnected", message = "Bluetooth input paused. Keep NONA open and set up Bluetooth again.")); return }
            update(LinkStatus("registered", registered = true, message = "Choose a paired computer, or pair a new one."))
        }

        override fun onConnectionStateChanged(device: BluetoothDevice, state: Int) {
            if (!current()) return
            try {
                if (device.address != selected?.address || device.bondState != BluetoothDevice.BOND_BONDED) {
                    if (state == BluetoothProfile.STATE_CONNECTED) hid.disconnect(device)
                    return
                }
                when (state) {
                    BluetoothProfile.STATE_CONNECTED -> {
                        connected = device; keyboard = HidReports.keyboard(); mouse = HidReports.mouse()
                        hid.sendReport(device, HidReports.KEYBOARD, keyboard)
                        hid.sendReport(device, HidReports.MOUSE, mouse)
                        preferences.edit().putString("address", device.address).apply()
                        update(LinkStatus("connected", true, host(device), "Connected. Open the controller when you're ready."))
                    }
                    BluetoothProfile.STATE_CONNECTING -> update(LinkStatus("connecting", true, message = "Connecting to ${host(device).name}…"))
                    BluetoothProfile.STATE_DISCONNECTED -> {
                        connected = null
                        update(LinkStatus("registered", true, message = "Computer disconnected. Select it to reconnect."))
                    }
                }
            } catch (_: SecurityException) { permissionLost() }
        }

        override fun onGetReport(device: BluetoothDevice, type: Byte, id: Byte, bufferSize: Int) {
            if (!current() || device.address != connected?.address) return
            try {
                val report = when (id.toInt()) { HidReports.KEYBOARD -> keyboard; HidReports.MOUSE -> mouse; else -> null }
                if (type != BluetoothHidDevice.REPORT_TYPE_INPUT || report == null)
                    hid.reportError(device, BluetoothHidDevice.ERROR_RSP_INVALID_RPT_ID)
                else if (bufferSize > 0 && bufferSize < report.size)
                    hid.reportError(device, BluetoothHidDevice.ERROR_RSP_INVALID_PARAM)
                else hid.replyReport(device, type, id, report)
            } catch (_: SecurityException) { permissionLost() }
        }

        override fun onSetReport(device: BluetoothDevice, type: Byte, id: Byte, data: ByteArray) {
            if (!current() || device.address != connected?.address) return
            try {
                hid.reportError(device, if (type == BluetoothHidDevice.REPORT_TYPE_OUTPUT && id.toInt() == 1 && data.size == 1)
                    BluetoothHidDevice.ERROR_RSP_SUCCESS else BluetoothHidDevice.ERROR_RSP_INVALID_PARAM)
            } catch (_: SecurityException) { permissionLost() }
        }

        override fun onSetProtocol(device: BluetoothDevice, protocol: Byte) {
            if (!current() || device.address != connected?.address || protocol == BluetoothHidDevice.PROTOCOL_REPORT_MODE) return
            disconnect()
            update(LinkStatus("error", true, message = "This computer requested an unsupported input mode. Reconnect or use the Wi-Fi controller."))
        }

        override fun onVirtualCableUnplug(device: BluetoothDevice) {
            if (!current() || device.address != selected?.address) return
            connected = null; selected = null; preferences.edit().remove("address").apply()
            update(LinkStatus("registered", true, message = "Computer removed the connection. Pair again to continue."))
        }
    }

    override fun computers(): List<Computer> {
        if (!permitted() || adapter == null) return emptyList()
        return try {
            val remembered = preferences.getString("address", null)
            adapter.bondedDevices.filter { it.type != BluetoothDevice.DEVICE_TYPE_LE }
                .map(::host).sortedWith(compareBy<Computer> { it.address != remembered }.thenBy { it.name.lowercase() })
        } catch (_: SecurityException) { emptyList() }
    }

    override fun connect(computer: Computer) {
        if (!permitted() || !status.registered || adapter == null) return
        disconnect()
        try {
            val peer = adapter.bondedDevices.firstOrNull { it.address == computer.address } ?: return
            selected = peer
            update(LinkStatus("connecting", true, message = "Connecting to ${computer.name}…"))
            if (proxy?.connect(peer) != true) update(LinkStatus("registered", true, message = "Connection could not start. Try pairing the computer again."))
        } catch (_: SecurityException) { permissionLost() }
    }

    override fun send(id: Int, report: ByteArray): Boolean {
        if (!ready || !permitted() || (id == 1 && report.size != 8) || (id == 2 && report.size != 4) || id !in 1..2) return false
        val peer = connected ?: return false
        return try {
            if (proxy?.sendReport(peer, id, report) != true) false
            else { if (id == 1) keyboard = report.copyOf() else mouse = report.copyOf(); true }
        } catch (_: SecurityException) { permissionLost(); false }
        catch (_: RuntimeException) { false }
    }

    override fun disconnect() {
        send(HidReports.KEYBOARD, HidReports.keyboard()); send(HidReports.MOUSE, HidReports.mouse())
        val peer = connected ?: selected
        connected = null; selected = null
        if (permitted() && peer != null) try { proxy?.disconnect(peer) } catch (_: RuntimeException) { }
        if (status.registered) update(LinkStatus("registered", true, message = "Choose a computer to connect."))
    }

    override fun stop() {
        disconnect(); wanted = false; requesting = false; ++epoch
        val service = proxy; proxy = null
        if (service != null) {
            try { if (permitted()) service.unregisterApp() } catch (_: RuntimeException) { }
            adapter?.closeProfileProxy(BluetoothProfile.HID_DEVICE, service)
        }
        update(LinkStatus("idle", message = "Bluetooth input paused. Open NONA to reconnect."))
    }

    private fun permissionLost() {
        wanted = false; connected = null; requesting = false
        update(LinkStatus("permission", message = "Bluetooth permission changed. Allow Nearby devices to reconnect."))
    }
}
