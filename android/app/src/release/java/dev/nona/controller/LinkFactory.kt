package dev.nona.controller

import android.app.Activity

object LinkFactory { fun create(activity: Activity): ControllerLink = BluetoothLink(activity) }
