import type {
  CompareResult,
  ModelInfo,
  Plant,
  PlantDetail,
  Run,
  Scenario,
  ScenarioInput,
  Timeseries,
} from './types'
import { supabase } from '../lib/supabase'

// Empty in dev (Vite proxies /api → :8000) and when a Vercel rewrite fronts
// the API on the same origin. Set VITE_API_BASE to call the backend directly.
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Content-Type', 'application/json')
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) headers.set('Authorization', `Bearer ${session.access_token}`)

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  plants: () => request<Plant[]>('/api/plants'),
  plant: (id: number) => request<PlantDetail>(`/api/plants/${id}`),
  scenarios: (plantId: number) => request<Scenario[]>(`/api/plants/${plantId}/scenarios`),
  createScenario: (plantId: number, body: ScenarioInput) =>
    request<Scenario>(`/api/plants/${plantId}/scenarios`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateScenario: (id: number, body: ScenarioInput) =>
    request<Scenario>(`/api/scenarios/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteScenario: (id: number) => request<void>(`/api/scenarios/${id}`, { method: 'DELETE' }),
  runScenario: (id: number, modelId = 'effluent_v1') =>
    request<Run>(`/api/scenarios/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    }),
  run: (id: number) => request<Run>(`/api/runs/${id}`),
  timeseries: (runId: number) => request<Timeseries>(`/api/runs/${runId}/timeseries`),
  compare: (runIds: number[]) =>
    request<CompareResult>('/api/compare', {
      method: 'POST',
      body: JSON.stringify({ run_ids: runIds }),
    }),
  models: () => request<ModelInfo[]>('/api/models'),
}
