# PLAN.md — Implementation Plan

Implementation plan for the Treatment Plant Scenario Simulation & Effluent Quality Prediction Platform (see PROJECT.md). This plan covers Phase 1 scope only.

---

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + TS + Vite)                           │
│  MapLibre + deck.gl map · Workspace UI · ECharts        │
│  Zustand (UI state) · React Query (server state)        │
└───────────────▲─────────────────────────────────────────┘
                │ REST (JSON)
┌───────────────┴─────────────────────────────────────────┐
│  Backend API (FastAPI)                                  │
│  /plants · /scenarios · /simulations · /models          │
│  Pydantic schemas = the contract                        │
└───────┬─────────────────────────────┬───────────────────┘
        │                             │
┌───────▼──────────┐        ┌─────────▼───────────────────┐
│ PostgreSQL +     │        │ Simulation Service (Python) │
│ PostGIS          │        │ Pluggable SimulationModel   │
│ plants, scenarios│        │ interface; v1 = process-    │
│ runs, results    │        │ based heuristic model       │
└──────────────────┘        └─────────┬───────────────────┘
                                      │
                            ┌─────────▼───────────┐
                            │ Parquet storage     │
                            │ time-series results │
                            └─────────────────────┘
```

Key decisions:

- **Monorepo** with `frontend/`, `backend/`, and `simulation/` packages. The simulation service lives as a Python package imported by FastAPI in Phase 1 (in-process execution) — no separate microservice yet, but the package boundary keeps it extractable later.
- **Synchronous simulation runs** in Phase 1 (runs complete in < a few seconds for a heuristic model). API still returns a `run_id` and results are persisted, so switching to async/background later is non-breaking.
- **Model registry pattern** so the frontend never knows model internals — it only sees `model_id` + metadata from `/models`.
- **Result time-series** stored as Parquet files keyed by run ID; summary KPIs and metadata in Postgres.

---

## 2. Repository Layout

```text
wwtp-dashboard/
├── PROJECT.md
├── PLAN.md
├── docker-compose.yml            # postgres+postgis, api, frontend dev
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py               # FastAPI app, CORS, routers
│   │   ├── config.py
│   │   ├── db/                   # SQLAlchemy models, session, migrations (Alembic)
│   │   ├── schemas/              # Pydantic: plant, scenario, simulation, results
│   │   ├── routers/
│   │   │   ├── plants.py
│   │   │   ├── scenarios.py
│   │   │   ├── simulations.py
│   │   │   └── models.py
│   │   ├── services/             # business logic, run orchestration
│   │   └── seed/                 # demo plants + baseline data seeding
│   └── tests/
├── simulation/
│   ├── pyproject.toml
│   └── wwtp_sim/
│       ├── interface.py          # SimulationModel ABC + registry
│       ├── models/
│       │   └── effluent_v1.py    # heuristic process model
│       ├── domain.py             # dataclasses: Forecast, Maintenance, Params, Results
│       ├── storage.py            # parquet read/write
│       └── tests/
└── frontend/
    ├── package.json              # Vite + React + TS
    ├── src/
    │   ├── api/                  # typed client + React Query hooks
    │   ├── stores/               # Zustand: scenario draft, workspace UI
    │   ├── pages/
    │   │   ├── MapPage.tsx       # plant selection map
    │   │   └── WorkspacePage.tsx # 3-panel simulation workspace
    │   ├── components/
    │   │   ├── map/              # MapLibre + deck.gl layers
    │   │   ├── scenario/         # config forms (left panel)
    │   │   ├── dashboard/        # charts, KPI cards (center)
    │   │   ├── results/          # predictions, risks (right panel)
    │   │   ├── comparison/       # scenario comparison view
    │   │   └── twin/             # 3D digital twin (deck.gl)
    │   └── lib/
    └── e2e/                      # Playwright smoke tests
