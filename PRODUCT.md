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
- authentik OIDC is the approved identity target; integration remains pending. Application identity must map uniquely by issuer and subject, not email alone.
- Research content may be published only after approval. No papers, citations, results or endorsements may be invented.
- Release APKs require production configuration, a durable signing identity and verified installation/update behavior. The existing synthetic debug APK is a build check, not a public release.
- Existing clients still depend on legacy Supabase; shared API migration is unfinished.
- Simulation outputs are illustrative and unvalidated until the documented validation gates are met.

## Brand commitments
Academic and industrial rigor, accurate evidence, clear provenance and restrained claims. Institutional branding or endorsement requires confirmed authority.

## Accessibility
Public pages and account flows must support keyboard navigation, visible focus, readable contrast, assistive technology and narrow screens. Installation instructions must remain usable without relying on images alone.

## Evidence
- User confirmed public downloads/articles, verified citizen registration and invitation-only operator access on 2026-10-02.
- User confirmed preparing the research section and publishing only approved content on 2026-10-02.
- Repository architecture, migration roadmap and scientific validation documentation describe current implementation boundaries.
- Current dashboard routes are `/` and `/plants/:plantId`; public portal and shared identity have not been implemented.

## Principles
Make the next action understandable. Describe evidence and uncertainty accurately. Enforce permissions in the API. Keep public research separate from private operational and citizen data. Preserve independent deployment and reproducible releases.
