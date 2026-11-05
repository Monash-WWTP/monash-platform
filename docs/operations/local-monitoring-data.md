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

## Simulation lab and demo baseline

The monitoring page links to `/dashboard/simulation`. This lists configured simulation plants separately from imported monitoring locations and identifies missing engineering configuration. Laboratory effluent concentrations do not supply influent BOD/COD/TSS/ammonia/TKN or flow. Real-site scenarios also need capacity, equipment/maintenance assumptions, factor applicability and calibration/validation evidence. Do not infer these values from final-effluent samples.

The local demo fixture was explicitly seeded on 2026-11-05 using the existing development-only fixture, then repeated to verify idempotence:

```sh
docker exec -e APP_ENV=development monash-staging-api-1 uv run --no-sync python -m app.devdata
```

This creates one `DEMO001` Synthetic Demonstration Plant and one Synthetic baseline scenario. The fixture is displayed in the lab and excluded from the real-station map. It uses editable synthetic capacity, influent, equipment and screening assumptions; it is not associated with PTG248 or NXP. Running or changing a scenario still requires an authorized operator session and MFA. The current local database had zero scenarios and zero saved simulation runs before this seed; no historical runs were removed. The fixture is development-only, not a production data import. Review/exclude demonstration data during production cutover.

## Local Tailscale demo adapter

Run `python3 scripts/serve_tailnet_demo.py` while Vite (8180) and authentik (9100) are running. This loopback-only adapter is specific to this demo host. Its two listeners are 8182 (web/API) and 9182 (identity). Tailscale Serve routes HTTPS 10575 to 8182, HTTPS 10577 to 9182 and HTTPS 10576 directly to Mailpit 8125. It preserves the local canonical OIDC issuer and registered callback while adapting browser URLs, including authentik's embedded frontend API base. WebSocket upgrades are tunneled for identity and Vite. No credentials or request payloads are logged.

The previous temporary proxy rewrote HTTP redirects but left authentik's frontend API base at localhost, causing “The request failed and the interceptors did not return an alternative response” in a remote browser. It also dropped WebSocket upgrades. The adapter now rewrites the embedded base and forwards upgrade handshakes. This is local demo compatibility, not the production domain/issuer/callback cutover design.
