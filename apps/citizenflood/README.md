# CitizenFlood

Flutter mobile app for citizen flood, rain, water-level and wastewater observations. The native client uses the shared FastAPI service and external-browser OIDC with PKCE. Refresh credentials are held in Android secure storage.

Use Flutter 3.44.7, an Android SDK and JDK 17. From this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter build apk --debug --dart-define-from-file=staging-config.example.json
test -s build/app/outputs/flutter-apk/app-debug.apk
```

For an operational development run, copy `env.example.json` to ignored `env.json`, supply an approved development project's URL and publishable key, then run `./scripts/run.sh`. Database authorization depends on legacy RLS policies. Never put a service-role key in the app. Synthetic CI values are for build checks only.

Release builds now require the project signing identity; debug signing is never a release fallback. The public signed Android release uses the existing live backend. The commands above are isolated CI compilation checks and must not produce a public distributable. See [direct release and signing custody](../../docs/operations/android-direct-release.md). iOS scaffolding is absent from the pinned source. See [toolchains](../../docs/operations/toolchains.md), [migration](../../docs/migration/ROADMAP.md), and [architecture](../../docs/architecture/README.md).
