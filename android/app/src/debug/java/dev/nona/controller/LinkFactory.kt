package dev.nona.controller

import android.app.Activity

object LinkFactory {
    var previewForTests = false
    fun create(activity: Activity): ControllerLink =
        if (previewForTests) PreviewLink() else BluetoothLink(activity)
}

// Instrumentation-only view preview. It never creates a Bluetooth proxy or sends OS input.
class PreviewLink : ControllerLink {
    override val preview = true
    override var changed: (LinkStatus) -> Unit = {}
    override var status = LinkStatus(); private set
    override val ready get() = status.ready
    val reports = mutableListOf<Pair<Int, ByteArray>>()
    private fun update(value: LinkStatus) { status = value; changed(value) }
    override fun start() = update(LinkStatus("registered", true, message = "Choose a paired computer, or pair a new one."))
    override fun computers() = listOf(Computer("preview", "Windows laptop"))
    override fun connect(computer: Computer) = update(LinkStatus("connected", true, computer, "Connected. Open the controller when you're ready."))
    override fun disconnect() = update(LinkStatus("registered", true))
    override fun stop() = update(LinkStatus())
    override fun send(id: Int, report: ByteArray): Boolean { if (!ready) return false; reports.add(id to report.copyOf()); return true }
}
