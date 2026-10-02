# CitizenFlood

An **Android** app where citizens record site environmental data — each reading tagged
with a photo and auto-captured GPS, and aggregated as tappable pins on a shared live map.
Built with Flutter + Supabase + OpenStreetMap (no Google services required).

## What you can record

| Category | Input | Unit |
|---|---|---|
| 🌧️ Rainfall | a number | mm |
| 💧 Water level | a number | m |
| 🌡️ Temperature | a number | °C |
| 🏭 Wastewater plant condition | a status | Normal / Warning / Critical |

Every reading also captures: an optional **photo** (camera or gallery), the device's
**GPS location** (automatic), an optional **note**, and a timestamp.

## How it works

```
Flutter app  ──►  Supabase
  • Report tab: pick a category → enter reading → photo → submit
  • Map tab:    live OpenStreetMap with colored pins; tap a pin to see the reading + photo
  • Me tab:     anonymous by default; optional email sign-in

Supabase backend (no custom server):
  • Postgres `citizen_reports` table (private, row-level security)
  • Sanitized `approved_citizen_observations` view for public/WWTP consumers
  • Private `citizen-report-photos` bucket with short-lived signed URLs
  • Anonymous auth so anyone can submit without signing up
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a deeper overview,
[`docs/WWTP_INTEGRATION.md`](docs/WWTP_INTEGRATION.md) for the unified platform setup,
`docs/specs/` for the original design, and `docs/plans/` for the build plan.

## Prerequisites

- Flutter SDK (stable) + Android toolchain — `flutter doctor` should be ✓ for Android.
- A Supabase project. Production uses the WWTP dashboard's shared project; run
  production migrations from the WWTP dashboard repository so there is one
  migration history. For local development, use the CitizenFlood Supabase CLI setup:

```bash
supabase link --project-ref YOUR_LOCAL_OR_DEV_PROJECT_REF
supabase config push
supabase db push
```

This applies `supabase/config.toml` (including anonymous authentication) and the
versioned migrations to a separate local/dev project. Do not use the
CitizenFlood CLI history to push production schema to the shared WWTP project.
For a one-off standalone setup, run `supabase/schema.sql` in the SQL Editor and
enable **Authentication → Providers → Anonymous**.

## Running locally

Secrets are injected at build time and never committed. Use a local `env.json`:

```bash
cp env.example.json env.json   # then fill in your Supabase URL + anon key
./scripts/run.sh               # wraps: flutter run --dart-define-from-file=env.json
```

`env.json` is git-ignored. You can also pass values directly:

```bash
flutter run \
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

## Tests

```bash
flutter test        # model + widget tests
flutter analyze     # static analysis (should be clean)
```

## Release build (Google Play)

```bash
flutter build appbundle --dart-define-from-file=env.json   # .aab for Play
flutter build apk --release --dart-define-from-file=env.json  # standalone .apk
```

## Tech stack

Flutter (Dart 3) · `supabase_flutter` · `flutter_map` + `latlong2` ·
`geolocator` · `image_picker` · `permission_handler` · `intl`

## Project layout

```
lib/
├── main.dart              # entry: Supabase init + anonymous sign-in
├── config/env.dart        # reads SUPABASE_URL / SUPABASE_ANON_KEY
├── models/report.dart     # Report + ReportCategory + Condition (pure Dart)
├── services/              # location_service.dart, report_repository.dart (all I/O)
├── widgets/               # category_tile.dart
└── screens/               # home_shell, category, report_form, map, profile
supabase/schema.sql        # tables, storage bucket, RLS policies
supabase/migrations/       # versioned production schema
test/                      # unit + widget tests
```

## Moderation and WWTP integration

New submissions start as `pending`. Their author can see them immediately, but the
shared map and external systems only receive `approved` rows from
`approved_citizen_observations`. A trusted operator approves or rejects a row in the
Supabase Table Editor by updating `moderation_status` and, optionally,
`moderation_note`.

The WWTP dashboard reads only that privacy-safe view with a publishable key. It
receives coarse coordinates but not free-text notes, reporter IDs, moderation
notes, GPS accuracy, or private photo paths. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the complete contract.
