# Shared account settings implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, task by task.

**Status:** Approved implementation and local acceptance completed; final local evidence and remaining release gates are recorded in `docs/operations/shared-account-settings.md`.

**Goal:** Add working registered-user Profile, Email & password and Security entries backed by the same identity used across mobile and dashboard.

**Architecture:** Reuse pinned authentik self-service and provider-native account handling, adding controlled verified-email/security flows and signed application revocation events. Add trusted settings-link discovery and a signed-claim display-name projection; no client credential editor or second identity store.

**Tech Stack:** Pinned authentik2026.8.3/Django flows, FastAPI/SQLAlchemy/Alembic, Flutter/system browser, React/TypeScript.

**Spec:** docs/superpowers/specs/2026-10-21-shared-account-settings.md (approved).

## Global constraints

- Preserve issuer/subject UUID, report ownership and server-granted capabilities; never merge or claim ownership by email.
- Profile display name is optional, trimmed, at most120 characters and not verified legal identity.
- Passwords, MFA seeds, recovery codes and identity-management credentials never enter platform APIs, client storage, Git or logs.
- Candidate email must be verified before replacing the authoritative old email; expire/cancel/replay/concurrent attempts safely.
- Security changes require recent authentication and revoke old provider/application proofs before success is displayed.
- Trusted configured HTTPS settings URLs only, with explicit loopback staging exception. Browser return is navigation, not proof of completion.
- Native MFA/session scope must be truthful; unified per-device API/mobile session correlation is deferred.
- No production provisioning, public signed APK release, account deletion or map-clustering changes.

## Review focus

- A second pending email change or old verification link must not overwrite the latest confirmed address.
- An unavailable revocation receiver must not leave a security change reported complete with usable old application proofs.
- Returning from settings after logout/account switch must not restore another account's name, email, draft or token.
- Provider default settings, direct URLs and native APIs must not bypass verified-email/recent-auth boundaries.
- A profile change must not accidentally grant permissions, replace identity keys or imply an authenticated browser closing means success.

## Task1 — Provider flow guardrails and shared revocation helper

Files: `infra/staging/identity/bootstrap.py`; create `infra/staging/identity/account_settings.py`; extend branded templates under `infra/staging/identity/templates/email/`; provider integration tests under `infra/staging/identity/tests/` and repository checks as needed.

Interfaces: helper functions `prepare_email_change(request) -> bool`, `complete_email_change(request) -> bool`, `change_password(request) -> bool`, `sign_out_all(request) -> bool`. Import helpers from the mounted `/monash-brand` directory in provider expression policies. Secrets use existing server environment only. Supported provider EmailStage reads `PLAN_CONTEXT_EMAIL_OVERRIDE`; use that mechanism to send to the candidate without first rewriting User.email. Its FlowToken stores the server-side flow context and enforces restored-token user matching.

- [x] Add provider tests proving default-user-settings currently permits disallowed identity edits, candidate verification cannot be substituted for another user, and old/concurrent verification attempts fail. Execute against an isolated synthetic identity in the pinned local image, not a human account.
- [x] Provision branded Profile flow `monash-account-profile` with only a display-name prompt, and replace/bind the default user-settings flow to the safe equivalent. Validate exact writable fields and120-character limit; block email, username, roles and privileged attributes through this profile path.
- [x] Provision `monash-account-email` with recent provider reauthentication, candidate prompt, pending-attempt preparation, EmailStage, completion helper and completion screen. Pending attempt is bound to user UUID/candidate/nonce/expiry; store latest-attempt marker under controlled provider attributes, with a user row lock. Verification expires30minutes; preparing another attempt invalidates the previous marker. Cancellation/expiry leaves old email authoritative. Reject conflicts without merging accounts.
- [x] Completion helper validates latest attempt after successful EmailStage, locks the provider user, updates email and `monash_verified_email` consistently, revokes provider access/refresh tokens and sessions, and delivers a signed application revocation event before transaction success. Use stable event UUID per attempt for safe delivery retry. On receiver failure, rollback provider changes and do not show success; an application revocation already committed on an uncertain response is safe to retry. Notify the previous address after successful email change; notification failure is surfaced/logged without secrets and does not silently revert verified ownership.
- [x] Provision `monash-account-password` with fresh/current authentication and password prompts using existing policy/native user password hashing. Keep mutation, provider revocation and signed application boundary in one controlled provider operation rather than separate independently committed UserWrite/revoke stages. No success when revocation cannot be confirmed. Retain distinct existing recovery flow/copy.
- [x] Provision `monash-account-signout-all` with explicit confirmation/recent authentication and the same signed revocation helper, without changing password/email. Configure Security entry to supported native MFA/session views; enforce current-factor/recent-auth checks for changes, including direct native routes. Do not advertise a control whose guard cannot be verified in the pinned image.
- [x] GREEN provider tests: profile allowed-fields, email old-until-confirmed, token expiry/replay/second-attempt conflict, unchanged UUID/roles, receiver-failure rollback, password old-proof rejection and all-session revocation. Document supported direct paths and user/API edit permissions. Commit provider changes.

## Task2 — Platform claims, links and revocation contracts

Files: `services/api/app/db/platform.py`, Alembic migration after `a61c84b0e921`; `app/http/contracts.py`, `app/identity/dependencies.py`, `app/routers/auth.py`, `app/routers/identity_events.py`, `app/config.py`; tests `services/api/tests/test_identity.py`, create `test_account_settings.py`, OpenAPI snapshot.

