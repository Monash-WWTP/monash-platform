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
import { fetchApi as request } from './transport'

export const api = {
  plants: () => request<Plant[]>('/api/v1/plants'),
  plant: (id: number) => request<PlantDetail>(`/api/v1/plants/${id}`),
  scenarios: (plantId: number) => request<Scenario[]>(`/api/v1/plants/${plantId}/scenarios`),
  createScenario: (plantId: number, body: ScenarioInput) =>
    request<Scenario>(`/api/v1/plants/${plantId}/scenarios`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateScenario: (id: number, body: ScenarioInput) =>
    request<Scenario>(`/api/v1/scenarios/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteScenario: (id: number) => request<void>(`/api/v1/scenarios/${id}`, { method: 'DELETE' }),
  runScenario: (id: number, modelId = 'effluent_v1') =>
    request<Run>(`/api/v1/scenarios/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId }),
    }),
  run: (id: number) => request<Run>(`/api/v1/runs/${id}`),
  timeseries: (runId: number) => request<Timeseries>(`/api/v1/runs/${runId}/timeseries`),
  compare: (runIds: number[]) =>
    request<CompareResult>('/api/v1/compare', {
      method: 'POST',
      body: JSON.stringify({ run_ids: runIds }),
    }),
  models: () => request<ModelInfo[]>('/api/v1/models'),
}
