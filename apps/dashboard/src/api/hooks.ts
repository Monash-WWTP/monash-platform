import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './client'
import type { ScenarioInput } from './types'

export const usePlants = () => useQuery({ queryKey: ['plants'], queryFn: api.plants })

export const usePlant = (id: number) =>
  useQuery({ queryKey: ['plant', id], queryFn: () => api.plant(id), enabled: !!id })

export const useScenarios = (plantId: number) =>
  useQuery({
    queryKey: ['scenarios', plantId],
    queryFn: () => api.scenarios(plantId),
    enabled: !!plantId,
  })

export const useRun = (runId: number | null) =>
  useQuery({ queryKey: ['run', runId], queryFn: () => api.run(runId!), enabled: !!runId })

export const useTimeseries = (runId: number | null) =>
  useQuery({
    queryKey: ['timeseries', runId],
    queryFn: () => api.timeseries(runId!),
    enabled: !!runId,
  })

export const useCompare = (runIds: number[]) =>
  useQuery({
    queryKey: ['compare', runIds],
    queryFn: () => api.compare(runIds),
    enabled: runIds.length >= 2,
  })

export const useModels = () => useQuery({ queryKey: ['models'], queryFn: api.models })

export function useCreateScenario(plantId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ScenarioInput) => api.createScenario(plantId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios', plantId] }),
  })
}

export function useUpdateScenario(plantId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: ScenarioInput }) =>
      api.updateScenario(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios', plantId] }),
  })
}

export function useDeleteScenario(plantId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteScenario(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios', plantId] }),
  })
}

export function useRunScenario(plantId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (scenarioId: number) => api.runScenario(scenarioId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios', plantId] }),
  })
}
