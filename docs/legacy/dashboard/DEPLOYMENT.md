# Deployment

Production layout: **Vercel** (frontend, static) → **Render** (FastAPI backend) →
**Supabase** (all data). The browser only ever talks to the Vercel domain; Vercel
rewrites `/api/*` to Render server-side (so there is no CORS to configure), and
both the frontend and backend read/write the same Supabase project.

```
 Browser ──► Vercel (React static + /api proxy) ──► Render (FastAPI) ──► Supabase Postgres
        └────────────────────── supabase-js (lab data, GHG views) ─────────────┘
```

## Why the backend had to change for hosting

Render's free tier (and most serverless/PaaS hosts) give the app **no persistent
disk** — local files are wiped on every restart, deploy, or wake-from-sleep. The
backend was therefore made **stateless**:

- Simulation runs — KPIs, exceedances, **and the full daily time-series** — persist
  as JSONB columns on `simulation_runs` in the database, not as local SQLite +
  Parquet files. (`backend/app/services/simulation.py` → `result_to_timeseries`,
  `simulation_runs.timeseries`.)
- `DATABASE_URL` and `CORS_ORIGINS` are read from the environment
  (`backend/app/config.py`), so the same code runs on SQLite locally and on
  Supabase Postgres in production with no edits.

A run's time-series is ~20–30 KB, so JSONB is the right tool here and Parquet is
unnecessary in production. The `wwtp_sim` package still ships Parquet helpers for
offline/analysis use; the API no longer uses them.

## Deploy config in the repo

| File | Purpose |
|---|---|
| `render.yaml` | Render Blueprint: build + start commands, health check, Python version, Supabase keys. `DATABASE_URL` and `CORS_ORIGINS` are marked `sync: false` (set in the Render dashboard). |
| `frontend/vercel.json` | Rewrites `/api/:path*` to the Render backend. Replace the placeholder host after the backend is live. |
| `frontend/src/api/client.ts` | Calls relative `/api/...` paths; honours optional `VITE_API_BASE` if you prefer calling the backend directly instead of via the rewrite. |

Build resolves the monorepo's local package by installing the simulation package
first so the backend's `wwtp-sim` dependency resolves locally rather than from
PyPI: `pip install ./simulation && pip install ./backend`.

## Step-by-step (Render + Vercel)

### 1. Supabase connection string

Supabase dashboard → project **IWK Data** → **Connect** → **Session pooler**. Copy
the URI and adapt it:

- change the scheme `postgresql://` → **`postgresql+psycopg://`**
- fill in your database password

