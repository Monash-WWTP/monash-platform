package au.edu.monash.citizenflood

import android.content.Intent
import android.os.Build
import au.edu.monash.citizenflood.ar.DepthLaunch
import au.edu.monash.citizenflood.ar.DepthInput
import au.edu.monash.citizenflood.ar.WaterPreviewActivity
import au.edu.monash.citizenflood.ar.DepthPreviewActivity
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "citizenflood/depth_preview")
            .setMethodCallHandler { call, result ->
                if (call.method == "close") {
                    DepthPreviewActivity.closeActive()
                    WaterPreviewActivity.closeActive()
                    result.success(null)
                    return@setMethodCallHandler
                }
                if (call.method != "open" && call.method != "open3d") { result.notImplemented(); return@setMethodCallHandler }
                val input = DepthInput.parse(call.argument<Any>("depthM"),
                    call.argument<Any>("reference"), call.argument<Any>("contextLabel"))
                if (input == null) {
                    result.error("invalid_depth", "Enter a valid depth and reference surface.", null)
                } else if (call.method == "open3d" && input.metres > 1000f) {
                    result.error("unavailable", "3D preview supports depths up to 1000 m. Your report is unchanged.", null)
                } else if (call.method == "open" && Build.VERSION.SDK_INT < 24) {
                    result.error("unavailable", "AR requires Android 7 or later. Continue reporting normally.", null)
                } else {
                    try {
                        DepthPreviewActivity.closeActive()
                        WaterPreviewActivity.closeActive()
                        val launchToken = DepthLaunch.begin()
                        val activity = if (call.method == "open3d") WaterPreviewActivity::class.java else DepthPreviewActivity::class.java
                        startActivity(Intent(this, activity)
                            .putExtra("launchToken", launchToken)
                            .putExtra("depthM", input.metres).putExtra("reference", input.reference)
                            .putExtra("contextLabel", input.context))
                        result.success(null)
                    } catch (_: Exception) {
                        result.error("unavailable", "Preview could not open. Continue reporting normally.", null)
                    }
                }
            }
    }
}
