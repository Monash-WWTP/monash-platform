# Unified successor repository for CitizenFlood and WWTP

Date: 2026-10-02

Status: proposed architecture for review

Scope: repository ownership, source import, shared runtime boundaries, documentation, and staged migration. No production cutover or public release is authorized by this document.

## 1. Purpose and acceptance criteria

Create one new successor repository, provisionally `Monash-WWTP/monash-platform`, containing the CitizenFlood Flutter application, the WWTP React dashboard, the shared FastAPI backend, the versioned simulation package, and the research and operational material needed to reproduce and maintain them. The existing `citizenflood` and `wwtp-dashboard` repositories remain intact as the deployed legacy systems until a rehearsed cutover. The successor repository is the place for new platform development once its imports pass parity checks.

The repository is a monorepo for code ownership and coordinated contract changes. Its products remain separate build and deployment units: mobile releases, dashboard releases, and API releases can occur independently. A single database is owned by the API; neither client accesses its tables directly. The exact runtime and data safeguards are those in the approved [shared-platform architecture](./2026-10-02-shared-platform-architecture-design.md), except that its separately deployable backend now lives in the successor repository.

Acceptance for the repository foundation is observable:

1. All application source needed to build both current clients and the API has a documented origin commit and destination path. No nested Git repositories or submodules obscure the source of truth.
2. The copied clients still build and run against their current integrations in development; no production endpoint is switched by the import. The API retains its PostgreSQL migration and 39-test foundation baseline.
3. The three products have independent build and test commands. A shared OpenAPI check detects client/server contract drift once clients are migrated.
4. Documentation distinguishes current behavior, target behavior, scientific assumptions, operational procedures, and migration status. A new engineer can identify the owner of each data table, external service, and release artifact.
5. The two legacy repositories and their deployed releases are not deleted, rewritten, or archived before cutover. Pre-existing uncommitted changes in `citizenflood/analysis_options.yaml` and `citizenflood/pubspec.lock` remain untouched in the legacy checkout.

## 2. Alternatives and decision

| Layout | Benefit | Cost | Decision |
| --- | --- | --- | --- |
| Keep the two client repos and add a third API repo | Smallest source move | Cross-repo contract changes and release checks remain distributed | Superseded by the requested successor repository |
| One successor monorepo with three independently released products | One review surface for API/client changes, shared docs and CI, clear provenance | CI and package boundaries must be explicit | Selected |
| One combined application or deployable | Fewer build definitions | Couples mobile, web, and API releases despite different lifecycles | Rejected |

GitHub supports workflows scoped to changed paths, but required checks must be designed so a skipped path-filtered workflow does not leave a pull request permanently pending. The monorepo will use product workflows plus an always-running contract/manifest gate. `CODEOWNERS` will route API, mobile, dashboard, and scientific-model changes to their responsible reviewers when those teams are defined.

## 3. Repository map and ownership

```text
monash-platform/
  apps/
    citizenflood/           Flutter mobile app and mobile tests
    dashboard/              React/Vite operator dashboard and web tests
  services/
    api/                    FastAPI app, Alembic chain, API tests, OpenAPI snapshot
  packages/
    simulation/             wwtp_sim model package, golden cases and validation status
  research/
    notebooks/              reviewed notebooks and reproducible analysis entry points
    data-preparation/       source parsers and documented transformations
  data/
    public/                 publishable snapshots with license and source manifest
  infra/
    local/                  disposable development services
    deployment/             standalone-server configuration, once reviewed
  docs/
    architecture/           runtime and domain boundaries, ADRs
    api/                    endpoint, unit, auth and error conventions
    science/                methods, assumptions, uncertainty and validation evidence
    migration/              origin map, reconciliation, cutover and rollback records
    operations/             runbooks, backups, restores, monitoring and incident steps
  .github/workflows/        product CI and shared checks
  README.md                 first-day setup and product navigation
```

