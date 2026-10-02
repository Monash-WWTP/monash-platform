# Verified local toolchains

The CitizenFlood import was checked on 2026-10-02 using the official Flutter
3.44.7 stable Linux SDK (framework revision `84fc5cbb22`, Dart 3.12.2,
DevTools 2.57.0). Its release archive SHA-256 was verified against Flutter's
release index: `a0edd646c159c0e816788c0e46a4f071199c1320495898f5a679599b583a05a4`.
The local Android SDK has platforms 35 and 36 and build-tools 36.0.0. The
local JDK is Android Studio's JBR 25.0.3; CI uses Temurin 17.

Mobile verification commands from `apps/citizenflood`:

```sh
flutter pub get
flutter analyze
flutter test
flutter build apk --debug \
  --dart-define=SUPABASE_URL=https://example.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=synthetic-ci-key
test -s build/app/outputs/flutter-apk/app-debug.apk
```

Synthetic values are only for a build check; the resulting APK is not an
operational client. Do not use production signing keys or credentials in CI.

## API, dashboard and research

Local tooling: uv 0.12.1, Python 3.12, Node v22.22.1, npm 9.2.0, PostgreSQL 16. Optional research plotting resolves to matplotlib 3.11.2 in the root lock. CI's toolchain configuration is committed; GitHub CI has not run before remote creation.

The dashboard production map smoke was run using Playwright 1.63.0 and Chrome 154.0.8037.92. It intercepts application services with synthetic fixtures and blocks external requests. Start the built dashboard using `npm --prefix apps/dashboard run preview -- --host 127.0.0.1 --port 5174`, then run:

```sh
uv run --with playwright==1.63.0 python scripts/smoke_dashboard_map.py --url http://127.0.0.1:5174 --browser-executable /usr/bin/google-chrome
```

Alternatively install Playwright's Chromium with `uv run --with playwright==1.63.0 playwright install chromium` and omit the executable flag. This focused check verifies canvas/worker initialization and attribution sanitization; live login, media upload and full user journeys remain release QA gates.

Mobile build warnings remain for the inherited package_info_plus Kotlin Gradle plugin and mismatched local Android SDK XML tooling. They did not prevent the debug APK. Recheck plugin compatibility when advancing Flutter. CodeGraph was initialized locally; its generated index is ignored. Use `codegraph init --yes` only when indexing a fresh checkout is intended.
