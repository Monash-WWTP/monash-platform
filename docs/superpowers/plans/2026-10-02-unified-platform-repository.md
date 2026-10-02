# Unified Platform Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a locally buildable successor monorepo containing the CitizenFlood app, WWTP dashboard, shared FastAPI API, simulation package, and the reviewed supporting research and documentation, while preserving both legacy repositories and their deployments.

**Architecture:** Initialize `/home/jienweng/projects/monash-platform` as a new local Git repository with an isolated implementation branch. Import pinned committed snapshots of both apps and the completed local API foundation; relocate the API and simulation packages into their target paths without changing behavior. Give every product its own build command and CI job, with a source-origin manifest and a root onboarding guide. This plan establishes the monorepo, not the later authentik, data migration, client API switch, or production cutover.

**Tech Stack:** Flutter/Dart, React/Vite/TypeScript, FastAPI/Python 3.12, uv, PostgreSQL 16, Alembic, pytest, npm, GitHub Actions, CodeGraph.

**Spec:** `/home/jienweng/projects/wwtp-dashboard/docs/superpowers/specs/2026-10-02-unified-platform-repository-design.md`

## Global Constraints

- Source revisions are `citizenflood` `5a80700`, `wwtp-dashboard` `202b72e`, and local `monash-platform-api` `d518a95`. Check these refs before importing; do not substitute later commits silently.
- Preserve the two legacy repositories and deployments. Do not alter their working trees or production Supabase migration chain. Preserve uncommitted `citizenflood/analysis_options.yaml` and `citizenflood/pubspec.lock` in the old checkout.
- Import both client applications as actual source, without nested `.git` directories or submodules. Keep their current Supabase integration during this repository-foundation work package.
- The shared API is a separate deployable under `/api/v1` and owns PostgreSQL application migrations. Its current operator adapter remains temporary and fail closed.
- Keep simulation `effluent_v1` at version `1.4.0`, with `illustrative_unvalidated` and `decision_use_permitted=false`. Citizen observations remain separate from laboratory samples and are never implicit model input.
- The new repository stays local until its source inventory, permissions, build/test checks, and contract snapshot have been reviewed. No public visibility or production cutover is part of this plan.
- Use CodeGraph before text searching or reading code in the indexed source repos. Initialize CodeGraph in the new repo after the imports; do not commit its index.

## Review Focus

1. A copied client accidentally points at the new API or production data during import: tests and config checks must show legacy endpoints and credentials remain unchanged.
2. Relocating `wwtp_sim` or `app` breaks package imports while old tests still pass from the source directory: run the complete API suite from the monorepo root and verify the installed workspace paths.
3. A file is omitted or a generated/restricted file is copied without explanation: compare a machine-readable source inventory with both pinned Git trees and require a disposition for every tracked file.
4. Client configuration or spreadsheet content leaks into a public repository: classify data and secret-like files before any remote is created; keep the local repo private by default.
5. Path-filtered CI skips a required check and leaves a pull request pending: keep required product/contract checks always running, with jobs deciding whether work is needed rather than suppressing workflow events.

---

## File map

All target paths are relative to the new repository.

| Path | Responsibility |
| --- | --- |
| `apps/citizenflood/**` | Pinned Flutter source, lockfile, assets, platform code, and tests |
| `apps/dashboard/**` | Pinned React frontend, lockfile, source, and build config |
| `services/api/**` | Relocated FastAPI app, Alembic chain, tests, OpenAPI snapshot |
| `packages/simulation/**` | Relocated `wwtp_sim` source and golden tests |
| `pyproject.toml`, `uv.lock` | Root uv workspace linking `services/api` and `packages/simulation` |
| `infra/local/compose.test.yaml` | Disposable PostgreSQL test service, with documented root command |
| `research/notebooks/**`, `research/data-preparation/**`, `data/public/**` | Reviewed and attributable scientific material from dashboard source |
| `legacy/**` | Clearly inactive Supabase migration and compatibility references, where retained |
| `docs/migration/SOURCE_ORIGINS.md`, `docs/migration/source-inventory.json` | Source SHAs and one disposition for every tracked source file |
| `scripts/check_import_inventory.py` | Validate disposition coverage and initial copied-file checksums |
| `docs/architecture/**`, `docs/api/**`, `docs/science/**`, `docs/operations/**` | Ownership, contracts, scientific limits, and operational guidance |
| `.github/workflows/api.yml`, `dashboard.yml`, `citizenflood.yml`, `inventory.yml` | Independent product gates and always-running source/contract check |
| `README.md`, `CONTRIBUTING.md`, `CODEOWNERS` | First-day setup, review routing, contribution rules |

