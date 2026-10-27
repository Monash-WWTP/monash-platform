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

Protocol revision2 adds optional flooding movement and owned-report follow-ups, plus private camera/gallery provenance. Follow-ups reuse the selected point without old GPS accuracy; changed points become ordinary reports. New context activates only when advertised by the API. See [protocol operations](../../docs/operations/citizen-observation-protocol.md); citizen observations remain separate from laboratory measurements and simulation inputs.

## Reported-depth AR (source feature; device acceptance pending)

For a water reading expressed as depth in metres above a described surface,
choose **Preview depth in AR** in the form or **Visualise reported depth** in
an owned report. The preview uses the existing value; it never measures water,
changes the reading or predicts flooding. Gauge stages, qualitative and
unstructured legacy reports are excluded. Saved reports show their observation
time, or explicitly state that it is unavailable.

On compatible Android phones, optional Google Play Services for AR setup and
camera access occur only on entry. Scan a safe, visible horizontal reference,
tap it, and confirm it matches the described surface. A bounded 3 m patch and
10 cm ruler ticks illustrate the depth. Reset if the reference drifts. Do not
enter floodwater; skip AR when the reference cannot be identified safely.
The selected surface is manual, not geographically registered to the report.
Historical reports are illustrated in the current scene, not reconstructed.

Native Kotlin uses pinned ARCore 1.57.0 and OpenGL ES. Environment-depth
occlusion is used when supported and a current depth image is available;
otherwise the screen explicitly identifies a simplified preview. Unsupported
phones and permission refusal retain normal reporting. Camera/depth frames
are not uploaded by this feature, and synthetic views cannot be attached as
report evidence. No new backend schema or cloud AR API is used.

Before public release, record physical-device evidence for depth and non-depth
ARCore phones, installation/permission refusal, no visible reference, tracking
loss/recovery, reset, background/resume, rotation, large text, reference-height
checks and sustained thermal/performance behaviour. Automated builds and
shader checks do not establish physical alignment or scientific accuracy.
