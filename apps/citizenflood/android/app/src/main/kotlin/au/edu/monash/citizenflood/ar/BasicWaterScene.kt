package au.edu.monash.citizenflood.ar

import android.content.Context
import android.opengl.GLSurfaceView
import android.view.MotionEvent
import android.view.ScaleGestureDetector

/** Compatibility path for devices that cannot render the full floating-point WebGL effect. */
class BasicWaterScene(context: Context, depthM: Float, failed: () -> Unit) : WaterScene {
    private val surface = GLSurfaceView(context).apply {
        setEGLContextClientVersion(2);setEGLConfigChooser(8,8,8,8,16,0)
        preserveEGLContextOnPause = true
        contentDescription = "Illustrative 3D water scene. View controls are below."
    }
    override val view = surface
    private val renderer = DepthRenderer(depthM, {}, {}, failed, standalone = true)
    private var lastX=0f
    private var lastY=0f
    private var destroyed=false
    init {
        surface.setRenderer(renderer)
        val scale=ScaleGestureDetector(context,object:ScaleGestureDetector.SimpleOnScaleGestureListener(){
            override fun onScale(detector:ScaleGestureDetector):Boolean {
                val factor=detector.scaleFactor;surface.queueEvent{renderer.zoom(factor)};return true
            }
        })
        surface.setOnTouchListener { _,event ->
            scale.onTouchEvent(event)
            if(event.actionMasked==MotionEvent.ACTION_MOVE&&event.pointerCount==1&&!scale.isInProgress){
                val dx=(event.x-lastX)/context.resources.displayMetrics.density*.008f
                val dy=(event.y-lastY)/context.resources.displayMetrics.density*.008f
                surface.queueEvent{renderer.rotate(dx,dy)}
            }
            lastX=event.x;lastY=event.y
            if(event.actionMasked==MotionEvent.ACTION_UP)surface.performClick()
            true
        }
    }
    override fun command(name:String) {
        if(destroyed)return
        surface.queueEvent {
            when(name){
                "ripple"->renderer.addRipple()
                "pause"->renderer.setPaused(true)
                "play"->renderer.setPaused(false)
                "reset"->renderer.resetScene()
                "rotateLeft"->renderer.rotate(-.2f,0f)
                "rotateRight"->renderer.rotate(.2f,0f)
                "viewHigher"->renderer.rotate(0f,.15f)
                "viewLower"->renderer.rotate(0f,-.15f)
                "zoomIn"->renderer.zoom(1.2f)
                "zoomOut"->renderer.zoom(1f/1.2f)
            }
        }
    }
    override fun resume(){if(!destroyed)surface.onResume()}
    override fun pause(){if(!destroyed)surface.onPause()}
    override fun destroy(){if(!destroyed){surface.onPause();destroyed=true}}
}
