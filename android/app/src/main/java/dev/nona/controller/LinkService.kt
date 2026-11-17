package dev.nona.controller

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

/**
 * Holds no input logic. It exists only to keep NONA's process at foreground-service
 * importance, because Android's HID device service unregisters an app that is no longer
 * visible (AOSP HidDeviceService, FOREGROUND_IMPORTANCE_CUTOFF). Without it, a screen lock
 * or an OEM full-screen pairing prompt drops the Windows connection.
 *
 * Input is still released when the controller leaves the screen; this only keeps the link.
 */
class LinkService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val manager = getSystemService(NotificationManager::class.java)
        manager?.createNotificationChannel(
            NotificationChannel(CHANNEL, "Bluetooth connection", NotificationManager.IMPORTANCE_LOW)
                .apply { description = "Shown while NONA stays connected to your computer." })
        val open = PendingIntent.getActivity(this, 0,
            Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val notification = Notification.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_nona)
            .setContentTitle("NONA is connected")
            .setContentText("Input is paused until you tap Play.")
            .setContentIntent(open)
            .setOngoing(true)
            .build()
        try {
            if (Build.VERSION.SDK_INT >= 29) startForeground(ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE)
            else startForeground(ID, notification)
            running = true
        } catch (_: RuntimeException) {
            // Start refused (background start limits, missing permission): fall back to the
            // 0.6 behaviour, where Android may unregister input once NONA leaves the screen.
            running = false
            stopSelf()
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() { running = false; super.onDestroy() }

    companion object {
        private const val CHANNEL = "nona-link"
        private const val ID = 6
        @Volatile var running = false; private set

        fun start(context: Context) {
            if (running) return
            try { context.startForegroundService(Intent(context, LinkService::class.java)) }
            catch (_: RuntimeException) { }
        }

        fun stop(context: Context) {
            try { context.stopService(Intent(context, LinkService::class.java)) } catch (_: RuntimeException) { }
            running = false
        }
    }
}
