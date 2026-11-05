# Local monitoring data and migration

The local demo uses the API-owned PostgreSQL database in the existing `monash-staging` Compose project, with the `application_db` named volume. Restarting containers preserves the records. Do not use `down -v`, reset schemas or run destructive API tests against this database.

## Source and current records

On 2026-11-05 the supplied Supabase public REST source was read through its publishable key: two stations (PTG248 and NXP), 154 final-effluent samples and eight emission-factor reference rows. The original checked-in snapshot remains unchanged. A new immutable snapshot, including column allowlists, row counts and CSV hashes, is retained outside Git at:

`~/.local/share/monash-platform/monitoring/2026-11-05/`

The application database holds two stations and 154 samples. Factor rows remain import provenance/reference data; they do not automatically configure scientific or operational factors. The monitoring import itself does not invent plant capacity, equipment, permit thresholds or account ownership. A subsequent, user-authorized local demo configuration adds explicitly synthetic engineering assumptions for NXP and PTG248; see below. Monitoring locations now appear on the map even before an operational plant configuration exists. A location without a linked configured plant cannot open a research workspace.

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

This creates one `DEMO001` Synthetic Demonstration Plant and one Synthetic baseline scenario. The fixture is displayed in the lab and excluded from the real-station map. It uses editable synthetic capacity, influent, equipment and screening assumptions; it is not associated with PTG248 or NXP. Running or changing a scenario requires a signed-in platform account. As requested on 2026-11-05, Simulation lab no longer requires an operator invitation, the legacy scenario:operate capability or MFA. The current local database had zero scenarios and zero saved simulation runs before this seed; no historical runs were removed. The fixture is development-only, not a production data import. Review/exclude demonstration data during production cutover.

## Local Tailscale demo adapter

Run `python3 scripts/serve_tailnet_demo.py` while Vite (8180) and authentik (9100) are running. This loopback-only adapter is specific to this demo host. Its two listeners are 8182 (web/API) and 9182 (identity). Tailscale Serve routes HTTPS 10575 to 8182, HTTPS 10577 to 9182 and HTTPS 10576 directly to Mailpit 8125. It preserves the local canonical OIDC issuer and registered callback while adapting browser URLs, including authentik's embedded frontend API base. WebSocket upgrades are tunneled for identity and Vite. No credentials or request payloads are logged.

The previous temporary proxy rewrote HTTP redirects but left authentik's frontend API base at localhost, causing “The request failed and the interceptors did not return an alternative response” in a remote browser. It also dropped WebSocket upgrades. The adapter now rewrites the embedded base and forwards upgrade handshakes. This is local demo compatibility, not the production domain/issuer/callback cutover design.

## Operator callback after first-time MFA enrollment

The 2026-11-05 operator callback failure occurred after a successful code/token exchange. The identity provider had just enrolled a TOTP device but had never validated an OTP through its validation stage (`last_used` remained empty), so its token carried password authentication without `mfa`. The API correctly rejected that operator proof. Ordinary citizen sign-in remained separate.

`identity/operator_mfa.py`, called by the identity bootstrap, adds a conditional validation stage before operator login completes. It requires code validation after setup, but skips the extra stage when the same flow already has validated MFA devices. The new stage denies missing authenticators and never derives MFA from device existence alone. Operator authorization requests also include `max_age=1` with `prompt=login` to avoid reusing an older password-only identity session. No MFA, nonce, signature, verified-email or capability checks were removed. Existing authenticators and accounts are preserved. A failed callback URL/code must not be reused; start a new login through the API entry point.

## Simulation access policy

Any verified signed-in account can read, create, edit, archive, run, replay and compare scenarios in the existing shared research lab. Anonymous requests remain denied, and browser mutations retain session/CSRF checks. Account administration, shared plant configuration, publication review and operational report response retain their separate server permissions and MFA requirements. No account was granted an administrative capability to enable lab access. The lab sign-in link uses ordinary account sign-in; operator MFA remains available for privileged tasks.

## Cable-free Samsung demo

Build CitizenFlood using `apps/citizenflood/tailscale-config.example.json` instead of the USB/localhost staging configuration. Its API and discovery transport use this host's Tailscale HTTPS services. Discovery endpoint URLs are adapted by `serve_tailnet_demo.py`; the canonical OIDC issuer identifier is deliberately preserved so existing account identities and report ownership do not change. The localhost issuer is an identity identifier here, not the network endpoint used by the phone. Approved account-settings action URLs are also adapted to the same remote identity origin.

