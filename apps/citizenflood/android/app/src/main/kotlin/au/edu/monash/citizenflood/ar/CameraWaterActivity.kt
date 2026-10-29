package au.edu.monash.citizenflood.ar

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.SurfaceTexture
import android.hardware.camera2.*
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.view.Gravity
import android.view.MotionEvent
import android.view.Surface
import android.view.View
import android.view.WindowManager
import android.widget.*
import java.lang.ref.WeakReference

/** Camera2 + local GLES effect. No ARCore, capture, microphone or upload path. */
class CameraWaterActivity:Activity(){
 companion object {
  private var active=WeakReference<CameraWaterActivity>(null)
  fun closeActive(){DepthLaunch.invalidate();active.get()?.let{a->a.runOnUiThread{a.finish()}}}
 }
 private lateinit var surface:GLSurfaceView
 private lateinit var renderer:CameraWaterRenderer
 private lateinit var status:TextView
 private lateinit var retry:Button
 private var device:CameraDevice?=null
 private var session:CameraCaptureSession?=null
 private var output:Surface?=null
 private var cameraThread:HandlerThread?=null
 private var cameraHandler:Handler?=null
 private var resumed=false
 private var permissionRequested=false
 private var opening=false
 private var generation=0
 private var paused=false
 private fun dp(n:Int)=(n*resources.displayMetrics.density).toInt()
 override fun onCreate(state:Bundle?){
  super.onCreate(state)
  if(!DepthLaunch.isCurrent(intent.getLongExtra("launchToken",-1))){finish();return}
  permissionRequested=state?.getBoolean("permissionRequested",false)?:false
  active=WeakReference(this)
  window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
  window.decorView.systemUiVisibility=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
  val root=FrameLayout(this).apply{setBackgroundColor(Color.WHITE)}
  status=TextView(this).apply{text="Opening camera…";textSize=16f;gravity=Gravity.CENTER;setTextColor(Color.WHITE);setBackgroundColor(0x99000000.toInt());setPadding(dp(16),dp(12),dp(16),dp(12));accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE}
  surface=GLSurfaceView(this).apply{setEGLContextClientVersion(nativeWaterGlVersion(this@CameraWaterActivity));preserveEGLContextOnPause=true;contentDescription="Camera water"}
  renderer=CameraWaterRenderer({texture->runOnUiThread{if(resumed&&!isDestroyed){stopCamera();openCamera(texture)}}},
   {runOnUiThread{if(resumed&&!isDestroyed){status.visibility=View.GONE;retry.visibility=View.GONE}}},
   {runOnUiThread{if(!isDestroyed){stopCamera();showError("Water graphics stopped. Retry or close.")}}})
  surface.setRenderer(renderer)
  surface.addOnLayoutChangeListener{_,left,top,right,bottom,_,_,_,_->
   if(right>left&&bottom>top){val size=CameraPreviewGeometry.renderSize(right-left,bottom-top);surface.holder.setFixedSize(size[0],size[1])}
  }
  root.addView(surface,FrameLayout.LayoutParams(-1,-1))
  val controls=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(12),dp(4),dp(12),dp(8));setBackgroundColor(0xeff2f7f4.toInt());isClickable=true}
  val coverage=SeekBar(this).apply{max=100;progress=55;contentDescription="Water coverage"}
  coverage.setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener{
   override fun onProgressChanged(bar:SeekBar?,progress:Int,fromUser:Boolean){if(fromUser)renderer.level=(progress/100f).coerceIn(.05f,.95f)}
   override fun onStartTrackingTouch(bar:SeekBar?){}
   override fun onStopTrackingTouch(bar:SeekBar?){}
  });controls.addView(coverage,LinearLayout.LayoutParams(-1,dp(48)))
  val row=LinearLayout(this)
  fun button(label:String,action:()->Unit)=Button(this).apply{text=label;textSize=12f;minWidth=0;minimumWidth=0;setPadding(dp(4),0,dp(4),0);setTextColor(Color.rgb(20,99,70));backgroundTintList=android.content.res.ColorStateList.valueOf(Color.WHITE);setOnClickListener{action()}}
  lateinit var pause:Button
  pause=button("Pause"){paused=!paused;pause.text=if(paused)"Play"else"Pause";val value=paused;surface.queueEvent{renderer.pauseWater(value)}}
  listOf(button("Ripple"){surface.queueEvent{renderer.ripple()}},pause,button("Reset"){paused=false;pause.text="Pause";coverage.progress=55;surface.queueEvent{renderer.reset()}},button("Close"){finish()})
   .forEach{row.addView(it,LinearLayout.LayoutParams(0,dp(52),1f))}
  controls.addView(row)
  retry=button("Retry"){
   if(checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)recreate()
   else if(permissionRequested&&!shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)){
    startActivity(android.content.Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,android.net.Uri.parse("package:$packageName")))
   }else{permissionRequested=true;requestPermissions(arrayOf(Manifest.permission.CAMERA),72)}
  }.apply{visibility=View.GONE}
  controls.addView(retry)
  root.addView(controls,FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM))
  root.addView(status,FrameLayout.LayoutParams(-1,-2,Gravity.TOP))
  var downX=0f;var downY=0f;var moved=false
  surface.setOnTouchListener{_,event->
   when(event.actionMasked){
    MotionEvent.ACTION_DOWN->{downX=event.x;downY=event.y;moved=false}
    MotionEvent.ACTION_MOVE->{if(kotlin.math.abs(event.y-downY)>dp(10)||kotlin.math.abs(event.x-downX)>dp(10))moved=true
     if(moved){val level=(1f-event.y/surface.height.coerceAtLeast(1)).coerceIn(.05f,.95f);renderer.level=level;coverage.progress=(level*100).toInt()}}
    MotionEvent.ACTION_UP->{if(!moved)surface.queueEvent{renderer.ripple()};surface.performClick()}
   };true
  }
  root.setOnApplyWindowInsetsListener{v,insets->v.setPadding(insets.systemWindowInsetLeft,insets.systemWindowInsetTop,insets.systemWindowInsetRight,insets.systemWindowInsetBottom);insets}
  setContentView(root)
 }
 private fun showError(message:String){status.text=message;status.visibility=View.VISIBLE;retry.visibility=View.VISIBLE}
 override fun onResume(){
  super.onResume()
  if(!DepthLaunch.isCurrent(intent.getLongExtra("launchToken",-1))){finish();return}
  if(!::surface.isInitialized)return
  resumed=true;cameraThread=HandlerThread("CameraWater").apply{start()};cameraHandler=Handler(cameraThread!!.looper)
  surface.onResume()
  if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){
   if(!permissionRequested){permissionRequested=true;requestPermissions(arrayOf(Manifest.permission.CAMERA),72)}
   else showError("Allow camera access to continue.")
  }else renderer.cameraTexture?.let{openCamera(it)}
 }
 @Suppress("DEPRECATION")
 private fun openCamera(texture:SurfaceTexture){
  if(!resumed||opening||device!=null||checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED)return
  try{
   val manager=getSystemService(CameraManager::class.java)
   val id=manager.cameraIdList.firstOrNull{manager.getCameraCharacteristics(it).get(CameraCharacteristics.LENS_FACING)==CameraCharacteristics.LENS_FACING_BACK}
    ?:throw IllegalStateException("Rear camera unavailable")
   val info=manager.getCameraCharacteristics(id)
   val sizes=info.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)?.getOutputSizes(SurfaceTexture::class.java)?.toList().orEmpty()
   val size=sizes.filter{it.width<=1280&&it.height<=720}.maxByOrNull{it.width.toLong()*it.height}
    ?:sizes.minByOrNull{it.width.toLong()*it.height}?:throw IllegalStateException("Camera preview unavailable")
   val displayDegrees=when(windowManager.defaultDisplay.rotation){Surface.ROTATION_90->90;Surface.ROTATION_180->180;Surface.ROTATION_270->270;else->0}
   renderer.bufferWidth=size.width;renderer.bufferHeight=size.height
   renderer.rotation=CameraPreviewGeometry.rotation(info.get(CameraCharacteristics.SENSOR_ORIENTATION)?:90,displayDegrees)
   texture.setDefaultBufferSize(size.width,size.height)
   val target=Surface(texture);output=target
   val tag=++generation;opening=true;status.text="Opening camera…";status.visibility=View.VISIBLE
   surface.queueEvent{renderer.beginCamera()}
   val handler=cameraHandler?:return
   manager.openCamera(id,object:CameraDevice.StateCallback(){
    override fun onOpened(camera:CameraDevice){runOnUiThread{
     if(!resumed||tag!=generation||isFinishing){camera.close();return@runOnUiThread}
     opening=false;device=camera
     try{
      camera.createCaptureSession(listOf(target),object:CameraCaptureSession.StateCallback(){
       override fun onConfigured(capture:CameraCaptureSession){runOnUiThread{
        if(!resumed||tag!=generation||device!==camera){capture.close();return@runOnUiThread}
        session=capture
        try{
         val request=camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW).apply{
          addTarget(target);set(CaptureRequest.CONTROL_MODE,CaptureRequest.CONTROL_MODE_AUTO)
          if(info.get(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES)?.contains(CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)==true)
           set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)
         }.build()
         capture.setRepeatingRequest(request,null,handler)
         android.util.Log.i("CameraWater","Rear camera $id ${size.width}x${size.height}, rotation ${renderer.rotation}")
        }catch(_:Exception){stopCamera();showError("Camera preview unavailable. Retry or close.")}
       }}
       override fun onConfigureFailed(capture:CameraCaptureSession){capture.close();runOnUiThread{if(tag==generation){stopCamera();showError("Camera preview unavailable. Retry or close.")}}}
      },handler)
     }catch(_:Exception){stopCamera();showError("Camera preview unavailable. Retry or close.")}
    }}
    override fun onDisconnected(camera:CameraDevice){camera.close();runOnUiThread{if(tag==generation){stopCamera();showError("Camera disconnected. Retry or close.")}}}
    override fun onError(camera:CameraDevice,error:Int){camera.close();runOnUiThread{if(tag==generation){stopCamera();showError("Camera unavailable. Retry or close.")}}}
   },handler)
  }catch(_:Exception){stopCamera();showError("Camera unavailable. Retry or close.")}
 }
 private fun stopCamera(){
  generation++;opening=false
  try{session?.stopRepeating()}catch(_:Exception){}
  session?.close();session=null;device?.close();device=null;output?.release();output=null
 }
 override fun onRequestPermissionsResult(code:Int,permissions:Array<out String>,results:IntArray){
  super.onRequestPermissionsResult(code,permissions,results)
  if(code==72&&resumed){if(results.firstOrNull()==PackageManager.PERMISSION_GRANTED)renderer.cameraTexture?.let{openCamera(it)}
   else showError("Allow camera access to continue.")}
 }
 override fun onSaveInstanceState(state:Bundle){state.putBoolean("permissionRequested",permissionRequested);super.onSaveInstanceState(state)}
 override fun onPause(){
  resumed=false;stopCamera()
  if(::surface.isInitialized)surface.onPause()
  cameraThread?.quitSafely();cameraThread?.join(1000);cameraThread=null;cameraHandler=null
  super.onPause()
 }
 override fun onDestroy(){
  if(::renderer.isInitialized)renderer.releaseTexture()
  if(active.get()===this)active.clear()
  super.onDestroy()
 }
}
