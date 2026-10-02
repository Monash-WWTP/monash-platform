# Data Dictionary — Petaling WWTP Effluent Monitoring Dataset

Final-effluent monitoring lab results and emission-factor reference data for
the **PETALING-MAWAR (PTG248)** sewage treatment plant, 2023–2025. Originally exported
from the legacy database by
[historical export helper](../../legacy/scripts/dashboard/export_public_dataset.py);
see [`manifest.json`](manifest.json) for the pinned version and generation timestamp. The helper is inactive in the successor repository.

This snapshot contains no derived GHG estimates and does not determine legal
compliance. The available samples are final effluent; the GHG calculation
equations described in the project documentation require influent measurements
and plant operating data.

**License:** [CC-BY 4.0](LICENSE-DATA) — reuse freely with attribution
(see [snapshot attribution](README.md)).

The `category` and `compliance` fields below are reproduced from the source
dataset. They have not been checked against PTG248's receiving-water catchment,
system approval history, current permit, or monitoring plan.

---

## `stations.csv` — treatment plants

| Column | Type | Unit | Description |
|---|---|---|---|
| `code` | text | — | Station identifier (primary key), e.g. `PTG248`. |
| `name` | text | — | Plant name. |
| `stp_type` | text | — | Treatment process, e.g. `SBR` (Sequencing Batch Reactor). |
| `category` | text | — | Source dataset category; not independent legal or permit verification. |
| `latitude` | float | °, WGS84 | Plant latitude. |
| `longitude` | float | °, WGS84 | Plant longitude. |
| `created_at` | timestamptz | ISO 8601 | Row creation time. |

## `effluent_samples.csv` — measured final-effluent lab results

One row per lab sample. Each metric `<m>` has a companion boolean `<m>_bdl`
flagging a **below-detection-limit** reading (the lab reported `"< x"`; the
stored value is the limit `x`).

| Column | Type | Unit | Description |
|---|---|---|---|
| `id` | int | — | Sample identifier (primary key). |
| `station_code` | text | — | FK → `stations.code`. |
| `sample_date` | date | ISO 8601 | Sampling date. |
| `sampling` | int | — | Sampling round/sequence within the visit. |
| `sample_point` | text | — | Sampling location; `FE` = final effluent. |
| `bod` | float | mg/L | Biochemical Oxygen Demand. |
| `cod` | float | mg/L | Chemical Oxygen Demand. |
| `nh3n` | float | mg/L | Ammoniacal Nitrogen, NH₃-N. |
| `no3n` | float | mg/L | Nitrate Nitrogen, NO₃-N. |
| `ph` | float | pH units | pH. |
| `oil_grease` | float | mg/L | Oil & Grease. |
| `tss` | float | mg/L | Total Suspended Solids. |
| `temperature` | float | °C | Effluent temperature. |
| `<metric>_bdl` | bool | — | `true` if the metric was below the detection limit. |
| `compliance` | text | — | Source-recorded status (`Comply` / `Not Comply`); not independently assessed against a permit. |
| `source_year` | int | — | Calendar year the source dataset covers. |
| `created_at` | timestamptz | ISO 8601 | Row creation time. |

## `emission_factors.csv` — process-specific GHG emission factors

Reference emission factors per treatment process from the cited accounting
guideline (Tables 5.6 / 5.8). They are not measured at PTG248 and do not by
themselves constitute a plant GHG inventory. The `GENERAL` row is the integrated
factor used when a plant's process is unmapped.

| Column | Type | Unit | Description |
|---|---|---|---|
| `process_type` | text | — | Process key (primary key), e.g. `SBR`, `GENERAL`. |
| `ef_ch4` | float | kg CH₄ / kg BOD₅ | Methane emission factor. |
| `ef_n2o` | float | kg N₂O-N / kg N | Nitrous-oxide emission factor. |
| `source` | text | — | Provenance note. |

---

### Caveats for reuse

- **Single station, 3 years (154 samples).** Treat aggregates as indicative, not
  population-level statistics.
- **BDL values are stored as the detection limit**, which biases low-end metrics
  upward. Use the `*_bdl` flags to censor or model them appropriately.
- Do not infer legal compliance from `category` or `compliance`; verify the
  applicable regulation, receiving water, system class, permit, and sampling
  requirements for the specific plant.
- Do not combine these final-effluent concentrations with the emission-factor
  table to produce plant GHG intensities. Use validated influent measurements
  and the documented system boundary.
