package au.edu.monash.citizenflood

import android.content.Intent
import android.os.Build
import au.edu.monash.citizenflood.ar.DepthInput
import au.edu.monash.citizenflood.ar.DepthPreviewActivity
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "citizenflood/depth_preview")
            .setMethodCallHandler { call, result ->
                if (call.method != "open") { result.notImplemented(); return@setMethodCallHandler }
                val input = DepthInput.parse(call.argument<Any>("depthM"),
                    call.argument<Any>("reference"), call.argument<Any>("contextLabel"))
                if (input == null) {
                    result.error("invalid_depth", "Enter a valid depth and reference surface.", null)
                } else if (Build.VERSION.SDK_INT < 24) {
                    result.error("unavailable", "AR requires Android 7 or later. Continue reporting normally.", null)
                } else {
                    try {
                        startActivity(Intent(this, DepthPreviewActivity::class.java)
                            .putExtra("depthM", input.metres).putExtra("reference", input.reference)
                            .putExtra("contextLabel", input.context))
                        result.success(null)
                    } catch (_: Exception) {
                        result.error("unavailable", "AR could not open. Continue reporting normally.", null)
                    }
                }
            }
    }
}
