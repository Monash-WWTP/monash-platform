import { useQuery } from '@tanstack/react-query'
import type { CommunityWastewaterObservation, EffluentSample, Station } from './monitoring-types'
import { allPages, fetchApi } from './transport'

export function useCommunityWastewaterObservations() {
  return useQuery({ queryKey: ['community-wastewater-observations'],
    queryFn: () => allPages<CommunityWastewaterObservation>('/api/v1/community/observations?category=wastewater'),
    staleTime: 30_000, refetchInterval: 60_000 })
}
export function useStations() {
  return useQuery({ queryKey: ['stations'], queryFn: () => allPages<Station>('/api/v1/monitoring/stations') })
}
export interface SampleFilters { year: number | 'all'; compliance: 'all' | 'Comply' | 'Not Comply' }
export function useSamples(stationCode: string | null, filters: SampleFilters) {
  return useQuery({ queryKey: ['samples', stationCode, filters], enabled: !!stationCode,
    queryFn: () => {
      const params = new URLSearchParams({ station_code: stationCode! })
      if (filters.year !== 'all') params.set('year', String(filters.year))
      if (filters.compliance !== 'all') params.set('compliance', filters.compliance)
      return allPages<EffluentSample>('/api/v1/monitoring/samples?' + params)
    } })
}
export function useSampleYears(stationCode: string | null) {
  return useQuery({ queryKey: ['sample-years', stationCode], enabled: !!stationCode,
    queryFn: () => fetchApi<number[]>('/api/v1/monitoring/years?station_code=' + encodeURIComponent(stationCode!)) })
}
