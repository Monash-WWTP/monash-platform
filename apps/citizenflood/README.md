# CitizenFlood

Flutter mobile app for citizen flood, rain, water-level and wastewater observations. The native client uses the shared FastAPI service and external-browser OIDC with PKCE. Refresh credentials are held in Android secure storage.

Use Flutter 3.44.7, an Android SDK and JDK 21. From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define-from-file=staging-config.example.json
test -s build/app/outputs/flutter-apk/app-debug.apk
```

The app opens on Map. The green + menu offers Flooding, Rain, Water appearance and Add measurement. Confirm a map point or use current location, complete the form, then review before submitting. Visual reports include an explicit Unsure answer. Optional measurements require their interval, reference or instrument context. New forms require the service to advertise citizen-observation revision1; they do not silently submit ambiguous legacy fields. My reports shows owner-only history and review status; public map locations remain approximate. Native MapLibre uses the dashboard’s OpenFreeMap Liberty style.

For USB testing with the checked-in local staging config, run `adb reverse tcp:8181 tcp:8181` and `adb reverse tcp:9100 tcp:9100` with the local API and identity services running. See [Samsung acceptance evidence](../../docs/operations/samsung-mobile-acceptance-2026-10-20.md).

For an operational development run, copy `staging-config.example.json` to ignored `env.json` and supply approved `API_BASE_URL`, `OIDC_ISSUER`, `OIDC_DISCOVERY_URL` and public `OIDC_CLIENT_ID` values, then run `./scripts/run.sh`. HTTPS is required except explicitly enabled loopback local staging. On a physical device, localhost is the device itself. Server capabilities enforce authorization; do not bundle a client secret or service-role key. The old Supabase `env.example.json` is retained as a legacy reference and does not configure the current client. Synthetic CI values are for build checks only.

Release builds now require the project signing identity; debug signing is never a release fallback. The public signed Android release uses the existing live backend. The commands above are isolated CI compilation checks and must not produce a public distributable. See [direct release and signing custody](../../docs/operations/android-direct-release.md). iOS scaffolding is absent from the pinned source. See [toolchains](../../docs/operations/toolchains.md), [migration](../../docs/migration/ROADMAP.md), and [architecture](../../docs/architecture/README.md).

See the [platform manual](https://monash-platform-docs.vercel.app) for Android setup, reporting, privacy and release gates.
