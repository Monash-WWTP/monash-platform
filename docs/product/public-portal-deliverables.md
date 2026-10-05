# Public portal and release deliverables

Status: scope and access policy confirmed; proposed route structure and implementation sequence awaiting brief review. Visual direction remains pending; the user selected visual concept first. No public APK, identity integration or publishing UI is delivered by this document.

## Deliverables

| Deliverable | Acceptance |
| --- | --- |
| Public landing page | Explains CitizenFlood, the operator dashboard and research; offers Android download, registration and login; makes no unsupported scientific or institutional claims. |
| Android distribution | A signed, production-configured APK served publicly over HTTPS, with version, release date, file size, minimum Android version, SHA-256 checksum, release notes and installation guidance. Fresh install and update from the previous release pass on supported devices. |
| Shared accounts | Verified citizen registration, recovery and login across both clients; invitation/MFA for operators; API enforces distinct permissions and rejects unauthorized requests. |
| Research section | Public article index and accessible article pages; approved content only, with authors, dates, publication status, citations and corrections. Empty collection has an honest unpublished state. |
| Deployment handover | Separate web/API/identity services, documented configuration, backups and restore rehearsal, release signing custody, rollback and operational ownership. |

## Proposed public routes

- `/`: public landing page. Introduce the platform, establish its evidence boundary and offer Download CitizenFlood, Create account and Log in. Provide access to research and the operator workspace.
- `/download`: current Android release and installation/update instructions. The button reads “Download Android APK”; installation is completed by Android with the user's consent. Desktop visitors also receive a QR code linking to this page.
- `/research`: published research articles, filterable only when the collection warrants it; no fabricated example papers.
- `/research/:slug`: approved research summary, linked paper/DOI where supplied, author attribution, citations, limitations and publication/correction history.
- `/login`, `/register`, `/account`: entry points into shared identity and profile flows. Redirect destinations are validated.
- `/dashboard` and `/dashboard/plants/:plantId`: operator workspace. Update existing links and provide deliberate compatibility handling for old plant URLs.
- `/privacy`, `/terms`, `/accessibility`: reviewed public policies and support information.

Route names are proposed, not current behavior. Keep public pages accessible independently of login. Do not imply that registering grants operator access.

## Account contract

Use one identity authority with separate OIDC clients for web and Android. The API owns the platform account and its permissions. Ensure both OIDC clients resolve to the same canonical `(issuer, subject)` mapping; verify provider issuer and subject settings before linking accounts. Never merge accounts merely because email addresses match.

Android uses the external browser authorization-code flow with PKCE. Web uses a backend-held session and secure cookie. Define logout, refresh/revocation, email verification, recovery, invitation expiry and MFA recovery behavior explicitly. A shared account does not guarantee that every device is already signed in.

The existing authentik choice remains the target. Its official provider documentation supports OIDC and PKCE: https://docs.goauthentik.io/add-secure-apps/providers/oauth2/.

## APK release contract

Public downloads must not require access to the private source repository. Publish immutable, versioned artifacts to public HTTPS hosting/object storage, keeping build/signing secrets private. A release manifest records the artifact URL, package ID, version name/code, minimum SDK, byte size, checksum and release notes. Publish the manifest only after upload and verification; retain prior versions for rollback planning.

Preserve the application signing identity for compatible updates, protect and back up its key, and document custody. Test fresh installation, upgrade preserving account/report state, interrupted download and unsupported device behavior. Download links must serve APK bytes rather than an HTML login page.

Android supports website distribution but installation can require device settings and confirmation; the website cannot silently install the app. Verify current device and regional developer-verification requirements before release. Official distribution guidance: https://developer.android.com/distribute/marketing-tools/alternative-distribution.

## Research publishing contract

Begin with repository-managed Markdown and validated metadata, reviewed through pull requests; avoid adding a CMS before an editorial workflow requires it. Render approved content into the independently deployed web build. Keep drafts out of public build output and search indexes.

Required metadata: stable slug, title, authors, approval record, publication date, article type/status and sources. Include DOI/publication links only when supplied and verified. Distinguish peer-reviewed papers, preprints and project notes. Host paper PDFs only when distribution rights are confirmed; otherwise link to the publisher or approved repository. Sanitize content and disallow arbitrary embedded scripts. Maintain correction history and explicit limitations.

## Interaction and responsive states

- Landing navigation and calls to action work with keyboard, touch and screen readers.
- Download page covers release unavailable, unsupported platform, failed download and installation guidance. Do not show an active release button before a verified artifact exists.
- Account flows cover verification pending, expired invitation, insufficient permission, expired session and recovery.
- Research covers no publications, missing article, loading/error where applicable, citations and accessible figures.
- On mobile, primary actions remain clear without obscuring reading. Desktop installation guidance bridges to Android through a page URL/QR code.

## Implementation sequence

1. Confirm the visual build workflow and surface brief; inspect existing visual assets and choose the landing composition with Impeccable.
2. Implement identity/account mapping and authorization tests before presenting registration as operational.
3. Migrate client data flows to the shared API and verify contract/privacy boundaries.
4. Build public routes and reviewed research content pipeline; migrate dashboard routing and links.
5. Establish signing custody and reproducible production APK releases; verify download, install and update on real supported devices.
6. Deploy independent services with TLS, backups, restore/rollback evidence and agreed support ownership.
7. Release only when end-to-end registration/login/reporting/operator authorization, public content and Android installation gates pass.

## Decisions still needed

- Landing-page composition and approved visual concept (visual concept first selected).
- Product name, approved institutional assets and public contact/support owner.
- Production domain, Android package/signing ownership and supported-device policy.
- Editorial approver and the first real research content.

Visual styling, palette and typography are intentionally undecided until the Impeccable surface discovery is complete.