```

---

## 3. Data Model (PostgreSQL + PostGIS)

| Table | Key fields |
|---|---|
| `plants` | id, name, status (`operational` / `maintenance` / `warning`), `geom` (PostGIS point), capacity_mld, metadata jsonb |
| `plant_units` | id, plant_id, type (`pump` / `aeration` / `clarifier`), name, baseline_availability |
| `scenarios` | id, plant_id, name, horizon (`1m`/`3m`/`6m`), forecast jsonb, maintenance jsonb, operating_params jsonb, is_baseline, created_at |
| `simulation_runs` | id, scenario_id, model_id, status, kpis jsonb, risks jsonb, result_path (parquet), created_at |
| `compliance_limits` | plant_id, metric, limit_value, unit |

Forecast jsonb shape: `{demand: "low"|"normal"|"high"|{custom}, weather: "dry"|"normal"|"wet", influent: {flow, bod, cod, tss, ammonia}}`.
Maintenance jsonb shape: `[{unit_type, start_date, duration_days, availability_pct}]`.

---

## 4. API Contract (FastAPI)

```text
GET    /api/plants                          # list with geojson + status
GET    /api/plants/{id}                     # detail incl. units, compliance limits
GET    /api/plants/{id}/scenarios
POST   /api/plants/{id}/scenarios           # create scenario
GET    /api/scenarios/{id}
PUT    /api/scenarios/{id}
DELETE /api/scenarios/{id}
POST   /api/scenarios/{id}/run              # body: {model_id?} → run with results
GET    /api/runs/{id}                       # kpis, risks, summary
GET    /api/runs/{id}/timeseries            # predicted effluent series (from parquet)
POST   /api/compare                         # body: {run_ids: []} → aligned comparison
GET    /api/models                          # registered models + metadata
```

Simulation engine I/O matches PROJECT.md:

```json
IN:  { "forecast": {}, "maintenance": {}, "operating_parameters": {}, "simulation_horizon": "3_months" }
OUT: { "predicted_effluent": {}, "kpis": {}, "risks": {} }
```

---

## 5. Simulation Model v1 (`effluent_v1`)

A transparent, deterministic process-heuristic model — good enough for decision support and easily replaceable behind the interface.

- **Time step:** daily, over the horizon (30/90/180 days).
- **Influent generation:** baseline influent (flow, BOD, COD, TSS, ammonia) modulated by demand level (±15–30% flow/load) and weather (wet → dilution + flow spikes via stochastic rain events with fixed seed for reproducibility; dry → concentration).
- **Treatment efficiency:** per-metric removal efficiencies (e.g., BOD 95%, TSS 93%, ammonia 90% via aeration/nitrification) scaled by:
  - aeration availability → ammonia, BOD removal
  - clarifier availability → TSS, turbidity, phosphorus
  - pump availability → hydraulic capacity → overload penalty when flow > capacity
- **Maintenance windows:** during each event, the affected unit's availability drops; removal efficiencies degrade proportionally (matching PROJECT.md example: aeration maintenance → +12% ammonia, +5% COD).
- **Outputs per metric:** BOD, COD, TSS, ammonia, nitrate, phosphorus, turbidity, pH — daily predicted effluent values.
- **KPIs:** compliance % (days within limits / total), average quality score (0–100 weighted across metrics), treatment capacity utilization %, risk level (low/medium/high from compliance + headroom).
- **Risks:** structured list, e.g. `{metric: "ammonia", period: [d45,d52], severity: "high", cause: "aeration maintenance overlaps wet-weather peak"}`.

Interface (in `simulation/wwtp_sim/interface.py`):

```python
class SimulationModel(ABC):
    model_id: str
    name: str
    version: str

    @abstractmethod
    def run(self, forecast, maintenance, operating_parameters, horizon) -> SimulationResult: ...

