import { useEffect, useRef, useState, type ReactNode } from 'react'
import { CalendarClock, Play, Plus, Trash2 } from 'lucide-react'

import {
  useCreateScenario,
  useDeleteScenario,
  useRunScenario,
  useScenarios,
  useUpdateScenario,
} from '../../api/hooks'
import type { MaintenanceEvent, Scenario, UnitType } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'
import { Button, Card, Input, Label, SegmentGroup, Select, Spinner } from '../ui'
import OperatorAccess from '../auth/OperatorAccess'

const UNIT_LABEL: Record<UnitType, string> = {
  pump: 'Pump Station',
  aeration: 'Aeration System',
  clarifier: 'Clarifier',
}

export default function ScenarioPanel({ plantId }: { plantId: number }) {
  const { data: scenarios, error: scenariosError, isLoading: scenariosLoading } = useScenarios(plantId)
  const createScenario = useCreateScenario(plantId)
  const updateScenario = useUpdateScenario(plantId)
  const deleteScenario = useDeleteScenario(plantId)
  const runScenario = useRunScenario(plantId)

  const {
    draft,
    editingScenarioId,
    setDraft,
    setForecast,
    setInfluent,
    setOperating,
    addMaintenance,
    removeMaintenance,
    loadScenario,
    resetDraft,
    setActiveRunId,
    setCenterTab,
  } = useWorkspaceStore()

  const mounted = useRef(true)
  useEffect(() => { mounted.current = true; return () => { mounted.current = false } }, [])
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [error, setError] = useState<string | null>(null)
  const busy = createScenario.isPending || updateScenario.isPending || runScenario.isPending

  async function saveAndRun() {
    setError(null)
    if (!draft.name.trim()) {
      setError('Give the scenario a name first.')
      return
    }
    if (!startDate || !Number.isFinite(Date.parse(startDate))) {
      setError('Choose a valid simulation start date.')
      return
    }
    const { influent } = draft.forecast
    const demand_change_pct = draft.forecast.demand_change_pct ?? 0
    const rainfall_mm_day = draft.forecast.rainfall_mm_day ?? 0
    const tkn = influent.tkn ?? 0
    const ch4_recovered_kg_m3 = draft.operating_parameters.ch4_recovered_kg_m3 ?? 0
    const n2o_recovered_kg_m3 = draft.operating_parameters.n2o_recovered_kg_m3 ?? 0
    if (
      !Number.isFinite(demand_change_pct) ||
      demand_change_pct < -100 ||
      demand_change_pct > 100
    ) {
      setError('Demand change must be between −100% and +100%.')
      return
    }
    if (!Number.isFinite(rainfall_mm_day) || rainfall_mm_day < 0 || rainfall_mm_day > 200) {
      setError('Rainfall must be between 0 and 200 mm/day.')
      return
    }
    if (!Number.isFinite(tkn) || tkn < 0) {
      setError('TKN must be a non-negative value.')
      return
    }
    if (!Number.isFinite(ch4_recovered_kg_m3) || ch4_recovered_kg_m3 < 0) {
      setError('Recovered CH₄ must be a non-negative value.')
      return
    }
    if (!Number.isFinite(n2o_recovered_kg_m3) || n2o_recovered_kg_m3 < 0) {
      setError('Recovered N₂O must be a non-negative value.')
      return
    }
    const payload = {
      ...draft,
      forecast: {
        ...draft.forecast,
        demand_change_pct,
        rainfall_mm_day,
        influent: { ...influent, tkn },
      },
      operating_parameters: {
        ...draft.operating_parameters,
        ch4_recovered_kg_m3,
        n2o_recovered_kg_m3,
      },
    }
    try {
      const scenario = editingScenarioId
        ? await updateScenario.mutateAsync({ id: editingScenarioId, body: payload })
        : await createScenario.mutateAsync(payload)
      if (!mounted.current) return
      if (!editingScenarioId) loadScenario(scenario.id, payload)
      const run = await runScenario.mutateAsync({ scenarioId: scenario.id, startDate })
      if (!mounted.current) return
      setActiveRunId(run.id)
      setCenterTab('trends')
    } catch (e) {
      if (!mounted.current) return
      setError(e instanceof Error ? e.message : 'Run failed')
    }
  }

  function loadExisting(s: Scenario) {
    loadScenario(s.id, {
      name: s.name,
      horizon: s.horizon,
      forecast: s.forecast,
      maintenance: s.maintenance,
      operating_parameters: s.operating_parameters,
      is_baseline: s.is_baseline,
    })
    setActiveRunId(s.latest_run_id)
  }

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <OperatorAccess />
      <Card
        title="Saved Scenarios"
        action={
          <Button variant="ghost" className="px-2 py-0.5 text-xs" onClick={resetDraft}>
            + New
          </Button>
        }
      >
        <div className="flex flex-col gap-1.5">
          {scenariosLoading && <Spinner />}
          {scenariosError && (
            <p role="alert" className="text-xs text-destructive">
              {scenariosError.message.startsWith('401')
                ? 'Sign in with an approved operator account to view saved scenarios.'
                : scenariosError.message.startsWith('403')
                  ? 'This account does not have WWTP operator access.'
                  : scenariosError.message.startsWith('503')
                    ? 'Operator access is not configured on the server.'
                    : 'Saved scenarios could not be loaded.'}
            </p>
          )}
          {(scenarios ?? []).map((s) => (
            <div
              key={s.id}
              className={`flex items-center justify-between rounded-md border px-2 py-1.5 text-sm ${
                editingScenarioId === s.id
                  ? 'border-primary bg-primary/10'
                  : 'border-border bg-muted'
              }`}
            >
              <button className="min-h-11 flex-1 truncate text-left sm:min-h-8" onClick={() => loadExisting(s)}>
                <span className="font-medium">{s.name}</span>
                {s.is_baseline && (
                  <span className="ml-2 text-[10px] text-primary uppercase">baseline</span>
                )}
              </button>
              {!s.is_baseline && (
                <button
                  className="ml-2 flex size-11 items-center justify-center text-muted-foreground hover:text-destructive sm:size-8"
                  onClick={() => deleteScenario.mutate(s.id)}
                  title="Delete scenario"
                  aria-label={`Delete ${s.name}`}
                >
                  <Trash2 className="size-3.5" />
                </button>
              )}
            </div>
          ))}
          {scenarios?.length === 0 && (
            <p className="text-xs text-muted-foreground">No scenarios yet — configure one below.</p>
          )}
        </div>
      </Card>

      <Card title="1. Configure scenario">
        <div className="flex flex-col gap-3">
          <div>
            <Label>Scenario Name</Label>
            <Input
              aria-label="Scenario name"
              placeholder="e.g. Assumed demand + maintenance"
              value={draft.name}
              onChange={(e) => setDraft({ name: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor="run-start-date" className="mb-1 block text-xs font-medium text-muted-foreground">Simulation start date (UTC)</label>
            <Input id="run-start-date" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
            <p className="mt-1 text-xs text-muted-foreground">Use the same dates and horizon for comparable runs.</p>
          </div>
          <div>
            <Label>Simulation horizon</Label>
            <SegmentGroup
              options={[
                { value: '1_month', label: '1 Month' },
                { value: '3_months', label: '3 Months' },
                { value: '6_months', label: '6 Months' },
              ]}
              value={draft.horizon}
              onChange={(horizon) => setDraft({ horizon })}
            />
          </div>
        </div>
      </Card>

      <Card title="Assumed influent and demand">
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Demand change</Label>
              <Input
                type="number"
                aria-label="Demand change (%)"
                min={-100}
                max={100}
                step={1}
                value={draft.forecast.demand_change_pct ?? 0}
                onChange={(e) => setForecast({ demand_change_pct: Number(e.target.value) })}
              />
              <span className="text-[10px] text-muted-foreground">% from baseline</span>
            </div>
            <div>
              <Label>Average rainfall · Context only</Label>
              <Input
                type="number"
                min={0}
                aria-label="Average rainfall, context only (mm/day)"
                max={200}
                step={0.1}
                value={draft.forecast.rainfall_mm_day ?? 0}
                onChange={(e) => setForecast({ rainfall_mm_day: Number(e.target.value) })}
              />
              <span className="text-[10px] text-muted-foreground">mm/day</span>
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground">
            Demand changes flow and pollutant load. Weather and rainfall are saved as context only; this model does not apply them because a site-specific hydrologic response has not been validated.
          </p>
          <div>
            <Label>Assumed influent</Label>
            <p className="mb-2 text-xs text-muted-foreground">All defaults are illustrative assumptions. Verify source, units and sampling period before changing them; monitoring data is not automatically imported.</p>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  ['flow', 'Flow (MLD)'],
                  ['bod', 'BOD₅ (mg/L)'],
                  ['cod', 'COD (mg/L)'],
                  ['tss', 'TSS (mg/L)'],
                  ['ammonia', 'Ammonia (mg/L)'],
                  ['tkn', 'TKN (mg N/L)'],
                ] as const
              ).map(([key, label]) => (
                <div key={key}>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] text-muted-foreground">{label}</span>
                    {key === 'tkn' && <AssumedBadge />}
                  </div>
                  <Input
                    type="number"
                    aria-label={label}
                    value={draft.forecast.influent[key] ?? 0}
                    onChange={(e) => setInfluent({ [key]: Number(e.target.value) })}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <InputDisclosure title={`Maintenance · ${draft.maintenance.length} events`}>
        <MaintenanceEditor
          events={draft.maintenance}
          onAdd={addMaintenance}
          onRemove={removeMaintenance}
        />
      </InputDisclosure>

      <InputDisclosure title={`Equipment availability · ${[draft.operating_parameters.aeration_availability, draft.operating_parameters.pump_availability, draft.operating_parameters.clarifier_availability].every(value => value === 100) ? 'all 100%' : 'adjusted'}`}>
        <div className="flex flex-col gap-2.5">
          {(
            [
              ['aeration_availability', 'Aeration System'],
              ['pump_availability', 'Pump Station'],
              ['clarifier_availability', 'Clarifier'],
            ] as const
          ).map(([key, label]) => (
            <div key={key}>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-mono">{draft.operating_parameters[key]}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                aria-label={`${label} availability (%)`}
                value={draft.operating_parameters[key]}
                onChange={(e) => setOperating({ [key]: Number(e.target.value) })}
                className="w-full accent-(--primary)"
              />
            </div>
          ))}
        </div>
      </InputDisclosure>

      <InputDisclosure title={`Carbon accounting · ${(draft.operating_parameters.ch4_recovered_kg_m3 ?? 0) !== 0 || (draft.operating_parameters.n2o_recovered_kg_m3 ?? 0) !== 0 ? 'recovery set' : 'no recovery'}`}>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-muted-foreground">Recovered CH₄ (kg/m³)</span>
              <AssumedBadge />
            </div>
            <Input
              type="number"
              min={0}
              step={0.001}
              aria-label="Recovered CH₄ (kg/m³)"
              value={draft.operating_parameters.ch4_recovered_kg_m3 ?? 0}
              onChange={(e) => setOperating({ ch4_recovered_kg_m3: Number(e.target.value) })}
            />
          </div>
          <div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-muted-foreground">Recovered N₂O (kg/m³)</span>
              <AssumedBadge />
            </div>
            <Input
              type="number"
              min={0}
              step={0.001}
              aria-label="Recovered N₂O (kg/m³)"
              value={draft.operating_parameters.n2o_recovered_kg_m3 ?? 0}
              onChange={(e) => setOperating({ n2o_recovered_kg_m3: Number(e.target.value) })}
            />
          </div>
        </div>
        <p className="mt-2 text-[10px] text-muted-foreground">
          Assumed unless replaced with measured recovery data. TKN is influent Kjeldahl nitrogen; ammonia is not a substitute.
        </p>
      </InputDisclosure>

      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

      <Button variant="primary" className="flex items-center justify-center gap-2 py-2.5" onClick={saveAndRun} disabled={busy}>
        {busy ? <Spinner /> : <Play className="size-4" />}
        {busy ? 'Running Simulation…' : '2. Run Simulation'}
      </Button>
    </div>
  )
}

function AssumedBadge() {
  return (
    <span
      className="rounded border border-border px-1 text-[9px] text-muted-foreground"
      title="Default or backend-filled value; not measured plant data"
    >
      assumed
    </span>
  )
}

function MaintenanceEditor({
  events,
  onAdd,
  onRemove,
}: {
  events: MaintenanceEvent[]
  onAdd: (ev: MaintenanceEvent) => void
  onRemove: (index: number) => void
}) {
  const [unitType, setUnitType] = useState<UnitType>('aeration')
  const mounted = useRef(true)
  useEffect(() => { mounted.current = true; return () => { mounted.current = false } }, [])
  const [startDate, setStartDate] = useState('')
  const [duration, setDuration] = useState(7)
  const [availability, setAvailability] = useState(50)

  return (
    <div className="flex flex-col gap-2">
      {events.map((ev, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-md border border-border bg-muted px-2 py-1.5 text-xs"
        >
          <div className="flex items-center gap-2">
            <CalendarClock className="size-3.5 text-muted-foreground" />
            <div>
              <div className="font-medium">{UNIT_LABEL[ev.unit_type]} Maintenance</div>
              <div className="text-muted-foreground">
                {ev.start_date} · {ev.duration_days}d · availability {ev.availability_pct}%
              </div>
            </div>
          </div>
          <button className="text-muted-foreground hover:text-destructive" aria-label={`Remove ${UNIT_LABEL[ev.unit_type]} maintenance on ${ev.start_date}`} onClick={() => onRemove(i)}>
            <Trash2 className="size-3.5" />
          </button>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-xs text-muted-foreground">No maintenance events planned.</p>
      )}

      <div className="mt-1 grid grid-cols-2 gap-2 rounded-md border border-dashed border-border p-2">
        <div className="col-span-2">
          <Label>Equipment</Label>
          <Select aria-label="Maintenance equipment" value={unitType} onChange={(e) => setUnitType(e.target.value as UnitType)}>
            <option value="pump">Pump Station</option>
            <option value="aeration">Aeration System</option>
            <option value="clarifier">Clarifier</option>
          </Select>
        </div>
        <div>
          <Label>Start Date</Label>
          <Input aria-label="Maintenance start date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div>
          <Label>Duration (days)</Label>
          <Input
            type="number"
            min={1}
            aria-label="Maintenance duration (days)"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </div>
        <div className="col-span-2">
          <Label>Availability during maintenance: {availability}%</Label>
          <input
            type="range"
            min={0}
            max={100}
            aria-label="Availability during maintenance (%)"
            value={availability}
            onChange={(e) => setAvailability(Number(e.target.value))}
            className="w-full accent-(--primary)"
          />
        </div>
        <Button
          className="col-span-2 flex items-center justify-center gap-1.5"
          onClick={() => {
            if (!startDate) return
            onAdd({
              unit_type: unitType,
              start_date: startDate,
              duration_days: duration,
              availability_pct: availability,
            })
            setStartDate('')
          }}
          disabled={!startDate}
        >
          <Plus className="size-3.5" /> Add Maintenance Event
        </Button>
      </div>
    </div>
  )
}

function InputDisclosure({ title, children }: { title: string; children: ReactNode }) {
  return <details className="rounded-lg border border-border bg-background p-4">
    <summary className="cursor-pointer text-sm font-semibold">{title}</summary>
    <div className="mt-4">{children}</div>
  </details>
}
