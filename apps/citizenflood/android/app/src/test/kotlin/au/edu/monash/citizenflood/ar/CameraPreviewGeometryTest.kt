package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class CameraPreviewGeometryTest {
 @Test fun rearSensorRotationAndCropFollowTheDisplay(){
  assertEquals(90,CameraPreviewGeometry.rotation(90,0))
  assertEquals(0,CameraPreviewGeometry.rotation(90,90))
  assertEquals(270,CameraPreviewGeometry.rotation(90,180))
  val portrait=CameraPreviewGeometry.crop(1080,2400,1280,720,90)
  assertEquals(.8f,portrait[0],.001f);assertEquals(1f,portrait[1],.001f)
  val landscape=CameraPreviewGeometry.crop(1920,1080,1280,720,0)
  assertArrayEquals(floatArrayOf(1f,1f),landscape,.001f)
 }
 @Test fun cameraEffectBoundsItsFramebufferBudget(){
  val size=CameraPreviewGeometry.renderSize(1080,2209)
  assertTrue(size[0]*size[1]<=800000)
  assertEquals(1080f/2209,size[0].toFloat()/size[1],.002f)
 }
}
