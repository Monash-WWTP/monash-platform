# Migration status and next work

| Work package | Status | Acceptance before advancing |
| --- | --- | --- |
| Successor source foundation | Imported locally; verification recorded separately | Inventory, product builds/tests, migration and OpenAPI checks, independent review |
| Identity | Implemented in source; production acceptance open | authentik staging, verified registration, operator invitation/MFA, issuer/subject mapping, recovery and fail-closed authorization |
| Monitoring read migration | Versioned API and source client implemented; real-data reconciliation open | Reviewed lab import, stations/samples/community projection API, filtering/pagination, privacy reconciliation, dashboard contract tests |
| Reporting and run hardening | Reports/media/moderation and immutable runs implemented; integrated release acceptance open | API-backed mobile report/media flows, moderation, immutable run inputs/provenance/failure states, generated clients |
| Server and cutover | Local staging exists; production cutover blocked | TLS, backups/restores, load evidence, data/access reconciliation, rollback rehearsal, client releases |

The source clients use the shared versioned API and API-owned application PostgreSQL. The published APK remains on its legacy backend until a qualified new release. The foundation imports source without switching production endpoints. Legacy Supabase migrations remain authoritative for deployed legacy data until cutover. Historical copies in this repo are inactive.

Do not claim old anonymous reports by email alone. Lab measurements and citizen observations stay separate. Approved community output must remove private identity, notes, precise coordinates and media paths. Every cutover needs reconciliation of data and authorization, a rollback checkpoint and an acceptance window. Legacy repositories are preserved; archival is a later owner decision.

Current verification and unresolved production gates: [2026-10-22 preparation review](../operations/production-readiness-2026-10-22.md). The [2026-10-18 acceptance record](../operations/staging-acceptance-2026-10-18.md) is historical. Source implementation does not establish production readiness.
