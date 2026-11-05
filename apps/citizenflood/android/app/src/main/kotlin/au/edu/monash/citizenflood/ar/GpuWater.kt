package au.edu.monash.citizenflood.ar

import android.opengl.GLES20 as GL
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer

/** Native GLES port of Evan Wallace's MIT ping-pong water solver. GL-thread owned. */
internal class GpuWater private constructor(private val patchSize:Float,private val amplitude:Float,private val dataType:Int,private val internalFormat:Int) {
 companion object {
  private const val SIZE=128
  fun create(patchSize:Float,amplitude:Float):GpuWater? {
   // Gfxstream native float targets can terminate the emulator host. Keep its proven compatibility path.
   if(GpuFormats.compatibilityOnly(android.os.Build.HARDWARE))return null
   val units=IntArray(1);GL.glGetIntegerv(GL.GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS,units,0)
   val extensions=GL.glGetString(GL.GL_EXTENSIONS).orEmpty().split(' ')
   if(amplitude<=0f)return null
   val es3=GL.glGetString(GL.GL_VERSION).orEmpty().contains("OpenGL ES 3")
   for(type in GpuFormats.supported(extensions.toSet(),units[0],es3)){
    val format=if(es3){if(type==GL.GL_FLOAT)0x8814 else 0x881A}else GL.GL_RGBA
    val water=GpuWater(patchSize,amplitude,type,format)
    try{water.savedState{water.initialize()};return water}
    catch(error:Exception){
     water.close()
     var count=0;while(count++<8&&GL.glGetError()!=GL.GL_NO_ERROR){}
     android.util.Log.w("NativeGpuWater","GPU format $type unavailable: ${error.message}")
    }
   }
   return null
  }
  private fun buffer(vararg values:Float)=ByteBuffer.allocateDirect(values.size*4).order(ByteOrder.nativeOrder()).asFloatBuffer().apply{put(values);position(0)}
 }
 private val textures=IntArray(2)
 private var front=0
 private var fbo=0
 private var quadVbo=0
 private val programs=ArrayList<Int>()
 private var drop=0
 private var update=0
 private var normal=0
 private val quad=buffer(-1f,-1f,1f,-1f,-1f,1f,1f,1f)
 val texture:Int get()=textures[front]
 private fun initialize(){
  val bufferId=IntArray(1);GL.glGenBuffers(1,bufferId,0);quadVbo=bufferId[0]
  GL.glBindBuffer(GL.GL_ARRAY_BUFFER,quadVbo);quad.position(0);GL.glBufferData(GL.GL_ARRAY_BUFFER,32,quad,GL.GL_STATIC_DRAW)
  val id=IntArray(1);GL.glGenFramebuffers(1,id,0);fbo=id[0]
  GL.glGenTextures(2,textures,0)
  for(t in textures){
   GL.glBindTexture(GL.GL_TEXTURE_2D,t)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_CLAMP_TO_EDGE)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_T,GL.GL_CLAMP_TO_EDGE)
   GL.glTexImage2D(GL.GL_TEXTURE_2D,0,internalFormat,SIZE,SIZE,0,GL.GL_RGBA,dataType,null)
   attach(t);GL.glClearColor(0f,0f,0f,0f);GL.glClear(GL.GL_COLOR_BUFFER_BIT)
  }
  drop=program(GpuWaterShaders.DROP);update=program(GpuWaterShaders.UPDATE);normal=program(GpuWaterShaders.NORMAL)
  // Exercise actual shader execution and float-FBO sampling, not extension names alone.
  disturb(0f,0f,.2f,minOf(.01f,amplitude));step(1)
  probe()
  clear()
  android.util.Log.i("NativeGpuWater","128x128 GPU simulation/readback verified, format $dataType")
 }
 private fun attach(texture:Int){
  GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,fbo)
  GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT0,GL.GL_TEXTURE_2D,texture,0)
  check(GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)==GL.GL_FRAMEBUFFER_COMPLETE){"Floating-point framebuffer unsupported"}
 }
 private fun pass(program:Int,uniforms:()->Unit={}){
  attach(textures[1-front]);GL.glViewport(0,0,SIZE,SIZE)
  GL.glUseProgram(program);GL.glActiveTexture(GL.GL_TEXTURE0);GL.glBindTexture(GL.GL_TEXTURE_2D,texture)
  GL.glUniform1i(GL.glGetUniformLocation(program,"texture"),0)
  GL.glUniform2f(GL.glGetUniformLocation(program,"delta"),1f/SIZE,1f/SIZE)
  GL.glUniform1f(GL.glGetUniformLocation(program,"maxAmplitude"),amplitude)
  GL.glUniform1f(GL.glGetUniformLocation(program,"patchSize"),patchSize)
  uniforms();drawQuad(program);front=1-front
 }
 private fun drawQuad(program:Int){
  val location=GL.glGetAttribLocation(program,"position")
  GL.glBindBuffer(GL.GL_ARRAY_BUFFER,quadVbo);GL.glEnableVertexAttribArray(location)
  GL.glVertexAttribPointer(location,2,GL.GL_FLOAT,false,0,0)
  GL.glDrawArrays(GL.GL_TRIANGLE_STRIP,0,4);GL.glDisableVertexAttribArray(location)
 }
 fun disturb(x:Float,z:Float,radius:Float,strength:Float)=savedState{
  pass(drop){
   GL.glUniform2f(GL.glGetUniformLocation(drop,"center"),x*2f/patchSize,z*2f/patchSize)
   GL.glUniform1f(GL.glGetUniformLocation(drop,"radius"),radius/patchSize)
   GL.glUniform1f(GL.glGetUniformLocation(drop,"strength"),strength.coerceIn(-amplitude,amplitude))
  }
 }
 fun step(count:Int)=savedState{repeat(count.coerceIn(0,6)){pass(update)};pass(normal);check(GL.glGetError()==GL.GL_NO_ERROR){"GPU solver GL error"}}
 fun clear()=savedState{
  GL.glClearColor(0f,0f,0f,0f)
  for(t in textures){attach(t);GL.glClear(GL.GL_COLOR_BUFFER_BIT)}
  front=0
 }
 private fun probe(){
  val p=program("""precision highp float;
   uniform highp sampler2D texture;uniform float maxAmplitude;varying vec2 coord;
   void main(){vec4 field=texture2D(texture,vec2(0.5));float h=field.r;
    gl_FragColor=vec4(h/maxAmplitude*0.25+0.5,(h>0.0&&h<=0.025&&field.g<0.0)?1.0:0.0,0.0,1.0);}
  """)
  val out=IntArray(1);GL.glGenTextures(1,out,0)
  try{
   GL.glBindTexture(GL.GL_TEXTURE_2D,out[0]);GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
   GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
   GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA,1,1,0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,null)
   attach(out[0]);GL.glViewport(0,0,1,1);GL.glUseProgram(p)
   GL.glBindTexture(GL.GL_TEXTURE_2D,texture);GL.glUniform1i(GL.glGetUniformLocation(p,"texture"),0)
   GL.glUniform1f(GL.glGetUniformLocation(p,"maxAmplitude"),amplitude);drawQuad(p)
   val pixel=ByteBuffer.allocateDirect(4);GL.glReadPixels(0,0,1,1,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,pixel)
   check((pixel.get(1).toInt() and 255)==255&&(pixel.get(0).toInt() and 255)>132){"GPU wave readback failed"}
   check(GL.glGetError()==GL.GL_NO_ERROR){"GPU initialization GL error"}
  }finally{GL.glDeleteTextures(1,out,0);GL.glDeleteProgram(p);programs.remove(p)}
 }
 private fun program(fragment:String):Int{
  fun shader(type:Int,source:String):Int{
   val s=GL.glCreateShader(type);GL.glShaderSource(s,source);GL.glCompileShader(s)
   val ok=IntArray(1);GL.glGetShaderiv(s,GL.GL_COMPILE_STATUS,ok,0)
   if(ok[0]==0){val error=GL.glGetShaderInfoLog(s);GL.glDeleteShader(s);error(error)}
   return s
  }
  val v=shader(GL.GL_VERTEX_SHADER,GpuWaterShaders.VERTEX)
  val f=try{shader(GL.GL_FRAGMENT_SHADER,fragment)}catch(e:Exception){GL.glDeleteShader(v);throw e}
  val p=GL.glCreateProgram();GL.glAttachShader(p,v);GL.glAttachShader(p,f);GL.glLinkProgram(p)
  GL.glDeleteShader(v);GL.glDeleteShader(f)
  val ok=IntArray(1);GL.glGetProgramiv(p,GL.GL_LINK_STATUS,ok,0)
  if(ok[0]==0){val error=GL.glGetProgramInfoLog(p);GL.glDeleteProgram(p);error(error)}
  programs.add(p);return p
 }
 private fun <T> savedState(block:()->T):T{
  fun integer(name:Int)=IntArray(1).also{GL.glGetIntegerv(name,it,0)}[0]
  val arrayBuffer=integer(GL.GL_ARRAY_BUFFER_BINDING)
  val framebuffer=integer(GL.GL_FRAMEBUFFER_BINDING);val program=integer(GL.GL_CURRENT_PROGRAM)
  val active=integer(GL.GL_ACTIVE_TEXTURE);GL.glActiveTexture(GL.GL_TEXTURE0)
  val binding=integer(GL.GL_TEXTURE_BINDING_2D)
  val viewport=IntArray(4);GL.glGetIntegerv(GL.GL_VIEWPORT,viewport,0)
  val color=FloatArray(4);GL.glGetFloatv(GL.GL_COLOR_CLEAR_VALUE,color,0)
  val blend=GL.glIsEnabled(GL.GL_BLEND);val depth=GL.glIsEnabled(GL.GL_DEPTH_TEST)
  GL.glDisable(GL.GL_BLEND);GL.glDisable(GL.GL_DEPTH_TEST)
  return try{block()}finally{
   GL.glBindBuffer(GL.GL_ARRAY_BUFFER,arrayBuffer)
   GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,framebuffer);GL.glViewport(viewport[0],viewport[1],viewport[2],viewport[3])
   GL.glClearColor(color[0],color[1],color[2],color[3]);GL.glUseProgram(program)
   GL.glActiveTexture(GL.GL_TEXTURE0);GL.glBindTexture(GL.GL_TEXTURE_2D,binding);GL.glActiveTexture(active)
   if(blend)GL.glEnable(GL.GL_BLEND)else GL.glDisable(GL.GL_BLEND)
   if(depth)GL.glEnable(GL.GL_DEPTH_TEST)else GL.glDisable(GL.GL_DEPTH_TEST)
  }
 }
 fun close(){
  if(quadVbo!=0){GL.glDeleteBuffers(1,intArrayOf(quadVbo),0);quadVbo=0}
  if(fbo!=0){GL.glDeleteFramebuffers(1,intArrayOf(fbo),0);fbo=0}
  GL.glDeleteTextures(2,textures,0);textures.fill(0)
  programs.forEach{GL.glDeleteProgram(it)};programs.clear()
 }
}

internal object GpuFormats {
 fun compatibilityOnly(hardware:String)=hardware=="ranchu"||hardware=="goldfish"
 fun contextVersion(maxVersion:Int,hardware:String)=if(!compatibilityOnly(hardware)&&maxVersion>=0x30000)3 else 2
 fun supported(extensions:Set<String>,vertexUnits:Int,es3:Boolean=false):List<Int> {
  if(vertexUnits<1)return emptyList()
  if(es3)return listOf(5126,5131)
  return listOfNotNull(if("GL_OES_texture_float" in extensions)5126 else null,
   if("GL_OES_texture_half_float" in extensions)0x8D61 else null)
 }
}

internal fun nativeWaterGlVersion(context:android.content.Context):Int {
 val manager=context.getSystemService(android.content.Context.ACTIVITY_SERVICE) as android.app.ActivityManager
 return GpuFormats.contextVersion(manager.deviceConfigurationInfo.reqGlEsVersion,android.os.Build.HARDWARE)
}