The root Python `uv` workspace includes `services/api` and `packages/simulation`; it produces one lockfile for their integration. Flutter and the dashboard retain their own package manifests and lockfiles. Product workflows use only their required toolchains. A change to a shared API schema triggers API and client contract checks; a model change triggers engine tests, API tests, and scientific review. A change to one UI does not force a release of the other UI.

The backend remains a modular monolith with explicit reporting, moderation, monitoring, scenario, and account boundaries. It owns validation, authorization, persistence, OpenAPI, and application migrations. The Flutter app and React dashboard own presentation and local interaction only. Authentik and private S3-compatible object storage are separate backing services, even if an initial standalone host runs their containers beside the API.

## 4. Source import and provenance

The successor repository starts from a new Git history. It imports clean source snapshots, records source repository URLs, exact commit SHAs, original paths, destination paths, import date, and any transformations in `docs/migration/SOURCE_ORIGINS.md`. The legacy repositories preserve their full historical commit, issue, and release record; their history is not rewritten to manufacture a combined chronology. Import commits are split by source and product so later diffs show where code came from. A file/hash inventory checks that the import is complete before adaptation begins.

Initial pinned inputs are:

| Source | Revision | Import intent |
| --- | --- | --- |
| `Monash-WWTP/citizenflood` | `5a80700` | Flutter app, tests, assets, platform files, and relevant documentation from committed source. Preserve local uncommitted changes only in the old checkout. |
| `Monash-WWTP/wwtp-dashboard` | `202b72e` | React app; research notebooks, data preparation, public data and source documentation after rights/privacy inventory. Existing FastAPI and simulation folders are recorded as the origin of the extracted foundation. |
| Local `monash-platform-api` feature branch | `d518a95` | Shared API, simulation, Alembic, tests, OpenAPI snapshot, and CI foundation. This is the working successor to the dashboard's backend copy. |

The current Supabase migrations stay authoritative for the legacy deployments until cutover. A historical copy may be placed under a clearly named `legacy/` archive for reference, but it is never wired into the new application's Alembic command. The successor API has one active application migration chain. Importing public datasets or notebooks requires checking their license, attribution, personal-data content, and reproducibility; generated or restricted datasets are linked in manifests or external storage rather than committed blindly. Secrets, service-role credentials, local databases, caches, and generated build output are excluded.

No application code is silently discarded. Each source file or directory is classified in the import inventory as imported, superseded by the extracted foundation, legacy reference, generated, restricted data, or intentionally omitted with reason. Where both sources contain a file with the same purpose, the inventory names the authoritative version and its parity test.

## 5. Runtime contract, identity, and data separation

Both clients eventually use the single `/api/v1` contract. The dashboard initially keeps its legacy Supabase reads during source import, then migrates monitoring, approved community observations, scenarios, and runs endpoint by endpoint. CitizenFlood initially keeps its legacy Supabase flows in the copied app, then migrates registration, report submission, owner history, media, and moderation visibility through API-backed repositories. Contract changes must update the tracked OpenAPI schema and generated TypeScript/Dart clients in the same reviewed change after generation is introduced. Client builds must reject stale generated contracts.

The target identity flow remains authentik OIDC: verified citizen accounts, invited operators with MFA, Flutter external-browser authorization-code with PKCE, and a dashboard backend-held session with secure cookie. Application roles and the unique `(issuer, subject)` link live in the API database. Institutional SSO, if approved, is brokered through authentik without changing API account IDs. The temporary Supabase operator adapter in the foundation is removed only after the new operator path passes authorization and recovery tests. Missing or invalid identity fails closed.

The API database keeps citizen observations, laboratory measurements, source factors, assumptions, and model outputs in distinct records. Approved community projections omit reporter identity, private notes, exact coordinates, and private photo paths. Citizen observations are never implicitly fed into simulation. Each simulation run must eventually carry the immutable inputs, source revisions, model artifact identity, results, and validation status specified in the shared-platform architecture. Until scientific validation is completed, the model stays `illustrative_unvalidated` with `decision_use_permitted=false`.

