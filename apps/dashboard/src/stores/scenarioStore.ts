import { create } from 'zustand'

import type { MaintenanceEvent, ScenarioInput } from '../api/types'

export const emptyDraft = (): ScenarioInput => ({
  name: '',
  horizon: '3_months',
  forecast: {
    demand: 'normal',
    demand_change_pct: 0,
    weather: 'normal',
    rainfall_mm_day: 0,
    // typical Malaysian municipal influent for a small SBR plant (matches backend baseline)
    influent: { flow: 6, bod: 250, cod: 520, tss: 300, ammonia: 30, tkn: 40 },
  },
  maintenance: [],
  operating_parameters: {
    aeration_availability: 100,
    pump_availability: 100,
    clarifier_availability: 100,
    ch4_recovered_kg_m3: 0,
    n2o_recovered_kg_m3: 0,
  },
})

interface WorkspaceState {
  draft: ScenarioInput
  editingScenarioId: number | null
  activeRunId: number | null
  baselineRunId: number | null
  compareRunIds: number[]
  centerTab: 'trends' | 'twin' | 'compare'
  timelineDay: number

  setDraft: (patch: Partial<ScenarioInput>) => void
  setForecast: (patch: Partial<ScenarioInput['forecast']>) => void
  setInfluent: (patch: Partial<ScenarioInput['forecast']['influent']>) => void
  setOperating: (patch: Partial<ScenarioInput['operating_parameters']>) => void
  addMaintenance: (ev: MaintenanceEvent) => void
  removeMaintenance: (index: number) => void
  loadScenario: (id: number, draft: ScenarioInput) => void
  resetDraft: () => void
  setActiveRunId: (id: number | null) => void
  setBaselineRunId: (id: number | null) => void
  toggleCompareRun: (id: number) => void
  setCenterTab: (tab: 'trends' | 'twin' | 'compare') => void
  setTimelineDay: (day: number) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  draft: emptyDraft(),
  editingScenarioId: null,
  activeRunId: null,
  baselineRunId: null,
  compareRunIds: [],
  centerTab: 'trends',
  timelineDay: 0,

  setDraft: (patch) => set((s) => ({ draft: { ...s.draft, ...patch } })),
  setForecast: (patch) =>
    set((s) => ({ draft: { ...s.draft, forecast: { ...s.draft.forecast, ...patch } } })),
  setInfluent: (patch) =>
    set((s) => ({
      draft: {
        ...s.draft,
        forecast: {
          ...s.draft.forecast,
          influent: { ...s.draft.forecast.influent, ...patch },
        },
      },
    })),
  setOperating: (patch) =>
    set((s) => ({
      draft: {
        ...s.draft,
        operating_parameters: { ...s.draft.operating_parameters, ...patch },
      },
    })),
  addMaintenance: (ev) =>
    set((s) => ({ draft: { ...s.draft, maintenance: [...s.draft.maintenance, ev] } })),
  removeMaintenance: (index) =>
    set((s) => ({
      draft: { ...s.draft, maintenance: s.draft.maintenance.filter((_, i) => i !== index) },
    })),
  loadScenario: (id, draft) => set({ editingScenarioId: id, draft }),
  resetDraft: () => set({ editingScenarioId: null, draft: emptyDraft() }),
  setActiveRunId: (id) => set({ activeRunId: id, timelineDay: 0 }),
  setBaselineRunId: (id) => set({ baselineRunId: id }),
  toggleCompareRun: (id) =>
    set((s) => ({
      compareRunIds: s.compareRunIds.includes(id)
        ? s.compareRunIds.filter((r) => r !== id)
        : s.compareRunIds.length < 4
          ? [...s.compareRunIds, id]
          : s.compareRunIds,
    })),
  setCenterTab: (tab) => set({ centerTab: tab }),
  setTimelineDay: (day) => set({ timelineDay: day }),
}))
