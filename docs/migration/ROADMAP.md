# Migration status and next work

| Work package | Status | Acceptance before advancing |
| --- | --- | --- |
| Successor source foundation | Imported locally; verification recorded separately | Inventory, product builds/tests, migration and OpenAPI checks, independent review |
| Identity | Planned | authentik staging, verified registration, operator invitation/MFA, issuer/subject mapping, recovery and fail-closed authorization |
| Monitoring read migration | Planned | Reviewed lab import, stations/samples/community projection API, filtering/pagination, privacy reconciliation, dashboard contract tests |
| Reporting and run hardening | Planned | API-backed mobile report/media flows, moderation, immutable run inputs/provenance/failure states, generated clients |
| Server and cutover | Planned | TLS, backups/restores, load evidence, data/access reconciliation, rollback rehearsal, client releases |

Both products eventually share API-owned application PostgreSQL. The foundation imports source without switching production endpoints. Legacy Supabase migrations remain authoritative for deployed legacy data until cutover. Historical copies in this repo are inactive.

Do not claim old anonymous reports by email alone. Lab measurements and citizen observations stay separate. Approved community output must remove private identity, notes, precise coordinates and media paths. Every cutover needs reconciliation of data and authorization, a rollback checkpoint and an acceptance window. Legacy repositories are preserved; archival is a later owner decision.