Interfaces: nullable `Account.display_name` up to120 chars synchronized from trusted signed name claims, never a client write endpoint. `/api/v1/auth/me` adds nullable `display_name`. Authenticated GET `/api/v1/auth/account-settings` returns allowlisted profile/email/password/security/session/signout-all URLs and explicit availability, no secret. Disabled/unconfigured service returns an actionable unavailable state; never construct links from client input. Extend signed IdentityEvent.action with `account.email_changed`, `credentials.changed`, `sessions.revoked`; all establish monotonic revoked-before boundaries and revoke browser sessions, without modifying capabilities. Unknown-account audit lookup recognizes all revoking actions to block old proofs after later account creation.

- [x] RED tests: valid signed name sync/trim/length handling; malformed name does not corrupt authentication; omitted name preserves a safe nullable label. New event actions reject invalid signatures/origins/times, deduplicate retries, invalidate old bearer/browser proofs and preserve report ownership/capabilities.
- [x] Implement migration, projection and event handling; choose null for missing/invalid optional signed name rather than blocking otherwise valid identity. Store only the normalized label, not a duplicate profile database.
- [x] RED trusted-link tests: HTTPS outside explicit loopback staging, no credentials/query-controlled destinations, unconfigured paths unavailable, same approved identity origin, no administrator URL. Implement deployment configuration for exact supported provider paths confirmed by Task1; add local staging values only after flow acceptance.
- [x] Verify migration upgrade/downgrade/upgrade/schema check on guarded disposable5433 database; full Python suite and regenerated OpenAPI. Commit.

## Task3 — Mobile Account entries and safe return lifecycle

Files: `apps/citizenflood/lib/screens/profile_screen.dart`, `lib/services/account_session.dart`; create `lib/services/account_settings_repository.dart` and `lib/services/account_settings_launcher.dart`; pubspec/lockfile if a system-browser launcher dependency is needed. Tests account_screen/account_session plus settings repository/return lifecycle tests.

Interfaces: repository loads Task2 link DTO; launcher `open(Uri uri) -> Future<bool>` opens external system browser only, validates approved URL before launch. Add `AccountSession.refreshAccountProof() -> Future<void>` to obtain fresh claims on return without inventing a new successful login. Invalid/revoked refresh proofs invalidate the local generation and require sign-in; transient network errors retain identity and offer Retry. Pin error classification to actual provider responses rather than treating every failure as revocation.

- [x] RED: signed-in screen has Profile, Email & password and Security; each invokes the correct configured action. Missing capability links show unavailable/retry; signed-out state does not present enabled account editors.
- [x] Implement short entry rows and focused Email & password/Security action sheets for the corresponding links. Label provider-session view honestly and Sign out all devices as a separate destructive-to-sessions action with explicit confirmation in the identity flow. No generic arbitrary URL launcher.
- [x] Observe WidgetsBinding lifecycle after launched settings; on resume refresh once for the same captured generation, then reload `/auth/me`. Cancellation/resume never means success. Delayed responses after logout/account switch are discarded. Preserve existing sign-in/sign-out, privacy clearing and account error states.
- [x] GREEN tests for changed-name reload, invalid_grant versus outage, cancellation, unconfigured link, resumed flow/account-switch race,200% text and narrow layout. Run full Flutter tests/analyzer/debug build; commit.

## Task4 — Web account entry points and local acceptance

Files: `apps/dashboard/src/pages/public/AccountPage.tsx`, `src/api/accounts.ts`, `src/components/auth/OperatorAccess.tsx`; focused settings components/tests; docs operations shared-accounts guide and existing account/Samsung acceptance docs.

- [x] RED tests: signed-out sign-in path, signed-in same trusted settings actions, unavailable service/error/retry, escaped display name and no claim that Android already provides unsupported editing. Implement using existing session transport and account caches; no password fields in dashboard.
- [x] Clear stale private account data on expired/revoked sessions; refresh signed identity after account settings rather than trusting browser return parameters. Run dashboard tests/build/lint.
- [x] Rebuild local API, run provider bootstrap/tests and apply migration. Use a new or existing agent-owned synthetic account with clearly marked addresses only; never change a human's email/password/MFA. Exercise display name, verified/expired/cancelled/concurrent email change, password old-proof rejection, MFA/session view and sign out all devices across native/web sessions. Mailpit only; never print verification links, passwords or MFA seeds.
- [x] Install latest staging debug APK and test account entry/system-browser return on unlocked Samsung; record any unavailable physical checks accurately. Keep public APK/production routes unchanged.
- [x] One fresh whole-change review and one regression-backed substantive fix pass. Full software/migration/OpenAPI/repository/inventory checks; document actual results and provider/session-scope limits. Commit/push linked PR with accurate readiness and CI status.

## Self-review

All approved sections map to Tasks1–4. Provider credential mutation and email verification precede advertising client controls. The verified-email attribute and immutable subject identity are explicit. Revocation delivery is idempotent and fail-closed across transaction boundaries; tests must demonstrate rollback/uncertain-delivery behavior. Native provider edit routes and permission bypass are part of acceptance, not assumptions. The app exposes real supported session scope; unified per-device correlation, deletion, production and map scaling stay outside this plan.
