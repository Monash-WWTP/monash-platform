# Successor foundation verification

Date: 2026-10-02. Code reviewed at `17c032581dc91256a40122b36af4f377c8f2039d`; final review fixes/evidence are recorded below. GitHub CI has not run yet because this verification precedes remote creation. These are local results, not a production readiness claim.

| Check | Result |
| --- | --- |
| Full pinned Git-tree/path/hash inventory | 207 files accounted for; every mapped target exists |
| Root policy/import/public-data tests plus API/simulation suite | 57 passed after the launcher fix (56 before it), 7 inherited warnings in the final run |
| PostgreSQL 16 migration upgrade and `alembic check` | Passed; no upgrade operations detected |
| OpenAPI export and tracked snapshot diff | No drift |
| Dashboard `npm ci`, lint, TypeScript/production build | Passed; large bundle warning remains |
| Dashboard npm audit | Zero advisories at verification time; CI rejects high/critical runtime findings |
| Production browser map smoke | Canvas and bundled worker initialized; unsafe attribution handlers removed; no browser errors |
| Flutter pub get / analyze / tests | Passed; analysis clean, 8 tests |
| Flutter Android debug build and nonempty APK check | Passed using synthetic values; release signing not assessed |
| Notebook reproduction | All code cells completed on 154 local samples, snapshot 1.1.0 |
| Repository whitespace / credential-path policy | Passed; narrow policy check, not an independent security audit |
| CodeGraph | Local index initialized and synced; generated index ignored |
| API onboarding smoke | Synthetic seed idempotent; health, plants, Swagger and all 11 schema paths served |

## Reproduce

Use [local verification commands](../operations/local-development.md), [dashboard](../../apps/dashboard/README.md), [mobile](../../apps/citizenflood/README.md), [research](../../research/README.md), and [toolchains/browser smoke](../operations/toolchains.md). Full source audit additionally uses:

```sh
python3 scripts/check_import_inventory.py --verify-targets \
  --source citizenflood=/home/jienweng/projects/citizenflood \
  --source dashboard=/home/jienweng/projects/wwtp-dashboard \
  --source api=/home/jienweng/projects/monash-platform-api
```

The origin audit needs those pinned checkouts. CI's recorded-manifest/target checks do not. The legacy CitizenFlood checkout still has exactly its pre-existing `analysis_options.yaml` and `pubspec.lock` edits; dashboard/API foundation checkouts are clean. Their deployment endpoints and histories were preserved.

## Limits

No required local foundation check was skipped. GitHub-hosted CI, real account journeys, production signing, iOS, load tests, restore rehearsal and production deployment have not been performed. Identity/client cutover is future work. The model remains illustrative and unvalidated. Inherited warnings concern Python datetime/Alembic configuration, Flutter plugin/SDK tooling, and dashboard bundle size; review these during the corresponding hardening work.

## Independent review

A fresh reviewer found no critical/important issues and one minor launcher-permission defect. It was regraded as an onboarding failure and fixed with a failing executable-permission test, then the full 57-test suite passed. The reviewer independently verified all 207 origins, policy checks, workspace imports/OpenAPI and 33 root/simulation tests; destructive database tests were not repeated by the reviewer.

The review accepted foundation integration. It did not assess live Supabase journeys, later identity/client migration, run hardening, scientific validity, production/signing/restore/load readiness, publication authority, hosted CI or iOS. Every scope ruling and its tradeoff is recorded in [implementation decisions](IMPLEMENTATION_DECISIONS.md). There are no deferred minor findings.
