package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class PreviewOrbitTest {
    @Test fun gesturesAreBoundedAndResettable() {
        val orbit = PreviewOrbit(.5f)
        val initial = orbit.eye()
        orbit.rotate(10000f, 10000f); orbit.zoom(1000f)
        assertTrue(orbit.eye().all { it.isFinite() })
        assertTrue(orbit.pitch in .4f..1.35f)
        assertTrue(orbit.zoomFactor in .65f..2f)
        orbit.rotate(Float.NaN, Float.POSITIVE_INFINITY); orbit.zoom(Float.NaN)
        assertTrue(orbit.eye().all { it.isFinite() })
        orbit.reset(); assertArrayEquals(initial, orbit.eye(), 0f)
    }
    @Test fun viewStaysAboveWaterAcrossDepthAndZoomRange() {
        for (depth in listOf(0f, .01f, .5f, 10f, 1000f)) {
            val orbit = PreviewOrbit(depth)
            orbit.rotate(0f, -1000f); orbit.zoom(1000f)
            assertTrue(orbit.eye().all { it.isFinite() })
            assertTrue(orbit.eye()[1] > depth)
        }
    }
    @Test fun illustrativeSurfaceRemainsInspectableAtLargeDepths() {
        for (depth in listOf(0f, .5f, 10f, 100f, 1000f)) {
            val orbit = PreviewOrbit(depth)
            val eye = orbit.eye()
            val distance = kotlin.math.sqrt(eye[0]*eye[0] + (eye[1]-depth/2)*(eye[1]-depth/2) + eye[2]*eye[2])
            assertTrue(orbit.surfaceSize / distance >= .49f)
        }
    }
}
