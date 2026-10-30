package au.edu.monash.citizenflood.ar

/** GPU solver runs at 120 Hz; CPU fallback uses 60 Hz without inheriting elapsed GPU time. */
class GpuWaveClock {
 private var previous=0L
 private var accumulated=0.0
 private var rate=120
 fun pause(){previous=0L;accumulated=0.0}
 fun tick(timestamp:Long,frequency:Int=120):Int {
  require(frequency==60||frequency==120)
  if(rate!=frequency){pause();rate=frequency}
  if(previous==0L){previous=timestamp;return 0}
  accumulated+=((timestamp-previous)/1e9).coerceIn(0.0,.05);previous=timestamp
  val steps=minOf(6,((accumulated+1e-9)*rate).toInt())
  accumulated-=steps/rate.toDouble();return steps
 }
}
