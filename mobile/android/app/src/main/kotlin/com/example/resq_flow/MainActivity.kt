package com.example.resq_flow

import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val CHANNEL = "resq_flow/mesh"

    override fun configureFlutterEngine(
        flutterEngine: FlutterEngine
    ) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->

            when (call.method) {
                "getPlatform" -> {
                    result.success("android")
                }

                "bluetoothAvailable" -> {
                    result.success(false)
                }

                "bluetoothPermissions" -> {
                    result.success(false)
                }

                "requestBluetoothPermissions" -> {
                    result.success(false)
                }

                "bluetoothStart" -> {
                    result.success(false)
                }

                "bluetoothSend" -> {
                    result.success(false)
                }

                "wifiStart" -> {
                    result.success(false)
                }

                "wifiSend" -> {
                    result.success(false)
                }

                else -> {
                    result.notImplemented()
                }
            }
        }
    }
}
