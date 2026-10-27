package au.edu.monash.citizenflood.ar

import java.util.concurrent.atomic.AtomicLong

/** Cancels pending Intents as well as already visible previews. Not persisted. */
object DepthLaunch {
    private val generation = AtomicLong(0)
    fun begin(): Long = generation.incrementAndGet()
    fun invalidate() { generation.incrementAndGet() }
    fun isCurrent(token: Long): Boolean = token > 0 && token == generation.get()
}
