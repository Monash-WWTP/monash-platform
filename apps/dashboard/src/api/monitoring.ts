import { useQuery } from '@tanstack/react-query'

import {
  supabase,
  type CommunityWastewaterObservation,
  type EffluentSample,
  type Station,
} from '@/lib/supabase'

/** Public, moderator-approved wastewater observations from CitizenFlood. */
export function useCommunityWastewaterObservations() {
  return useQuery({
    queryKey: ['community-wastewater-observations'],
    queryFn: async (): Promise<CommunityWastewaterObservation[]> => {
      const { data, error } = await supabase
        .from('approved_wastewater_observations')
        .select(
          'id, category, condition, note, latitude, longitude, location_accuracy_m, observed_at, created_at',
        )
        .order('observed_at', { ascending: false })
        .limit(500)
      if (error) throw error
      return data as CommunityWastewaterObservation[]
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useStations() {
  return useQuery({
    queryKey: ['stations'],
    queryFn: async (): Promise<Station[]> => {
      const { data, error } = await supabase.from('stations').select('*').order('code')
      if (error) throw error
      return data
    },
  })
}

export interface SampleFilters {
  year: number | 'all'
  compliance: 'all' | 'Comply' | 'Not Comply'
}

export function useSamples(stationCode: string | null, filters: SampleFilters) {
  return useQuery({
    queryKey: ['samples', stationCode, filters],
    enabled: !!stationCode,
    queryFn: async (): Promise<EffluentSample[]> => {
      let q = supabase
        .from('effluent_samples')
        .select('*')
        .eq('station_code', stationCode!)
        .order('sample_date')
      if (filters.year !== 'all') q = q.eq('source_year', filters.year)
      if (filters.compliance !== 'all') q = q.eq('compliance', filters.compliance)
      const { data, error } = await q
      if (error) throw error
      return data
    },
  })
}

export function useSampleYears(stationCode: string | null) {
  return useQuery({
    queryKey: ['sample-years', stationCode],
    enabled: !!stationCode,
    queryFn: async (): Promise<number[]> => {
      const { data, error } = await supabase
        .from('effluent_samples')
        .select('source_year')
        .eq('station_code', stationCode!)
      if (error) throw error
      return [...new Set((data ?? []).map((r) => r.source_year))].sort()
    },
  })
}
