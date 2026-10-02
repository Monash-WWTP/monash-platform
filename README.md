# Monash platform

Successor source repository for CitizenFlood, the WWTP dashboard, and their
shared API. See [source origins](docs/migration/SOURCE_ORIGINS.md). Legacy
repositories and deployments remain active during the staged migration.

The WWTP dashboard lives in `apps/dashboard`. Run `npm ci`, `npm run lint`,
and `npm run build` from that directory. Its data path is still the legacy
Supabase/API configuration during this import.
