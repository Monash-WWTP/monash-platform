package au.edu.monash.citizenflood.ar
import java.nio.ByteBuffer

/** Portable GLES2/3 upload: low depth byte in R, high byte in A. Zero stays unknown. */
internal object DepthRgbaPacking {
 fun copy(source:ByteBuffer,width:Int,height:Int,rowStride:Int,pixelStride:Int,target:ByteBuffer){
  val start=source.position();target.clear()
  for(y in 0 until height)for(x in 0 until width){
   val offset=start+y*rowStride+x*pixelStride
   target.put(source.get(offset));target.put(0);target.put(0);target.put(source.get(offset+1))
  }
  target.flip()
 }
}
