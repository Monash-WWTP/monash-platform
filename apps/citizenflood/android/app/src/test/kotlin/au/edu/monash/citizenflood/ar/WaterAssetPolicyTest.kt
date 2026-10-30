package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class WaterAssetPolicyTest {
    @Test fun permitsOnlyBundledAssetsAtTheExactOrigin() {
        assertEquals("water/index.html", WaterAssetPolicy.path("https://water.citizenflood.invalid/index.html?depthM=0.5"))
        assertEquals("water/vendor/water.js", WaterAssetPolicy.path("https://water.citizenflood.invalid/vendor/water.js"))
        for (url in listOf("http://water.citizenflood.invalid/index.html", "https://evil.test/index.html",
            "https://water.citizenflood.invalid.evil.test/index.html", "https://user@water.citizenflood.invalid/index.html",
            "https://water.citizenflood.invalid:443/index.html", "https://water.citizenflood.invalid/../private.txt",
            "https://water.citizenflood.invalid/%2e%2e/private.txt", "file:///data/private.txt",
            "content://private", "https://water.citizenflood.invalid/unknown.js")) assertNull(url, WaterAssetPolicy.path(url))
    }
}
