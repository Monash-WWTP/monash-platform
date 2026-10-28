package au.edu.monash.citizenflood.ar

import android.app.Activity
import android.graphics.Color
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.view.Gravity
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import android.view.WindowManager
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import java.lang.ref.WeakReference

/** Camera-free illustrative scene. Never creates an ARCore session or changes a report. */
class WaterPreviewActivity : Activity() {
    companion object {
        private var active = WeakReference<WaterPreviewActivity>(null)
        fun closeActive() {
            DepthLaunch.invalidate()
            active.get()?.let { activity -> activity.runOnUiThread { activity.finish() } }
        }
    }
    private lateinit var surface: GLSurfaceView
    private lateinit var renderer: DepthRenderer
    private var paused = false
    private var failed = false
    private var lastX = 0f
    private var lastY = 0f
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!DepthLaunch.isCurrent(intent.getLongExtra("launchToken", -1))) { finish(); return }
        val input = DepthInput.parse(intent.getFloatExtra("depthM", Float.NaN),
            intent.getStringExtra("reference"), intent.getStringExtra("contextLabel"))
        if (input == null || input.metres > 1000f) { finish(); return }
        active = WeakReference(this)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.decorView.systemUiVisibility = android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(242, 247, 244))
        }
        val instruction = TextView(this).apply {
            text = "Drag to rotate · pinch to zoom"
            textSize = 14f; setTextColor(Color.rgb(24, 40, 32))
        }
        surface = GLSurfaceView(this).apply {
            setEGLContextClientVersion(2)
            setEGLConfigChooser(8, 8, 8, 8, 16, 0)
            preserveEGLContextOnPause = true
            contentDescription = "Illustrative 3D water scene. View controls are below."
        }
        renderer = DepthRenderer(input.metres, {}, {}, {
            runOnUiThread {
                if (!isDestroyed && !failed) {
                    failed = true
                    surface.onPause()
                    instruction.text = "3D rendering is unavailable on this device. Close to return to your report."
                }
            }
        }, standalone = true)
        surface.setRenderer(renderer)
        val scale = ScaleGestureDetector(this, object : ScaleGestureDetector.SimpleOnScaleGestureListener() {
            override fun onScale(detector: ScaleGestureDetector): Boolean {
                val factor = detector.scaleFactor
                surface.queueEvent { renderer.zoom(factor) }
                return true
            }
        })
        surface.setOnTouchListener { _, event ->
            scale.onTouchEvent(event)
            if (event.actionMasked == MotionEvent.ACTION_MOVE && event.pointerCount == 1 && !scale.isInProgress) {
                val dx = (event.x - lastX) / resources.displayMetrics.density * .008f
                val dy = (event.y - lastY) / resources.displayMetrics.density * .008f
                surface.queueEvent { renderer.rotate(dx, dy) }
            }
            lastX = event.x; lastY = event.y
            if (event.actionMasked == MotionEvent.ACTION_UP) surface.performClick()
            true
        }
        val title = TextView(this).apply {
            text = "${input.metres} m · 3D water preview"
            textSize = 20f; setTextColor(Color.rgb(24, 40, 32))
            setPadding(dp(16), dp(12), dp(16), dp(4))
        }
        root.addView(title)
        root.addView(surface, LinearLayout.LayoutParams(-1, 0, 1f))
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(8), dp(16), dp(8))
        }
        panel.addView(TextView(this).apply {
            text = "Illustrative scene · not your location"
            textSize = 14f; setTextColor(Color.rgb(24, 40, 32))
        })
        panel.addView(TextView(this).apply {
            text = "${input.context} · Reference: ${input.reference}"
            textSize = 14f; maxLines = 2
            ellipsize = android.text.TextUtils.TruncateAt.END
            setTextColor(Color.rgb(24, 40, 32))
        })
        panel.addView(instruction)
        fun button(label: String, action: () -> Unit) = Button(this).apply {
            text = label; setTextColor(Color.rgb(20, 99, 70))
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.WHITE)
            setOnClickListener { if (!failed) action() }
        }
        fun row(vararg controls: Button) {
            val buttons = LinearLayout(this)
            controls.forEach { buttons.addView(it) }
            panel.addView(HorizontalScrollView(this).apply { addView(buttons) })
        }
        lateinit var pause: Button
        pause = button("Pause") {
            paused = !paused; pause.text = if (paused) "Play" else "Pause"
            val value = paused
            surface.queueEvent { renderer.setPaused(value) }
        }
        row(button("Ripple") { surface.queueEvent { renderer.addRipple() } }, pause,
            button("Reset") {
                paused = false; pause.text = "Pause"
                surface.queueEvent { renderer.resetScene() }
            })
        val viewControls = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; visibility = android.view.View.GONE }
        panel.addView(button("View controls") {
            viewControls.visibility = if (viewControls.visibility == android.view.View.GONE) android.view.View.VISIBLE else android.view.View.GONE
        })
        val viewButtons = LinearLayout(this)
        listOf(
            "Rotate left" to { renderer.rotate(-.2f, 0f) },
            "Rotate right" to { renderer.rotate(.2f, 0f) },
            "View higher" to { renderer.rotate(0f, .15f) },
            "View lower" to { renderer.rotate(0f, -.15f) },
            "Zoom in" to { renderer.zoom(1.2f) },
            "Zoom out" to { renderer.zoom(1f / 1.2f) },
        ).forEach { (label, action) -> viewButtons.addView(button(label) { surface.queueEvent(action) }) }
        viewControls.addView(HorizontalScrollView(this).apply { addView(viewButtons) })
        panel.addView(viewControls)
        panel.addView(Button(this).apply {
            text = "Close preview"; setTextColor(Color.rgb(20, 99, 70));
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.WHITE); setOnClickListener { finish() }
        })
        val controls = object : ScrollView(this) {
            override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
                val limit = (resources.displayMetrics.heightPixels * .4f).toInt()
                super.onMeasure(widthMeasureSpec, android.view.View.MeasureSpec.makeMeasureSpec(
                    minOf(android.view.View.MeasureSpec.getSize(heightMeasureSpec), limit), android.view.View.MeasureSpec.AT_MOST))
            }
        }.apply { addView(panel) }
        root.addView(controls, LinearLayout.LayoutParams(-1, -2))
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
        if (::surface.isInitialized && !failed) surface.onResume()
    }
    override fun onPause() {
        if (::surface.isInitialized) surface.onPause()
        super.onPause()
    }
    override fun onDestroy() {
        if (active.get() === this) active.clear()
        super.onDestroy()
    }
}
