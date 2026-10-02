# CitizenFlood — Mobile Reporting App Proposal

**Date:** 2026-06-05
**Prepared for:** Supervisor review (non-technical summary first)
**Status:** Design approved, ready for implementation planning

---

## 1. Plain-language summary (for everyone)

We want a simple mobile app that lets ordinary citizens report what they see during
flooding and heavy rain — a flooded street, rising river water, a rain-gauge reading —
straight from their phone. Each report includes a **photo** and the phone's **GPS
location**, captured automatically. Every report appears as a pin on a **shared map**
that researchers and the public can view.

The app is modeled on the existing **Waterproofing Data** citizen-science app
(flood area, rain, river gauge, water level). It is intended as a **small pilot first**:
prove it works in one area, then grow.

**Key facts at a glance:**

| Question | Answer |
|---|---|
| What does it do? | Citizens photograph + report flood/rain/water observations tied to a location; all reports show on a shared map. |
| Who uses it? | The general public (report anonymously, no signup needed) + researchers viewing the data. |
| What phones? | Android, iPhone, **and Huawei** — covered from launch. |
| Software running cost | **≈ $0 per month** at pilot scale. |
| One-time / yearly fees | $25 once (Google Play) + $99/year (Apple) + $0 (Huawei). |
| Main investment | The developer's time, not software fees. |
| Time to build | **~6 weeks** to live on all three stores (see Section 7). |

---

## 2. What the app does (features)

1. **Welcome screen** — start reporting immediately, anonymously. Optional sign-in.
2. **Category selection** — four big tappable categories:
   - 🌊 Flood area
   - 🌧️ Rain
   - 📏 River gauge reading
   - 💧 Water level
3. **Report form** — add a photo (camera or gallery), location captured automatically
   via GPS, a severity choice, and an optional note. One tap to submit.
4. **Live map** — all submitted reports shown as colored pins on a map, plus a list of
   the most recent reports.
5. **Simple navigation** — a 3-tab bar: Report · Map · Me.

**Design intent:** clean and minimal, one job per screen, a full report takes under
20 seconds. Anonymous-first so there is no signup friction.

### Out of scope for the pilot (deliberately, to keep it simple)
- Offline reporting (save-without-signal). *Noted as the first future upgrade — valuable
  for flood zones with patchy signal, added once the pilot proves demand.*
- Report moderation / admin dashboard beyond the basic Supabase data view.
- Push notifications.
- Comments, likes, or social features.

---

## 3. Technology choices (and why)

The app is built to be **"worryless"**: a managed backend with no server to run or
maintain, free/open tools, and a stack that publishes cleanly to all three app stores.
It is also chosen to be **AI-assisted ("vibe-coded")** friendly — these tools are
well understood by AI coding assistants, which speeds development.

| Layer | Choice | Why |
|---|---|---|
| **App framework** | **Flutter** (Dart) | One codebase builds Android, iPhone and Huawei. Excellent map/camera/GPS support. Very AI-friendly to write. |
| **Map** | **OpenStreetMap** via `flutter_map` | Free, and **not** Google Maps — so it works on Huawei phones, which have no Google services. |
| **Location** | `geolocator` | Reads GPS directly, no Google dependency. |
| **Photos** | `image_picker` | Native camera and gallery access. |
| **Backend** | **Supabase** (hosted) | Database + login + photo storage + security rules in one managed service. **No server to run or patch.** |
| **Login** | Supabase **anonymous + optional email** | Citizens report instantly; no signup wall. |

### Why this matters for Huawei coverage
Huawei phones (newer models) do **not** include Google services. Apps that rely on
Google Maps or Google location quietly break on them. This design uses **OpenStreetMap**
and **direct GPS** instead, so the same app runs identically on Android, iPhone, and Huawei.

### Bonus: fits existing research tools
Supabase stores data in a standard Postgres database. That data **exports cleanly into
the kepler.gl mapping tool already used in this project**, so collected reports can flow
straight into existing research visualizations.

---

## 4. How it works (simple architecture)

```
   Citizen's phone (Flutter app)
        │  submit report: photo + GPS + category + note
        ▼
   Supabase (managed cloud backend)
        ├─ Auth        → anonymous / optional email login
        ├─ Database    → each report: type, location, severity, note, time
        └─ Storage     → the uploaded photos
        │
        ▼
   Live map in the app  ←  reads all reports back as map pins
        │
        └─ (research) export to kepler.gl for analysis
```

There is **no custom server** to build or maintain — Supabase is a hosted service.
This is the single biggest reason the app is low-maintenance.

---

## 5. Data captured per report

| Field | Example | Source |
|---|---|---|
| Category | Flood area | User taps |
| Photo | (image file) | Camera / gallery |
| Location (lat/long) | -37.91, 145.13 | Auto GPS |
| Severity | Low / Medium / High | User taps |
| Note (optional) | "Water over the footpath" | User types |
| Timestamp | 2026-06-05 10:33 | Automatic |
| Reporter | Anonymous ID (or email if signed in) | Automatic |

---

## 6. Costs

### One-time and recurring fees

| Item | Cost | Type |
|---|---|---|
| Supabase backend | **$0 / month** | Free tier covers pilot scale |
| Map tiles (OpenStreetMap) | **$0** | Free at pilot volumes |
| Google Play developer account | **$25** | One-time |
| **Apple App Store developer program** | **$99 / year** | Recurring — the one ongoing fee |
| Huawei AppGallery developer account | **$0** | Free |
| **Total software running cost** | **≈ $0 / month** | — |

