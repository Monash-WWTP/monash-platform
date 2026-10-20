# Audit remediation execution ledger

User authorization: resolve all readiness-checklist items now. Root-cause evidence and required corrections are in the 2026-10-20 audit. Existing fixes proceed inline/test-first; new admin subsystem has a separately reviewable design.

- [x] R2/R3/R9 Android identity-bound state, async authentication fencing and consistent submission/retry state.
- [x] R4/R5 backend finite physical inputs and canonical threshold units/provenance.
- [x] R6/R7/R8 shared trusted issuer enforcement, required production revocation and nonblocking uploads.
- [ ] R10 current Android release instructions and a qualified build path.
- [x] Admin specification review, implementation plan review, implementation and permission/provenance tests.
- [ ] Production prerequisites and deployment artifacts; integrated local acceptance and restore/load evidence where authorized.
- [ ] Regression suites, OpenAPI/schema checks, independent review, PR and authorized squash merge.
- [ ] Production deployment and APK publication after actual target/environment acceptance.
- [ ] Independent scientific calibration/validation: external data/reviewer gate; never infer from software tests.

Boundaries: existing worktree reused on fix/audit-remediation from origin/main fd96a4d; unrelated main-checkout audit/plan files preserved. No invented production hostname, hidden synthetic fallback or model validation claim.

## Verified source evidence (2026-10-20)

- Combined API/model/repository suite: 203 passed, 1 skipped before final review; final review added three regression tests (see final verification below).
- Dashboard: 44 tests, lint and production build passed. Browser checked current API-backed admin users, plant/station creation, history and status at desktop and 390px widths; no horizontal overflow. Fixtures were local/disposable only.
- Android: 27 tests and analyzer passed; debug APK compiled using staging example. This is not a qualified production release.
- Independent final review found three Important issues, all reproduced RED then fixed GREEN: actual scenario POST/PUT omission inheritance, rejecting unsupported single pH thresholds, recording effective fallback screening limits/units/provenance. Admin suite: 20 passed.
- Ruling: reject new single pH admin thresholds rather than invent range semantics; existing model pH behavior is unchanged. Cost if wrong: pH configuration requires a later scientifically reviewed contract.
- Ruling: retain model fallback screening and expose it in immutable snapshots rather than treating removal as disabling screening. Cost if wrong: users must explicitly inspect effective run limits; documentation explains this behavior.
- Server provisioning deferred explicitly by owner. Production templates are structurally tested; no deployment, restore/load drill, public APK replacement or scientific acceptance is claimed.

Final verification: combined API/simulation/repository suites **206 passed, 1 skipped**; dashboard **44 passed**, lint/build passed. Repository policy and 207-file pinned import inventory passed. Final review had no Critical findings and its three Important findings are fixed; no deferred minor findings. Existing map/chart bundle-size advisories remain. Production and scientific acceptance remain pending as above.
