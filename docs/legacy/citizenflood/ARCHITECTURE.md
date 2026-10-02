# Architecture

CitizenFlood is a thin Flutter client talking directly to a hosted Supabase backend.
There is no custom server.

## Layers

```
┌─────────────────────────────────────────────┐
│  Screens (UI only)                           │
│  home_shell · category · report_form · map · │
│  profile                                     │
├─────────────────────────────────────────────┤
│  Services (all I/O)                          │
│  LocationService   → GPS via geolocator      │
│  ReportRepository  → Supabase insert/upload/ │
│                       fetch                   │
├─────────────────────────────────────────────┤
│  Models (pure Dart, fully unit-tested)       │
│  Report · ReportCategory · Condition         │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│  Supabase                                    │
│  `citizen_reports` · approved public view    │
│  private photos     · Anonymous Auth         │
└─────────────────────────────────────────────┘
```

**Rules of the boundary**
- Screens never call Supabase directly — they go through `ReportRepository`.
- Models contain no Flutter or Supabase imports, so they're trivially testable.
- Secrets enter the app only through `config/env.dart` (via `--dart-define`).

## Data model — `public.citizen_reports`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | primary key |
| `category` | text | `rainfall` · `water_level` · `temperature` · `wastewater` |
| `reading_value` | float8 | the measured number (mm / m / °C); null for wastewater |
| `reading_unit` | text | `mm` · `m` · `°C`; null for wastewater |
| `condition` | text | `normal` · `warning` · `critical`; wastewater only |
| `note` | text | optional, maximum 2,000 characters |
| `latitude`, `longitude` | float8 | auto-captured GPS |
| `location_accuracy_m` | float8 | optional device-reported accuracy |
| `station_code` | text | optional WWTP station association |
| `photo_path` | text | private path in the `citizen-report-photos` bucket |
| `observed_at` | timestamptz | when the citizen made the observation |
| `moderation_status` | text | `pending` · `approved` · `rejected` |
| `moderation_note` | text | private operator note |
| `reporter_id` | uuid | `auth.uid()` (anonymous or signed-in) |
| `created_at`, `updated_at` | timestamptz | server timestamps |

A `reading_shape` CHECK constraint enforces the rule: numeric categories must carry a
`reading_value` in the category's expected unit, and wastewater must carry a
`condition` (and no value).

## Public integration contract

`public.approved_citizen_observations` is the public, sanitized view for approved
observations across CitizenFlood's categories. The WWTP dashboard uses the narrower
`public.approved_wastewater_observations` view, which contains only approved
wastewater condition reports. Both views omit:

- `reporter_id`
- `photo_path`
- `moderation_note`
- internal update state

They also omit free-text notes and GPS accuracy from public results, and return
coordinates rounded to three decimal places. Exact values remain in the protected
report table for the reporter and moderators.

The WWTP web frontend reads `approved_wastewater_observations` through PostgREST
with the shared project's publishable key. It displays reports in a distinct map
layer and does not join them to plants, lab samples, compliance summaries, or
simulation inputs. Reports have GPS coordinates, but the current CitizenFlood form
does not assign a station code, so the dashboard does not infer a plant association.
Production database migrations are managed from the WWTP dashboard repository;
CitizenFlood continues to own its report model and collection workflow.

## Security (row-level)

- **Submit:** authenticated identities can insert only their own pending reports.
  Anonymous sign-in satisfies this without a sign-up flow.
- **Private read:** reporters can read their own rows, including pending submissions.
- **Public read:** anyone can read only approved, sanitized observations through the
  view.
- **Photos:** uploads and reads are limited to the reporter's user-ID folder. The app
  displays them with ten-minute signed URLs; external consumers receive no photo path.
- **Moderation:** client roles cannot approve or reject reports. An operator performs
  moderation in the Supabase dashboard or through a future privileged service.

## Why these choices

- **Supabase, no server** — fastest path to a working pilot; managed Postgres + storage
  + auth with no ops.
- **OpenStreetMap, not Google Maps** — no Google Play Services dependency, so the same
  build runs on any Android device.
- **Anonymous-first** — removes sign-up friction, which matters for citizen adoption.
- **Moderated public view** — prevents unreviewed citizen content and private metadata
  from flowing into the WWTP dashboard.
- **Shared Supabase project with scoped views and RLS** — both apps use one managed
  Postgres/Auth/Storage project. CitizenFlood can submit only its own pending rows;
  public consumers can read only the approved sanitized views.
- **`StatefulWidget` + `FutureBuilder`** — no heavy state-management library; easy to
  read and extend at pilot scale.
