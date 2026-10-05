<!-- impeccable:product-schema 1 -->
# Product

## Platform
web

The public portal and WWTP operator dashboard are web surfaces. CitizenFlood is a separately deployed Flutter Android companion application.

## Users
Citizens download CitizenFlood and submit observations. Invited operators work with monitoring data and scenarios. Research readers access approved publications and explanatory articles.

## Purpose
Provide a shared platform for citizen observations, wastewater monitoring and transparent research communication, with clear distinctions between observations, laboratory measurements and model outputs.

## Operating context
A public website introduces the products, distributes the Android application and presents approved research. Authenticated workflows use the shared FastAPI backend. Migration to a standalone server is planned; web, mobile, API and identity remain independently deployable.

## Capabilities and constraints
- APK downloads and published research are public and require no account.
- Citizen registration requires verification. Operator access requires invitation and MFA.
- Both applications use one platform account with separate application permissions.
- authentik OIDC is implemented in local staging with verified registration and operator MFA; production identity deployment remains pending. Application identity must map uniquely by issuer and subject, not email alone.
- Research content may be published only after approval. No papers, citations, results or endorsements may be invented.
- Release APKs require production configuration, a durable signing identity and verified installation/update behavior. The published signed APK 1.0.0 (code 2) uses the real legacy backend. The native shared-account .staging debug app is a local acceptance build, not a public release.
- The current source clients use the shared API. The published APK still uses legacy Supabase and remains immutable until a verified native release. Private legacy report/photo migration requires the authorized source export.
- Simulation outputs are illustrative and unvalidated until the documented validation gates are met.

## Brand commitments
Academic and industrial rigor, accurate evidence, clear provenance and restrained claims. Institutional branding or endorsement requires confirmed authority.

## Accessibility
Public pages and account flows must support keyboard navigation, visible focus, readable contrast, assistive technology and narrow screens. Installation instructions must remain usable without relying on images alone.

## Evidence
- User confirmed public downloads/articles, verified citizen registration and invitation-only operator access on 2026-10-02.
- User confirmed preparing the research section and publishing only approved content on 2026-10-02.
- Repository architecture, migration roadmap and scientific validation documentation describe current implementation boundaries.
- Public portal routes include `/`, `/download`, `/research`, `/login` and `/register`; monitoring is `/dashboard`. Public APK downloads exist. Shared identity runs locally and is not publicly deployed.

## Principles
Make the next action understandable. Describe evidence and uncertainty accurately. Enforce permissions in the API. Keep public research separate from private operational and citizen data. Preserve independent deployment and reproducible releases.
