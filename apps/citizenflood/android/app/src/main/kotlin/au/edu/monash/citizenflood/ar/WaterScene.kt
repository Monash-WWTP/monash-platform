package au.edu.monash.citizenflood.ar

import android.view.View

/** One illustrative scene; all lifecycle/commands are invoked on the UI thread. */
interface WaterScene {
    val view: View
    fun command(name: String)
    fun resume()
    fun pause()
    fun destroy()
}
