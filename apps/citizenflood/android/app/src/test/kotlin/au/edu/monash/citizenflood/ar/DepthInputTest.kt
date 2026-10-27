package au.edu.monash.citizenflood.ar

import org.junit.Assert.*
import org.junit.Test

class DepthInputTest {
    @Test fun rejectsInvalidDistancesAndReferences() {
        for (value in listOf(-1.0, Double.NaN, Double.POSITIVE_INFINITY, Double.MAX_VALUE)) {
            assertNull(DepthInput.parse(value, "road", "Draft depth"))
        }
        assertNull(DepthInput.parse(0.5, " ", "Draft depth"))
        assertNull(DepthInput.parse("0.5", "road", "Draft depth"))
    }
    @Test fun preservesZeroAndMetres() {
        assertEquals(0f, DepthInput.parse(0, "road", "Draft depth")!!.metres, 0f)
        assertEquals(0.5f, DepthInput.parse(0.5, "road", "Draft depth")!!.metres, 0f)
    }
}
