# Shared account settings for registered users

Status: design and inline implementation approved. Implementation and local acceptance completed; see the shared-account-settings operations guide for verified scope and remaining production gates.

## Purpose and platform fit

Let a registered citizen manage the same identity used by CitizenFlood and the operator dashboard. Preserve issuer/subject identity, report ownership and server-granted permissions. Account changes must not create a second password store, merge accounts by email or let a user grant themselves operator access. Keep the existing green branding and concise mobile layout.

This is a shared-identity extension: mobile entry points, branded identity flows, application claims/session handling and dashboard account links must agree. Geographic map loading/clustering is separate work and is not included here.

## Existing state and approach

The mobile Account tab currently shows email/verified status, sign-in/sign-out and About. The pinned authentik instance already has default-user-settings-flow and native authenticator/session management. Existing enrollment verifies email, recovery uses separate reset copy, and signed identity events revoke application sessions after credential resets/disabling. The public web Account page currently points users back to Android.

Reuse and brand the provider's supported self-service UI, with purpose-built verified email/password flows where necessary. Do not build password/MFA editors in the platform API. Merely linking the default settings page is insufficient if it permits unverified email edits or fails to revoke application-held sessions. A fully native credential editor would duplicate security logic and is not recommended.

## Citizen Account screen

Signed-in view: optional display name, verified email, then three clear rows: Profile; Email & password; Security. About stays collapsed and Sign out remains available. Each row opens a trusted, configured identity URL in the system browser; external secure-account context is stated briefly. No provider administrator links, role controls or secret fields.

On return/resume, reload account information using fresh identity proof. Do not display success merely because the browser closed. If email/password/session changes revoked the app's proof, show Sign in again and clear stale private state through existing generation fencing. Cancelled/failed actions retain the current account rather than displaying an invented updated value. Provide retry when the service cannot be reached. Unsupported/unconfigured settings are unavailable explicitly, not dead buttons.

## Profile

Edit optional display name only, trimmed and bounded to120 characters. It is a display label, not a verified legal name or unique identifier. Keep account UUID, issuer/subject and roles read-only. Existing accounts without a name remain valid; registration does not acquire new mandatory demographic fields. Synchronize the label from trusted signed identity claims on authentication/refresh; application responses never trust a client-supplied identity/name claim. Escape text in all consumers.

## Email and password

Require recent authentication for sensitive changes. Email change collects a candidate address and confirms delivery to that address before replacing the verified identity email; the existing email remains authoritative until completion. Confirmation uses change-email language, separate from enrollment and recovery, with expiry, cancellation and replay protection. Duplicate/conflicting addresses must not merge identities or transfer reports. Bind the verification to the same user and candidate, invalidate stale concurrent attempts and notify the previous address after successful change without exposing tokens in application logs.

After successful email change, update the verified-email attribute consistently and invalidate old provider tokens/sessions plus application browser sessions through the signed-event boundary. Preserve issuer/subject and original report ownership. Fail closed when application revocation cannot be confirmed; document recovery/retry rather than reporting completion prematurely.

Password change uses provider-native handling, recent/current authentication and the existing password policy. No password enters the platform API or mobile storage. Revoke old proofs across the provider and application, then require a fresh sign-in. Keep Forgot password recovery available as its distinct flow.

## Security and session scope

Offer provider-managed MFA setup/removal with recent authentication and current-factor checks where configured. Operators still require MFA for protected actions; citizens do not obtain operator rights by configuring MFA. Do not add a weaker fallback or silently reset MFA.

Expose the provider's supported active-session view, labeling its actual scope. Do not imply that removing an identity-browser session revokes every mobile/API session unless tested. Provide a clearly distinct Sign out all devices flow only when it revokes provider access/refresh tokens, identity sessions and platform browser sessions together via signed events. Audit without storing tokens, passwords, MFA seeds or recovery codes. Per-device unified app-session listing/revocation is deferred unless the provider/application can reliably correlate those sessions; do not fabricate device names or activity times.

## Trusted links and web integration

Settings URLs derive from approved deployment configuration and explicit provider paths, with HTTPS required outside loopback staging. No arbitrary return URLs or client-controlled issuer/origin. Browser return links are navigation only, never authentication proof. The dashboard/public Account page should expose the same account-management entry points and truthful sign-in/service states rather than claiming Android already offers editing. App and web remain independently deployable; no production origin or secret is invented.

## Acceptance

Use an agent-owned synthetic account. Test display-name edit and fresh reload; cancelled and expired email change; verified completion, old/new email claim behavior and unchanged report ownership; password change and old-token rejection; MFA/session scope; sign out all devices and application revocation; browser cancellation, offline errors, account switch, mobile return and narrow/large-text layout. Verify identity flows in the pinned image before advertising them as working. Add API/claims/session regressions, Flutter account-entry/resume tests and dashboard link/state tests. Regenerate OpenAPI/migrations only where actual contracts/persistence change.

One final independent review and regression-backed fixes precede delivery. Document actual local results and remaining production/SMTP/identity-host acceptance. No production provisioning, public signed APK release, account deletion or research-data/consent changes are included.
