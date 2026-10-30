package au.edu.monash.citizenflood.ar

import java.net.URI

/** Exact local asset mapping; no URL ever falls through to the network or filesystem. */
object WaterAssetPolicy {
    const val ORIGIN = "https://water.citizenflood.invalid"
    private val files = setOf("index.html", "style.css", "scene-config.js", "textures.js", "scene.js",
        "vendor/lightgl.js", "vendor/water.js", "vendor/renderer.js", "vendor/cubemap.js")
    fun path(url: String): String? = try {
        val uri = URI(url)
        val file = uri.rawPath?.removePrefix("/")
        if (uri.scheme == "https" && uri.rawAuthority == "water.citizenflood.invalid" && file in files)
            "water/$file" else null
    } catch (_: Exception) { null }
}
