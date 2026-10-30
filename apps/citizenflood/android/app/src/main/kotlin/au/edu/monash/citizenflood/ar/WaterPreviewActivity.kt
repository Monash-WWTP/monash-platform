package au.edu.monash.citizenflood.ar

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.WindowManager
import android.widget.FrameLayout
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
    private var scene: WaterScene? = null
    private lateinit var container: FrameLayout
    private lateinit var instruction: TextView
    private lateinit var underButton: Button
    private lateinit var modeButton: Button
    private lateinit var pauseButton: Button
    private lateinit var input: DepthInput
    private val renderControls = ArrayList<Button>()
    private var paused = false
    private var underwater = false
    private var basic = false
    private var resumed = false
    private var sceneGeneration = 0
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!DepthLaunch.isCurrent(intent.getLongExtra("launchToken", -1))) { finish(); return }
        val parsed = DepthInput.parse(intent.getFloatExtra("depthM", Float.NaN),
            intent.getStringExtra("reference"), intent.getStringExtra("contextLabel"))
        if (parsed == null || parsed.metres > 1000f) { finish(); return }
        input = parsed
        active = WeakReference(this)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.decorView.systemUiVisibility = android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(242, 247, 244))
        }
        instruction = TextView(this).apply {
            text = "Preparing water…"
            textSize = 14f; setTextColor(Color.rgb(24, 40, 32))
        }
        container = FrameLayout(this)
        val title = TextView(this).apply {
            text = "${input.metres} m · 3D water preview"
            textSize = 20f; setTextColor(Color.rgb(24, 40, 32))
            setPadding(dp(16), dp(12), dp(16), dp(4))
        }
        root.addView(title)
        root.addView(container, LinearLayout.LayoutParams(-1, 0, 1f))
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
        fun button(label: String, renderAction: Boolean = true, action: () -> Unit) = Button(this).apply {
            text = label; setTextColor(Color.rgb(20, 99, 70))
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.WHITE)
            if (renderAction) { renderControls.add(this); isEnabled = false }
            setOnClickListener { action() }
        }
        fun row(vararg controls: Button) {
            val buttons = LinearLayout(this)
            controls.forEach { buttons.addView(it) }
            panel.addView(HorizontalScrollView(this).apply { addView(buttons) })
        }
        pauseButton = button("Pause") {
            paused = !paused; pauseButton.text = if (paused) "Play" else "Pause"
            scene?.command(if (paused) "pause" else "play")
        }
        underButton = button("Underwater") {
            underwater = !underwater; underButton.text = if (underwater) "Above water" else "Underwater"
            scene?.command(if (underwater) "underwater" else "above")
        }
        row(button("Ripple") { scene?.command("ripple") }, pauseButton, underButton,
            button("Reset") {
                paused = false; underwater = false; pauseButton.text = "Pause"; underButton.text = "Underwater"
                scene?.command("reset")
            })
        val viewControls = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; visibility = android.view.View.GONE }
        panel.addView(button("View controls", false) {
            viewControls.visibility = if (viewControls.visibility == android.view.View.GONE) android.view.View.VISIBLE else android.view.View.GONE
        })
        val viewButtons = LinearLayout(this)
        listOf("Rotate left" to "rotateLeft", "Rotate right" to "rotateRight",
            "View higher" to "viewHigher", "View lower" to "viewLower",
            "Zoom in" to "zoomIn", "Zoom out" to "zoomOut")
            .forEach { (label, command) -> viewButtons.addView(button(label) { scene?.command(command) }) }
        viewControls.addView(HorizontalScrollView(this).apply { addView(viewButtons) })
        modeButton = button("Basic graphics", false) { loadScene(!basic) }
        viewControls.addView(modeButton)
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
        loadScene(false)
    }

    private fun controlsReady() {
        renderControls.forEach { it.isEnabled = true }
        underButton.isEnabled = !basic && input.metres > 0f
        instruction.text = if (basic) "Basic graphics · drag to rotate · pinch to zoom"
            else "Tap water · drag to rotate · pinch to zoom"
    }

    private fun loadScene(useBasic: Boolean) {
        val generation = ++sceneGeneration
        scene?.destroy(); scene = null; container.removeAllViews()
        basic = useBasic; paused = false; underwater = false
        pauseButton.text = "Pause"; underButton.text = "Underwater"
        modeButton.text = if (basic) "Full graphics" else "Basic graphics"
        renderControls.forEach { it.isEnabled = false }
        instruction.text = "Preparing water…"
        fun current() = generation == sceneGeneration && !isDestroyed && !isFinishing
        val newScene = if (basic) BasicWaterScene(this, input.metres) {
            runOnUiThread {
                if (current()) {
                    scene?.pause(); renderControls.forEach { it.isEnabled = false }
                    instruction.text = "3D rendering unavailable. Close to return to your report."
                }
            }
        } else try {
            WebWaterScene(this, input.metres, {
                if (current()) controlsReady()
            }, {
                if (current()) loadScene(true)
            })
        } catch (_: Exception) {
            loadScene(true); return
        }
        scene = newScene
        container.addView(newScene.view, FrameLayout.LayoutParams(-1, -1))
        if (resumed) newScene.resume() else newScene.pause()
        if (basic) controlsReady()
    }

    override fun onResume() {
        super.onResume()
        if (!DepthLaunch.isCurrent(intent.getLongExtra("launchToken", -1))) { finish(); return }
        resumed = true; scene?.resume()
    }
    override fun onPause() {
        resumed = false; scene?.pause()
        super.onPause()
    }
    override fun onDestroy() {
        sceneGeneration++; scene?.destroy(); scene = null
        if (active.get() === this) active.clear()
        super.onDestroy()
    }
}
