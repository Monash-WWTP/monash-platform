# Implementation decisions and tradeoffs

- Ruling: The new repo has a minimal main commit and an ignored feature worktree — isolates implementation while preserving a clean local integration target — cost if wrong: local merge remains at finishing stage.

- Task 3: Ruling: the pinned dashboard fails six source lint rules; eight minimal adaptations restore lint/build without changing API paths, recorded in IMPORT_ADAPTATIONS.md — cost if wrong: hot-reload or chart presentation may differ and needs browser QA before release.

- Task 3: Ruling: inherited npm audit reports a critical MapLibre XSS advisory (GHSA-jrc7-96c5-q579); this import remains undeployed and the dependency is a deployment blocker for follow-up remediation — cost if wrong: unsafe map content could execute script if a client release proceeds without the upgrade.

- Task 4: Ruling: reduce inherited Gradle heap/metaspace to 2 GB/1 GB and workers to two after kernel-confirmed OOM killed the first build; require a nonempty APK artifact — cost if wrong: slower Android builds on larger hosts.

- Task 5: Ruling: hold three raw yearly CSVs outside the explicit public-data license as restricted; preserve hashes and controlled legacy retrieval — cost if wrong: extra rights review before raw ETL can be reproduced.

- Task 5: Ruling: preserve the effluent-to-GHG helper and unrestricted live public export helper as inactive legacy references; adapt the notebook to the local pinned snapshot — avoids unsupported scientific outputs and uncontrolled snapshot refresh — cost if wrong: live ETL needs a separate reviewed implementation.

- Task 5: Ruling: remediate inherited dashboard dependencies in the successor rather than leave the critical deployment gate open; audit RED→GREEN, remove unused deck.gl umbrella, upgrade MapLibre to 6.11.2 with namespace import, compatible lock updates — cost if wrong: major MapLibre change requires browser release QA.

- Task 5: Ruling: source-checkout parity test skips only when pinned local checkouts are absent in CI; always-running manifest classifier and target checks still run — cost if wrong: CI cannot independently reconstruct origin Git trees without fetching the legacy repos.

- Task 6: Ruling: retain approved design/plan artifacts in the successor after spotting that pinned application commits predate them; record their separate origin — cost if wrong: historical proposed-status text needs the roadmap pointer to avoid confusion.

- Final: Ruling: Live Supabase/account/media/privacy journeys remain release QA gates — foundation preserves legacy behavior and makes no live cutover claim — cost if wrong: latent legacy integration/privacy defects remain untested.

- Final: Ruling: Authentik/generated clients/reporting-monitoring/client cutover remain later packages — the approved plan explicitly establishes source foundation first — cost if wrong: both clients continue relying on Supabase until migration.

- Final: Ruling: Immutable run records/replay/failure hardening remain later scope — foundation retains extracted run behavior without claiming scientific reproducibility — cost if wrong: existing run records are insufficient for research replay.

- Final: Ruling: Scientific validity remains unapproved — model is explicitly illustrative and decision use prohibited — cost if wrong: using outputs operationally would exceed available evidence.

- Final: Ruling: Server/signing/backups/restores/load capacity remain open release gates — no production configuration or release has been claimed — cost if wrong: standalone production is not ready.

- Final: Ruling: Publication authority remains an owner decision — restricted blobs are excluded and software rights are not inferred from dataset licensing — cost if wrong: public release may require additional rights review.

- Final: Ruling: Hosted CI awaits remote creation — committed workflows and equivalent local commands passed — cost if wrong: host-specific CI/toolchain failures may still occur.

- Final: Ruling: iOS is excluded from build readiness — the pinned source has no iOS scaffolding and this plan requires Android debug verification — cost if wrong: an iOS release needs platform setup and separate verification.

No deferred minor findings. The single launcher issue was corrected before handoff.
