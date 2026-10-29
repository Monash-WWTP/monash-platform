package au.edu.monash.citizenflood.ar

import android.graphics.SurfaceTexture
import android.opengl.GLES11Ext
import android.opengl.GLES20 as GL
import android.opengl.GLSurfaceView
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicBoolean
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/** Live camera compositing, independent of ARCore. No capture/upload interfaces. */
internal class CameraWaterRenderer(private val textureReady:(SurfaceTexture)->Unit,
 private val firstFrame:()->Unit,private val failed:()->Unit):GLSurfaceView.Renderer {
 @Volatile var cameraTexture:SurfaceTexture?=null;private set
 @Volatile var bufferWidth=1280
 @Volatile var bufferHeight=720
 @Volatile var rotation=90
 @Volatile var level=.55f
 private val frameAvailable=AtomicBoolean(false)
 private var cameraId=0
 private var program=0
 private var quadVbo=0
 private var dummy=0
 private var gpu:GpuWater?=null
 private val clock=GpuWaveClock()
 private var width=1
 private var height=1
 private var sampleStart=0L
 private var renderedFrames=0
 private var cameraFrames=0
 private var hasFrame=false
 private var broken=false
 private var paused=false
 private var seconds=0f
 private var previous=0L
 private var dropTime=0f
 private var pulseTime=-10f
 private val transform=FloatArray(16)
 private val quad=ByteBuffer.allocateDirect(32).order(ByteOrder.nativeOrder()).asFloatBuffer().apply{
  put(floatArrayOf(-1f,-1f,1f,-1f,-1f,1f,1f,1f));position(0)
 }
 fun beginCamera(){hasFrame=false;frameAvailable.set(false)}
 fun pauseWater(value:Boolean){paused=value;clock.pause();previous=0L}
 fun ripple(){gpuAction{it.disturb(0f,0f,.3f,.018f)};pulseTime=seconds}
 fun reset(){gpuAction{it.clear()};clock.pause();seconds=0f;previous=0L;dropTime=0f;pulseTime=-10f;paused=false;level=.55f}
 override fun onSurfaceCreated(gl:GL10?,config:EGLConfig?){
  try{
   cameraTexture?.release();hasFrame=false;frameAvailable.set(false);broken=false;previous=0L;clock.pause()
   val ids=IntArray(1);GL.glGenTextures(1,ids,0);cameraId=ids[0]
   GL.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,cameraId)
   GL.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GL.GL_TEXTURE_MIN_FILTER,GL.GL_LINEAR)
   GL.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
   GL.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GL.GL_TEXTURE_WRAP_S,GL.GL_CLAMP_TO_EDGE)
   GL.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,GL.GL_TEXTURE_WRAP_T,GL.GL_CLAMP_TO_EDGE)
   GL.glGenTextures(1,ids,0);dummy=ids[0];GL.glBindTexture(GL.GL_TEXTURE_2D,dummy)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
   GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA,1,1,0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,ByteBuffer.allocateDirect(4))
   GL.glGenBuffers(1,ids,0);quadVbo=ids[0];GL.glBindBuffer(GL.GL_ARRAY_BUFFER,quadVbo)
   quad.position(0);GL.glBufferData(GL.GL_ARRAY_BUFFER,32,quad,GL.GL_STATIC_DRAW)
   gpu=GpuWater.create(3f,.025f)
   program=compile()
   cameraTexture=SurfaceTexture(cameraId).apply{setOnFrameAvailableListener{frameAvailable.set(true)}}
   textureReady(cameraTexture!!)
  }catch(error:Exception){android.util.Log.e("CameraWater","Graphics initialization failed",error);broken=true;failed()}
 }
 override fun onSurfaceChanged(gl:GL10?,w:Int,h:Int){width=w;height=h;GL.glViewport(0,0,w,h)}
 override fun onDrawFrame(gl:GL10?){
  if(broken)return
  try{
   if(frameAvailable.getAndSet(false)){
    cameraTexture?.updateTexImage();cameraTexture?.getTransformMatrix(transform);cameraFrames++
    if(!hasFrame){hasFrame=true;firstFrame()}
   }
   GL.glClearColor(0f,0f,0f,1f);GL.glClear(GL.GL_COLOR_BUFFER_BIT)
   if(!hasFrame)return
   val now=System.nanoTime()
   val elapsed=if(previous==0L||paused)0f else((now-previous)/1e9f).coerceIn(0f,.05f)
   previous=now;seconds+=elapsed;dropTime+=elapsed
   gpuAction{water->
    if(paused)clock.pause()
    if(dropTime>.8f&&!paused){dropTime=0f;water.disturb(kotlin.math.sin(seconds*.71f),kotlin.math.cos(seconds*.53f),.22f,.006f)}
    water.step(if(paused)0 else clock.tick(now))
   }
   GL.glUseProgram(program);GL.glDisable(GL.GL_DEPTH_TEST);GL.glDisable(GL.GL_BLEND)
   GL.glActiveTexture(GL.GL_TEXTURE0);GL.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,cameraId)
   GL.glUniform1i(location("cameraFeed"),0)
   GL.glActiveTexture(GL.GL_TEXTURE1);GL.glBindTexture(GL.GL_TEXTURE_2D,gpu?.texture?:dummy)
   GL.glUniform1i(location("waterField"),1);GL.glUniform1f(location("gpuWater"),if(gpu!=null)1f else 0f)
   GL.glUniform1f(location("waterLine"),level.coerceIn(.05f,.95f));GL.glUniform1f(location("time"),seconds)
   GL.glUniform1f(location("pulseTime"),pulseTime)
   GL.glUniform1i(location("rotation"),rotation/90)
   val crop=CameraPreviewGeometry.crop(width,height,bufferWidth,bufferHeight,rotation)
   GL.glUniform2f(location("crop"),crop[0],crop[1]);GL.glUniformMatrix4fv(location("cameraTransform"),1,false,transform,0)
   val p=GL.glGetAttribLocation(program,"position");GL.glBindBuffer(GL.GL_ARRAY_BUFFER,quadVbo);GL.glEnableVertexAttribArray(p)
   GL.glVertexAttribPointer(p,2,GL.GL_FLOAT,false,0,0);GL.glDrawArrays(GL.GL_TRIANGLE_STRIP,0,4);GL.glDisableVertexAttribArray(p)
   check(GL.glGetError()==GL.GL_NO_ERROR){"Camera compositor GL error"}
   if(sampleStart==0L)sampleStart=now
   renderedFrames++
   if(now-sampleStart>=4_000_000_000L){
    val elapsedSeconds=(now-sampleStart)/1e9
    android.util.Log.i("CameraWater","Frames ${renderedFrames/elapsedSeconds} camera ${cameraFrames/elapsedSeconds}, ${width}x$height, GPU ${gpu!=null}")
    sampleStart=now;renderedFrames=0;cameraFrames=0
   }
  }catch(error:Exception){android.util.Log.e("CameraWater","Camera rendering stopped",error);broken=true;failed()}
 }
 private fun gpuAction(action:(GpuWater)->Unit):Boolean {
  val water=gpu?:return false
  return try{action(water);true}catch(error:Exception){
   gpu=null;clock.pause();water.close();android.util.Log.w("CameraWater","Using standard water graphics",error);false
  }
 }
 fun releaseTexture(){cameraTexture?.release();cameraTexture=null}
 private fun location(name:String)=GL.glGetUniformLocation(program,name)
 private fun compile():Int{
  fun shader(type:Int,source:String):Int{
   val s=GL.glCreateShader(type);GL.glShaderSource(s,source);GL.glCompileShader(s)
   val ok=IntArray(1);GL.glGetShaderiv(s,GL.GL_COMPILE_STATUS,ok,0)
   if(ok[0]==0){val message=GL.glGetShaderInfoLog(s);GL.glDeleteShader(s);error(message)}
   return s
  }
  val v=shader(GL.GL_VERTEX_SHADER,VERTEX);val f=try{shader(GL.GL_FRAGMENT_SHADER,FRAGMENT)}catch(e:Exception){GL.glDeleteShader(v);throw e}
  val p=GL.glCreateProgram();GL.glAttachShader(p,v);GL.glAttachShader(p,f);GL.glLinkProgram(p)
  GL.glDeleteShader(v);GL.glDeleteShader(f)
  val ok=IntArray(1);GL.glGetProgramiv(p,GL.GL_LINK_STATUS,ok,0)
  if(ok[0]==0){val message=GL.glGetProgramInfoLog(p);GL.glDeleteProgram(p);error(message)}
  return p
 }
 companion object{
 private const val VERTEX="""attribute vec2 position;varying vec2 screen;
 void main(){screen=position*0.5+0.5;gl_Position=vec4(position,0.0,1.0);}"""
 private const val FRAGMENT="""
 #extension GL_OES_EGL_image_external : require
 precision highp float;
 uniform samplerExternalOES cameraFeed;uniform highp sampler2D waterField;uniform mat4 cameraTransform;
 uniform vec2 crop;uniform int rotation;uniform float waterLine;uniform float gpuWater;uniform float time;uniform float pulseTime;
 varying vec2 screen;
 vec3 camera(vec2 uv){
  vec2 p=(clamp(uv,vec2(0.001),vec2(0.999))-0.5)*crop;
  if(rotation==1)p=vec2(-p.y,p.x);else if(rotation==2)p=-p;else if(rotation==3)p=vec2(p.y,-p.x);
  return texture2D(cameraFeed,(cameraTransform*vec4(p+0.5,0.0,1.0)).xy).rgb;
 }
 void main(){
  vec3 original=camera(screen);
  if(screen.y>=waterLine){gl_FragColor=vec4(original,1.0);return;}
  vec2 coord=vec2(screen.x,screen.y/max(waterLine,0.01));
  vec3 n;
  if(gpuWater>0.5){
   vec4 info=texture2D(waterField,coord);
   for(int i=0;i<3;i++){coord+=info.ba*.005;info=texture2D(waterField,coord);}
   n=normalize(vec3(info.b,sqrt(max(0.0,1.0-dot(info.ba,info.ba))),info.a));
  }else{
   vec2 slope=vec2(cos(coord.x*24.0+time*1.5),sin(coord.y*21.0-time*1.2))*.045;
   vec2 d=coord-vec2(.5);float age=max(0.0,time-pulseTime);
   slope+=normalize(d+vec2(.0001))*sin(length(d)*45.0-age*8.0)*exp(-age*1.8)*.12;
   n=normalize(vec3(slope.x,1.0,slope.y));
  }
  float nearLine=clamp(screen.y/max(waterLine,.01),0.0,1.0);
  vec2 distortion=n.xz*.04;
  vec3 transmitted=mix(camera(screen+distortion),vec3(.035,.23,.26),.18);
  vec3 reflected=camera(vec2(screen.x,2.0*waterLine-screen.y)+distortion*.6);
  float fresnel=.12+.7*pow(nearLine,4.0);
  float highlight=pow(max(0.0,dot(n,normalize(vec3(.15,1.0,.1)))),100.0)*.14;
  vec3 water=mix(transmitted,reflected,fresnel)+vec3(highlight);
  float edge=(1.0-smoothstep(waterLine-.008,waterLine,screen.y));
  gl_FragColor=vec4(mix(original,water,edge),1.0);
 }
 """
 }
}
