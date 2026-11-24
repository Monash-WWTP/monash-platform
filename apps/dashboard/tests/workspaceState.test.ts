import assert from 'node:assert/strict'
import test from 'node:test'
import { useWorkspaceStore } from '../src/stores/scenarioStore'

test('changing plants resets every run reference and editing state', () => {
  useWorkspaceStore.setState({ activeRunId: 10, baselineRunId: 10, compareRunIds: [10, 20], centerTab: 'compare', editingScenarioId: 5 })
  useWorkspaceStore.getState().resetWorkspace()
  const state = useWorkspaceStore.getState()
  assert.equal(state.activeRunId, null)
  assert.equal(state.baselineRunId, null)
  assert.deepEqual(state.compareRunIds, [])
  assert.equal(state.centerTab, 'trends')
  assert.equal(state.editingScenarioId, null)
})
test('removing the reference selection clears the reference', () => {
  useWorkspaceStore.setState({ baselineRunId: 10, compareRunIds: [10, 20] })
  useWorkspaceStore.getState().toggleCompareRun(10)
  assert.equal(useWorkspaceStore.getState().baselineRunId, null)
  assert.deepEqual(useWorkspaceStore.getState().compareRunIds, [20])
})

test('a late replay cannot replace a newer run selection', () => {
  useWorkspaceStore.setState({ activeRunId: 20 })
  useWorkspaceStore.getState().activateReplay(10, 11)
  assert.equal(useWorkspaceStore.getState().activeRunId, 20)
  useWorkspaceStore.setState({ activeRunId: 10 })
  useWorkspaceStore.getState().activateReplay(10, 11)
  assert.equal(useWorkspaceStore.getState().activeRunId, 11)
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.getState().activateReplay(11, 12)
  assert.equal(useWorkspaceStore.getState().activeRunId, null)
})

test('a new scenario keeps the current horizon so its runs stay comparable', () => {
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.getState().setDraft({ name: 'Baseline', horizon: '1_month' })
  useWorkspaceStore.getState().loadScenario(7, { ...useWorkspaceStore.getState().draft })
  useWorkspaceStore.getState().resetDraft()
  const { draft, editingScenarioId } = useWorkspaceStore.getState()
  assert.equal(editingScenarioId, null)
  assert.equal(draft.name, '')
  assert.equal(draft.horizon, '1_month')
})

test('the default influent flow follows the plant design capacity', () => {
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.getState().applyPlantCapacity(2.5)
  assert.equal(useWorkspaceStore.getState().draft.forecast.influent.flow, 2.5)
  useWorkspaceStore.getState().resetDraft()
  assert.equal(useWorkspaceStore.getState().draft.forecast.influent.flow, 2.5)
})

test('plant capacity never overwrites a scenario being edited or a typed flow', () => {
  useWorkspaceStore.getState().resetWorkspace()
  useWorkspaceStore.getState().setInfluent({ flow: 4 })
  useWorkspaceStore.getState().applyPlantCapacity(2.5)
  assert.equal(useWorkspaceStore.getState().draft.forecast.influent.flow, 4)
  useWorkspaceStore.getState().loadScenario(3, { ...useWorkspaceStore.getState().draft, name: 'Saved' })
  useWorkspaceStore.getState().applyPlantCapacity(9)
  assert.equal(useWorkspaceStore.getState().draft.forecast.influent.flow, 4)
})