### Task 1: Create the successor repo and exhaustive source inventory

**Files:** Create `.gitignore`, `docs/migration/SOURCE_ORIGINS.md`, `docs/migration/source-inventory.json`, `scripts/check_import_inventory.py`, `tests/test_import_inventory.py`, `README.md`.

**Interfaces:** Produces `source-inventory.json` entries with `source_repo`, `source_commit`, `source_path`, `disposition` (`imported`, `superseded`, `legacy_reference`, `generated`, `restricted`, `omitted`), `target_path` or `reason`, and `source_sha256`. Task 5 consumes these entries.

- [ ] **Step 1: Initialize a new local repository and isolated branch.** Create `/home/jienweng/projects/monash-platform`, initial `main` commit with `.gitignore`, and an ignored feature worktree. Do not configure a GitHub remote. Ignore `.worktrees/`, `.venv/`, `node_modules/`, build outputs, local secrets, `.codegraph/`, and agent scratch. Record this new-repo isolation ruling if the worktree skill requires it.
- [ ] **Step 2: Write the failing inventory test.** `tests/test_import_inventory.py::test_every_pinned_source_file_has_one_disposition` loads `source-inventory.json`, checks no duplicate `(source_repo, source_path)`, checks exact allowed dispositions, and checks every imported item has a target and SHA-256. The executable checker accepts `--source citizenflood=PATH --source dashboard=PATH --source api=PATH` and compares each manifest source SHA with `git show <pinned-commit>:<source_path>`; it exits nonzero on missing or extra tracked paths. Expected before implementation: manifest/checker absent or incomplete. Copied-file parity is tested in Tasks 2-4 as each product arrives.
- [ ] **Step 3: Implement the inventory generator/checker and manifest.** Enumerate `git ls-tree -r --name-only` for each pinned ref. Record one disposition per tracked file. Import mappings for Flutter, React, API, simulation, docs, research, data, Supabase histories, and legacy scripts are explicit; generated output and restricted material get reasons. `source_sha256` is computed from Git blob bytes, not the possibly dirty working tree. Do not copy the citizen local edits. Mark the dashboard's old backend/simulation as `superseded` by the API foundation and link its origin commit.
- [ ] **Step 4: Verify and commit.** Run the checker against all three source repositories, inspect `git status` in those repositories, run `python3 -m pytest -q tests/test_import_inventory.py` if Python pytest is available through the eventual root uv workspace, and commit `chore: record successor source inventory`. If Task 1 lacks the uv workspace, use `uv run --with pytest python -m pytest ...` and lock the test dependency in Task 2. Expected: every tracked file has exactly one disposition and source repos remain unchanged.

### Task 2: Relocate the shared API and simulation package

**Files:** Create `services/api/**`, `packages/simulation/**`, `pyproject.toml`, `uv.lock`, `infra/local/compose.test.yaml`; move `backend/openapi.json` and `scripts/export_openapi.py` from the local API foundation; update path-dependent test/config files.

**Interfaces:** Consumes Task 1 source manifest. Produces root `uv run --locked python -m pytest -q services/api/tests packages/simulation/wwtp_sim/tests` and `uv run --locked alembic -c services/api/alembic.ini upgrade head`; keeps `from app.main import app` and `from wwtp_sim import get_model` working.