### The iPhone requirement (important to budget)
Building and submitting the **iPhone** version requires either a **Mac computer** or a
**cloud build service** (e.g. Codemagic, roughly $0–30/month), plus Apple's **$99/year**
fee. Android and Huawei need neither. Since we are covering all three stores from launch,
budget for the Apple fee and a build machine/service.

> **The real cost is developer time, not software.** At pilot scale the tools are
> essentially free to run.

---

## 7. Timeline

Estimate assumes **one student/freelance developer using AI-assisted coding**, building
the approved scope (online-only pilot, all three stores).

| Phase | Work | Part-time (~15 hrs/wk) | Full-time |
|---|---|---|---|
| 1. Setup | Flutter project, Supabase project + database, anonymous login | Week 1 | ~2 days |
| 2. Core reporting | Welcome + category screens, report form (photo + GPS + submit) | Week 2 | ~3 days |
| 3. Map | Live map with pins + recent-reports list, navigation | Week 3 | ~3 days |
| 4. Polish & test | UI polish, app icon/splash, testing on real Android/iPhone/Huawei devices | Week 4 | ~3 days |
| 5. Store submission | Build + submit to Google Play, Apple App Store, Huawei AppGallery; respond to review feedback | Weeks 5–6 | ~1 week |

**Summary:**
- **Working app (testable build):** ~3 weeks part-time / ~1.5 weeks full-time.
- **Live on all three stores:** ~6 weeks part-time / ~3 weeks full-time.

**Note on store review times** (outside our control): Google Play approval is usually
hours-to-a-day, Huawei 1–2 days, Apple typically 1–3 days. These run after submission in
Phase 5.

---

## 8. Recommendation

Proceed with the **Flutter + Supabase + OpenStreetMap** build as a **pilot in one area**,
published to **all three stores**. It is low-cost (≈ $0/month to run), low-maintenance
(no server), works on Android/iPhone/Huawei, and the collected data feeds existing
research tools. If the pilot succeeds, the natural next steps are **offline reporting**
and a **moderation/admin dashboard**.

---

## 9. Android-first budget (Malaysia, RM)

To keep the first release cheap and simple, we build and publish the **Android version
first** (Google Play). This avoids Apple's yearly fee and the need for a Mac. Huawei can
be added later at almost no extra cost; iPhone is the only path that adds a recurring fee.

All figures are in **Malaysian Ringgit (RM)**, except the Google Play fee which is charged
in **USD 25** (≈ RM 118 one-time). Two scenarios are shown: **Lean** (built by a student
developer, do-it-yourself graphics) and **Typical** (built by a freelance developer with
some design polish).

### One-time cost

| Item | Lean (student dev) | Typical (freelancer) | Notes |
|---|---|---|---|
| Test phone — **Samsung Galaxy A07 LTE × 1** | **RM 699** | **RM 699** | Price per Samsung Malaysia website. Has the GPS + camera the app needs. |
| Google Play developer account | **USD 25** (≈ RM 118) | **USD 25** (≈ RM 118) | One-time, lifetime. |
| App icon / store graphics | RM 0 (DIY) | ~RM 300 | Can be made free; small budget buys a cleaner look. |
| Privacy-policy hosting | RM 0 | RM 0 | Required by Play — hosted free (e.g. GitHub Pages). |
| Developer's computer | RM 0 | RM 0 | Existing Mac/PC; Android needs no special hardware. |
| **Developer time** ⭐ | ~RM 1,500 | ~RM 3,600 | The main cost — see breakdown below. |
| **One-time total** | **≈ RM 2,300 + USD 25** | **≈ RM 4,600 + USD 25** | |

### Ongoing (monthly) running cost

| Item | Pilot cost | Notes |
|---|---|---|
| Supabase backend | **RM 0 / month** | Free tier covers a pilot. |
| Map tiles (OpenStreetMap) | **RM 0 / month** | Free at pilot volumes. |
| **Monthly total** | **≈ RM 0 / month** | Only grows (≈ USD 25/mo ≈ RM 118/mo for Supabase Pro) if usage exceeds the free tier. |

### Developer-time breakdown
- **Effort:** ~50–70 hours for a polished, tested, **published** Android app (AI-assisted,
  Android-only scope).
- **Rate:** ~RM 25/hr (student RA) → ≈ RM 1,500; ~RM 60/hr (junior freelancer) → ≈ RM 3,600.
- If the developer is an existing paid research assistant, this is **time already budgeted**,
  not new spending.

### Bottom line
- **Cash outlay to ship Android (excluding labour):** ≈ **RM 700–1,100 + USD 25** one-time,
  then ≈ **RM 0/month**.
- **All-in including labour:** ≈ **RM 2,300 (lean) to RM 4,600 (typical) + USD 25** one-time.
- **Adding Huawei later:** ≈ RM 0 (free account); only an optional second test phone if you
  want to verify on Huawei hardware.
- **Adding iPhone later:** this is what introduces the **USD 99/year** Apple fee.

---

*This document is the agreed design. The next step is a detailed implementation plan
(task-by-task build order) for the developer.*
