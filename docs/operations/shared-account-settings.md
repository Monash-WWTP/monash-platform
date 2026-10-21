# Shared account settings

CitizenFlood's Account tab and the web `/account` page use the same identity service. Profile edits change only an optional display name. Email changes require candidate-address verification; password changes and Security require the current password and any configured MFA. Neither client stores a second password database or grants operator permissions.

## Controls and identity boundaries

| Control | Provider flow | Effect |
| --- | --- | --- |
| Profile | `monash-account-profile` | Trimmed optional display label, maximum 120 characters. |
| Change email | `monash-account-email` | Candidate email stays pending for up to 30 minutes; only the latest verified attempt can replace the old address. |
| Change password | `monash-account-password` | Provider password hashing; at least 12 characters, repeated confirmation. |
| MFA & account sessions | `monash-account-security` | Fresh verification, then native provider Credentials/Sessions views. |
| Sign out all devices | `monash-account-signout-all` | Explicit confirmation, provider token/session revocation and signed platform-session revocation. |

Email, password and MFA changes revoke old provider proofs and platform browser sessions before success. A failed platform revocation delivery prevents the provider mutation from completing. Uncertain deliveries may already have revoked platform sessions; retry is safe and signing in again may be necessary. Email attempts use stable event IDs. Provider and platform identity keys, report ownership and capabilities remain unchanged.

Removing an individual **provider session** is not a unified mobile/API device-session control. Use Sign out all devices for that broader effect. Native app-password/token creation is intentionally blocked for ordinary users; it is not a supported account feature. MFA setup/removal requires a same-user verification marker no older than five minutes, including native flow/API paths. These changes can sign the current browser out as well.

`default-user-settings-flow` and `default-password-change` are replaced with the reviewed flows, so old direct links cannot restore unrestricted profile or password edits. A supported `data.user_settings` hook mounts `AccountSettingsGuard` in the pinned authentik image. Non-superuser direct user/token writes are denied. Initial administrator grants and secrets remain server-only.

## Client return behavior

The API exposes only configured, allowlisted settings links. `ACCOUNT_SETTINGS_ENABLED` defaults to false; enable it only after provisioning and accepting the provider flows. HTTPS is required outside explicit loopback development/test/staging. Local staging configuration is not a production deployment recipe.

Mobile opens the system browser. On resume it refreshes identity proof once for the captured account generation and reloads account details. A browser closing is not proof that a change succeeded. Revoked refresh tokens clear the local identity; connection failures retain identity for retry. Delayed results cannot restore a logged-out or switched account.

Web clears cached private queries when leaving for settings, then obtains fresh signed claims through OIDC on return. The return destination is a fixed `/account` choice, not an arbitrary URL. Display labels come only from signed claims; a monotonic claim timestamp prevents older proofs reverting a newer label. Changes within the same issued-at second may need a later refresh.

## Email templates

All four platform account emails extend `email/monash_base.html`: registration confirmation, password recovery, candidate-email confirmation and previous-address notification. The base owns the logo, typography, spacing, action-button styling and footer. Child templates supply purpose-specific wording; recovery must never masquerade as registration. The previous-address notice has no confirmation button. Local Mailpit verifies rendering/delivery only, not production SMTP deliverability.

## Local acceptance, 21 October 2026

- Synthetic accounts only; no human credentials, email address, password or MFA changed.
- Live branded Profile flow saved a label; fresh web OIDC claims displayed it.
- Live email change kept the old address authoritative until candidate confirmation, updated the verified attribute and sent the old-address notice. The initial post-revocation return error was corrected by clearing the current provider session before middleware saves it; regression covers this session boundary.
- Live password change completed and the changed password authenticated successfully. Native TOTP enrollment after Security verification completed and signed prior sessions out.
- Provider integration tests cover field allowlists, stale/replayed/expired/wrong-user email confirmation, receiver-failure rollback, password handling, session clearing, planned current-user binding, direct API recency guards, expired-browser navigation and rendered shared email templates.
- Samsung staging APK installed. Synthetic sign-in returned to CitizenFlood; the three Account entries were visible in portrait and Profile opened the system browser at reauthentication. A concurrent synthetic MFA test revoked that phone session as designed. Full completed-edit return on the final APK remains a separate physical acceptance step.
- Migration `b72a05e3c114` upgrade/downgrade/upgrade and schema check passed on disposable PostgreSQL; local staging upgraded. Public signed APK and production services were not changed.

Production identity host, API, SMTP, TLS, private storage, monitoring and deployment acceptance remain pending provisioning. Do not describe this local acceptance as a production launch qualification.
