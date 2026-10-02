# Standalone server readiness

No production deployment configuration or cutover is complete. Start with independent dashboard/static hosting and API processes behind TLS, application PostgreSQL, authentik with a separate identity database, and private object storage. A shared physical server is acceptable initially; keep service credentials, database roles and backup procedures distinct.

Before deployment, record domains, TLS/DNS ownership, approved maintainers, measured request/photo volume, resource limits, API workers, object retention, RPO/RTO, and recovery owners. Use secret injection outside Git, restricted DB networking, least-privilege DB roles, durable object storage and versioned release artifacts. Migrations run as an explicit release step before traffic changes. Do not deploy the disposable Compose service or its credentials.

Current blockers:

- Identity, reporting/monitoring contracts, client cutover and privacy reconciliation remain planned.
- The inherited npm audit findings were remediated locally (MapLibre upgrade, removal of unused umbrella dependency, compatible lockfile updates). The current audit is clean; require the CI audit and browser release checks before deployment.
- Mobile release signing is inherited debug signing; production signing/distribution is pending.
- Simulation remains illustrative and unvalidated; scientific decision use is prohibited.
- Software licensing and actual CODEOWNERS assignments need owner decisions.

## Backup and restore gate

Application and identity PostgreSQL need independent encrypted backups with WAL/PITR appropriate to the agreed RPO. Include object data, configuration, encryption/signing keys and access policy in the recovery inventory. Monitor backup completion and retention; do not treat an untested dump as recovery evidence.

Before cutover, restore both databases and objects into an isolated environment. Verify schema revisions, row counts/checksums, account `(issuer, subject)` mappings, media references and access controls, then measure achieved recovery time and data loss. Record evidence and owner sign-off against RTO/RPO. No restore has been rehearsed by this foundation.

Release/cutover also needs health and dependency checks, error/latency/resource monitoring, structured logs with request IDs and redaction, authorization sampling, data reconciliation and load testing. Retain a pre-cutover backup and compatible prior artifacts; rehearse rollback and migration reversibility before disabling direct legacy writes. The [roadmap](../migration/ROADMAP.md) owns the sequencing.
