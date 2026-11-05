import type { Plant } from '../api/types'
import type { Station } from '../api/monitoring-types'

export type MonitoringLocation = Pick<Station, 'code' | 'name' | 'latitude' | 'longitude'> & {
  capacity_mld?: number
}

/** Monitoring stations remain browsable before operational configuration exists. */
export function monitoringLocations(plants: Plant[], stations: Station[]): MonitoringLocation[] {
  const locations = new Map<string, MonitoringLocation>()
  for (const station of stations) locations.set(station.code, station)
  for (const plant of plants) {
    if (plant.code === 'DEMO001') continue // Synthetic fixture belongs in the lab, not the real station map.
    const code = plant.code ?? `plant-${plant.id}`
    locations.set(code, { ...plant, code })
  }
  return [...locations.values()]
}
