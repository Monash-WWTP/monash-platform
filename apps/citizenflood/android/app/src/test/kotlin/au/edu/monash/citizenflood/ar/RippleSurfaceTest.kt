package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class RippleSurfaceTest {
 @Test fun restingSurfaceIsFlatAndFinite() {
  val water=RippleSurface(17)
  repeat(100){water.step()}
  assertTrue(water.heights.all{it==0f})
 }
 @Test fun disturbancePropagatesAndRemainsBounded() {
  val water=RippleSurface(33)
  water.drop(0f,0f,.2f,.01f)
  val initial=water.heights.copyOf()
  repeat(20){water.step()}
  assertFalse(initial.contentEquals(water.heights))
  repeat(2000){water.step()}
  assertTrue(water.heights.all{it.isFinite() && kotlin.math.abs(it)<=.025f})
  water.clear();assertTrue(water.heights.all{it==0f})
 }
}
