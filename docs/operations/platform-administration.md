# Platform administration

The source dashboard includes `/dashboard/admin`. Its API requires application administrator permission and a current operator MFA proof on every request. It is not publicly usable until the successor API and identity service are deployed and qualified. Server provisioning remains pending by owner instruction.

## First administrator

1. Register and verify a native shared-platform account through the configured identity service. Complete operator sign-in with MFA. Registration itself grants no administrative permission.
2. Obtain that account's UUID from `/api/v1/auth/me` in its authenticated browser session. Do not identify an account by email alone or claim a legacy anonymous account by email.
3. An authorized server administrator runs the trusted CLI with the account UUID and an approval reason. Run inside the API environment with the correct application database; never copy database secrets into the browser or chat:

```sh
uv run --locked python scripts/administer_account.py \
  --account-id VERIFIED-ACCOUNT-UUID \
  --capability report:own \
  --capability platform:admin \
  --administrator APPROVING-OWNER \
  --reason 'Approved platform administrator'
```

This command replaces the capability set, audits the change and revokes affected browser sessions. Include every intended approved capability, not just the newly added one. Reauthenticate through the operator MFA flow, then open `/dashboard/admin`.

Only the trusted CLI can grant/revoke platform-administrator permission. Browser administrators cannot change their own permissions or promote another user to platform administrator. Keep a separately controlled recovery administrator and audit its custody; no independent recovery test is implied here.

## Daily tasks

- **Users:** search native registered accounts; grant/revoke submission, report-review, monitoring and research-scenario permissions with a reason. Permission changes revoke that user's browser sessions; bearer requests re-read server-owned permissions. Account enrollment, invitations/email delivery, password resets and identity-provider disabling remain in authentik. Removing an application permission is not an identity-provider disable.
- **Plants:** create/update identity, location, design capacity, equipment baselines and settings. A plant's code should match its monitoring station code when they represent the same facility; the two records are edited explicitly rather than silently rewriting each other. Availability is a percentage, not measured removal efficiency or reactor geometry.
- **Stations:** create/update metadata only. Historical laboratory samples and source-import provenance are not editable or deletable through this panel.
- **History:** inspect administrator, timestamp, reason and previous/new values. The history view excludes report notes/photos, authentication proofs and secrets.
- **Status:** refresh database/storage/identity readiness and model policy. A ready dependency does not establish successful recovery, restore, physical-device testing, production acceptance or scientific validity.
- **Report review:** follow the existing moderation link. Access still requires its own reviewer permission and MFA; administrator status alone does not silently grant report access.

## Configuration and evidence

Each saved plant configuration creates an immutable numbered revision and an audit event. Source reference and applicability text are required for emission factors and each screening threshold. Existing settings without a recorded source display their actual values with unknown provenance; an administrator must supply evidence before saving the first versioned revision. User-supplied references are explicitly unverified, not automatically accepted scientific evidence.

Canonical screening units are mg/L for BOD/COD/TSS/ammonia/nitrate/phosphorus, NTU for turbidity and unitless for pH. Unsupported units are rejected rather than silently converted. Verify the value and its source before explicitly changing its unit. Methane factors use kg CH4/kg BOD5; nitrous-oxide factors use kg N2O-N/kg N. The current GHG interpretation/applicability limitations remain in [scientific validation](../science/VALIDATION.md).

Changes affect future run resolution; previous result records, snapshots and configuration revisions remain unchanged. Explicit scenario operating assumptions take precedence over plant equipment defaults. Existing scenarios may explicitly specify 100% availability: changing a baseline does not silently rewrite those scenarios. Review resolved run snapshots and comparison input differences.

Concurrent edits are rejected when their expected revision or prior permissions no longer match. Keep your unsaved values, review the error, then explicitly discard/reload the latest record before editing again. Do not repeatedly save an uncertain timed-out action without checking history/current state.

## Boundaries and acceptance

There is no browser secret/password editor, shell, SQL console, historical result deletion or scientific-validation switch. Deployment trust origins, SMTP credentials, S3/database credentials and signing keys remain server-side. Model `effluent_v1` 1.4.1 remains illustrative and unvalidated. Historical 1.4.0 runs are retained but cannot be replayed by the changed model implementation.

Before production, verify role/MFA/CSRF denial, user revocation, configuration save/reload/conflict behavior, public station contracts, immutable prior runs and redacted history using the actual deployed clients. See [production preparation](../../infra/production/README.md) and the [server setup guide](production-server-setup.md).

Screening supports upper limits for BOD, COD, TSS, ammonia, nitrate, phosphorus and turbidity. pH is not configurable here because a single upper limit does not represent its range semantics. When a configured BOD/COD/TSS limit is absent, the model retains its existing 50/200/100 mg/L fallback; each new run records these effective limits, units and `model_fallback_unverified` provenance. Removing a setting does not disable fallback screening. Scenario API omissions inherit plant equipment availability; explicitly supplied scenario values remain overrides.