Result looks like (this project's actual pooler host — **`aws-1`**, not `aws-0`):

```
postgresql+psycopg://postgres.eaxekwlmvpvftpgxiwlu:YOUR_PASSWORD@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
```

**Copy the host verbatim from the dashboard** — do not hand-type the shard prefix.
Supabase migrated newer projects from `aws-0-` to `aws-1-`; using the wrong one
fails with `FATAL: (ENOTFOUND) tenant/user postgres.<ref> not found` (the pooler
shard you reached doesn't host your project).

Use the **session** pooler (port 5432) for a long-lived web service. The
transaction pooler (6543) also works — the engine disables psycopg prepared
statements for Postgres so either port is safe (`backend/app/db/session.py`).

> **`password authentication failed for user "postgres"`** means host/shard are
> right but the password is wrong. Usually a special character in the password
> isn't URL-encoded (`@`→`%40`, `#`→`%23`, etc. — a `DATABASE_URL` is a URI).
> Simplest fix: Supabase → Project Settings → Database → **Reset database
> password** to an alphanumeric-only value, no encoding needed. It's the database
> password, not the account password or API key. The backend connects as `postgres`, so RLS does not
restrict it; it creates its own tables (`plants`, `scenarios`, `simulation_runs`,
…) in the `public` schema alongside the existing data tables on first startup.

> **Must use the pooler, not "Direct connection".** Supabase's direct host
> (`db.<ref>.supabase.co`) is **IPv6-only**, and Render's free tier has no
> outbound IPv6 — using it fails at startup with
> `connection ... port 5432 failed: Network is unreachable` against an IPv6
> address (`2406:...`). The **Session pooler** host (`aws-0-<region>.pooler.supabase.com`)
> is reachable over IPv4. Tell-tale sign you have the right one: the username is
> `postgres.<project-ref>`, not bare `postgres`.

### 2. Backend on Render

1. render.com → sign up with GitHub → **New + → Blueprint**.
2. Select `JienWeng/wwtp-dashboard`. Render reads `render.yaml` and shows the
   `wwtp-api` service.
3. Set the prompted env vars:
   - `DATABASE_URL` = the string from step 1
   - `CORS_ORIGINS` = `http://localhost:5173` (placeholder; not used by the Vercel
     proxy path, harmless to leave)
   - `WWTP_OPERATOR_EMAILS` = comma-separated, confirmed operator email addresses
4. **Apply**. First build ~3–5 min. Confirm at `https://<your-service>.onrender.com/api/health`
   → `{"status":"ok"}`.

Before operators sign in, add their email accounts in Supabase → Authentication →
Users and set the Auth URL Configuration redirect allow-list to include the local
development origin and the deployed Vercel origin. Public sign-up is disabled in
the dashboard flow; only invited, email-confirmed users whose address is listed in
`WWTP_OPERATOR_EMAILS` can view or change scenarios and saved runs, run simulations,
or compare runs. The API validates each bearer token with Supabase Auth; no service
key is sent to the browser.

### 3. Point the frontend at the backend

Edit `frontend/vercel.json`, replace `REPLACE-WITH-RENDER-URL.onrender.com` with
the real Render host, then:

```bash
git commit -am "set render url" && git push
```

### 4. Frontend on Vercel

1. vercel.com → sign up with GitHub → **Add New → Project** → import `wwtp-dashboard`.
2. **Root Directory = `frontend`** (monorepo — this matters). Framework auto-detects
   as Vite.
3. **Deploy**. The resulting `https://wwtp-dashboard-*.vercel.app` is the live app.

## Environment variables reference

**Backend (Render):**

| Var | Example | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://…pooler.supabase.com:5432/postgres` | Supabase session pooler. Defaults to local SQLite if unset. |
| `CORS_ORIGINS` | `https://wwtp-dashboard.vercel.app` | Comma-separated. Only needed if the frontend calls the backend directly (no Vercel rewrite). |
| `SUPABASE_URL` / `SUPABASE_KEY` | preset in `render.yaml` | Publishable key; used at startup to sync stations + emission factors. |
| `WWTP_OPERATOR_EMAILS` | `operator@monash.edu` | Comma-separated allow-list of confirmed Supabase Auth users who may access scenario and run data or run models. Empty means protected actions stay disabled. |

**Frontend (Vercel):**

| Var | When |
|---|---|
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_KEY` | Optional — hardcoded fallbacks exist in `src/lib/supabase.ts`. Set to override. |
| `VITE_API_BASE` | Optional — only if you skip the `vercel.json` rewrite and call Render directly (then also set `CORS_ORIGINS` on Render). |

The dashboard sends Supabase session access tokens to the API. Add the deployed
frontend origin to Supabase Auth's redirect allow-list so magic links return to
the dashboard. Keep account provisioning and the operator allow-list restricted
to staff who should be able to change shared scenario data.

## Free-tier behaviour

Render free **sleeps after ~15 min idle**; the first request after sleep takes
~50 s to wake, then it's fast. Acceptable for demos and reviews. To keep it
always-on: Render paid ($7/mo), or **GitHub Student Pack → DigitalOcean** ($200/yr
credit with a Monash email — effectively free for a year, never sleeps; deploys the
same `backend/` from GitHub).

## Redeploys

Both platforms auto-deploy on push to `main`. Because the backend is stateless,
redeploys and restarts are safe — nothing is lost. Schema changes to the Supabase
data tables/views go through `supabase/migrations/` (applied with the Supabase CLI
or the Management API). The backend's own tables are created automatically by
SQLAlchemy on startup.