The phone must have Tailscale installed, signed into the same authorized tailnet and connected. The computer must remain awake with Docker services, Vite and the demo adapter running. USB reverse is unnecessary for this build. It can use Wi-Fi or mobile data through Tailscale; it does not work with this computer/services turned off. This remains a separate staging debug package, not a replacement for the public production APK.

```sh
cd apps/citizenflood
flutter build apk --debug --dart-define-from-file=tailscale-config.example.json
```

The prepared APK is shared only within the tailnet on HTTPS port 10578. Install it over the existing staging app (same debug signing identity); do not uninstall merely to update, as that would remove local drafts. Cable-free sign-in was subsequently checked on the Samsung, as recorded below. Report submission/upload acceptance remains pending.

APK delivery uses a loopback file server on 8184 serving only `~/.local/share/monash-platform/apks/`, proxied by Tailscale HTTPS 10578. The current artifact is `citizenflood-tailnet-demo.apk`; it is copied out of Flutter's mutable build output so a later USB build cannot silently replace this download. Keep this file server running while downloading. The tailnet-only download URL is `https://asus-dev.tail66f665.ts.net:10578/citizenflood-tailnet-demo.apk`.

Cable-free phone acceptance (2026-11-05): the Tailscale APK was installed over the existing staging app on Samsung SM-A076B. Tailscale was connected; `adb reverse --list` was empty. The app loaded its observation feed without a connection error and opened the CitizenFlood identity page over HTTPS. The user confirmed sign-in returned to CitizenFlood. Station/laboratory records are not currently a mobile map layer: the phone loads approved community reports plus the signed-in user's own reports, whereas the dashboard also loads monitoring stations and historical lab samples. Upload/report submission over Tailscale is not established by the sign-in check alone.

## NXP and PETALING-MAWAR runnable demo configurations (2026-11-05)

At the user's explicit request, both imported locations now have linked plant configurations and a **Demo assumptions baseline** scenario. Imported station metadata and historical samples were preserved. These are local demonstration configurations, not measured engineering records or validated plant models.

| Setting | Both demonstration baselines | Provenance |
| --- | --- | --- |
| Design capacity | 10 MLD | Existing synthetic development fixture; assumed |
| Influent flow | 6 MLD | Existing synthetic development fixture; assumed |
| Influent BOD₅ / COD / TSS | 250 / 520 / 300 mg/L | Synthetic influent, not final-effluent samples |
| Influent ammonia / TKN | 30 / 40 mg/L | Synthetic influent |
| Equipment | One simulated pump, aeration unit and clarifier, each 100% available | Assumed equipment, not an asset inventory |
| Maintenance | No events | Demo assumption, not a confirmed schedule |
| Screening BOD₅ / COD / TSS | 50 / 200 / 100 mg/L | Synthetic screening values, not plant permits |
| CH₄ / N₂O factors | 0.0121 kg CH₄/kg BOD₅; 0.0093 kg N₂O-N/kg N | Synthetic fixture's generic factors; site applicability unverified |
| Plant status | Unknown | No operating-status evidence supplied |

NXP retains its imported IETS label and coordinates; PTG248 retains its SBR label and coordinates. Neither label establishes the applicability of the generic factors or model. Imported factor-reference rows were not automatically promoted to site-approved factors. Equipment names and plant descriptions identify the assumptions. Configuration revisions and administrative history retain their source and the user's authorization reason.

On this local database, NXP is plant 2 / scenario 2 / completed run 3; PETALING-MAWAR is plant 3 / scenario 3 / completed run 4. Both runs start on 2026-11-05 with a three-month horizon. These identifiers are local and must not be hardcoded into another environment. Successful execution establishes software behavior only; it does not establish scientific accuracy.

Open the Simulation lab, choose the plant and select **Demo assumptions baseline**. Replace assumed capacity/equipment/thresholds/factors through Administration → Plants; replace influent and maintenance in the scenario. New configuration revisions affect future runs; retain existing saved-run provenance. Before production transfer, explicitly exclude these demo scenarios/configurations or replace them with reviewed site records. Do not import them silently as real engineering data.

Pre-change application database snapshot: `~/.local/share/monash-platform/backups/before-engineering-demo-20261105.sql` (owner-only, unencrypted local dump). Treat it as private; encrypt before any transfer. The earlier encrypted backups predate these two configurations and runs. Create a new coordinated encrypted backup before migration; do not assume the earlier bundles contain the latest state.