MODEL_REGISTRY: dict[str, SimulationModel]   # frontend picks by model_id only
```

---

## 6. Frontend Design

**Map page (`/`):** Full-screen MapLibre basemap (free demotiles or OSM raster), deck.gl `ScatterplotLayer`/`IconLayer` for plants colored by status, hover tooltip (name, status, capacity), click → navigate to `/plants/:id`.

**Workspace page (`/plants/:id`):** Three-panel layout per PROJECT.md:

- **Left — Scenario Configuration:** scenario name, horizon selector (1m/3m/6m), demand forecast (low/normal/high or custom values), weather forecast (dry/normal/wet), influent condition inputs (flow, BOD, COD, TSS, ammonia), maintenance event editor (add pump/aeration/clarifier events with start date + duration), equipment availability sliders. Saved scenario list with load/duplicate/delete. "Run Simulation" button. Draft state in Zustand.
- **Center — Simulation Dashboard:** plant header (name, status, capacity), tabbed view: **Trends** (ECharts multi-series time charts of predicted effluent per metric, with compliance limit reference lines and maintenance windows shaded as mark areas) and **Digital Twin** (deck.gl 3D scene: extruded `PolygonLayer` representing tanks/clarifiers/pump station on a simple site plan, units colored by availability/maintenance state, animated over the simulation timeline with a scrubber).
- **Right — Predicted Results:** KPI cards (Compliance %, Avg Quality Score, Capacity Utilization, Risk Level badge), per-metric compliance status list (pass/warn/fail), maintenance impact summary (delta vs baseline per affected metric), risk list with severity badges.

**Comparison view:** select 2–3 runs (baseline + scenarios) → side-by-side KPI table with deltas, overlaid trend charts per metric, risk comparison.

State: React Query for all server data (plants, scenarios, runs); Zustand only for scenario draft form and workspace UI (selected tab, timeline position, comparison selection).

Styling: Tailwind + shadcn/ui (cards, tabs, dialogs, forms, selects, sliders, badges, toasts). Dark-friendly engineering-dashboard aesthetic.

---

## 7. Execution Phases

### Phase A — Scaffolding & Infrastructure
1. Monorepo structure, `docker-compose.yml` (postgres:16 + postgis), backend `pyproject.toml` (FastAPI, SQLAlchemy, Alembic, pandas, pyarrow), frontend Vite + React + TS + Tailwind + shadcn/ui init.
2. DB schema + Alembic migration, seed script: 4–6 demo plants (realistic coordinates, e.g. Victoria, Australia), units, compliance limits, one baseline scenario per plant.
3. Health-check endpoint; frontend dev proxy to API.

### Phase B — Simulation Engine
4. `wwtp_sim` package: domain dataclasses, `SimulationModel` ABC, registry.
5. `effluent_v1` model implementation (influent generation, efficiency model, maintenance impacts, KPIs, risks).
6. Parquet result storage; unit tests asserting maintenance degrades quality, wet weather increases risk, compliance math is correct, runs are deterministic.

### Phase C — Backend API
7. Plants endpoints (GeoJSON), scenarios CRUD, run endpoint wired to registry, timeseries endpoint reading parquet, compare endpoint, models endpoint.
8. API tests for the full happy path: create scenario → run → fetch results → compare.

### Phase D — Frontend: Map & Workspace Shell
9. Typed API client + React Query hooks.
10. Map page with plant layer, status colors, tooltips, click-through.
11. Workspace 3-panel shell with routing and plant header.

### Phase E — Frontend: Scenario Config & Results
12. Scenario configuration forms (forecast, influent, maintenance editor, availability) + scenario list management.
13. Run execution flow with loading state; results panel (KPI cards, compliance list, risks, maintenance impact).
14. ECharts trend charts with limit lines and maintenance shading.

### Phase F — Comparison & Digital Twin
15. Scenario comparison view (KPI deltas + overlaid charts).
16. 3D digital twin (deck.gl extruded site layout, availability coloring, timeline scrubber).

### Phase G — Polish & Verification
17. Empty states, error handling, toasts, responsive pass.
18. Playwright e2e: success-criteria walk-through (select plant → configure → run → review → compare).
19. README with setup/run instructions.

Dependency order: A → B → C → (D ∥ continues from C) → E → F → G. B and D can proceed in parallel once A is done.

---

## 8. Out of Scope (per PROJECT.md)

AI agent, SCADA integration, real-time control, BIM models, enterprise planning, 12-month horizon (interface supports adding it later), async job queue, auth/multi-tenancy.

## 9. Acceptance Checklist (maps to Success Criteria)

- [x] Map shows plants with status; clicking opens workspace (list fallback when WebGL unavailable)
- [x] Scenario with name + horizon can be created and saved
- [x] Demand/weather/influent forecast inputs accepted (presets + custom)
- [x] Maintenance events (pump/aeration/clarifier) with dates, durations, availability
- [x] Run completes and persists; rerunning a scenario is reproducible (seeded RNG, asserted in tests)
- [x] Effluent predictions for all 8 metrics over 1/3/6 months with compliance status
- [x] KPI summary: compliance %, quality score, capacity, risk level
- [x] Risks listed with cause, period, severity
- [x] Maintenance impact deltas shown (Impact vs Baseline panel)
- [x] Baseline vs Scenario A vs Scenario B comparison works (KPI table + trend overlay)
- [x] 3D digital twin implemented (deck.gl extruded site, availability colours, timeline scrubber); requires WebGL — graceful fallback message otherwise

Verified 2026-06-11: 8 engine unit tests + 2 API tests pass; full user journey
(map → workspace → configure → run → results → compare) exercised in a headless
browser with zero console errors. Deviations from plan: SQLite default instead
of Postgres (no Docker on this machine; compose file provided), hand-rolled
shadcn-style components instead of shadcn CLI, headless-browser QA instead of a
committed Playwright e2e suite.
