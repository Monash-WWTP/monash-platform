# Portal release acceptance

These checks define production release evidence. Current source verification is recorded in REVIEW_STATE.md; identity, real-device APK and production operations gates remain outstanding.

## Public website

- Landing/download/research routes load without authentication.
- Mobile and desktop navigation expose download, account and research entry points.
- Keyboard focus, accessible names, contrast, heading order and narrow-screen overflow are verified.
- Release-unavailable state offers guidance without a broken or misleading download button.
- Public pages and search output contain neither unpublished drafts nor private operational/citizen records.

## Identity

- One verified citizen can sign in on Android and web and resolves to one application account.
- An ordinary citizen cannot read or mutate operator-only resources, including through direct API requests.
- Operator invitation, expiry, MFA, recovery, session expiry and logout have explicit acceptance cases.
- Email changes do not change account ownership or silently merge identities.
- Invalid issuer/audience/signature, expired tokens and revoked access fail closed.

## Android release

- Published manifest values match the verified APK's metadata, byte size and SHA-256.
- APK is production configured and signed with the release key; private keys are not in source, assets or logs.
- A supported Android device can download over HTTPS and install after the required system confirmation.
- An update signed by the same authorized identity preserves expected local state and account access.
- Public download works without private GitHub access. Unsupported devices get understandable guidance.
- Current Android developer-verification and regional installation requirements are checked before public release.

## Research

- Each published item has author attribution, approval, date, type/status, sources and stable URL.
- Supplied DOI links resolve to the cited publication; publication status is represented accurately.
- PDF hosting rights are confirmed or the page links to an authorized source.
- Figures have useful alternative text and citations remain usable on mobile.
- Unvalidated model outputs are identified as such; project notes are not labeled peer-reviewed papers.
- Corrections and withdrawal behavior preserve an accountable publication history.

## Operations

- Frontend/API/identity can be deployed and updated independently with documented compatible contracts.
- TLS, backups, restore rehearsal, signing custody and rollback have evidence and named owners.
- End-to-end report submission and authorized operator workflows pass against the intended production configuration before release.
