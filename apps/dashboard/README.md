# WWTP dashboard

React/Vite operator interface for lab monitoring, approved community observations and illustrative scenarios. From the repository root:

```sh
npm --prefix apps/dashboard ci
npm --prefix apps/dashboard test
npm --prefix apps/dashboard run lint
npm --prefix apps/dashboard run build
npm --prefix apps/dashboard run dev
```

Vite configuration uses `VITE_SUPABASE_URL`, `VITE_SUPABASE_KEY` (publishable key only), and `VITE_API_BASE`. The default development proxy sends `/api` to localhost:8000. Scenario calls still use legacy `/api/*` routes: supply a compatible legacy development API. The successor `/api/v1` contract is not wired to this client yet. Monitoring retains the source's public Supabase defaults.

The production build runs TypeScript checking. There is no inherited browser test suite; build success does not verify live authentication or map interaction. See the [deployment gate](../../docs/operations/deployment.md), [migration status](../../docs/migration/ROADMAP.md), [scientific limits](../../docs/science/VALIDATION.md), and [import changes](../../docs/migration/IMPORT_ADAPTATIONS.md).

## Public portal

Public routes: `/`, `/download`, `/research`, `/research/references`, `/research/:slug`, `/login`, `/register`.
Operator routes: `/dashboard`, `/dashboard/plants/:plantId`. Old `/plants/:plantId` links redirect. Operator code is loaded separately from the public entry bundle.

The cross-surface UI, route behavior, API cutover, science and operations acceptance items are tracked in the [platform resolution checklist](../../docs/product/platform-resolution-checklist.md).

Shared accounts are **not integrated yet**; account entry pages explain this without collecting credentials. CitizenFlood 1.0.0 is publicly available from the download page; its immutable artifact and verification record are documented in [Android release](../../docs/operations/android-release-1.0.0.json). The public research collection is empty until approved content is supplied.

### Publish a release

Replace the derived `src/releases/current.json` manifest after signature, Android runtime and anonymous public HTTPS checksum verification. `currentRelease` is validated through `parseRelease(manifest)`. The first release passed Android 16 emulator installation, launch and same-version reinstall; physical-device and cross-version updates remain untested and must be recorded for subsequent release qualification. Required fields: versionName, monotonically increasing versionCode, minAndroid, ISO publication date, byteSize, lowercase SHA-256, public artifactUrl and nonempty release notes (`notes`). Invalid metadata returns null; no active APK link is rendered without a release. Metadata validation alone does not establish that the file exists, is public or signed. See [release acceptance](../../docs/product/portal-acceptance-checklist.md).

### Publish research

Pass only approved items into `validatePublishedArticles` in `src/research/articles.ts`. Required fields: unique stable slug, title, authors, publication date, type (`peer-reviewed`, `preprint`, `project-note`), approval reference, HTTPS sources, paragraphs, explicit limitations and correction history (`corrections`, empty if none). Corrections require a valid date on or after publication and description. Content is escaped plain text. Keep drafts outside imports from public routes; additions are reviewed in Git. Verify publication status, citation URLs and hosting rights before publishing. Withdrawals currently require an editorial code change; no CMS or withdrawal automation is claimed.

Reference resources are listed separately in `src/research/references.ts` and rendered at `/research/references`. The landing page links directly to the supplied, byte-identical PDF at `public/references/urban-water-carbon-accounting-guidelines.pdf`. This copy is distributed unchanged under the non-commercial CC BY-NC-ND 4.0 terms stated in the edition; the reference listing retains the third-party-material caveat. Record the DOI, citation, license and how the resource informs platform work. A reference does not establish that the simulator implements or is validated against the publication.

### Browser verification

With a local preview running, from the repository root:

```sh
uv run --with playwright==1.63.0 python scripts/smoke_public_portal.py --url http://127.0.0.1:5174
uv run --with playwright==1.63.0 python scripts/smoke_dashboard_map.py --url http://127.0.0.1:5174 --browser-executable /usr/bin/google-chrome
```

These checks block external requests. They cover public states, copy-link handoff, mobile legend, responsive widths, old deep links and synthetic map worker/attribution handling. They do not verify live integrations or real-device APK installation.
