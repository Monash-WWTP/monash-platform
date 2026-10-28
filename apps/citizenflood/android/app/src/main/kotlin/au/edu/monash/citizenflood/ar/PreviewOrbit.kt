package au.edu.monash.citizenflood.ar

import kotlin.math.*

/** GL-thread-owned camera for the illustrative scene, independent of AR tracking. */
class PreviewOrbit(private val depthM: Float) {
    init { require(depthM.isFinite() && depthM in 0f..1000f) }
    // This is a synthetic scene: widen its unlabelled footprint to keep large depths inspectable.
    val surfaceSize = 3f + depthM
    private var yaw = .65f
    var pitch = .8f; private set
    var zoomFactor = 1f; private set
    fun rotate(horizontal: Float, vertical: Float) {
        if (!horizontal.isFinite() || !vertical.isFinite()) return
        yaw = (yaw + horizontal.coerceIn(-10f, 10f)) % (2f * PI.toFloat())
        pitch = (pitch + vertical).coerceIn(.4f, 1.35f)
    }
    fun zoom(scale: Float) {
        if (!scale.isFinite() || scale <= 0f) return
        zoomFactor = (zoomFactor / scale).coerceIn(.65f, 2f)
    }
    fun reset() { yaw = .65f; pitch = .8f; zoomFactor = 1f }
    fun eye(): FloatArray {
        val distance = (5f + depthM * 2f) * zoomFactor
        return floatArrayOf(sin(yaw) * cos(pitch) * distance,
            depthM / 2f + sin(pitch) * distance, cos(yaw) * cos(pitch) * distance)
    }
}
