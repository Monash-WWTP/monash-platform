package au.edu.monash.citizenflood.ar

/** No coordinates, report identifiers or photos cross this boundary. */
data class DepthInput(val metres: Float, val reference: String, val context: String) {
    companion object {
        fun parse(value: Any?, reference: Any?, context: Any?): DepthInput? {
            val depth = (value as? Number)?.toDouble() ?: return null
            val surface = (reference as? String)?.trim().orEmpty()
            val label = (context as? String)?.trim().orEmpty()
            if (!depth.isFinite() || depth < 0 || !depth.toFloat().isFinite() ||
                surface.isEmpty() || label.isEmpty()) return null
            return DepthInput(depth.toFloat(), surface.take(500), label.take(200))
        }
    }
}
