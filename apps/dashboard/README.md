# WWTP dashboard

React/Vite operator interface for lab monitoring, approved community observations and illustrative scenarios. From the repository root:

```sh
npm --prefix apps/dashboard ci
npm --prefix apps/dashboard run lint
npm --prefix apps/dashboard run build
npm --prefix apps/dashboard run dev
```

Vite configuration uses `VITE_SUPABASE_URL`, `VITE_SUPABASE_KEY` (publishable key only), and `VITE_API_BASE`. The default development proxy sends `/api` to localhost:8000. Scenario calls still use legacy `/api/*` routes: supply a compatible legacy development API. The successor `/api/v1` contract is not wired to this client yet. Monitoring retains the source's public Supabase defaults.

The production build runs TypeScript checking. There is no inherited browser test suite; build success does not verify live authentication or map interaction. See the [deployment gate](../../docs/operations/deployment.md), [migration status](../../docs/migration/ROADMAP.md), [scientific limits](../../docs/science/VALIDATION.md), and [import changes](../../docs/migration/IMPORT_ADAPTATIONS.md).
