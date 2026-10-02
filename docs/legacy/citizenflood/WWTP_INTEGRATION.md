# WWTP platform integration

CitizenFlood is the collection and moderation side of the unified platform. The
WWTP dashboard is a read-only consumer of approved observations.

## Shared project

- project ref: `eaxekwlmvpvftpgxiwlu`
- region: `ap-northeast-1` (Tokyo)
- URL: `https://eaxekwlmvpvftpgxiwlu.supabase.co`

The Flutter app receives this URL and the project's publishable key from the
git-ignored `env.json`; no Supabase key is committed to this repository. Run the
app with:

```bash
./scripts/run.sh
```

## Shared contract

The app writes pending rows to `public.citizen_reports`. Operators approve or
reject them in the Supabase Table Editor. The WWTP frontend reads only
`public.approved_wastewater_observations`, a read-only view of wastewater reports
that have been approved. It excludes:

- reporter identity;
- private photo paths;
- moderation notes;
- free-text report notes and GPS accuracy;
- pending and rejected submissions.

Public map coordinates are rounded to three decimal places; exact coordinates
remain only in the protected report table.

The WWTP map shows these rows in a separate, purple “Approved community
wastewater” layer. It labels them as community reports, not laboratory results.
The current reports do not have a station association, so the dashboard does not
attach them to a plant or include them in compliance calculations, GHG estimates,
or simulation inputs. The layer refreshes every 60 seconds.

## Required Supabase settings

1. In the WWTP dashboard repository, authenticate with `npx supabase login`, link
   `eaxekwlmvpvftpgxiwlu`, and apply the database migrations with `npx supabase db push`.
   That repository is the production migration source of truth and includes the
   CitizenFlood schema, wastewater-only view, and privacy-safe public projection.
2. Enable **Authentication → Providers → Allow anonymous sign-ins**.
3. Keep the `citizen-report-photos` bucket private.
4. Set the Flutter `SUPABASE_URL` and `SUPABASE_ANON_KEY` build values to this
   shared project's URL and publishable key.

Never place a secret/service-role key in the Flutter app or the WWTP frontend.

## Acceptance test

1. Submit a wastewater condition report from the Flutter app.
2. Verify it is absent from both public approved views while pending.
3. Approve it in the Table Editor.
4. Verify it appears in `approved_wastewater_observations` and on the dashboard's
   separate community-observation map layer.
5. Verify it does not change any lab-result, compliance, GHG, or simulation data.

The canonical deployment and database migration details live in the WWTP dashboard
repository at `docs/CITIZENFLOOD_INTEGRATION.md`.
