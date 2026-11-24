import { create } from 'zustand'

import type { MaintenanceEvent, ScenarioInput } from '../api/types'

export const DEFAULT_FLOW_MLD = 6

export const emptyDraft = (
  horizon: ScenarioInput['horizon'] = '3_months',
  flow = DEFAULT_FLOW_MLD,
): ScenarioInput => ({
  name: '',
  horizon,
  forecast: {
    demand: 'normal',
    demand_change_pct: 0,
    weather: 'normal',
    rainfall_mm_day: 0,
    // Illustrative draft assumptions, not measurements or calibrated site defaults.
    influent: { flow, bod: 250, cod: 520, tss: 300, ammonia: 30, tkn: 40 },
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
  /** Plant design capacity used as the default assumed flow for new drafts. */
  defaultFlow: number | null
  activeRunId: number | null
  baselineRunId: number | null
  compareRunIds: number[]
  centerTab: 'trends' | 'compare'

  setDraft: (patch: Partial<ScenarioInput>) => void
  setForecast: (patch: Partial<ScenarioInput['forecast']>) => void
  setInfluent: (patch: Partial<ScenarioInput['forecast']['influent']>) => void
  setOperating: (patch: Partial<ScenarioInput['operating_parameters']>) => void
  addMaintenance: (ev: MaintenanceEvent) => void
  removeMaintenance: (index: number) => void
  loadScenario: (id: number, draft: ScenarioInput) => void
  resetDraft: () => void
  applyPlantCapacity: (capacityMld: number) => void
  resetWorkspace: () => void
  activateReplay: (sourceRunId: number, resultRunId: number) => void
  setActiveRunId: (id: number | null) => void
  setBaselineRunId: (id: number | null) => void
  toggleCompareRun: (id: number) => void
  setCenterTab: (tab: 'trends' | 'compare') => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  draft: emptyDraft(),
  editingScenarioId: null,
  defaultFlow: null,
  activeRunId: null,
  baselineRunId: null,
  compareRunIds: [],
  centerTab: 'trends',

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
  // Keep the horizon: runs are only comparable over identical simulated dates.
  resetDraft: () =>
    set((s) => ({
      editingScenarioId: null,
      draft: emptyDraft(s.draft.horizon, s.defaultFlow ?? DEFAULT_FLOW_MLD),
    })),
  applyPlantCapacity: (capacityMld) =>
    set((s) => {
      if (!(capacityMld > 0)) return {}
      const untouched =
        s.editingScenarioId === null &&
        s.draft.forecast.influent.flow === (s.defaultFlow ?? DEFAULT_FLOW_MLD)
      return {
        defaultFlow: capacityMld,
        ...(untouched
          ? {
              draft: {
                ...s.draft,
                forecast: {
                  ...s.draft.forecast,
                  influent: { ...s.draft.forecast.influent, flow: capacityMld },
                },
              },
            }
          : {}),
      }
    }),
  resetWorkspace: () => set({ draft: emptyDraft(), editingScenarioId: null, defaultFlow: null, activeRunId: null, baselineRunId: null, compareRunIds: [], centerTab: 'trends' }),
  activateReplay: (sourceRunId, resultRunId) => set(s => s.activeRunId === sourceRunId ? { activeRunId: resultRunId } : {}),
  setActiveRunId: (id) => set({ activeRunId: id }),
  setBaselineRunId: (id) => set({ baselineRunId: id }),
  toggleCompareRun: (id) =>
    set((s) => ({
      baselineRunId: s.compareRunIds.includes(id) && s.baselineRunId === id ? null : s.baselineRunId,
      compareRunIds: s.compareRunIds.includes(id)
        ? s.compareRunIds.filter((r) => r !== id)
        : s.compareRunIds.length < 4
          ? [...s.compareRunIds, id]
          : s.compareRunIds,
    })),
  setCenterTab: (tab) => set({ centerTab: tab }),
}))
