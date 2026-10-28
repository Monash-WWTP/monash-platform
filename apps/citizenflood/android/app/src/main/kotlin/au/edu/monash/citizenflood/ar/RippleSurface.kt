package au.edu.monash.citizenflood.ar

import kotlin.math.*

/** Damped heightfield based on Evan Wallace's MIT WebGL Water (2011).
 * Portable CPU implementation: no floating-point framebuffer requirement.
 * Heights are decorative metre offsets around the reported mean surface. */
class RippleSurface(val size: Int = 49) {
    init { require(size >= 5) }
    val heights = FloatArray(size * size)
    private val velocity = FloatArray(size * size)
    private val next = FloatArray(size * size)
    fun clear() { heights.fill(0f); velocity.fill(0f); next.fill(0f) }
    fun drop(x: Float, z: Float, radius: Float, strength: Float) {
        require(radius > 0f && radius.isFinite() && strength.isFinite())
        for (j in 1 until size-1) for (i in 1 until size-1) {
            val dx = -1.5f + i * 3f/(size-1) - x
            val dz = -1.5f + j * 3f/(size-1) - z
            val t = max(0f, 1f-sqrt(dx*dx+dz*dz)/radius)
            val d = (1f-cos(t*PI.toFloat()))*.5f
            val k=j*size+i
            heights[k]=(heights[k]+d*strength).coerceIn(-.025f,.025f)
        }
    }
    fun step() {
        for (j in 1 until size-1) for (i in 1 until size-1) {
            val k=j*size+i
            val average=(heights[k-1]+heights[k+1]+heights[k-size]+heights[k+size])*.25f
            velocity[k]=(velocity[k]+(average-heights[k])*2f)*.985f
            next[k]=(heights[k]+velocity[k]).coerceIn(-.025f,.025f)
        }
        next.copyInto(heights)
    }
    fun height(i:Int,j:Int)=heights[j.coerceIn(0,size-1)*size+i.coerceIn(0,size-1)]
}