- [ ] **Step 1: Add a failing relocation smoke test.** `services/api/tests/test_workspace_paths.py` asserts the installed `app` module resolves under `services/api/app`, `wwtp_sim` under `packages/simulation/wwtp_sim`, and `GET /api/v1/health` returns 200 without DDL or a Supabase request. Run it before the package paths are configured; expected import/path failure.
- [ ] **Step 2: Copy pinned foundation source and rewrite only workspace paths.** Import branch `d518a95` from `/home/jienweng/projects/monash-platform-api` into the target folders without caches, its `.git`, or `.codegraph`. Root `pyproject.toml` retains project name `monash-platform-workspace`, dependencies `wwtp-backend` and `wwtp-sim`, and dev dependencies `pytest`/`httpx`; workspace members become `services/api` and `packages/simulation`. Adjust the simulation path in `services/api/pyproject.toml`, Alembic `script_location`, snapshot/export path, and compose location. Keep API behavior and migration revision `0001_initial` unchanged.
- [ ] **Step 3: Verify against fresh PostgreSQL and commit.** Run `uv lock && uv sync --locked`; start PostgreSQL 16 via `docker compose -f infra/local/compose.test.yaml up -d --wait db`; set both database URLs to `postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test` and `APP_ENV=test`; run migration, `alembic check`, the full API/simulation suite, OpenAPI export and diff. Expected: at least the 39 foundation tests plus relocation test pass, no schema drift, no OpenAPI diff. Commit `feat: relocate shared API foundation`.

### Task 3: Import the WWTP dashboard client without switching its data path

**Files:** Create `apps/dashboard/**` from source `frontend/**`; create `.github/workflows/dashboard.yml`; update root README and inventory mappings.

**Interfaces:** Consumes the inventory from Task 1 and produces `npm ci && npm run lint && npm run build` in `apps/dashboard`. Retains the current `/api/*` and Supabase paths in the copied client until its own migration work package.

- [ ] **Step 1: Write a failing client-baseline check.** A script or test validates that `apps/dashboard/package-lock.json` matches the pinned source hash and that `src/api/client.ts` still targets legacy `/api/plants` during import. Assert `src/api/monitoring.ts` still uses the current Supabase read path. Run before copy; expected missing app files.
- [ ] **Step 2: Copy `frontend/**` exactly from dashboard commit `202b72e`.** Use `git archive` or Git blobs, not the working tree. Preserve lockfile and Vite config. Do not add a new proxy to `/api/v1` in this task. No backend code from the old dashboard is copied into `apps/dashboard`.
- [ ] **Step 3: Install and verify.** In `apps/dashboard`, run `npm ci`, `npm run lint`, and `npm run build`; record any pinned-source baseline failure separately before changing code. Add an always-running dashboard workflow that executes these commands and reports success on unrelated changes without skipping the required job. Re-run the inventory/checksum check and commit `feat: import WWTP dashboard client`.

### Task 4: Import CitizenFlood without losing legacy work

**Files:** Create `apps/citizenflood/**` from source commit `5a80700`; create `.github/workflows/citizenflood.yml`; update root README and inventory mappings.

**Interfaces:** Consumes the Task 1 manifest and produces `flutter pub get`, `flutter analyze`, `flutter test`, and a debug Android build under `apps/citizenflood`. The copied app retains its legacy Supabase configuration and no production signing credentials are used.

- [ ] **Step 1: Write a failing Flutter import check.** Validate that `apps/citizenflood/pubspec.yaml`, `lib/main.dart`, `lib/services/report_repository.dart`, test files, Android source, and assets exist at source blob hashes. Check the copied `pubspec.lock` is the committed blob from `5a80700`, not the dirty legacy worktree version. Run before copy; expected missing files.
- [ ] **Step 2: Copy the pinned Flutter application.** Import tracked app/config/platform/test/docs files from `5a80700` to `apps/citizenflood`; exclude only files explicitly marked restricted, generated, or legacy-reference in the manifest. Re-run the baseline check and inspect `citizenflood` status to confirm the two pre-existing edits remain untouched.
- [ ] **Step 3: Verify with Flutter SDK and commit.** Install Flutter `3.44.7` in an isolated local toolchain directory (its bundled Dart meets the source constraint `^3.12.1`); record `flutter --version` output in `docs/operations/toolchains.md`. Run `flutter pub get`, `flutter analyze`, `flutter test`, and `flutter build apk --debug` using synthetic `--dart-define` values. Flutter is absent on the current host, so obtain the official stable SDK and required Android toolchain before claiming this task complete; do not report an unrun mobile build as passing. Add an always-running mobile workflow pinned to Flutter `3.44.7`, then commit `feat: import CitizenFlood client`.

