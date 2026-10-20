# Audit remediation execution ledger

User authorization: resolve all readiness-checklist items now. Root-cause evidence and required corrections are in the 2026-10-20 audit. Existing fixes proceed inline/test-first; new admin subsystem has a separately reviewable design.

- [ ] R2/R3/R9 Android identity-bound state, async authentication fencing and consistent submission/retry state.
- [ ] R4/R5 backend finite physical inputs and canonical threshold units/provenance.
- [ ] R6/R7/R8 shared trusted issuer enforcement, required production revocation and nonblocking uploads.
- [ ] R10 current Android release instructions and a qualified build path.
- [ ] Admin specification review, implementation plan review, implementation and permission/provenance tests.
- [ ] Production prerequisites and deployment artifacts; integrated local acceptance and restore/load evidence where authorized.
- [ ] Regression suites, OpenAPI/schema checks, independent review, PR and authorized squash merge.
- [ ] Production deployment and APK publication after actual target/environment acceptance.
- [ ] Independent scientific calibration/validation: external data/reviewer gate; never infer from software tests.

Boundaries: existing worktree reused on fix/audit-remediation from origin/main fd96a4d; unrelated main-checkout audit/plan files preserved. No invented production hostname, hidden synthetic fallback or model validation claim.
