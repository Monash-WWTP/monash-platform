import { ApiRequestError, fetchApi, type Page } from './transport'

export const ordinaryCapabilities = ['report:own', 'report:review', 'monitor:read', 'scenario:operate'] as const
export const capabilityLabels: Record<string, string> = { 'report:own': 'Submit own reports', 'report:review': 'Review reports', 'monitor:read': 'Read monitoring data', 'scenario:operate': 'Run research scenarios', 'platform:admin': 'Platform administrator' }
export interface AdminUser { id: string; email: string; capabilities: string[] }
export interface Equipment { unit_type: string; name: string; baseline_availability: number }
export interface Threshold { metric: string; value: number; unit: string; source: string; applicability: string }
export interface FactorSettings { ef_ch4: number; ef_n2o: number; ch4_unit: string; n2o_unit: string; source: string; applicability: string }
export interface PlantSettings {
  id?: number; code: string; name: string; latitude: number; longitude: number; capacity_mld: number
  description: string; stp_type: string; status: string; revision: number; units: Equipment[]
  configuration: { thresholds: Threshold[]; emission_factors: FactorSettings }
}
export interface AdminStation { code: string; payload: { name: string; category: string | null; stp_type: string | null; latitude: number; longitude: number }; revision: string }
export interface HistoryEvent { id: string; actor_id: string | null; action: string; resource_id: string; details: Record<string, unknown>; created_at: string }
export interface AdminStatus { environment: string; model: { id: string; version: string; validation_status: string; decision_use_permitted: boolean }; dependencies: Record<string, string>; release_acceptance: string }
const base = '/api/v1/admin'
export const adminApi = {
  users: (q = '', offset = 0) => fetchApi<Page<AdminUser>>(`${base}/users?limit=25&offset=${offset}&q=${encodeURIComponent(q)}`),
  permissions: (user: AdminUser, capabilities: string[], reason: string) => fetchApi<AdminUser>(`${base}/users/${encodeURIComponent(user.id)}`, { method: 'PATCH', body: JSON.stringify({ capabilities, expected_capabilities: user.capabilities, reason }) }),
  plants: (offset = 0) => fetchApi<Page<PlantSettings>>(`${base}/plants?limit=25&offset=${offset}`),
  savePlant: (plant: PlantSettings, reason: string) => {
    const { id, revision, code, name, latitude, longitude, capacity_mld, description, stp_type, status, units, configuration } = plant
    const fields = { code, name, latitude, longitude, capacity_mld, description, stp_type, status, units, configuration }
    return fetchApi<PlantSettings>(`${base}/plants${id ? `/${id}` : ''}`, { method: id ? 'PUT' : 'POST', body: JSON.stringify({ ...fields, expected_revision: revision, reason }) })
  },
  stations: (offset = 0) => fetchApi<Page<AdminStation>>(`${base}/stations?limit=25&offset=${offset}`),
  saveStation: (station: AdminStation, reason: string, creating: boolean) => fetchApi<AdminStation>(`${base}/stations${creating ? '' : `/${encodeURIComponent(station.code)}`}`, { method: creating ? 'POST' : 'PUT', body: JSON.stringify({ code: station.code, name: station.payload.name, latitude: station.payload.latitude, longitude: station.payload.longitude, category: station.payload.category || null, stp_type: station.payload.stp_type || null, expected_revision: station.revision || null, reason }) }),
  history: (offset = 0) => fetchApi<Page<HistoryEvent>>(`${base}/history?limit=25&offset=${offset}`),
  status: () => fetchApi<AdminStatus>(`${base}/status`),
}

export function adminErrorText(error: unknown): string {
  const message = error instanceof Error ? error.message : 'The change could not be saved. Please retry.'
  if (!(error instanceof ApiRequestError) || !Array.isArray(error.details)) return message
  const fields = error.details.map((item: { field?: string; message?: string; loc?: unknown[]; msg?: string }) => [item.field?.replace(/^body\./, '') ?? item.loc?.filter(v => v !== 'body').join('.'), item.message ?? item.msg].filter(Boolean).join(': '))
  return [message, ...fields].join(' · ')
}

export const newPlant = (): PlantSettings => ({ code: '', name: '', latitude: 0, longitude: 0, capacity_mld: 1, description: '', stp_type: '', status: 'unknown', revision: 0, units: [], configuration: { thresholds: [], emission_factors: { ef_ch4: 0.0121, ef_n2o: 0.0093, ch4_unit: 'kg CH4/kg BOD5', n2o_unit: 'kg N2O-N/kg N', source: '', applicability: '' } } })
