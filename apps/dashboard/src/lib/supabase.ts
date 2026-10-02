import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL ?? 'https://eaxekwlmvpvftpgxiwlu.supabase.co'
const key =
  import.meta.env.VITE_SUPABASE_KEY ?? 'sb_publishable_3-3Y9gvsPaJvErjgB80s6A__xFEcU1j'

export const supabase = createClient(url, key)

export interface Station {
  code: string
  name: string
  stp_type: string | null
  category: string | null
  latitude: number
  longitude: number
}

export interface EffluentSample {
  id: number
  station_code: string
  sample_date: string
  sampling: number
  sample_point: string
  bod: number | null
  bod_bdl: boolean
  cod: number | null
  cod_bdl: boolean
  nh3n: number | null
  nh3n_bdl: boolean
  no3n: number | null
  no3n_bdl: boolean
  ph: number | null
  ph_bdl: boolean
  oil_grease: number | null
  oil_grease_bdl: boolean
  tss: number | null
  tss_bdl: boolean
  temperature: number | null
  compliance: string
  source_year: number
}

/** Moderator-approved CitizenFlood wastewater report, not a lab sample. */
export interface CommunityWastewaterObservation {
  id: string
  category: 'wastewater'
  condition: 'normal' | 'warning' | 'critical'
  note: string | null
  latitude: number
  longitude: number
  location_accuracy_m: number | null
  observed_at: string
  created_at: string
}

/** Lab parameters shown without assuming a station's discharge permit limits. */
export const SAMPLE_METRICS: Record<string, { label: string; unit: string }> = {
  bod: { label: 'BOD', unit: 'mg/L' },
  cod: { label: 'COD', unit: 'mg/L' },
  tss: { label: 'TSS', unit: 'mg/L' },
  nh3n: { label: 'NH₃-N', unit: 'mg/L' },
  no3n: { label: 'NO₃-N', unit: 'mg/L' },
  oil_grease: { label: 'Oil & Grease', unit: 'mg/L' },
  ph: { label: 'pH', unit: '' },
  temperature: { label: 'Temperature', unit: '°C' },
}
