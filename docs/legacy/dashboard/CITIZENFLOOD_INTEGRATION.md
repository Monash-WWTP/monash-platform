# CitizenFlood integration

CitizenFlood collects public, location-based reports. The WWTP dashboard displays
moderator-approved wastewater condition reports in a separate map layer. They are
not lab measurements and are not used for compliance, GHG accounting, or simulation.

## Shared Supabase project

Production uses the existing WWTP project:

- Project ref: `eaxekwlmvpvftpgxiwlu`
- URL: `https://eaxekwlmvpvftpgxiwlu.supabase.co`
- Region: `ap-northeast-1` (Tokyo)

The dashboard repository is the production migration source of truth. It contains
the WWTP monitoring migrations and a mirrored CitizenFlood schema migration so the
shared project's migration history is managed from one place.

## Data flow and separation

1. CitizenFlood inserts a report into `public.citizen_reports` as
   `moderation_status = 'pending'`. RLS permits an authenticated citizen to insert
   only their own pending row and read only their own rows.
2. An operator approves or rejects reports in the Supabase Table Editor.
3. `public.approved_citizen_observations` exposes approved observations with no
   reporter identity, note, location accuracy, or private photo path. Public map
   coordinates are rounded to three decimal places.
4. `public.approved_wastewater_observations` narrows that view to the `wastewater`
   category and the fields needed for map markers and details.
5. The WWTP frontend reads only the wastewater view with its publishable key. It
   shows up to the latest 500 reports as distinct purple `W` markers labelled as
   approved community reports, not laboratory measurements.

Citizen reports carry GPS coordinates, but the current report form does not set
`station_code`. The dashboard therefore plots their reported locations without
claiming they belong to a particular treatment plant. It does not merge them with
`effluent_samples`, GHG views, compliance summaries, or simulation records.

## Provision and configure

From this repository, after `npx supabase login`:

```bash
npx supabase link --project-ref eaxekwlmvpvftpgxiwlu
npx supabase migration list --linked
npx supabase db push --dry-run
npx supabase db push
```

The dashboard repository owns the shared migration chain, including
`20260928000003_privacy_safe_public_observations.sql`. The CLI applies only
migrations missing from the linked project's migration history. Review the
dry-run list before applying it. Never run `db reset` against
the production project.

The shared project also needs **Authentication → Providers → Allow anonymous
sign-ins** enabled for CitizenFlood submissions. Keep the
`citizen-report-photos` Storage bucket private. Set the Flutter app's build-time
`SUPABASE_URL` and `SUPABASE_ANON_KEY` to the shared project URL and publishable
key; do not put a service-role key in either client.

## Existing CitizenFlood data

Applying migrations creates the shared schema; it does not copy existing report
rows or Storage objects from CitizenFlood's former project. Before switching the
released app build, export and import any report history that needs to remain
available, and migrate Storage objects separately if their photos must be kept.
The view intentionally omits photo paths, so public dashboard markers do not
depend on photo migration.

## Acceptance checks

- A pending wastewater report is absent from both approved views.
- After approval, the wastewater report appears in
  `approved_wastewater_observations` and the dashboard's separate map layer.
- Approved rainfall, water-level, and temperature reports do not appear in the
  WWTP observation layer.
- Community reports do not change lab-result tables, compliance summaries, GHG
  estimates, or simulation inputs.
- The raw report table remains unavailable to `anon`; photo storage remains private.