### Task 5: Import reviewed research and finish documentation/CI

**Files:** Create `research/**`, `data/public/**`, `legacy/**`, `docs/architecture/**`, `docs/api/**`, `docs/science/**`, `docs/operations/**`, `docs/migration/**`, `.github/workflows/api.yml`, `inventory.yml`, `CONTRIBUTING.md`, `CODEOWNERS`; update `README.md` and source inventory.

**Interfaces:** Consumes the imported products and manifest; produces documented first-day commands and independent always-running CI checks. The old Supabase migration files are inactive references only.

- [ ] **Step 1: Test the inventory and documentation commands.** Add a test that rejects unclassified source files, duplicate active migration chains, committed `env.json`/database/cache files, and a missing root link to each product's setup, API docs, scientific limits, and operations. Run it red before importing docs/research.
- [ ] **Step 2: Import supporting material according to the manifest.** Place reviewed notebooks, data-preparation code, public-data snapshots with license/manifest, and legacy Supabase histories in their assigned paths. If a spreadsheet or dataset cannot be cleared for this repository, mark it `restricted` and provide its origin/hash and controlled retrieval instructions; do not commit it merely to satisfy completeness. Update relative documentation links and label old deployment instructions as legacy.
- [ ] **Step 3: Write concise operational docs.** Root README gives exact commands for all three products; `SOURCE_ORIGINS.md` records source URLs/SHAs, transformations, omissions, and local-edit preservation; architecture explains deployment boundaries; API docs link `/docs` and `/openapi.json`; science states model limitations and input classes; operations records the disposable database, deployment prerequisites, backups and restore gate. `CONTRIBUTING.md` explains tests, contract review, and release independence. `CODEOWNERS` uses actual approved teams/users only; until identified, omit enforced ownership patterns and explain the pending assignment.
- [ ] **Step 4: Add and verify CI.** API workflow runs PostgreSQL migration, `alembic check`, API/simulation tests, and OpenAPI drift. Inventory workflow always runs the manifest classifier and secret-like/path policy checks. All required workflows trigger on every pull request, avoiding path-filter pending checks; jobs may cheaply short-circuit only with a successful status. Run the root onboarding commands, `git diff --check`, and every locally available product test. Commit `docs: complete unified platform repository foundation`.

### Task 6: Review the local successor and prepare the GitHub handoff

**Files:** Modify `docs/migration/SOURCE_ORIGINS.md` and `README.md` only if verification finds gaps.

**Interfaces:** Consumes Tasks 1-5; produces a clean local branch, final source-origin report, and a reviewable request to create the private `Monash-WWTP/monash-platform` remote. No production deployment or legacy archival occurs.

- [ ] **Step 1: Run a fresh whole-repository review.** Compare source inventories, verify no credentials or restricted data, re-run API tests and migration drift, dashboard lint/build, mobile analyze/test/debug build, and contract snapshot. Record exact commands, counts, skipped checks, toolchain versions, and source SHAs. Check legacy repo statuses are unchanged.
- [ ] **Step 2: Fix material review findings with failing tests first.** Use the execution skill's final reviewer and fix pass. A failed or unavailable required verification is an explicit blocker to claiming the successor foundation complete; do not silently downgrade it.
- [ ] **Step 3: Present the concrete GitHub creation result for approval.** Report local branch path, commit ID, visibility `private`, intended remote name, permissions/ownership assumptions, and CI status. Create and push the GitHub repository only after the local result is reviewable and the user has approved that external write. The local successor remains useful if GitHub creation is deferred.

## Later work packages

This plan imports both applications and establishes the successor source of truth for new development. It does not implement the authentik identity foundation, reporting/monitoring API endpoints, client cutover, or standalone production deployment; the approved architecture assigns those to separate plans with their own tests and review gates. Until cutover, the legacy deployments and their active Supabase migration history remain authoritative for production data.
