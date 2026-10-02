export type Horizon = '1_month' | '3_months' | '6_months'
export type DemandLevel = 'low' | 'normal' | 'high'
export type WeatherLevel = 'dry' | 'normal' | 'wet'
export type UnitType = 'pump' | 'aeration' | 'clarifier'
export type Severity = 'low' | 'medium' | 'high'

export const EFFLUENT_METRICS = [
  'bod',
  'cod',
  'tss',
  'ammonia',
  'nitrate',
  'phosphorus',
  'turbidity',
  'ph',
] as const
export type Metric = (typeof EFFLUENT_METRICS)[number]

export const METRIC_LABELS: Record<string, string> = {
  bod: 'BOD',
  cod: 'COD',
  tss: 'TSS',
  ammonia: 'Ammonia',
  nitrate: 'Nitrate',
  phosphorus: 'Phosphorus',
  turbidity: 'Turbidity',
  ph: 'pH',
}

export const METRIC_UNITS: Record<string, string> = {
  bod: 'mg/L',
  cod: 'mg/L',
  tss: 'mg/L',
  ammonia: 'mg/L',
  nitrate: 'mg/L',
  phosphorus: 'mg/L',
  turbidity: 'NTU',
  ph: '',
}

export interface Plant {
  id: number
  code: string | null
  name: string
  status: 'operational' | 'maintenance' | 'warning' | 'unknown'
  latitude: number
  longitude: number
  capacity_mld: number
  description: string
}

export interface PlantUnit {
  id: number
  unit_type: UnitType
  name: string
  baseline_availability: number
}

export interface ComplianceLimit {
  metric: string
  limit_value: number
  unit: string
}

export interface PlantDetail extends Plant {
  units: PlantUnit[]
  compliance_limits: ComplianceLimit[]
}

export interface Influent {
  flow: number
  bod: number
  cod: number
  tss: number
  ammonia: number
  tkn?: number
}

export interface Forecast {
  demand: DemandLevel
  demand_multiplier?: number | null
  demand_change_pct?: number | null
  weather: WeatherLevel
  rainfall_mm_day?: number | null
  influent: Influent
}

export interface MaintenanceEvent {
  unit_type: UnitType
  start_date: string
  duration_days: number
  availability_pct: number
}

export interface OperatingParameters {
  capacity_mld?: number | null
  aeration_availability: number
  pump_availability: number
  clarifier_availability: number
  ch4_recovered_kg_m3?: number
  n2o_recovered_kg_m3?: number
}

export interface ScenarioInput {
  name: string
  horizon: Horizon
  forecast: Forecast
  maintenance: MaintenanceEvent[]
  operating_parameters: OperatingParameters
  is_baseline?: boolean
}

export interface Scenario extends ScenarioInput {
  id: number
  plant_id: number
  created_at: string
  latest_run_id: number | null
}

export interface Exceedance {
  metric: string
  start_day: number
  end_day: number
  peak_value: number
  limit_value: number
  peak_ratio: number
  factors: string[]
}

export interface Kpis {
  compliance_pct: number
  exceedance_days: number
  capacity_utilization_pct: number
  ch4_mean_kgco2e_m3: number
  n2o_mean_kgco2e_m3: number
  ghg_mean_kgco2e_m3: number
  [key: string]: number | string
}

export interface Run {
  id: number
  scenario_id: number
  scenario_name: string
  plant_id: number
  horizon: Horizon
  model_id: string
  model_version: string
  validation_status: 'illustrative_unvalidated'
  decision_use_permitted: false
  status: string
  kpis: Kpis
  exceedances: Exceedance[]
  created_at: string
}

export interface Timeseries {
  run_id: number
  dates: string[]
  series: Record<string, number[]>
  compliance_limits: Record<string, number>
}

export interface CompareResult {
  runs: Run[]
  timeseries: Timeseries[]
}

export interface ModelInfo {
  model_id: string
  name: string
  version: string
  description: string
}
