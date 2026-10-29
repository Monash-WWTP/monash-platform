package au.edu.monash.citizenflood.ar

internal object CameraPreviewGeometry {
 fun renderSize(width:Int,height:Int):IntArray {
  val w=width.coerceAtLeast(1);val h=height.coerceAtLeast(1)
  val scale=minOf(1.0,kotlin.math.sqrt(800000.0/(w.toDouble()*h)))
  return intArrayOf((w*scale).toInt().coerceAtLeast(1),(h*scale).toInt().coerceAtLeast(1))
 }
 fun rotation(sensor:Int,displayDegrees:Int)=(sensor-displayDegrees+360)%360
 fun crop(viewW:Int,viewH:Int,bufferW:Int,bufferH:Int,rotation:Int):FloatArray {
  val rotated=rotation%180!=0
  val source=(if(rotated)bufferH else bufferW).toFloat()/(if(rotated)bufferW else bufferH).coerceAtLeast(1)
  val target=viewW.toFloat()/viewH.coerceAtLeast(1)
  return floatArrayOf(minOf(1f,target/source),minOf(1f,source/target))
 }
}