## 6. Delivery, verification, and standalone deployment

Repository setup first proves source parity and product builds, then delivers the remaining work packages in this order:

1. **Successor repository foundation:** source inventory, snapshot imports, package paths, readmes, local development commands, separate CI jobs, API relocation, CodeGraph index, and parity checks. The imported clients retain their old integrations. No GitHub repository is made public before rights/privacy review.
2. **Identity foundation:** authentik staging instance and separate identity PostgreSQL database, verified registration, operator MFA, account mapping, capability checks, and legacy identity claim procedure. Old anonymous reports are not reassigned by email alone.
3. **Monitoring read migration:** reviewed data import into API-owned tables, stations/laboratory samples/community projections, API pagination/filtering, dashboard client migration, privacy reconciliation.
4. **Reporting and run hardening:** CitizenFlood API-backed report and media flows, moderation workflow, immutable simulation records and failure states, generated clients, and compatibility tests.
5. **Standalone deployment and cutover:** TLS reverse proxy, independent API/web deployment, mobile release, PostgreSQL/authentik/object-store backups and restore rehearsal, metrics/logging, load test, data reconciliation, access sampling, rollback snapshot, and controlled disabling of direct Supabase writes.

CI gates include Flutter analyze/test/build, dashboard typecheck/test/build, API and simulation tests against PostgreSQL 16, Alembic drift and revision-generation checks, OpenAPI snapshot drift, generated-client compatibility, secret scanning, and import-manifest validation. Tests use synthetic data only. Scientific and data changes receive source/units/method checks and independent review; passing software tests does not promote the heuristic to a validated operational model.

The initial deployment topology is one reverse proxy in front of the dashboard and `/api/v1`, an independently scalable API process, application PostgreSQL, separate authentik PostgreSQL, and private object storage. Credentials, database roles, backups, and restore procedures are independent even if the first installation shares a physical server. Exact storage product and host sizing are chosen from measured photo volume, request rate, and restore-time requirements.

## 7. Documentation contract

The root README states what each product does, what is running today, the source/import revisions, prerequisites, exact local commands, and where to find API docs and runbooks. Every domain module has a short owner and interface note. `docs/architecture` records why the monorepo has independent deployables; `docs/api` defines units, pagination, errors, auth, and versioning; `docs/science` contains equations, input provenance, assumptions, uncertainty, and validation status; `docs/migration` records source manifests, counts, hashes, access decisions, and rollback checkpoints; `docs/operations` contains deployment, backup/restore, observability, and incident procedures. Documentation examples use synthetic data and are exercised where commands are operationally significant.

The source import is not the production cutover. The old repositories continue to serve existing deployments while the successor products are developed and verified. After cutover and its acceptance window, the old repositories may be labelled legacy and archived read-only; archiving is a separate owner decision.

## 8. Explicit boundaries and open decisions

This design does not merge the two user interfaces, make their release cycles synchronous, authorize publication of research data, or imply that the current simulation is scientifically validated. It does not choose a physical server size or object-store brand without measurements. The provisional repository name and initial private visibility can be adjusted before creating the GitHub remote without changing the architecture.

## References

- [GitHub Actions path filters](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow) — independent monorepo workflows and the pending-check caveat.
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) — path ownership and review routing.
- [GitHub repository archiving](https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories) — read-only legacy record after cutover.
- [OpenAPI Specification](https://spec.openapis.org/oas/) — shared language-neutral API contract.
- [OAuth 2.0 Security Best Current Practice, RFC 9700](https://www.rfc-editor.org/info/rfc9700/) — authorization-code and PKCE baseline.
- [W3C PROV-O](https://www.w3.org/TR/prov-o/) — model and data provenance vocabulary.
