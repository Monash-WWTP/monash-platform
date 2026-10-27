package au.edu.monash.citizenflood.ar

import java.lang.ref.WeakReference
import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.pm.PackageManager
import android.graphics.Color
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.view.Gravity
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.FrameLayout
import android.widget.TextView
import android.widget.ScrollView
import android.widget.HorizontalScrollView
import android.text.TextUtils
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session

/** Optional local illustration. No capture, location or upload functionality. */
class DepthPreviewActivity : Activity() {
    companion object {
        private var active = WeakReference<DepthPreviewActivity>(null)
        fun closeActive() {
            DepthLaunch.invalidate()
            active.get()?.let { activity -> activity.runOnUiThread { activity.finish() } }
        }
    }
    private var session: Session? = null
    private lateinit var surface: GLSurfaceView
    private lateinit var renderer: DepthRenderer
    private lateinit var status: TextView
    private lateinit var confirm: Button
    private var installRequested = false
    private var failed = false
    private var running = false
    private var destroyed = false
    private var lastStatus = ""
    private val green = Color.rgb(20, 99, 70)
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!DepthLaunch.isCurrent(intent.getLongExtra("launchToken", -1))) { finish(); return }
        active = WeakReference(this)
        val input = DepthInput.parse(intent.getFloatExtra("depthM", Float.NaN),
            intent.getStringExtra("reference"), intent.getStringExtra("contextLabel"))
        if (input == null) { finish(); return }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        surface = GLSurfaceView(this).apply {
            setEGLContextClientVersion(2)
            setEGLConfigChooser(8, 8, 8, 8, 16, 0)
            preserveEGLContextOnPause = true
        }
        renderer = DepthRenderer(input.metres, { statusText ->
            if (statusText != lastStatus) {
                lastStatus = statusText
                runOnUiThread { if (!destroyed) status.text = statusText }
            }
        }, { available -> runOnUiThread { if (!destroyed) confirm.isEnabled = available } },
            { runOnUiThread { if (!destroyed) fail("The camera preview stopped. Close and retry; your report is unchanged.") } })
        surface.setRenderer(renderer)
        surface.setOnTouchListener { _, event ->
            if (event.action == MotionEvent.ACTION_UP) {
                renderer.tap(event.x, event.y)
                surface.performClick()
            }
            true
        }
        val root = FrameLayout(this)
        root.addView(surface)
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(12), dp(20), dp(12))
            setBackgroundColor(Color.rgb(242, 247, 244))
        }
        fun text(value: String, size: Float) = TextView(this).apply {
            text = value; textSize = size; setTextColor(Color.rgb(24, 40, 32))
            setPadding(0, dp(3), 0, dp(3))
        }
        val details = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        val scroll = ScrollView(this).apply {
            isFillViewport = false
            addView(details)
        }
        val infoHeight = minOf(dp(190), (resources.displayMetrics.heightPixels * 0.32f).toInt())
        panel.addView(text("Illustration only · not a measurement or forecast", 14f))
        panel.addView(scroll, LinearLayout.LayoutParams(-1, infoHeight))
        details.addView(text("${input.metres} m · ${input.context}", 20f))
        details.addView(text("Reference: ${input.reference}", 14f).apply {
            maxLines = 2; ellipsize = TextUtils.TruncateAt.END
        })
        status = text("Preparing camera…", 16f).apply { accessibilityLiveRegion = android.view.View.ACCESSIBILITY_LIVE_REGION_POLITE }
        details.addView(status)
        val buttons = LinearLayout(this)
        confirm = Button(this).apply {
            text = "Confirm surface"; isEnabled = false; setTextColor(green)
            setOnClickListener {
                AlertDialog.Builder(this@DepthPreviewActivity)
                    .setTitle("Use this reference surface?")
                    .setMessage("Confirm the selected visible surface matches: ${input.reference}. If submerged or inaccessible, return to the report. Never enter floodwater.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Use surface") { _, _ -> surface.queueEvent { renderer.confirmReference() } }
                    .show()
            }
        }
        buttons.addView(confirm, LinearLayout.LayoutParams(-2, -2))
        buttons.addView(Button(this).apply {
            text = "Reset"; setTextColor(green)
            setOnClickListener { surface.queueEvent { renderer.reset() } }
        }, LinearLayout.LayoutParams(-2, -2))
        panel.addView(HorizontalScrollView(this).apply {
            isFillViewport = true
            addView(buttons)
        })
        panel.addView(Button(this).apply { text = "Close preview"; setTextColor(green); setOnClickListener { finish() } })
        root.addView(panel, FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM))
        // The camera remains edge-to-edge within system bars; controls honour insets.
        root.setOnApplyWindowInsetsListener { view, insets ->
            view.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop,
                insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
            insets
        }
        setContentView(root)
    }

    override fun onResume() {
        super.onResume()
        if (!DepthLaunch.isCurrent(intent.getLongExtra("launchToken", -1))) { finish(); return }
        if (failed || !::surface.isInitialized) return
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CAMERA), 71); return
        }
        startSession()
    }

    private fun startSession() {
        if (failed || running || isFinishing) return
        try {
            if (session == null) {
                when (ArCoreApk.getInstance().requestInstall(this, !installRequested)) {
                    ArCoreApk.InstallStatus.INSTALL_REQUESTED -> { installRequested = true; return }
                    ArCoreApk.InstallStatus.INSTALLED -> Unit
                }
                val created = Session(this)
                session = created
                created.configure(Config(created).apply {
                    planeFindingMode = Config.PlaneFindingMode.HORIZONTAL
                    depthMode = if (created.isDepthModeSupported(Config.DepthMode.AUTOMATIC))
                        Config.DepthMode.AUTOMATIC else Config.DepthMode.DISABLED
                })
            }
            session!!.resume()
            renderer.session = session
            renderer.rotation = windowManager.defaultDisplay.rotation
            surface.onResume()
            running = true
        } catch (_: Exception) {
            fail("AR is unavailable or camera access failed. Close to continue reporting normally.")
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 71) {
            if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) startSession()
            else fail("Camera access was not granted. Close to continue reporting normally.")
        }
    }

    private fun fail(message: String) {
        if (failed) return
        failed = true
        if (running) { surface.onPause(); session?.pause(); running = false }
        renderer.session = null
        surface.visibility = android.view.View.INVISIBLE
        confirm.isEnabled = false
        status.text = message
    }

    override fun onPause() {
        if (::surface.isInitialized && running) {
            surface.onPause() // Stop GL/update before pausing ARCore.
            session?.pause()
            running = false
        }
        super.onPause()
    }
    override fun onDestroy() {
        destroyed = true
        if (active.get() === this) active.clear()
        if (::renderer.isInitialized) renderer.session = null
        session?.close(); session = null
        super.onDestroy()
    }
}
