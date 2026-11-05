package au.edu.monash.citizenflood.ar
import java.nio.ByteBuffer
import org.junit.Assert.*
import org.junit.Test
class DepthRgbaPackingTest {
 @Test fun stridedLittleEndianDepthBecomesRedLowAlphaHighWithoutMovingSource(){
  val source=ByteBuffer.wrap(byteArrayOf(99,0xD0.toByte(),7,0xE8.toByte(),3,88,88,0,0,1,0,88,88));source.position(1)
  val target=ByteBuffer.allocate(16)
  DepthRgbaPacking.copy(source,2,2,6,2,target)
  assertEquals(1,source.position());assertEquals(16,target.remaining())
  assertArrayEquals(byteArrayOf(0xD0.toByte(),0,0,7,0xE8.toByte(),0,0,3,0,0,0,0,1,0,0,0),target.array())
 }
}
