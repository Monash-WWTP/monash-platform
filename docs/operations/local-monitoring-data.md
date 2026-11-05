# Local monitoring data and migration

The local demo uses the API-owned PostgreSQL database in the existing `monash-staging` Compose project, with the `application_db` named volume. Restarting containers preserves the records. Do not use `down -v`, reset schemas or run destructive API tests against this database.

## Source and current records

On 2026-11-05 the supplied Supabase public REST source was read through its publishable key: two stations (PTG248 and NXP), 154 final-effluent samples and eight emission-factor reference rows. The original checked-in snapshot remains unchanged. A new immutable snapshot, including column allowlists, row counts and CSV hashes, is retained outside Git at:

`~/.local/share/monash-platform/monitoring/2026-11-05/`

The application database holds two stations and 154 samples. Factor rows remain import provenance/reference data; they do not automatically configure scientific or operational factors. No plant capacity, equipment, permit threshold or account ownership was invented to make a demo. Monitoring locations now appear on the map even before an operational plant configuration exists. A location without a linked configured plant cannot open a research workspace.

## Repeat the workflow

Set the approved source URL and publishable key in `SUPABASE_URL` and `SUPABASE_KEY` outside Git, then capture to a **new** directory:

```sh
uv run --locked python scripts/snapshot_public_monitoring.py --destination /private/path/new-snapshot
```

Use the configured destination `DATABASE_URL` and run:

```sh
uv run --locked python scripts/migrate_platform.py --public-snapshot /private/path/new-snapshot --reuse-identical
```

Reusing the same snapshot is idempotent. A new snapshot may reuse identical station/sample payloads and add missing identifiers; changed existing records are rejected for review, never overwritten. Import manifests and digests are stored in `import_records`. The public REST reads are sequential, not a provider-level transactional export; compare against a transaction-consistent source export for final production reconciliation. Keep snapshots private until distribution rights for new rows are reviewed.

## Retention and production transfer

An encrypted full local backup was created at `~/.local/share/monash-platform/backups/demo-2026-11-05.enc`. It includes application and identity database dumps, one private media object and local configuration. Its separate encryption key stays outside Git and chat. Use `scripts/staging_backup.py` and the existing backup/restore runbook for isolated restore rehearsal; never restore over a valuable database for testing.

For production, either import a reviewed snapshot into a migrated empty application database, or restore the application/identity/private-storage bundle through the approved cutover plan. Reconcile record counts, identifiers and import digests. Retain historical censoring flags, dates, units and source labels. Domain/issuer and account ownership mapping, production secrets, SMTP and storage still require deployment configuration; a local backup is not an automatic production cutover. The supplied database URL contains `[YOUR-PASSWORD]` and has not been used as a production connection.
