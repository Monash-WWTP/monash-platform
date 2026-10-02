# WWTP Scenario Analysis & Effluent Quality Screening Platform

Web platform for illustrative scenario screening of treatment plant performance
and effluent quality over 1–6 month horizons. The current process heuristic is
not calibrated for plant decisions.
See `PROJECT.md` for the product spec and `PLAN.md` for the implementation plan.

## Stack

- **Frontend** — React + TypeScript + Vite, Tailwind v4 + shadcn/ui, MapLibre 3D map
  (OpenFreeMap Liberty with building extrusions, fly-to zoom on station click),
  deck.gl (3D digital twin), ECharts (trends), React Query + Zustand,
  supabase-js (real monitoring data)
- **Data** — Supabase (`stations`, `effluent_samples` tables, RLS public-read).
  Real PTG248 PETALING-MAWAR lab results 2023–2025 uploaded from `data-to-upload/`
  via `scripts/upload_to_supabase.py` (re-runnable, idempotent; uses the Supabase
  CLI's keychain token + Management API).
- **Citizen observations** — CitizenFlood shares this Supabase project. Only
  moderator-approved wastewater reports appear in a separate community map layer;
  they are not lab results or simulation inputs. See
  [`docs/CITIZENFLOOD_INTEGRATION.md`](docs/CITIZENFLOOD_INTEGRATION.md).
- **Scenario GHG estimates** — The simulation backend calculates CH₄ and N₂O
  treatment-process estimates from entered or assumed influent BOD₅/TKN, factors,
  and recovery terms. The process model is heuristic and unvalidated against a
  plant; outputs are illustrative scenario comparisons, not a verified inventory
  or operational estimate. See [Backend carbon accounting](docs/CARBON_ACCOUNTING.md).
- **Sample GHG views** — Migration
  `20260928000003_privacy_safe_public_observations.sql` revokes public access to
  the sample-based GHG views because the available measurements are final
  effluent, while the cited calculations require influent measurements. Apply
  this migration before treating the shared database as privacy-safe.
- **Backend** — FastAPI + SQLAlchemy, **stateless** (no local files). Plants sync
  from Supabase stations at startup; scenario/run state — including each run's full
  time-series — persists as JSONB in the database (SQLite locally, Supabase Postgres
  in production via `DATABASE_URL`). The simulator screens BOD/COD/TSS against
  Standard A/B thresholds but does not provide a complete legal compliance assessment.
- **Simulation** — `wwtp_sim` Python package with a pluggable `SimulationModel`
  interface; v1 is a deterministic process-heuristic model that also computes CH₄/N₂O
  emission intensities.

## Quick start

```bash
# 1. Python env (from repo root)
uv venv .venv --python 3.12
uv pip install -p .venv/bin/python -e "./simulation[dev]" -e "./backend[dev]"

# 2. Backend (syncs the PTG248 station from Supabase on first start)
cd backend && WWTP_OPERATOR_EMAILS=operator@monash.edu ../.venv/bin/python -m uvicorn app.main:app --port 8000

# 3. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — the 3D map zooms into a station when clicked and
opens its monitoring dashboard (filter real lab samples by year, compliance,
and parameter). From there, open the simulation workspace, configure a scenario
(forecast, maintenance, availability), sign in with an invited operator email,
press **Run Simulation**, then explore the scenario trends and comparisons. Add
that email to Supabase Auth and to `WWTP_OPERATOR_EMAILS`; also add
`http://localhost:5173` to Supabase Auth's redirect allow-list.

To re-upload or refresh monitoring data (requires `supabase login` + linked project):

```bash
python3 scripts/upload_to_supabase.py
```

## Tests

```bash
.venv/bin/python -m pytest simulation/wwtp_sim/tests   # engine (10 tests, incl. GHG equations)
cd backend && ../.venv/bin/python -m pytest tests      # API happy path
```

## Carbon-accounting reference

The backend implementation, API fields, output keys, worked example, and
accounting boundaries are documented in
[`docs/CARBON_ACCOUNTING.md`](docs/CARBON_ACCOUNTING.md).

## Open data for researchers

The monitoring measurements and emission-factor reference data are published as
an open, citable dataset under [CC-BY 4.0](LICENSE-DATA). Sample-based GHG
intensities are excluded because the available measurements are final effluent,
not the influent measurements required for those calculations.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Monash-WWTP/wwtp-dashboard/blob/main/notebooks/wwtp_explore.ipynb)

- **Explore it now** — the badge opens [`notebooks/wwtp_explore.ipynb`](notebooks/wwtp_explore.ipynb)
  in Google Colab. It loads a fixed snapshot straight from GitHub (no key/setup) and
  has starter views for source-recorded status and effluent trends. It does not
  calculate legal compliance or sample-based GHG intensities.
- **Snapshot files** — [`public-data/`](public-data/) holds CSV (and Parquet, if
  generated) for `stations`, `effluent_samples`, and `emission_factors`, plus a
  [data dictionary](public-data/DATA_DICTIONARY.md) and a
  `manifest.json` (version + generation timestamp).
- **Cite it** — see [`CITATION.cff`](CITATION.cff).

Snapshots are decoupled from the live database on purpose: researchers' notebooks
keep working even when the internal schema changes. Refresh the snapshot only after
reviewing changes to its source data and field meanings.

### Refreshing the snapshot

```bash
python3 scripts/export_public_dataset.py     # re-reads Supabase (read-only) -> public-data/
# pip install pandas pyarrow first if you also want Parquet output
```

Then commit `public-data/` and bump `DATASET_VERSION` in the script for any
column/semantics change.

### Minting a DOI (one-time setup)

To make each release citable with a DOI, link the repo to **Zenodo**:

1. Sign in to [zenodo.org](https://zenodo.org) with GitHub and flip the switch on
   the `Monash-WWTP/wwtp-dashboard` repository.
2. Create a GitHub **Release** (e.g. `data-v1.0.0`). Zenodo archives that commit —
   including `public-data/` — and mints a DOI.
3. Add the minted DOI to `CITATION.cff` (uncomment the `identifiers` block) and a
   DOI badge here.

## Deployment

Live hosting (Vercel + Render + Supabase) is documented in
[`DEPLOYMENT.md`](DEPLOYMENT.md). The backend is stateless, so set `DATABASE_URL`
to a Supabase Postgres connection string in production and it persists everything
there.

## Adding a new simulation model

Implement `SimulationModel` in `simulation/wwtp_sim/models/` and call
`register_model(...)` (see `effluent_v1.py`). It appears automatically in
`GET /api/models`; the frontend selects models by `model_id` only.
