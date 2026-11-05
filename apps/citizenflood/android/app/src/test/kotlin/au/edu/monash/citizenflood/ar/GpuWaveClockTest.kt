package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class GpuWaveClockTest {
 @Test fun elapsedStepsAreBoundedAndPauseDropsCatchup(){
  val c=GpuWaveClock();assertEquals(0,c.tick(1000000000L))
  assertEquals(2,c.tick(1016666667L));assertTrue(c.tick(5000000000L)<=6)
  c.pause();assertEquals(0,c.tick(9000000000L))
 }
 @Test fun switchingToCpuAfterLongGpuUseDoesNotReplayGpuTime(){
  val c=GpuWaveClock();var now=1000000000L
  repeat(36000){now+=16666667L;c.tick(now)}
  assertEquals(0,c.tick(now+16666667L,60))
  assertEquals(1,c.tick(now+33333334L,60))
 }
}
